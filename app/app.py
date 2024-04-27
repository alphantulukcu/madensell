from flask import Flask, jsonify
import os
from datetime import datetime, date
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import errorcode
from flask import Flask, render_template, request, redirect, url_for, session, flash
import firebase_admin
from firebase_admin import credentials, storage

cred = credentials.Certificate("app/madensell-dc0c4-firebase-adminsdk-e1l49-c41a93f84c.json")
app1 = firebase_admin.initialize_app(cred, {
    'storageBucket': 'madensell-dc0c4.appspot.com'
})


app = Flask(__name__)


# Obtain connection string information from the portal

config = {
  'host':'madensell.mysql.database.azure.com',
  'user':'fackd',
  'password':'Konur123',
  'database':'madensell'
}
app.secret_key = 'alphan'  # Replace with a unique and secret key

def delete_picture(pic_url):
    bucket = storage.bucket()

    # Assuming pic_url is the full URL to the object and needs parsing to get the exact path
    parts = pic_url.split('madensell-dc0c4.appspot.com/')
    desired_part = parts[-1] if len(parts) > 1 else parts[0]

    blob = bucket.blob(desired_part)
    try:
        blob.delete()
        return True
    except Exception as e:
        print(f"Failed to delete: {e}")
        return False


def add_picture(pic, userid):

    # set the storage bucket to add the image to

    bucket = storage.bucket()

    # sets the location and image name
    # if you need to store inside a folder use the following
    blob = bucket.blob(str(userid) + "/" + pic.filename)
    #blob = bucket.blob(pic.filename)
    
    # uploads the image
    blob.upload_from_string(pic.read(), content_type=pic.content_type)

    # makes the image's url public so it can be viewed by anyone
    # this can be configured for more advance features dealing with auth
    blob.make_public()

    # returns url
    url = blob.public_url
    return url

@app.route('/')


@app.route('/login', methods =['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        print(username)
        password = request.form['password']
        print(password)
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user[0]
            session['username'] = user[1]
            session['user_type'] = user[5]
            return redirect(url_for('profile'))
        else:
            message = 'Please enter correct email / password !' + username + password
    return render_template('login.html', message=message, message_type='error')


@app.route("/customer-register", methods=["POST", "GET"])
def customer_register():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        email = request.form['email']
        username = request.form['username']
        first_name = request.form['first_name'].title()
        last_name = request.form['last_name'].title()
        password = request.form['password']
        phone = request.form['phone']
        address = request.form['address']
        
        pp_path = "https://storage.googleapis.com/madensell-dc0c4.appspot.com//default.png"
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        user_exists = account is not None
        if user_exists:
            message = "Email already exists"
            return render_template('register_customer.html', message=message, message_type='error')
        else:
            cursor.execute('INSERT INTO users(username, email, password, user_type, address, phone_number) VALUES (%s, %s, %s, %s, %s, %s)',(username, email, password, 1, address, phone))
            conn.commit()
            cursor.execute('SELECT user_id FROM users u WHERE u.email = %s AND u.password = %s', (email, password))
            user_id = cursor.fetchone()
            user_id = user_id[0]
            cursor.execute(
                """   
                                INSERT INTO customer(user_id, first_name, last_name, profile_image)
                                VALUES (%s, %s, %s, %s);
                            """,
                (user_id, first_name, last_name, pp_path))
            conn.commit()
            cursor.execute(
                'SELECT * FROM users u, customer c WHERE c.user_id = u.user_id AND u.email = %s AND u.password = %s',
                (email, password))
            message = 'You have successfully registered!'
            return render_template('login.html', message=message, message_type='success')
    return render_template('register_customer.html', message=message, message_type='error')

@app.route("/business-register", methods=["POST", "GET"])
def business_register():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        email = request.form['email']
        username = request.form['username']
        business_name = request.form['business_name'].title()
        password = request.form['password']
        phone = request.form['phone']
        address = request.form['address']
        # Validate birthdate
        min_date = date(1920, 1, 1)
        max_date = date.today()

        pp_path = "https://storage.googleapis.com/madensell-dc0c4.appspot.com//default.png"
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        user_exists = account is not None
        if user_exists:
            message = "Email already exists"
            return render_template('register_business.html', message=message)
        else:
            cursor.execute('INSERT INTO users(username, email, password, user_type, address, phone_number) VALUES (%s, %s, %s, %s, %s, %s)',(username, email, password, 2, address, phone))
            conn.commit()
            cursor.execute('SELECT user_id FROM users u WHERE u.email = %s AND u.password = %s', (email, password))
            user_id = cursor.fetchone()
            user_id = user_id[0]
            cursor.execute(
                """   
                                INSERT INTO business(user_id, business_name, overall_point, profile_image)
                                VALUES (%s, %s, %s, %s);
                            """,
                (user_id, business_name, 0, pp_path))
            conn.commit()
            cursor.execute(
                'SELECT * FROM users u, business b WHERE b.user_id = u.user_id AND u.email = %s AND u.password = %s',
                (email, password))
            message = 'You have successfully registered!'
            return render_template('login.html', message=message, message_type='success')
    return render_template('register_business.html', message=message, message_type='error')


@app.route("/profile", methods=["POST", "GET"])
def profile():
    if 'loggedin' in session and 'user_type' in session:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        if session['user_type'] == 1:
            if request.method == 'POST':
                status = request.form['status']
                order_id = request.form['order_id']
                cursor.execute(
                    """   
                                UPDATE orders         
                                SET status = %s       
                                WHERE order_id = %s;
                                """,
                    (status, order_id))
                conn.commit()
            cursor.execute(
                'SELECT * FROM users u, customer c WHERE c.user_id = u.user_id AND u.user_id = %s',
                (session['userid'],))
            user = cursor.fetchone()
            customer_id=session['userid']
            cursor.execute('''
                SELECT p.*, b.*, s.*, c.*, MIN(i.image_url) as single_image
                FROM product p
                JOIN business b ON p.business_id = b.user_id
                JOIN subcategory s ON p.subcategory_id = s.subcategory_id
                JOIN category c ON s.category_id = c.category_id
                LEFT JOIN images i ON p.product_id = i.product_id
                JOIN favorites f ON p.product_id = f.product_id
                WHERE f.cust_id = %s
                GROUP BY p.product_id, b.user_id, s.subcategory_id, c.category_id
            ''', (customer_id,))
            favorites = cursor.fetchall()

            cursor.execute('''
              SELECT 
                o.order_id,            -- Order ID
                o.info_id,             -- Shipping Information ID
                o.product_id,          -- Product ID
                o.num_of_products,     -- Number of products ordered
                o.status,              -- Order status
                p.title,               -- Product title
                p.description,         -- Product description
                p.price,               -- Price of the product
                s.subcategory_name, -- Subcategory name
                c.category_name,    -- Category name
                si.address_title,
                si.address,
                si.phone_number,
                si.city,   -- Shipping address from the shipping info
                si.town,   -- Shipping address from the shipping info
                si.postal_code,   -- Shipping address from the shipping info
                MIN(i.image_url) as single_image           -- Image URL for the product
                
            FROM orders o
            JOIN product p ON o.product_id = p.product_id
            JOIN subcategory s ON p.subcategory_id = s.subcategory_id
            JOIN category c ON s.category_id = c.category_id
            LEFT JOIN images i ON p.product_id = i.product_id
            JOIN shipping_info si ON o.info_id = si.info_id
            WHERE si.customer_id = %s
            GROUP BY o.order_id, 
                o.info_id,       
                o.product_id,         
                o.num_of_products,   
                o.status,          
                p.title,             
                p.description,      
                p.price,               
                s.subcategory_name, 
                c.category_name,
                 si.address_title,
                si.address,
                si.phone_number,
                si.city,   -- Shipping address from the shipping info
                si.town,   -- Shipping address from the shipping info
                si.postal_code
            ORDER BY o.order_id DESC

            ''', (customer_id,))
            orders = cursor.fetchall()

            # Separate products with and without images
            products_with_images = [prod for prod in favorites if prod[-1] is not None]
            products_without_images = [prod for prod in favorites if prod[-1] is None]

            if len(favorites) == 0:
                favorites = 'Empty'
            # Pass the account information to render the main page
            return render_template('profile_customer.html', products_with_images=products_with_images, products_without_images=products_without_images, user=user, favorites=favorites, orders=orders)

        elif session['user_type'] == 2:
            if request.method == 'POST':
                status = request.form['status']
                order_id = request.form['order_id']
                cursor.execute(
                    """   
                                UPDATE orders         
                                SET status = %s       
                                WHERE order_id = %s;
                                """,
                    (status, order_id))
                conn.commit()

            cursor.execute(
                'SELECT * FROM users u, business b WHERE b.user_id = u.user_id AND u.user_id = %s',
                (session['userid'],))
            user = cursor.fetchone()
            cursor.execute('''
                SELECT p.*, b.*, s.*, c.*, MIN(i.image_url) as single_image
                FROM product p
                JOIN business b ON p.business_id = b.user_id
                JOIN subcategory s ON p.subcategory_id = s.subcategory_id
                JOIN category c ON s.category_id = c.category_id
                JOIN images i ON p.product_id = i.product_id
                WHERE b.user_id = %s
                AND p.status = 1
                GROUP BY p.product_id, b.user_id, s.subcategory_id, c.category_id
                ''', (session['userid'],))  # Notice the comma to make it a tuple
            products = cursor.fetchall()
            if len(products) == 0:
                products = 'Empty'

            cursor.execute('''
                              SELECT 
                                o.order_id,            -- Order ID
                                o.info_id,             -- Shipping Information ID
                                o.product_id,          -- Product ID
                                o.num_of_products,     -- Number of products ordered
                                o.status,              -- Order status
                                p.title,               -- Product title
                                p.description,         -- Product description
                                p.price,               -- Price of the product
                                s.subcategory_name, -- Subcategory name
                                c.category_name,    -- Category name
                                cu.first_name, 
                                cu.last_name, 
                                cu.profile_image,
                                si.address_title,
                                si.address,
                                si.phone_number,
                                si.city,   -- Shipping address from the shipping info
                                si.town,   -- Shipping address from the shipping info
                                si.postal_code,   -- Shipping address from the shipping info
                                MIN(i.image_url) as single_image           -- Image URL for the product

                            FROM orders o
                            JOIN product p ON o.product_id = p.product_id
                            JOIN subcategory s ON p.subcategory_id = s.subcategory_id
                            JOIN category c ON s.category_id = c.category_id
                            LEFT JOIN images i ON p.product_id = i.product_id
                            JOIN shipping_info si ON o.info_id = si.info_id
                            JOIN customer cu ON cu.user_id = si.customer_id
                            WHERE p.business_id = %s
                            GROUP BY o.order_id, 
                                o.info_id,       
                                o.product_id,         
                                o.num_of_products,   
                                o.status,          
                                p.title,             
                                p.description,      
                                p.price,               
                                s.subcategory_name, 
                                c.category_name,
                                cu.first_name, 
                                cu.last_name, 
                                cu.profile_image,
                                si.address_title,
                                si.address,
                                si.phone_number,
                                si.city,   -- Shipping address from the shipping info
                                si.town,   -- Shipping address from the shipping info
                                si.postal_code
                            ORDER BY o.order_id DESC

                            ''', (session['userid'],))
            orders = cursor.fetchall()
            # Pass the account information to render the main page
            return render_template('profile_business.html', user=user, products=products, orders=orders)
    else:
        # User is not logged in, redirect to login page
        return redirect(url_for('login'))


@app.route("/customer-edit-profile", methods=["POST", "GET"])
def customer_edit_profile():
    if 'loggedin' in session and 'user_type' in session:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM users u, customer c WHERE c.user_id = u.user_id AND u.user_id = %s',
            (session['userid'],))
        user = cursor.fetchone()
        message = ''
        if request.method == 'POST' and 'username' in request.form:
            email = request.form['email']
            username = request.form['username']
            first_name = request.form['first_name'].title()
            last_name = request.form['last_name'].title()
            phone = request.form['phone']
            address = request.form['address']
            profile_image = request.files['profile_pic']
            if profile_image:
                if(user[11] != "https://storage.googleapis.com/madensell-dc0c4.appspot.com//default.png"):
                    delete_picture(user[11])
                profile_image = add_picture(profile_image, user[0])
            else:
                profile_image = user[11]
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            account = cursor.fetchone()
            user_exists = account is not None and user[0] != account[0]
            if user_exists:
                message = "Email already exists"
                return render_template('edit_profile_customer.html', message=message, message_type='error',user=user)
            else:
                #update customer with procedure here
                cursor.callproc('UpdateCustomerProfile', [
                    session['userid'],
                    email,
                    username,
                    first_name,
                    last_name,
                    phone,
                    address, 
                    profile_image
                ])
                conn.commit()  # Commit the transaction
                message = "Profile updated successfully!"
                return render_template('edit_profile_customer.html', message=message, message_type='success', user=user)
        return render_template('edit_profile_customer.html', message=message, message_type='error', user=user)




@app.route("/add-product", methods=["POST", "GET"])
def add_product():
    message = ''
    if 'loggedin' in session and 'user_type' in session:
        if request.method == 'POST':
            title = request.form['post_title']
            description = request.form['post_description']
            category_id = int(request.form['category'])
            subcategory_id = int(request.form['subcategory'])
            stock_num = int(request.form['stock_num'])
            price = request.form['post_price']
            images = request.files.getlist('product_images')  # Corrected here

            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()

            if not any(image.filename for image in images):
                flash('Please upload at least one image', 'error')
                return redirect(url_for('add_product'))

            if len(images) > 3:
                flash('Cannot upload more than 3 images', 'error')
                return redirect(url_for('add_product'))
            
            cursor.execute('INSERT INTO product(business_id, price, title, description, stock_num, subcategory_id ) VALUES (%s, %s, %s, %s, %s, %s)',(session['userid'], price, title, description, stock_num, subcategory_id))
            conn.commit()
            # Get the ID of the newly created product
            product_id = cursor.lastrowid

            for image in images:
                if image:
                    image_url = add_picture(image, session['userid'])
                    cursor.execute('INSERT INTO images(product_id, created_at, image_url) VALUES (%s, %s, %s)', (product_id, datetime.now(), image_url))
                    conn.commit()
                else:
                    # Handle the case when no image is provided
                    pass
            return redirect(url_for('profile'))
        else:
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM users u, business b WHERE b.user_id = u.user_id AND u.user_id = %s',
                (session['userid'],))
            user = cursor.fetchone()

            cursor.execute(
                'SELECT category_id, category_name FROM category',
                ())
            category = cursor.fetchall()
            cursor.execute(
                'SELECT subcategory_id, subcategory_name FROM subcategory',
                ())
            subcategory = cursor.fetchall()
            return render_template('add_product.html', user=user, categories=category, subcategories=subcategory)


@app.route('/logout')
def logout():
    # Remove session data
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('username', None)
    session.pop('user_type', None)
    return redirect(url_for('login'))


def get_products(cursor, category=None, subcategory=None, sort=None, price=None):
    query = '''
        SELECT p.*, b.*, s.*, c.*, MIN(i.image_url) as single_image
        FROM product p
        JOIN business b ON p.business_id = b.user_id
        JOIN subcategory s ON p.subcategory_id = s.subcategory_id
        JOIN category c ON s.category_id = c.category_id
        LEFT JOIN images i ON p.product_id = i.product_id
        WHERE p.status = 1
    '''

    params = []

    if category:
        query += ' AND c.category_id = %s'
        params.append(category)

    if subcategory:
        query += ' AND s.subcategory_id = %s'
        params.append(subcategory)

    if price:
        query += ' AND p.price <= %s'
        params.append(price)

    query += ' GROUP BY p.product_id, b.user_id, s.subcategory_id, c.category_id'

    if sort == 'oldest':
        query += ' ORDER BY p.created_at ASC'
    elif sort == 'newest':
        query += ' ORDER BY p.created_at DESC'
    elif sort == 'price_low':
        query += ' ORDER BY p.price ASC'
    elif sort == 'price_high':
        query += ' ORDER BY p.price DESC'

    cursor.execute(query, params)
    return cursor.fetchall()

@app.route("/market", methods=["POST", "GET"])
def market():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    if request.method == 'POST':
        category_id = request.form.get('post_categories')
        subcategory_id = request.form.get('post_subcategories')
        sort = request.form.get('post_sort')
        products = get_products(cursor, category=category_id, subcategory=subcategory_id, sort=sort)
    else:
        products = get_products(cursor,sort='newest')

    cursor.execute('SELECT category_id, category_name FROM category')
    categories = cursor.fetchall()
    cursor.execute('SELECT subcategory_id, subcategory_name FROM subcategory')
    subcategories = cursor.fetchall()

    # Separate products with and without images
    products_with_images = [prod for prod in products if prod[-1] is not None]
    products_without_images = [prod for prod in products if prod[-1] is None]

    return render_template('market.html', user_type=session['user_type'], products_with_images=products_with_images, products_without_images=products_without_images, categories=categories, subcategories=subcategories)



@app.route("/detail/<int:product_id>/", methods=["POST", "GET"])
def post_detail(product_id):
    message = ''
    if 'loggedin' in session and 'user_type' in session:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        if request.method == 'POST': # comment
            comment = request.form['comment']
            numofproducts = request.form['numofproducts']
            if comment:
                cursor.execute(
                    """   
                                    INSERT INTO comments(product_id, customer_id, comment) 
                                    VALUES (%s,%s,%s)
                                """,
                    (product_id, session['userid'], comment))
                conn.commit()

            elif numofproducts: # add to basket
                numofproducts = int(numofproducts)
                cursor.execute(
                    """   
                                    SELECT basket_id FROM basket where product_id = %s AND customer_id = %s
                                """,
                    (product_id, session['userid'],))
                basket = cursor.fetchone()
                if basket:
                    cursor.execute(
                        """   
                                    UPDATE basket         
                                    SET num_of_products = num_of_products + %s         
                                    WHERE basket_id = %s;
                                    """,
                        (numofproducts, basket[0]))
                    conn.commit()
                else:
                    cursor.execute(
                        """   
                                        INSERT INTO basket(product_id, customer_id, num_of_products) 
                                        VALUES (%s,%s,%s)
                                    """,
                        (product_id, session['userid'], numofproducts))
                    conn.commit()
                return redirect(url_for('basket', product_id=0))


        cursor.execute(
            'SELECT * FROM product p, business b, users u, subcategory s, category c WHERE b.user_id = u.user_id AND p.business_id = b.user_id AND s.subcategory_id = p.subcategory_id AND s.category_id = c.category_id AND p.product_id = %s',
            (product_id,))
        product = cursor.fetchone()

        cursor.execute(
            'SELECT * FROM (comments com NATURAL JOIN customer c) NATURAL JOIN product p WHERE p.product_id = %s AND c.user_id = com.customer_id',
            (product_id,))
        comments = cursor.fetchall()
        
        cursor.execute(
            'SELECT * FROM product p, images s WHERE s.product_id = p.product_id AND p.product_id = %s', 
            (product_id,))
        images = cursor.fetchall()

        return render_template('post_detail.html',user_type=session['user_type'], product=product, comments=comments, images=images)


@app.route("/basket/<int:product_id> ", methods=["POST", "GET"])
def basket(product_id):
    message = ''
    if 'loggedin' in session and 'user_type' in session:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        if request.method == 'POST':
            updated_amount = request.form['numofproducts']
            if int(updated_amount) > 0:
                cursor.execute(
                    """   
                     UPDATE basket         
                      SET num_of_products = %s         
                      WHERE customer_id = %s AND product_id = %s;
                    """,
                    (updated_amount, session['userid'], product_id, ))
                conn.commit()
            else:
                cursor.execute(
                    """   
                     DELETE FROM basket               
                     WHERE customer_id = %s AND product_id = %s;
                    """,
                    (session['userid'], product_id,))
                conn.commit()
        cursor.execute(
            'SELECT * FROM basket b NATURAL JOIN product p WHERE b.customer_id = %s',
            (session['userid'],))
        products = cursor.fetchall()

        cursor.execute(
            'SELECT SUM(p.price * b.num_of_products) FROM basket b NATURAL JOIN product p WHERE b.customer_id = %s',
            (session['userid'],))
        total_sum = cursor.fetchone()[0]
        if total_sum is None:
            total_sum = 0

        return render_template('basket.html', products=products, total_sum=total_sum)


@app.route("/order/<int:type>", methods=["POST", "GET"])
def order(type):
    message = ''
    if 'loggedin' in session and 'user_type' in session:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM users u, customer c WHERE c.user_id = u.user_id AND u.user_id = %s',
            (session['userid'],))
        user = cursor.fetchone()
        if request.method == 'POST':
            if type == 0:
                address_title = request.form['address_title']
                city = request.form['city']
                phone = request.form['phone']
                address = request.form['address']
                town = request.form['town']
                postal_code = request.form['postal_code']
                cursor.execute(
                    """   
                                    INSERT INTO shipping_info(customer_id, phone_number, address_title, address, city, town, postal_code) 
                                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                                """,
                    (session['userid'], phone, address_title, address, city, town, int(postal_code)))
                conn.commit()
            elif type == 1:
                shipping_info = request.form['shipping_info_id']
                cursor.callproc('ProcessOrder', [
                    shipping_info,
                ])
                conn.commit()  # Commit the transaction

                return redirect(url_for('profile'))



        cursor.execute(
            'SELECT * FROM basket b NATURAL JOIN product p WHERE b.customer_id = %s',
            (session['userid'],))
        products = cursor.fetchall()

        cursor.execute(
            'SELECT SUM(p.price * b.num_of_products) FROM basket b NATURAL JOIN product p WHERE b.customer_id = %s',
            (session['userid'],))
        total_sum = cursor.fetchone()[0]
        if total_sum is None:
            total_sum = 0

        cursor.execute(
            'SELECT * FROM wallet  WHERE user_id = %s',
            (session['userid'],))
        wallet = cursor.fetchone()

        cursor.execute(
            'SELECT * FROM shipping_info  WHERE customer_id = %s',
            (session['userid'],))
        shipping_infos = cursor.fetchall()
        if shipping_infos is None:
            shipping_infos = 'Empty'

        return render_template('order.html', shipping_infos=shipping_infos, wallet=wallet, user=user, products=products, total_sum=total_sum)


@app.route('/toggle_favorite/<int:product_id>', methods=['POST'])
def toggle_favorite(product_id):
    # Check if user is logged in
    if 'loggedin' not in session:
        flash('You need to be logged in to favorite items!')
        return redirect(url_for('login'))

    # Get the customer's user ID from the session
    cust_id = session['userid']

    # Open a new database connection
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    # Check if the product is already in the customer's favorites
    cursor.execute('SELECT * FROM favorites WHERE cust_id = %s AND product_id = %s', (cust_id, product_id))
    favorite = cursor.fetchone()

    if favorite:
        # If the product is already in favorites, remove it
        cursor.execute('DELETE FROM favorites WHERE cust_id = %s AND product_id = %s', (cust_id, product_id))
        flash('Item removed from favorites.')
    else:
        # If the product is not in favorites, add it
        cursor.execute('INSERT INTO favorites (cust_id, product_id) VALUES (%s, %s)', (cust_id, product_id))
        flash('Item added to favorites.')

    # Commit changes and close the connection
    conn.commit()
    cursor.close()
    conn.close()

    # Redirect back to the market page
    return redirect(url_for('market'))


@app.route("/wallet", methods=["POST", "GET"])
def wallet():
    if 'loggedin' not in session or 'user_type' not in session:
        return jsonify({"error": "User not logged in"}), 403

    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    if request.method == 'POST':
        insert_amount = request.form.get('insert_amount', type=int)
        if insert_amount and insert_amount > 0:
            cursor.execute("""
                 UPDATE wallet
                 SET balance = balance + %s
                 WHERE user_id = %s;
            """, (insert_amount, session['userid']))
            conn.commit()
            return jsonify({'message': "Amount added successfully!"})
        else:
            return jsonify({'message': "Invalid amount."})

    if session['user_type'] == 2:
        # For GET requests, return wallet info and business details in JSON
        cursor.execute('''
            SELECT w.balance, b.business_name, b.profile_image
            FROM wallet w
            JOIN business b ON b.user_id = w.user_id
            WHERE w.user_id = %s
        ''', (session['userid'],))
        result = cursor.fetchone()
        if result:
            balance, business_name, profile_image = result
            return jsonify({"balance": balance, "name": business_name, "profile_image": profile_image})
        else:
            return jsonify({"error": "Wallet not found"}), 404
    if session['user_type'] == 1:
        cursor.execute('''
            SELECT w.balance, c.first_name, c.last_name, c.profile_image
            FROM wallet w
            JOIN customer c ON c.user_id = w.user_id
            WHERE w.user_id = %s
        ''', (session['userid'],))
        result = cursor.fetchone()
        if result:
            balance, first_name, last_name, profile_image = result
            name = first_name + ' ' + last_name
            return jsonify({"balance": balance, "name": name, "profile_image": profile_image})
        else:
            return jsonify({"error": "Wallet not found"}), 404


@app.route("/business-edit-profile", methods=["POST", "GET"])
def business_edit_profile():
    if 'loggedin' in session and 'user_type' in session:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM users u, business b WHERE b.user_id = u.user_id AND u.user_id = %s',
            (session['userid'],))
        user = cursor.fetchone()
        message = ''
        if request.method == 'POST' and 'username' in request.form:
            email = request.form['email']
            username = request.form['username']
            business_name = request.form['businessname'].title()
            phone = request.form['phone']
            address = request.form['address']
            profile_image = request.files['profile_pic']
            if profile_image:
                if(user[11] != "https://storage.googleapis.com/madensell-dc0c4.appspot.com//default.png"):
                    delete_picture(user[11])
                profile_image = add_picture(profile_image, user[0])
            else:
                profile_image = user[11]
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            account = cursor.fetchone()
            user_exists = account is not None and user[0] != account[0]
            if user_exists:
                message = "Email already exists"
                return render_template('edit_profile_customer.html', message=message, message_type='error',user=user)
            else:
                #update customer with procedure here
                cursor.callproc('UpdateBusinessProfile', [
                    session['userid'],
                    email,
                    username,
                    business_name,
                    phone,
                    address, 
                    profile_image
                ])
                conn.commit()  # Commit the transaction
                message = "Profile updated successfully!"
                return render_template('edit_profile_business.html', message=message, message_type='success', user=user)
        return render_template('edit_profile_business.html', message=message, message_type='error', user=user)


@app.route('/api/monthly-stats')
def get_monthly_stats():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    # Query to count orders per month for a specific business
    orders_query = """
    SELECT 
        DATE_FORMAT(o.created_at, '%Y-%m') AS month,
        COUNT(*) AS OrderNum
    FROM 
        orders o
    JOIN 
        product p ON o.product_id = p.product_id
    WHERE 
        p.business_id = %s
    GROUP BY 
        month
    ORDER BY 
        month DESC;
    """

    # Query to count favorites per month for a specific business
    favorites_query = """
    SELECT 
        DATE_FORMAT(f.created_at, '%Y-%m') AS month,
        COUNT(*) AS FavoritesNum
    FROM 
        favorites f
    JOIN 
        product p ON f.product_id = p.product_id
    WHERE 
        p.business_id = %s
    GROUP BY 
        month
    ORDER BY 
        month DESC;
    """

    # Execute orders query
    cursor.execute(orders_query, (session['userid'],))
    orders_result = cursor.fetchall()

    # Execute favorites query
    cursor.execute(favorites_query, (session['userid'],))
    favorites_result = cursor.fetchall()

    # Combine results
    stats = {}
    for row in orders_result:
        month, order_num = row
        if month not in stats:
            stats[month] = {'Month': datetime.strptime(month, '%Y-%m').strftime('%b %Y'), 'OrderNum': order_num,
                            'FavoritesNum': 0}
        else:
            stats[month]['OrderNum'] = order_num

    for row in favorites_result:
        month, favorites_num = row
        if month not in stats:
            stats[month] = {'Month': datetime.strptime(month, '%Y-%m').strftime('%b %Y'), 'OrderNum': 0,
                            'FavoritesNum': favorites_num}
        else:
            stats[month]['FavoritesNum'] = favorites_num

    cursor.close()
    conn.close()
    return jsonify(list(stats.values()))


@app.route('/api/daily-stats')
def get_daily_stats():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    # Execute orders query
    orders_query = """
    SELECT 
        DATE(o.created_at) AS date,
        COUNT(*) AS OrderNum
    FROM 
        orders o
    JOIN 
        product p ON o.product_id = p.product_id
    WHERE 
        p.business_id = %s
    GROUP BY 
        date
    ORDER BY 
        date DESC;
    """
    cursor.execute(orders_query, (session['userid'],))
    orders_result = cursor.fetchall()

    # Execute favorites query
    favorites_query = """
    SELECT 
        DATE(f.created_at) AS date,
        COUNT(*) AS FavoritesNum
    FROM 
        favorites f
    JOIN 
        product p ON f.product_id = p.product_id
    WHERE 
        p.business_id = %s
    GROUP BY 
        date
    ORDER BY 
        date DESC;
    """
    cursor.execute(favorites_query, (session['userid'],))
    favorites_result = cursor.fetchall()

    # Combine results
    stats = {}
    for date, order_num in orders_result:
        if date not in stats:
            stats[date] = {'Date': date, 'OrderNum': order_num, 'FavoritesNum': 0}
        else:
            stats[date]['OrderNum'] = order_num

    for date, favorites_num in favorites_result:
        if date not in stats:
            stats[date] = {'Date': date, 'OrderNum': 0, 'FavoritesNum': favorites_num}
        else:
            stats[date]['FavoritesNum'] = favorites_num

    cursor.close()
    conn.close()
    return jsonify(list(stats.values()))

@app.route('/api/weekly-stats')
def get_weekly_stats():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    # Execute orders query
    orders_query = """
    SELECT 
        YEAR(o.created_at) AS year,
        WEEK(o.created_at, 1) AS week,
        COUNT(*) AS OrderNum
    FROM 
        orders o
    JOIN 
        product p ON o.product_id = p.product_id
    WHERE 
        p.business_id = %s
    GROUP BY 
        year, week
    ORDER BY 
        year DESC, week DESC;
    """
    cursor.execute(orders_query, (session['userid'],))
    orders_result = cursor.fetchall()

    # Execute favorites query
    favorites_query = """
    SELECT 
        YEAR(f.created_at) AS year,
        WEEK(f.created_at, 1) AS week,
        COUNT(*) AS FavoritesNum
    FROM 
        favorites f
    JOIN 
        product p ON f.product_id = p.product_id
    WHERE 
        p.business_id = %s
    GROUP BY 
        year, week
    ORDER BY 
        year DESC, week DESC;
    """
    cursor.execute(favorites_query, (session['userid'],))
    favorites_result = cursor.fetchall()

    # Combine results
    stats = {}
    for year, week, order_num in orders_result:
        key = f'{year}-W{week}'
        if key not in stats:
            stats[key] = {'Year-Week': key, 'OrderNum': order_num, 'FavoritesNum': 0}
        else:
            stats[key]['OrderNum'] = order_num

    for year, week, favorites_num in favorites_result:
        key = f'{year}-W{week}'
        if key not in stats:
            stats[key] = {'Year-Week': key, 'OrderNum': 0, 'FavoritesNum': favorites_num}
        else:
            stats[key]['FavoritesNum'] = favorites_num

    cursor.close()
    conn.close()
    return jsonify(list(stats.values()))


@app.route('/stats', methods=['GET'])
def stats():
    if 'loggedin' in session and 'user_type' in session:
        return render_template('stats.html')


if __name__ == "__main__":
    port = int(os.environ.get('PORT',8000))
    app.run(debug=True, host='0.0.0.0', port=port)
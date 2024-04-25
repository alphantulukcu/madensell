from flask import Flask
import os
from datetime import datetime, date
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import errorcode
from flask import Flask, render_template, request, redirect, url_for, session, flash
import firebase_admin
from firebase_admin import credentials, storage

cred = credentials.Certificate("madensell-dc0c4-firebase-adminsdk-e1l49-c41a93f84c.json")
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
    return render_template('login.html', message=message)


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

        pp_path = os.path.join('static', 'default.png')
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        user_exists = account is not None
        if user_exists:
            message = "Email already exists"
            return render_template('register_customer.html', message=message)
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
            return redirect(url_for('login'))
    return render_template('register_customer.html', message=message)

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

        pp_path = os.path.join('static', 'default.png')
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
            return redirect(url_for('login'))
    return render_template('register_business.html', message=message)


@app.route("/profile", methods=["POST", "GET"])
def profile():
    if 'loggedin' in session and 'user_type' in session:
            if session['user_type'] == 1:
                conn = mysql.connector.connect(**config)
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM users u, customer c WHERE c.user_id = u.user_id AND u.user_id = %s',
                    (session['userid'],))
                user = cursor.fetchone()
                cursor.execute(
                    'SELECT p.price, p.description FROM favorites f, customer c, product p WHERE f.cust_id = c.user_id AND f.product_id = p.product_id AND c.user_id = %s',
                    (session['userid'],))
                favorites = cursor.fetchall()
                if len(favorites) == 0:
                    favorites = 'Empty'
                # Pass the account information to render the main page
                return render_template('profile_customer.html', user=user, favorites=favorites)

            elif session['user_type'] == 2:
                conn = mysql.connector.connect(**config)
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM users u, business b WHERE b.user_id = u.user_id AND u.user_id = %s',
                    (session['userid'],))
                user = cursor.fetchone()
                cursor.execute(
                    'SELECT * FROM product p, business b, subcategory s, category c WHERE p.business_id = b.user_id AND s.subcategory_id = p.subcategory_id AND s.category_id = c.category_id AND b.user_id = %s',
                    (session['userid'],))
                products = cursor.fetchall()
                if len(products) == 0:
                    products = 'Empty'
                # Pass the account information to render the main page
                return render_template('profile_business.html', user=user, products=products)
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
                return render_template('edit_profile_customer.html', message=message)
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
                return redirect(url_for('profile'))
        return render_template('edit_profile_customer.html', user=user)




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

            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO product(business_id, price, title, description, stock_num, subcategory_id ) VALUES (%s, %s, %s, %s, %s, %s)',(session['userid'], price, title, description, stock_num, subcategory_id))
            conn.commit()
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



@app.route("/market", methods=["POST", "GET"])
def market():
    message = ''
    if 'loggedin' in session and 'user_type' in session:
        if request.method == 'POST':
            category_id = int(request.form['post_categories'])
            subcategory_id = int(request.form['post_subcategories'])
            sort = request.form['post_sort']

        else:
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT category_id, category_name FROM category',
                ())
            category = cursor.fetchall()
            cursor.execute(
                'SELECT subcategory_id, subcategory_name FROM subcategory',
                ())
            subcategory = cursor.fetchall()
            cursor.execute(
                'SELECT * FROM product p, business b, subcategory s, category c WHERE p.business_id = b.user_id AND s.subcategory_id = p.subcategory_id AND s.category_id = c.category_id',
                ())
            products = cursor.fetchall()

            return render_template('market.html', products=products, categories=category, subcategories=subcategory)


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

        return render_template('post_detail.html', product=product, comments=comments)


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

        return render_template('basket.html', products=products, total_sum=total_sum)


if __name__ == "__main__":
    port = int(os.environ.get('PORT',8000))
    app.run(debug=True, host='0.0.0.0', port=port)
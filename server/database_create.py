import os
import mysql.connector
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# MySQL credentials
config = {
  'host':'madensell.mysql.database.azure.com',
  'user':'fackd',
  'password':'Konur123',
  'database':'madensell',
  'client_flags': [mysql.connector.ClientFlag.SSL],
  'ssl_ca': 'DigiCertGlobalRootG2.crt.pem'
}


def create_tables():
    connection = mysql.connector.connect(**config)
    run_sql_file('/Users/alphantulukcu/Desktop/CS353/madensell/server/tables.sql', connection)
    cursor = connection.cursor()
    cursor.execute(
        """ CREATE PROCEDURE IF NOT EXISTS UpdateCustomerProfile(
                IN p_user_id INT,
                IN p_email VARCHAR(50),
                IN p_username VARCHAR(20),
                IN p_first_name VARCHAR(20),
                IN p_last_name VARCHAR(20),
                IN p_phone VARCHAR(255),
                IN p_address VARCHAR(255),
                IN p_profile_image VARCHAR(255)
            )
            BEGIN
                DECLARE v_email VARCHAR(50);
                DECLARE v_username VARCHAR(20);
                DECLARE v_first_name VARCHAR(20);
                DECLARE v_last_name VARCHAR(20);
                DECLARE v_phone VARCHAR(255);
                DECLARE v_address VARCHAR(255);
                DECLARE v_profile_image VARCHAR(255);
            
                SELECT u.email, u.username, c.first_name, c.last_name, u.phone_number, u.address, c.profile_image  
                INTO v_email, v_username, v_first_name, v_last_name,  v_phone, v_address, v_profile_image
                FROM users u NATURAL JOIN customer c
                WHERE u.user_id = p_user_id;
            
                IF p_email != v_email THEN
                    UPDATE users SET email = p_email WHERE user_id = p_user_id;
                END IF;
            
                IF p_username != v_username THEN
                    UPDATE users SET username = p_username WHERE user_id = p_user_id;
                END IF;
            
                IF p_first_name != v_first_name THEN
                    UPDATE customer SET first_name = p_first_name WHERE user_id = p_user_id;
                END IF;
            
                IF p_last_name != v_last_name THEN
                    UPDATE customer SET last_name = p_last_name WHERE user_id = p_user_id;
                END IF;
                        
                IF p_phone != v_phone THEN
                    UPDATE users SET phone_number = p_phone WHERE user_id = p_user_id;
                END IF;
            
                IF p_address != v_address THEN
                    UPDATE users SET address = p_address WHERE user_id = p_user_id;
                END IF;

                IF p_profile_image != v_profile_image THEN
                    UPDATE customer SET profile_image = p_profile_image WHERE user_id = p_user_id;
                END IF;
            END
            """)  # Include the whole procedure creation statement here.

    cursor.execute(
        """CREATE PROCEDURE IF NOT EXISTS ProcessOrder(IN input_info_id INT)
                BEGIN
                    DECLARE v_customer_id INT;
                    DECLARE v_business_id INT;
                    DECLARE total_cost INT DEFAULT 0;
                
                    START TRANSACTION;
                
                        -- Retrieve customer ID from shipping_info using the input info_id
                        SELECT s.customer_id INTO v_customer_id FROM shipping_info s WHERE s.info_id = input_info_id;
                
                        -- Calculate the total cost of all products in the customer's basket
                        SELECT SUM(p.price * b.num_of_products) INTO total_cost
                        FROM basket b
                        JOIN product p ON b.product_id = p.product_id
                        WHERE b.customer_id = v_customer_id;
                
                        -- Insert order details into orders table from the basket
                        INSERT INTO orders (info_id, product_id, num_of_products, status)
                        SELECT input_info_id, product_id, num_of_products, 1
                        FROM basket
                        WHERE customer_id = v_customer_id;
                
                        -- Update the product stock based on the basket content
                        UPDATE product p
                        JOIN basket b ON p.product_id = b.product_id
                        SET p.stock_num = p.stock_num - b.num_of_products
                        WHERE b.customer_id = v_customer_id;
                
                        -- Deduct the total cost from the customer's wallet
                        UPDATE wallet
                        SET balance = balance - total_cost
                        WHERE user_id = v_customer_id;
                
                        -- Update business wallet balances based on products sold
                        UPDATE wallet w
                        JOIN (
                            SELECT p.business_id, SUM(p.price * b.num_of_products) AS revenue
                            FROM basket b
                            JOIN product p ON b.product_id = p.product_id
                            WHERE b.customer_id = v_customer_id
                            GROUP BY p.business_id
                        ) AS business_revenue ON w.user_id = business_revenue.business_id
                        SET w.balance = w.balance + business_revenue.revenue;
                
                        -- Clear the customer's basket after processing the order
                        DELETE FROM basket WHERE customer_id = v_customer_id;
                
                    COMMIT;
                END

    """
    )

    cursor.execute(
        """ CREATE PROCEDURE IF NOT EXISTS UpdateBusinessProfile(
            IN p_user_id INT,
            IN p_email VARCHAR(50),
            IN p_username VARCHAR(20),
            IN p_business_name VARCHAR(20),
            IN p_phone VARCHAR(255),
            IN p_address VARCHAR(255),
            IN p_profile_image VARCHAR(255)
        )
        BEGIN
            DECLARE v_email VARCHAR(50);
            DECLARE v_username VARCHAR(20);
            DECLARE v_business_name VARCHAR(20);
            DECLARE v_phone VARCHAR(255);
            DECLARE v_address VARCHAR(255);
            DECLARE v_profile_image VARCHAR(255);

            SELECT u.email, u.username, b.business_name, u.phone_number, u.address, b.profile_image  
            INTO v_email, v_username, v_business_name,  v_phone, v_address, v_profile_image
            FROM users u NATURAL JOIN business b
            WHERE u.user_id = p_user_id;

            IF p_email != v_email THEN
                UPDATE users SET email = p_email WHERE user_id = p_user_id;
            END IF;

            IF p_username != v_username THEN
                UPDATE users SET username = p_username WHERE user_id = p_user_id;
            END IF;

            IF p_business_name != v_business_name THEN
                UPDATE business SET business_name = p_business_name WHERE user_id = p_user_id;
            END IF;

            IF p_phone != v_phone THEN
                UPDATE users SET phone_number = p_phone WHERE user_id = p_user_id;
            END IF;

            IF p_address != v_address THEN
                UPDATE users SET address = p_address WHERE user_id = p_user_id;
            END IF;

            IF p_profile_image != v_profile_image THEN
                UPDATE business SET profile_image = p_profile_image WHERE user_id = p_user_id;
            END IF;
        END
        """)

    cursor.execute(
        """ 
        CREATE TRIGGER IF NOT EXISTS update_business_point
            AFTER INSERT ON review
            FOR EACH ROW
            BEGIN
                DECLARE new_average DECIMAL(10,2);
                DECLARE related_business_id INT;
            
                -- Retrieve the business_id directly from the inserted product
                SELECT p.business_id INTO related_business_id
                FROM product p
                WHERE p.product_id = NEW.product_id;
            
                -- Ensure the business_id was successfully retrieved
                IF related_business_id IS NOT NULL THEN
            
                    -- Calculate the new average points for the business based on all reviews of its products
                    SELECT IFNULL(AVG(r.avg_point), 0) INTO new_average
                    FROM review r
                    JOIN product p ON r.product_id = p.product_id
                    WHERE p.business_id = related_business_id;
            
                    -- Update the business's overall point with the new average
                    UPDATE business
                    SET overall_point = new_average
                    WHERE user_id = related_business_id;
            
                END IF;
            END;
        """)
    print('Tables created')
    connection.commit()
    connection.close()


def run_sql_file(file_path, connection):
    with open(file_path, 'r') as file:
        sql_commands = file.read().split(';')
        for command in sql_commands:
            if command.strip():  # Ignore empty lines and spaces
                connection.cursor().execute(command)


if __name__ == '__main__':
    create_tables()
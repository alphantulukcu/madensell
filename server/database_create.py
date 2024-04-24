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
        """ CREATE PROCEDURE UpdateCustomerProfile(
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
            
                SELECT u.email, u.username, c.first_name, c.last_name, u.phone_number, u.address,  
                INTO v_email, v_username, v_first_name, v_last_name,  v_phone, v_address, 
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
                    UPDATE users SET profile_image = p_profile_image WHERE user_id = p_user_id;
                END IF;
            END
            """)  # Include the whole procedure creation statement here.

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
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
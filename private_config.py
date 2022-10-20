SECRET_KEY = b'123'
DATABASE_NAME = 'bf_analytics'
DATABASE_USER = 'postgres'
DATABASE_USER_PASSWORD = '123'
SQLALCHEMY_DATABASE_URI = 'postgresql://{db_user}:{db_password}@localhost/{db_name}'\
    .format(db_user=DATABASE_USER, db_password=DATABASE_USER_PASSWORD, db_name=DATABASE_NAME)

DATA_API_KEYS = ['123', '456']
COVALENT_API_KEY = 'ckey_2eb7d408bb564e14bbc0b38b09a'
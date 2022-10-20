# Babelfish Analytics Dashboard

Analytics Dashboard visualizes Babelfish data in a user-friendly way.

## API usage

API allows you to receive protocol data via HTTP and complies with REST rules.

### Request format

http(s)://[bf_analytics_site].[tld]/api/[endpoint]/[parameters]

### Endpoints:

* /api/balances/ - Returns time series of the balance (composition) of a basket of stablecoins.
* /api/net_deposits/ - Returns time series of net deposits.
* /api/wallets/unique/ - Returns time series of unique wallets.
* /api/wallets/active/ - Returns time series of active wallets.
* /api/all/ - Returns all the above in one JSON-response.

### Parameters
#### Optional
* start-date - date in ISO format, e.g. '2021-08-01'
* end-date - date in ISO format, e.g. '2021-08-15'
* limit - integer, limits the number of records in the response, e.g. '10'
* order - sets the order of records in the response, 'asc' or 'desc' only
#### Required
* api-key


## Deployment notes

1. Clone the project from git repository.

2. Set up virtual environment and don't forget to install all requirements:
```bash
pip install -r requirements.txt
```

3. Create a file 'private_config.py' in 'bf_analytics_app' folder with the following content:
```python
DATABASE_NAME = '***'
DATABASE_USER = '***'
DATABASE_USER_PASSWORD = '***'
SQLALCHEMY_DATABASE_URI = 'postgresql://{db_user}:{db_password}@localhost/{db_name}'\
    .format(db_user=DATABASE_USER, db_password=DATABASE_USER_PASSWORD, db_name=DATABASE_NAME)

DATA_API_KEYS = ['***', '***']
COVALENT_API_KEY = '***'
```
Replace *** with appropriate values.

4. Set up and start your wsgi server.

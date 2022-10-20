import requests
import json
import datetime
from .helpers import *
from .config import COVALENT as api
from .private_config import COVALENT_API_KEY
api['api_key'] = COVALENT_API_KEY

import traceback
import pprint

from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_result


# TENACITY DECORATORS
def is_none_p(value):
    """Return True if value is None"""
    return value is None

def return_last_value(retry_state):
    """return the result of the last call attempt"""
    return retry_state.outcome.result()



# protects the system from unexpected external data
def data_protector(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exception:
            traceback.print_exc()
            return None
    return wrapper


# items - list of items with date:value
def create_timeseries(items, date_key, value_key):
    timeseries = {}
    for item in items:
        item_date = str(get_datetime_from_string(item[date_key]).date())

        if not item_date in timeseries:
            timeseries[item_date] = item

        if get_datetime_from_string(item[date_key]) > get_datetime_from_string(timeseries[item_date][date_key]):
            timeseries[item_date] = item

    value_timeseries = {}
    for k in timeseries.keys():
        value_timeseries[k] = timeseries[k][value_key]

    return value_timeseries


# separate function for getting url with "retry" decorator
@retry(retry=retry_if_result(is_none_p), stop=stop_after_attempt(api['retry_attempts']), wait=wait_fixed(api['retry_wait_time']), 
    retry_error_callback=return_last_value)
@data_protector
def get_request_data(url, params):
    r = requests.get(url, params=params)
    data = r.json()
    # items = data['data']
    return data['data']


# returns first block by given datetime
@data_protector
def get_block_by_datetime(dt=None):
    if not dt:
        dt = get_today_start_datetime()
    dt_start = dt
    dt_end = dt_start + datetime.timedelta(minutes=5)
    blocks = get_blocks(start_date=dt_start, end_date=dt_end)
    endpoint_value_key = api['endpoint_keys']['block']['value_key']
    first_block = blocks[0][endpoint_value_key] if len(blocks) != 0 else None
    return first_block


@retry(retry=retry_if_result(is_none_p), stop=stop_after_attempt(api['retry_attempts']), wait=wait_fixed(api['retry_wait_time']), 
    retry_error_callback=return_last_value)
@data_protector
def get_blocks(start_date=api['XUSD_metadata']['creation_date'], end_date='latest', page_size=1000):
    if isinstance(start_date, datetime.datetime):
        start_date = get_string_from_datetime(start_date)
    if isinstance(end_date, datetime.datetime):
        end_date = get_string_from_datetime(end_date)

    url = ('{api_url}{api_ver}/{chain_id}/block_v2/'+ start_date +'/'+ end_date +'/')\
        .format_map(api)
    params = {'key': api['api_key'], 'page-size': page_size}
    has_more_blocks = True
    page_counter = 0
    blocks = []
    while has_more_blocks:
        params['page-number'] = page_counter
        # r = requests.get(url, params=params)
        # data = r.json()

        data = get_request_data(url, params=params)
        items = data['items']
        # print()
        # pprint.pprint(data)
        # print()

        # items = data['data']['items']
        if len(items) == 0:
            has_more_blocks = False
            break
        blocks.extend(items)
        page_counter = page_counter + 1
    return blocks


@retry(retry=retry_if_result(is_none_p), stop=stop_after_attempt(api['retry_attempts']), wait=wait_fixed(api['retry_wait_time']), 
    retry_error_callback=return_last_value)
@data_protector
def get_balances(wallet_address=None):
    url = '{api_url}{api_ver}/{chain_id}/address/{basket_address}/balances_v2/?key={api_key}'\
        .format_map(api)
    if wallet_address:
        url = '{api_url}{api_ver}/{chain_id}/address/{wallet_address}/balances_v2/?key={api_key}'\
            .format_map({**api, 'wallet_address':wallet_address})

    r = requests.get(url)
    data = r.json()
    items = data['data']['items']
    return items


# returns list of latest transactions
@retry(retry=retry_if_result(is_none_p), stop=stop_after_attempt(api['retry_attempts']), wait=wait_fixed(api['retry_wait_time']), 
    retry_error_callback=return_last_value)
@data_protector
def get_transactions(contract_address=api['basket_address'], page_size=100, page_number=0):
    url = ('{api_url}{api_ver}/{chain_id}/address/'+ contract_address +'/transactions_v2/')\
        .format_map(api)
    params = {'key': api['api_key'], 'page-size': page_size, 'page-number': page_number}
    r = requests.get(url, params=params)
    data = r.json()
    items = data['data']['items']
    return items


# returns list of all transactions
@data_protector
def get_all_transactions(contract_address=api['basket_address'], page_size=100, start_date=None, resp_greater_date=None):
    if start_date and isinstance(start_date, str):
        start_date = get_datetime_from_string(start_date)
    has_more_transactions = True
    page_counter = 0
    transactions = []
    while has_more_transactions:
        items = get_transactions(contract_address=contract_address, page_size=page_size, page_number=page_counter)
        if len(items) == 0:
            has_more_transactions = False
            break
        if start_date:
            tx_index = next((i for i, item in enumerate(items) if get_datetime_from_string(item['block_signed_at']) < start_date), None)
            # if the date of the most recent transaction is greater than the start_date
            # either the start_date is set incorrectly or the data from the blockchain has not yet been updated
            if tx_index == 0 and page_counter == 0:
                print('start_date is greater than date of the most recent transaction.',
                    f'Latest tx date: {items[tx_index]["block_signed_at"]}')
                return resp_greater_date
            if tx_index:
                # tx_index-1 is the index of the first transaction starting with start_date
                items = items[:tx_index]
                has_more_transactions = False

        transactions.extend(items)
        page_counter = page_counter + 1

    return transactions


@retry(retry=retry_if_result(is_none_p), stop=stop_after_attempt(api['retry_attempts']), wait=wait_fixed(api['retry_wait_time']), 
    retry_error_callback=return_last_value)
@data_protector
def get_events(contract_address=api['XUSD_address'], start_block=None, end_block='latest', 
        match_query=None, page_size=100, page_number=0):
    if not start_block:
        start_block = get_block_by_datetime()
    url = ('{api_url}{api_ver}/{chain_id}/events/address/'+ contract_address +'/')\
        .format_map(api)
    params = {'key': api['api_key'], 'starting-block': start_block, 'ending-block': end_block, 
        'page-size': page_size, 'page-number': page_number}
    if match_query:
        params['match'] = match_query
    r = requests.get(url, params=params)
    data = r.json()
    # print()
    # print('get_events')
    # pprint.pprint(data)
    return data['data']['items']


@data_protector
def get_all_events(contract_address=api['XUSD_address'], 
        start_block=get_block_by_datetime(get_datetime_from_string(api['XUSD_metadata']['creation_date'])),
        end_block='latest', 
        match_query=None, page_size=500):
    events = []
    page_counter = 0
    while True:
        items = get_events(contract_address=contract_address, start_block=start_block, end_block=end_block,
            match_query=match_query, page_size=page_size, page_number=page_counter)
        if len(items) == 0:
            break
        events.extend(items)
        page_counter = page_counter + 1
    return events


@data_protector
def get_unique_wallets(contract_address=api['XUSD_address'], block_height=None, page_size=10000):
    page_counter = 0
    wallets_count = 0
    while True:
        url = ('{api_url}{api_ver}/{chain_id}/tokens/'+ contract_address +'/token_holders/')\
            .format_map(api)
        params = {'key': api['api_key'], 'page-size': page_size, 'page-number': page_counter}
        if block_height:
            params['block-height'] = block_height
        data = get_request_data(url, params=params)
        items = data['items']
        items_count = len(items)
        if items_count == 0:
            break
        wallets_count += items_count
        page_counter += 1
    return wallets_count


@data_protector
def get_all_unique_wallets(contract_address=api['XUSD_address'], start_date=api['XUSD_metadata']['creation_date']):
    blocks = get_blocks(start_date=start_date)
    endpoint_keys = api['endpoint_keys']['block']
    blocks_timeseries = create_timeseries(blocks, date_key=endpoint_keys['date_key'], value_key=endpoint_keys['value_key'])
    wallets_timeseries = {}
    for k in blocks_timeseries.keys():        
        wallets_timeseries[k] = get_unique_wallets(contract_address=contract_address, block_height=blocks_timeseries[k])
    return wallets_timeseries


@retry(retry=retry_if_result(is_none_p), stop=stop_after_attempt(api['retry_attempts']), wait=wait_fixed(api['retry_wait_time']), 
    retry_error_callback=return_last_value)
@data_protector
def get_prices_by_ticker_name(from_date_str, to_date_str, ticker_name='BTC'):
    url = ('{api_url}{api_ver}/pricing/historical/USD/{ticker_name}/')\
        .format_map({**api, 'ticker_name': ticker_name})
    params = {'key': api['api_key'], 'quote-currency': 'USD', 'from': from_date_str, 'to': to_date_str}
    r = requests.get(url, params=params)
    data = r.json()
    # print(r.url)
    # print(r.json())
    return data['data']['prices']
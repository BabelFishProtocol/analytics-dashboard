import datetime 
from .helpers import *
from .config import COVALENT as api
from .private_config import COVALENT_API_KEY
api['api_key'] = COVALENT_API_KEY
import pprint
from .data_extractor import data_protector

def get_readable_value_from_decimals(value, decimals_power=18, ndigits=2):
    return round(int(value) / pow(10, int(decimals_power)), ndigits)


def get_processed_balance(extracted_balance):
    processed_balance = {}
    for item in extracted_balance:
        ticker = item['contract_ticker_symbol']
        p = get_readable_value_from_decimals(item['balance'], item['contract_decimals'])
        if p > 0:
            processed_balance[ticker] = p
    dt_now = str(datetime.datetime.utcnow().date())
    return {dt_now: processed_balance}


def get_transfers_from_transactions(transactions, contract_address=api['basket_address'], token_address=None):
    transfers = []

    for tx in transactions:
        if not tx['successful']:
            continue
        events = tx['log_events']
        for event in events:
            if not event['sender_address']:
                continue
            if token_address and event['sender_address'].lower() != token_address.lower():
                continue
            event_data = event['decoded']
            if not event_data:
                continue
            if event_data['name'] != 'Transfer':
                continue
            
            params = event_data['params']
            transfer_params = {}
            for p in params:
                transfer_params[p['name']] = p['value']
            
            transfer_direction = 1
            if transfer_params['from'].lower() == contract_address.lower():
                transfer_direction = -1
            elif transfer_params['to'].lower() == contract_address.lower():
                transfer_direction = 1
            else:
                continue
            transfer_value = get_readable_value_from_decimals(transfer_params['value']) * transfer_direction
            transfer = { 'date': event['block_signed_at'], 'value': { event['sender_contract_ticker_symbol']: transfer_value }}

            transfers.append(transfer)

    return transfers



def generate_dates_range(start_date, end_date):
    if isinstance(start_date, str):
        start_date = get_datetime_from_string(start_date).date()
    if isinstance(end_date, str):
        end_date = get_datetime_from_string(end_date).date()

    delta = end_date - start_date
    dates_list = []
    for i in range(delta.days + 1):
        date = start_date + datetime.timedelta(days=i)
        dates_list.append(date)
    return dates_list


# items - list of items with date:value
def create_transfers_timeseries(items, date_key='date', value_key='value'):
    timeseries = {}

    # creating timestamps of a time series, regardless of data from the blockchain
    dates_range = generate_dates_range(items[-1][date_key], items[0][date_key])
    for date in dates_range:
        timeseries[str(date)] = {}

    for item in items:
        transfer_date = str(get_datetime_from_string(item[date_key]).date())
        transfer_ticker = list(item[value_key])[0]
        transfer_value = item[value_key][transfer_ticker]

        if not transfer_date in timeseries:
            timeseries[transfer_date] = {}

        if not transfer_ticker in timeseries[transfer_date]:
            timeseries[transfer_date][transfer_ticker] = 0

        timeseries[transfer_date][transfer_ticker] += transfer_value

    return timeseries


def get_net_deposits(transactions):
    transfers = get_transfers_from_transactions(transactions)
    transfers_timeseries = create_transfers_timeseries(transfers)
    return transfers_timeseries


def get_balances_by_net_deposits(net_deposits):
    dates_strings = list(net_deposits.keys())
    dates = [datetime.date.fromisoformat(date_string) for date_string in dates_strings]
    dates.sort()
    balance = {}
    for index, date in enumerate(dates):
        date_str = str(date)
        prev_date_str = str(dates[index-1]) if index > 0 else None
        balance[date_str] = {}

        if prev_date_str and prev_date_str in balance:
            balance[date_str] = balance[prev_date_str].copy()

        for ticker in list(net_deposits[date_str].keys()):
            if ticker not in balance[date_str]:
                balance[date_str][ticker] = 0
            balance[date_str][ticker] += net_deposits[date_str][ticker]

    return balance


def get_daily_active_wallets(events):
    wallets = {}
    for event in events:
        event_date = event['block_signed_at'].split('T')[0]
        event_data = event['decoded']
        if not event_data:
            continue
        if event_data['name'] != 'Transfer':
            continue
        params = event_data['params']
        transfer_params = {}
        for p in params:
            transfer_params[p['name']] = p['value']

        if event_date not in wallets:
            wallets[event_date] = []
        
        wallets[event_date].append(transfer_params['from'])

    for date in wallets.keys():
        wallets[date] = list(set(wallets[date]))
        
        for ignored_wallet in api['daw_to_ignore']:
            if ignored_wallet in wallets[date]:
                wallets[date].remove(ignored_wallet)

    return wallets


def get_daily_active_wallets_counts(wallets):
    counts = {}
    wallets_keys = list(wallets.keys())
    for date in wallets_keys:
        counts[date] = len(wallets[date])
    
    dates_range = generate_dates_range(get_date_from_string(wallets_keys[0]), get_date_from_string(wallets_keys[-1]))

    for date in dates_range:
        if str(date) not in wallets_keys:
            counts[str(date)] = 0
    
    return counts


def get_conversions_from_events(events, token_address=api['FISH_address']):
    conversions = []

    for event in events:
        event_data = event['decoded']
        if not event_data:
            continue
        if event_data['name'] != 'Conversion':
            continue
        params = event_data['params']
        conversion_params = {}
        for p in params:
            conversion_params[p['name']] = p['value']
        
        swap_pair = {}

        if conversion_params['_fromToken'].lower() == api['FISH_address'].lower():
            swap_pair['FISH'] = conversion_params['_fromAmount']
            swap_pair['WRBTC'] = conversion_params['_toAmount']
        elif conversion_params['_toToken'].lower() == api['FISH_address'].lower():
            swap_pair['FISH'] = conversion_params['_toAmount']
            swap_pair['WRBTC'] = conversion_params['_fromAmount']
        else:
            continue


        swap_pair['FISH'] = get_readable_value_from_decimals(swap_pair['FISH'])
        swap_pair['WRBTC'] = get_readable_value_from_decimals(swap_pair['WRBTC'], ndigits=8)

        conversion = { 'date': event['block_signed_at'], 'value': swap_pair }

        # conversion = { 'date': event['block_signed_at'], 'block_height': event['block_height'], 'value': swap_pair }


        conversions.append(conversion)

    return conversions


def get_prices_from_conversions(conversions, base_cur_prices=None, token='FISH', base_cur = 'WRBTC'):
    prices = []
    for c in conversions:
        price_value = {}
        try:
            price_base_cur = c['value'][base_cur] / c['value'][token]
        except:
            price_base_cur = 0
        price_value[base_cur] = price_base_cur

        if base_cur_prices:
            for bcp in base_cur_prices:
                if bcp['date'] != c['date'].split('T')[0]:
                    continue
                price_value['USD'] = price_base_cur * bcp['price']
        
        price_snapshot = { 'date': c['date'], 'value': price_value }
        prices.append(price_snapshot)
    return prices

# items - list of items with date:value
@data_protector
def create_prices_timeseries(items, date_key='date', value_key='value'):
    timeseries = {}

    # creating timestamps of a time series, regardless of data from the blockchain
    dates_range = generate_dates_range(items[0][date_key], items[-1][date_key])
    for date in dates_range:
        timeseries[str(date)] = {}

    for item in items:
        item_date = str(get_datetime_from_string(item[date_key]).date())

        if not timeseries[item_date]:
            timeseries[item_date] = item

        if get_datetime_from_string(item[date_key]) > get_datetime_from_string(timeseries[item_date][date_key]):
            timeseries[item_date] = item

    # fill missing value from prev. day in case in some days weren't any trades
    # test -> timeseries[list(timeseries.keys())[5]] = {}
    for i, k in enumerate(timeseries.keys()):
        if not timeseries[k] and i > 0:
            timeseries[k] = timeseries[list(timeseries.keys())[i-1]]

    value_timeseries = {}
    for k in timeseries.keys():
        value_timeseries[k] = timeseries[k][value_key]

    return value_timeseries


# ta - tracked addresses
def get_ta_balances_all_time(address, start_date):
    transactions = get_all_transactions(contract_address=address, start_date=start_date)
    transfers = get_transfers_from_transactions(transactions=transactions, contract_address=address, token_address=api['FISH_address'])
    transfers_timeseries = create_transfers_timeseries(transfers)
    balances = get_balances_by_net_deposits(transfers_timeseries)
    for key in balances.keys():
        balances[key] = balances[key]['FISH']
    return balances


# ta - tracked addresses
def get_ta_balances(address):
    balances = get_balances(wallet_address=address)
    if not balances:
        return
    p_balances = get_processed_balance(balances)
    for key in p_balances.keys():
        p_balances[key] = p_balances[key]['FISH']

    return p_balances



def get_funds_in_vesting_from_transactions(transactions):
    staked_funds = []
    vesting_contracts = []

    for tx in transactions:
        if not tx['successful']:
            continue
        staked_funds_data = { 'date': tx['block_signed_at'], 'value': 0 }
        events = tx['log_events']
        for event in events:
            event_data = event['decoded']
            if not event_data:
                continue
            if event_data['name'] != 'TokensStaked':
                continue
            
            params = event_data['params']
            staking_params = {}
            for p in params:
                staking_params[p['name']] = p['value']
            
            if 'caller' in staking_params:
                continue

            vesting_contracts.append(staking_params['staker'])

            staked_value = get_readable_value_from_decimals(staking_params['totalStaked'])
            staked_funds_data['value'] += staked_value

        staked_funds.append(staked_funds_data)


    vesting_contracts = list(set(vesting_contracts))
    
    return staked_funds, vesting_contracts 




def create_vesting_timeseries(items, date_key='date', value_key='value'):
    timeseries = {}

    # creating timestamps of a time series, regardless of data from the blockchain
    dates_range = generate_dates_range(items[-1][date_key], items[0][date_key])
    for date in dates_range:
        timeseries[str(date)] = 0

    for item in items:
        transfer_date = str(get_datetime_from_string(item[date_key]).date())
        transfer_value = item[value_key]

        if not transfer_date in timeseries:
            timeseries[transfer_date] = 0

        timeseries[transfer_date] += transfer_value

    return timeseries


def get_funds_out_vesting_from_events(events, vesting_contracts):
    unstaked_funds = []

    for event in events:
        event_data = event['decoded']
        if not event_data:
            continue
        if event_data['name'] != 'TokensWithdrawn':
            continue
        
        params = event_data['params']
        staking_params = {}
        for p in params:
            staking_params[p['name']] = p['value']
        
        if 'caller' in staking_params:
            continue

        if not staking_params['staker'] in vesting_contracts:
            continue

        unstaked_value = get_readable_value_from_decimals(staking_params['amount'])
        unstaked_funds_data = { 'date': event['block_signed_at'], 'value': unstaked_value }
        unstaked_funds.append(unstaked_funds_data)

    return unstaked_funds


def get_vesting_balances_by_deposits(net_vesting_deposits):
    dates_strings = list(net_vesting_deposits.keys())
    dates = [datetime.date.fromisoformat(date_string) for date_string in dates_strings]
    dates.sort()
    balance = {}
    for index, date in enumerate(dates):
        date_str = str(date)
        prev_date_str = str(dates[index-1]) if index > 0 else None
        balance[date_str] = 0

        if prev_date_str and prev_date_str in balance:
            balance[date_str] = balance[prev_date_str]

        balance[date_str] += net_vesting_deposits[date_str]

    return balance


def get_vesting_deposits(staked_funds, unstaked_funds):
    staked_funds = create_vesting_timeseries(staked_funds)
    unstaked_funds = create_vesting_timeseries(unstaked_funds)

    net_vesting_deposits = {}

    dates = list(staked_funds.keys()) + list(unstaked_funds.keys())
    dates = list(set(dates))
    dates.sort()

    for d in dates:
        staked = staked_funds[d] if d in staked_funds else 0
        unstaked = unstaked_funds[d] if d in unstaked_funds else 0
        net_vesting_deposits[d] = staked - unstaked

    return net_vesting_deposits



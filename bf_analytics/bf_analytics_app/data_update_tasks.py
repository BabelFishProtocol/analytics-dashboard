from flask import Blueprint
from . import app, db, celery
from celery.signals import task_prerun, task_postrun
from celery.schedules import crontab
import datetime
import redis
from sqlalchemy import func
import pprint
from .helpers import get_today_start_datetime, get_date_from_string, get_string_from_datetime
from .data_extractor import get_block_by_datetime, get_balances, get_transactions, get_all_transactions, \
get_all_events, get_unique_wallets, get_all_unique_wallets, get_datetime_from_string, get_prices_by_ticker_name, \
api
from .data_processor import get_processed_balance, get_net_deposits, get_balances_by_net_deposits, \
get_daily_active_wallets, get_daily_active_wallets_counts, get_conversions_from_events, get_prices_from_conversions, \
create_prices_timeseries, get_transfers_from_transactions, create_transfers_timeseries, get_funds_in_vesting_from_transactions, \
get_funds_out_vesting_from_events, create_vesting_timeseries, get_vesting_balances_by_deposits, get_vesting_deposits, generate_dates_range
from .data_keeper import save_balances, save_net_deposits, save_unique_wallets_count, save_daily_active_wallets_count, save_prices, \
save_circulating_supply, save_market_cap, save_fish_unique_wallets_count, save_fish_daily_active_wallets_count, save_fish_vesting, \
save_fish_vesting_contracts, save_fish_staking, save_fish_multisig_balance

from .models.data_models import Balance, CirculatingSupply, Price, FishVesting, FishVestingContract
# import pprint
data_update_bp = Blueprint('data_update', __name__)


def lock_handler(func):
    def wrapper():
        lock_key = app.config['EXTRACTION_LOCK_KEY']
        redis_app = redis.Redis()
        
        if redis_app.exists(lock_key):
            print('Lock is set, the command cannot be executed. Wait for another data extraction command to complete and try again.')
            return
        
        redis_app.set(lock_key, 'locked')
        print('Lock is set.')

        func()

        print('Lock deleted.')
        redis_app.delete(lock_key)
    return wrapper


@celery.task()
def remove_lock():
    lock_key = app.config['EXTRACTION_LOCK_KEY']
    redis_app = redis.Redis()
    redis_app.delete(lock_key)


# disposinng ORM engine and removing session for the correct operation of distributed tasks related to writing to the database
@task_prerun.connect
def prerun_handler(sender=None, headers=None, body=None, **kwargs):
    db.engine.dispose()


@task_postrun.connect
def postrun_handler(sender=None, headers=None, body=None, **kwargs):
    db.session.remove()


@celery.on_after_configure.connect
def setup_monitoring(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='*/10'),
        update_all_intraday_data.s()
    )


@celery.on_after_configure.connect
def setup_lock_removal(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='27', hour='6,12,18'),
        remove_lock.s()
    )


# INTRA-DAY/LATEST UPDATES
def update_net_deposits(start_date=None, update_balances=None):
    if start_date:
        transactions = get_all_transactions(start_date=start_date)
    else:
        transactions = get_all_transactions(start_date=get_today_start_datetime())
    if not transactions:
        return
    net_deposits = get_net_deposits(transactions)
    net_deposits_extended = []
    for item in net_deposits.items():
        date = get_date_from_string(item[0])
        nd_by_collateral = item[1]
        nd_total_value = sum(nd_by_collateral.values())

        net_deposits_extended.append({
            'date': date, 
            'net_deposits_by_collateral': nd_by_collateral,
            'net_deposits_total_value': nd_total_value
        })
    net_deposits_extended.sort(key=lambda nd:nd['date'])
    print('[update_net_deposits]', net_deposits_extended)
    save_net_deposits(net_deposits_extended)

    if update_balances:
        start_balance_date = net_deposits_extended[0]['date'] - datetime.timedelta(days=1)
        start_balance_dt = datetime.datetime.combine(start_balance_date, datetime.datetime.min.time())
        db_balance = Balance.query.filter(Balance.timestamp == start_balance_dt).first()
        if not db_balance:
            db_balance = {'balance': {}}
        else:
            db_balance = db_balance.__dict__

        balances = []
        start_balance = db_balance['balance'].copy()
        for nd in net_deposits_extended:
            data = {'date': nd['date'], 'balance': start_balance}
            for ticker in list(nd['net_deposits_by_collateral'].keys()):
                if ticker not in data['balance']:
                    data['balance'][ticker] = 0
                data['balance'][ticker] += nd['net_deposits_by_collateral'][ticker]
            balances.append(data)
            start_balance = data['balance'].copy()

        print(balances)
        save_balances(balances)


def update_balance():
    balance = get_balances()
    if not balance:
        return
    p_balance = get_processed_balance(balance)
    data = {
        'date': get_date_from_string(list(p_balance.keys())[0]),
        'balance': list(p_balance.values())[0]
    }
    print('[update_balance]', data)
    save_balances(data)

# @app.cli.command("update_unique")
def update_unique_wallets_count():
    unique_wallets = get_unique_wallets()
    if not unique_wallets:
        return
    data = {
        'date': datetime.datetime.utcnow().date(),
        'unique_wallets_count': unique_wallets
    }
    print('[update_unique_wallets_count]', data)
    save_unique_wallets_count(data)


# @app.cli.command("update_daw")
def update_daily_active_wallets_count():
    events = get_all_events(start_block=get_block_by_datetime())
    if not events:
        return
    daw = get_daily_active_wallets_counts(
            get_daily_active_wallets(events))
    data = {
        'date': get_date_from_string(list(daw.keys())[0]),
        'daw_count': list(daw.values())[0]
    }
    print('[update_daily_active_wallets_count]', data)
    save_daily_active_wallets_count(data)


def update_prices():
    all_events = get_all_events(contract_address=api['DEX_address'], match_query=None, 
        start_block=get_block_by_datetime(get_today_start_datetime()))

    if not all_events:
        return

    conversions = get_conversions_from_events(all_events)

    today_date_str = get_string_from_datetime(get_today_start_datetime()).split('T')[0]
    base_cur_prices = get_prices_by_ticker_name(from_date_str=today_date_str, to_date_str=today_date_str)
    
    prices = get_prices_from_conversions(conversions, base_cur_prices=base_cur_prices)

    prices_timeseries = create_prices_timeseries(prices)
    if not prices_timeseries:
        return

    prices_extended = []
    for item in prices_timeseries.items():
        date = get_date_from_string(item[0])
        prices_extended.append({
            'date': date, 
            'ticker': 'fish',
            'prices': item[1]
        })
    prices_extended.sort(key=lambda p:p['date'])
    save_prices(prices_extended)

# @app.cli.command("update_supply")
def update_supply():
    return update_supply_data(for_all_time=False)


def update_market_cap():
    mc = get_market_cap(start_date=get_today_start_datetime().date())
    save_market_cap(mc)


# @app.cli.command("update_fish_unique")
def update_fish_unique_wallets_count():
    unique_wallets = get_unique_wallets(contract_address=api['FISH_address'])
    if not unique_wallets:
        return
    data = {
        'date': datetime.datetime.utcnow().date(),
        'unique_wallets_count': unique_wallets
    }
    print('[update_fish_unique_wallets_count]', data)
    save_fish_unique_wallets_count(data)


# @app.cli.command("update_fish_daw")
def update_fish_daily_active_wallets_count():
    events = get_all_events(contract_address=api['FISH_address'], start_block=get_block_by_datetime())
    if not events:
        return
    daw = get_daily_active_wallets_counts(
            get_daily_active_wallets(events))
    data = {
        'date': get_date_from_string(list(daw.keys())[0]),
        'daw_count': list(daw.values())[0]
    }
    print('[update_fish_daily_active_wallets_count]', data)
    save_fish_daily_active_wallets_count(data)


# @app.cli.command("update_vesting")
def update_vesting():
    update_vesting_data(for_all_time=False)



# ALL-TIME UPDATES
@app.cli.command("update_net_deposits_all_time")
@lock_handler
def update_net_deposits_all_time():
    transactions = get_all_transactions()
    net_deposits = get_net_deposits(transactions)
    balances = get_balances_by_net_deposits(net_deposits)
    # net deposits in the format for writing to the database  + calculated total_value
    net_deposits_extended = []
    for item in net_deposits.items():
        date = get_date_from_string(item[0])
        nd_by_collateral = item[1]
        nd_total_value = sum(nd_by_collateral.values())

        net_deposits_extended.append({
            'date': date, 
            'net_deposits_by_collateral': nd_by_collateral,
            'net_deposits_total_value': nd_total_value
        })
    net_deposits_extended.sort(key=lambda nd:nd['date'])

    balances_extended = []
    for item in balances.items():
        date = get_date_from_string(item[0])
        balance = item[1]

        balances_extended.append({
            'date': date,
            'balance': balance
        })

    save_net_deposits(net_deposits_extended)
    save_balances(balances_extended)
    # return {'net_deposits': net_deposits_extended, 'balances': balances_extended}


@app.cli.command("update_unique_wallets_all_time")
@lock_handler
def update_unique_wallets_all_time():
    unique_wallets = get_all_unique_wallets()
    unique_wallets_extended = []
    for item in unique_wallets.items():
        unique_wallets_extended.append({
            'date': get_date_from_string(item[0]),
            'unique_wallets_count': item[1]
        })
    save_unique_wallets_count(unique_wallets_extended)


@app.cli.command("update_daw_count_all_time")
@lock_handler
def update_daily_active_wallets_count_all_time():
    daw = get_daily_active_wallets_counts(
            get_daily_active_wallets(
                get_all_events()))
    daw_extended = []
    for item in daw.items():
        daw_extended.append({
            'date': get_date_from_string(item[0]),
            'daw_count': item[1]
        })
    save_daily_active_wallets_count(daw_extended)


@app.cli.command("update_prices_all_time")
@lock_handler
def update_prices_all_time():
    all_events = get_all_events(contract_address=api['DEX_address'], match_query=None, 
        start_block=get_block_by_datetime(get_datetime_from_string(api['FISH_metadata']['creation_date'])))

    if not all_events:
        return

    conversions = get_conversions_from_events(all_events)

    fish_creation_date_str = api['FISH_metadata']['creation_date'].split('T')[0]
    today_date_str = get_string_from_datetime(get_today_start_datetime()).split('T')[0]
    base_cur_prices = get_prices_by_ticker_name(from_date_str=fish_creation_date_str, to_date_str=today_date_str)
    
    prices = get_prices_from_conversions(conversions, base_cur_prices=base_cur_prices)

    prices_timeseries = create_prices_timeseries(prices)

    prices_extended = []
    for item in prices_timeseries.items():
        date = get_date_from_string(item[0])
        prices_extended.append({
            'date': date, 
            'ticker': 'fish',
            'prices': item[1]
        })
    prices_extended.sort(key=lambda p:p['date'])
    save_prices(prices_extended)


@app.cli.command("update_supply_all_time")
@lock_handler
def update_supply_all_time():
    return update_supply_data(for_all_time=True)


@app.cli.command("update_market_cap_all_time")
@lock_handler
def update_market_cap_all_time():
    mc = get_market_cap(start_date=api['FISH_metadata']['creation_date'])
    save_market_cap(mc)


@app.cli.command("update_fish_unique_wallets_all_time")
@lock_handler
def update_fish_unique_wallets_all_time():
    unique_wallets = get_all_unique_wallets(contract_address=api['FISH_address'], start_date=api['FISH_metadata']['creation_date'])
    if not unique_wallets:
        return
    # unique_wallets = get_all_unique_wallets(contract_address=api['FISH_address'], start_date='2021-12-21T22:58:29Z')
    unique_wallets_extended = []
    for item in unique_wallets.items():
        unique_wallets_extended.append({
            'date': get_date_from_string(item[0]),
            'unique_wallets_count': item[1]
        })
    save_fish_unique_wallets_count(unique_wallets_extended)


@app.cli.command("update_fish_daw_count_all_time")
@lock_handler
def update_fish_daily_active_wallets_count_all_time():
    start_block = get_block_by_datetime(get_datetime_from_string(api['FISH_metadata']['creation_date']))
    # start_block = get_block_by_datetime(get_datetime_from_string('2021-12-21T22:58:29Z'))
    daw = get_daily_active_wallets_counts(
            get_daily_active_wallets(
                get_all_events(contract_address=api['FISH_address'], start_block=start_block)))
    daw_extended = []
    for item in daw.items():
        daw_extended.append({
            'date': get_date_from_string(item[0]),
            'daw_count': item[1]
        })
    save_fish_daily_active_wallets_count(daw_extended)


@app.cli.command("update_vesting_all_time")
def update_vesting_all_time():
    update_vesting_data(for_all_time=True)



# CLI INTERFACES FOR 'UPDATE' TASKS
@celery.task()
@lock_handler
def update_all_intraday_data():
    if datetime.datetime.utcnow().hour < 1:
        prev_day_start_dt = get_today_start_datetime() - datetime.timedelta(days=1)
        update_net_deposits(start_date=prev_day_start_dt, update_balances=True)
    else:
        update_net_deposits()
        update_balance()
        update_prices()
        update_vesting()
        update_supply()
        update_market_cap()


    update_unique_wallets_count()
    update_daily_active_wallets_count()
    update_fish_unique_wallets_count()
    update_fish_daily_active_wallets_count()




@app.cli.command("update_latest_data")
def cst_update_all_latest_data():
    update_all_intraday_data.delay()





# Supply data functions 

def get_saved_vesting_balances_by_dates(staking_dates):
    staking_dates.sort(key=lambda d:get_date_from_string(d))
    vesting_balances = FishVesting.query.filter(func.date(FishVesting.timestamp) >= get_date_from_string(staking_dates[0]), 
        func.date(FishVesting.timestamp) <= get_date_from_string(staking_dates[-1])).all()
    vesting_ts = {}
    for vb in vesting_balances:
        date = str(vb.timestamp.date())
        balance = vb.funds_in_vesting
        vesting_ts[date] = balance
    return vesting_ts


def update_supply_data(for_all_time=False):
    balances = get_all_ta_balances(for_all_time=for_all_time)
    if not balances:
        return
    circulating_supply = {}
    out_supply = {}
    
    staking_balance = {}
    staking_dates = list(balances['staking_contract'].keys())
    vesting_ts = get_saved_vesting_balances_by_dates(staking_dates)

    multisig_balance = balances['multisig_wallet']

    for item in api['tracked_addresses'].items():
        _name = item[0]
        _data = item[1]
        if not ('out_of_circulation' in _data and _data['out_of_circulation']):
            continue

        for wallet_name, balance in balances.items():
            if wallet_name != _name:
                continue
            for key, value in balance.items():
                if not key in out_supply:
                    out_supply[key] = 0
                out_supply[key] += value


            if wallet_name == 'staking_contract':
                for key, value in balance.items():
                    if not key in staking_balance:
                        staking_balance[key] = 0
                    vesting_value = vesting_ts[key] if key in vesting_ts else 0
                    staking_balance[key] += value - vesting_value


    for key, value in out_supply.items():
        circulating_supply[key] = api['FISH_metadata']['total_supply'] - value

    cs_unified = get_unified_dict(circulating_supply, key_name='circulating_supply')
    cs_unified.sort(key=lambda cs: cs['date'])
    # print()
    # print('cs_unified_sorted')
    # pprint.pprint(cs_unified)
    save_circulating_supply(cs_unified)
    
    # print('staking', staking_balance)

    staking_unified = get_unified_dict(staking_balance, key_name='funds_in_staking')
    staking_unified.sort(key=lambda cs: cs['date'])
    save_fish_staking(staking_unified)

    multisig_unified = get_unified_dict(multisig_balance, key_name='balance')
    multisig_unified.sort(key=lambda cs: cs['date'])
    save_fish_multisig_balance(multisig_unified)

    return cs_unified


# ta - tracked addresses
def get_all_ta_balances(for_all_time=False):
    address_timeseries = {}
    for item in api['tracked_addresses'].items():
        _name = item[0]
        _data = item[1]
        if for_all_time:
            address_timeseries[_name] = get_ta_balances_all_time(address=_data['address'], start_date=api['FISH_metadata']['creation_date'])
        else:
            address_timeseries[_name] = get_ta_balances(address=_data['address'])

    return address_timeseries


# ta - tracked addresses
def get_ta_balances_all_time(address, start_date):
    transactions = get_all_transactions(contract_address=address, start_date=start_date)
    if not transactions:
        return
    transfers = get_transfers_from_transactions(transactions=transactions, contract_address=address, token_address=api['FISH_address'])
    transfers_timeseries = create_transfers_timeseries(transfers)
    balances = get_balances_by_net_deposits(transfers_timeseries)
    for key in balances.keys():
        balances[key] = balances[key]['FISH']

    # filling in missing dates and values to the current day 
    balances_dates = list(balances.keys())
    balances_dates.sort(key=lambda d : get_date_from_string(d))
    max_date = get_date_from_string(balances_dates[-1])
    dates_range = generate_dates_range(max_date, get_today_start_datetime().date())
    for date in dates_range:
        if str(date) in balances:
            continue
        balances[str(date)] = balances[str(max_date)]

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


def get_unified_dict(orig, key_name='balance'):
    extended = []
    for item in orig.items():
        date = get_date_from_string(item[0])
        balance = item[1]

        extended.append({
            'date': date,
            key_name: balance
        })
    return extended



# Market Cap function 
def get_market_cap(start_date):
    circ_supply = CirculatingSupply.query.filter(CirculatingSupply.timestamp >= start_date).all()
    prices = Price.query.filter(Price.timestamp >= start_date).all()

    market_cap = []
    for cs in circ_supply:
        for p in prices:
            if cs.timestamp == p.timestamp:
                mc_value_usd = cs.circulating_supply * p.prices['USD']
                mc_value_btc = cs.circulating_supply * p.prices['WRBTC']

                market_cap.append({
                    'date': cs.timestamp.date(),
                    'market_cap': {'WRBTC': mc_value_btc, 'USD': mc_value_usd}
                })

    return market_cap




# Vesting data
def update_vesting_data(for_all_time=False):
    if for_all_time:
        staked_funds, vesting_contracts = get_funds_in_vesting() # start_date='2022-01-01T00:00:00Z'
        # print('staked_funds', type(staked_funds))
        if not staked_funds:
            return
        vesting_contracts = update_vesting_contracts(vesting_contracts)
        unstaked_funds = get_funds_out_vesting(vesting_contracts) # start_date='2022-01-01T00:00:00Z'
        # print('unstaked_funds', type(unstaked_funds))
    else:
        staked_funds, vesting_contracts = get_funds_in_vesting(start_date=get_string_from_datetime(get_today_start_datetime()))
        if not staked_funds:
            return
        # print('staked_funds', staked_funds)
        vesting_contracts = update_vesting_contracts(vesting_contracts)
        unstaked_funds = get_funds_out_vesting(vesting_contracts, start_date=get_string_from_datetime(get_today_start_datetime()))
        # print('unstaked_funds', unstaked_funds)
    
    if not unstaked_funds:
        return

    net_vesting_deposits = get_vesting_deposits(staked_funds, unstaked_funds)
    funds_in_vesting = get_vesting_balances_by_deposits(net_vesting_deposits)

    if not for_all_time:
        dates = list(net_vesting_deposits.keys())
        dates.sort()
        prev_dt = get_date_from_string(dates[0]) - datetime.timedelta(days=1)
        prev_vesting = FishVesting.query.filter(func.date(FishVesting.timestamp) == prev_dt).first()
        if prev_vesting:
            for date in funds_in_vesting.keys():
                funds_in_vesting[date] += prev_vesting.funds_in_vesting


    # filling in missing dates and values to the current day 
    if for_all_time:
        balances_dates = list(funds_in_vesting.keys())
        balances_dates.sort(key=lambda d : get_date_from_string(d))
        max_date = get_date_from_string(balances_dates[-1])
        dates_range = generate_dates_range(max_date, get_today_start_datetime().date())
        for date in dates_range:
            if str(date) in funds_in_vesting:
                continue
            funds_in_vesting[str(date)] = funds_in_vesting[str(max_date)]

    # print()
    # print('funds_in_vesting')
    # pprint.pprint(funds_in_vesting)


    funds_in_vesting_extended = []
    for date, value in funds_in_vesting.items():
        funds_in_vesting_extended.append({
            'date': get_date_from_string(date),
            'funds_in_vesting': value
        })

    # print()
    # print('funds_in_vesting_extended')
    # pprint.pprint(funds_in_vesting_extended) 


    save_fish_vesting(funds_in_vesting_extended)


# @app.cli.command("update_fiv")
def get_funds_in_vesting(start_date=api['FISH_vesting']['logic_contract_creation_date']):
    staked_funds, vesting_contracts = None, None

    transactions = get_all_transactions(contract_address=api['FISH_vesting']['logic_contract'], 
        page_size=100, start_date=start_date, resp_greater_date='NoRecentTransactions')
    
    if transactions == [] or transactions == 'NoRecentTransactions':
        staked_funds = [{ 'date': start_date, 'value': 0 }]
    elif not transactions:
        return None, None
    else:
        staked_funds, vesting_contracts = get_funds_in_vesting_from_transactions(transactions)

    return staked_funds, vesting_contracts


# @app.cli.command("update_fov")
def get_funds_out_vesting(vesting_contracts, start_date=api['FISH_vesting']['staking_contract_creation_date']):
    events = get_all_events(contract_address=api['tracked_addresses']['staking_contract']['address'], 
        start_block=get_block_by_datetime(get_datetime_from_string(start_date)))
    if events == []:
        unstaked_funds = [{ 'date': start_date, 'value': 0 }]
    elif not events:
        return
    else:
        unstaked_funds = get_funds_out_vesting_from_events(events, vesting_contracts)
        unstaked_funds = [{ 'date': start_date, 'value': 0 }] if unstaked_funds == [] else unstaked_funds
    
    unstaked_funds.reverse()
    return unstaked_funds


def update_vesting_contracts(new_vesting_contracts=None):
    saved_addresses = []
    update_addresses = []
    new_vesting_contracts = [] if not new_vesting_contracts else new_vesting_contracts
    saved_vesting_contracts = FishVestingContract.query.all()

    for c in saved_vesting_contracts:
        saved_addresses.append(c.address.lower())
    
    for nc in new_vesting_contracts:
        new_addr = nc.lower()
        if new_addr in saved_addresses:
            continue
        update_addresses.append(new_addr)

    new_addresses_to_saving = []
    for addr in update_addresses:
        new_addresses_to_saving.append({'address': addr})

    save_fish_vesting_contracts(new_addresses_to_saving)

    return saved_addresses+update_addresses



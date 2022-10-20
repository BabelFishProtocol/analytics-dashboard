import click
from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from .flask_celery import make_celery
from sqlalchemy import desc, asc
import copy

app = Flask(__name__)
app.config.from_object('bf_analytics_app.config')
app.config.from_object('bf_analytics_app.celeryconfig')
app.config.from_object('bf_analytics_app.private_config')

db = SQLAlchemy(app)

from .models.data_models import *

db.create_all()

celery = make_celery(app)


from .data_update_tasks import data_update_bp
app.register_blueprint(data_update_bp)


def get_data_from_model(Model, limit, start_date=None, end_date=None, order='desc'):
    fields = app.config['MODELS_FIELDS'][Model.__name__]
    order_func = asc if order=='asc' else desc
    db_query = Model.query
    if start_date:
        db_query = db_query.filter(Model.timestamp >= start_date) #, Model.timestamp <= dates_range[1]
    if end_date:
        db_query = db_query.filter(Model.timestamp <= end_date)
    db_data = db_query.order_by(order_func(Model.timestamp)).limit(limit).all()
    data = []
    for record in db_data:
        record_dict = record.__dict__
        data_point = {}
        for field in fields:
            data_point[field] = record_dict[field]
        data.append(data_point)
    return data


@app.route("/")
def analytics():
    days_limit = app.config['DAYS_INTERVAL_SIZE']
    balances = get_data_from_model(Balance, days_limit)
    net_deposits = get_data_from_model(NetDeposits, days_limit)
    unique_wallets = get_data_from_model(UniqueWallets, days_limit)
    active_wallets = get_data_from_model(ActiveWallets, days_limit)

    balances.reverse()
    net_deposits.reverse()
    unique_wallets.reverse()
    active_wallets.reverse()


    latest_balance_formated = "${:,.2f}".format(sum(balances[-1]['balance'].values()))

    latest_net_deposits_formated = "${:,.2f}".format(abs(net_deposits[-1]['net_deposits_value']))
    if net_deposits[-1]['net_deposits_value'] < 0:
        latest_net_deposits_formated = '-' + latest_net_deposits_formated

    latest_active_wallets_formated = active_wallets[-1]['daily_active_wallets_count']
    latest_unique_wallets_formated = unique_wallets[-1]['unique_wallets_count']

    return render_template('analytics.html', **locals())


@app.route("/fish")
def fish_analytics():
    days_limit = app.config['DAYS_INTERVAL_SIZE']
    price = get_data_from_model(Price, days_limit)
    market_cap = get_data_from_model(MarketCap, days_limit)
    circulating_supply = get_data_from_model(CirculatingSupply, days_limit)
    vesting = get_data_from_model(FishVesting, days_limit)
    staking = get_data_from_model(FishStaking, days_limit)
    multisig_balance = get_data_from_model(FishMultisig, days_limit)
    unique_wallets = get_data_from_model(FishUniqueWallets, days_limit)
    active_wallets = get_data_from_model(FishActiveWallets, days_limit)

    # for p in price:
    #     if p['ticker'].lower() == 'fish':
    #         continue
    #     price.remove(p)

    price.reverse()
    market_cap.reverse()
    circulating_supply.reverse()
    vesting.reverse()
    staking.reverse()
    multisig_balance.reverse()
    unique_wallets.reverse()
    active_wallets.reverse()

    for v in vesting:
        if v['funds_in_vesting'] < 0:
            v['funds_in_vesting'] = 0
    for s in staking:
        if s['funds_in_staking'] < 0:
            s['funds_in_staking'] = 0
    

    latest_price_formated = {
        'USD': round(price[-1]['prices']['USD'], 4), 
        'BTC': round(price[-1]['prices']['WRBTC'] * 100000000)
    }
    latest_market_cap_formated = {
        'USD': "{:,}".format(int(round(market_cap[-1]['market_cap']['USD'], 0))), 
        'BTC': round(market_cap[-1]['market_cap']['WRBTC'])
    }
    latest_circ_supply_formated = "{:,}".format(circulating_supply[-1]['circulating_supply'])
    latest_locked_funds_formated = app.config['COVALENT']['FISH_metadata']['total_supply'] - circulating_supply[-1]['circulating_supply']
    latest_locked_funds_formated = "{:,}".format(latest_locked_funds_formated)
    latest_active_wallets_formated = active_wallets[-1]['daily_active_wallets_count']
    latest_active_wallets_formated = "{:,}".format(latest_active_wallets_formated)
    latest_unique_wallets_formated = unique_wallets[-1]['unique_wallets_count']
    latest_unique_wallets_formated = "{:,}".format(latest_unique_wallets_formated)

    latest_circ_supply_share = circulating_supply[-1]['circulating_supply'] / app.config['COVALENT']['FISH_metadata']['total_supply']
    latest_circ_supply_share = "{0:.0%}".format(latest_circ_supply_share)
    latest_locked_funds_share = (app.config['COVALENT']['FISH_metadata']['total_supply'] - circulating_supply[-1]['circulating_supply']) \
        / app.config['COVALENT']['FISH_metadata']['total_supply']
    latest_locked_funds_share = "{0:.0%}".format(latest_locked_funds_share)
    
   
    # filling missing starting values (if any) in all locked funds timeseries (vesting, staking, multisig)
    vesting_start_ts = [ item['timestamp'] for item in vesting[0:5] ]
    staking_start_ts = [ item['timestamp'] for item in staking[0:5] ]
    multisig_start_ts = [ item['timestamp'] for item in multisig_balance[0:5] ]
    circ_supply_start_ts = [ item['timestamp'] for item in circulating_supply[0:5] ]
    lf_start_timestamps = vesting_start_ts + staking_start_ts + multisig_start_ts + circ_supply_start_ts
    lf_start_timestamps = list(set(lf_start_timestamps))
    lf_start_timestamps.sort()
    lf_start_timestamps = lf_start_timestamps[0:5]
    # print('lf_start_timestamps', lf_start_timestamps)
    # print('vesting_start_ts', vesting_start_ts)
    # print('staking_start_ts', staking_start_ts)
    # print('multisig_start_ts', multisig_start_ts)
    temp_vesting = []
    temp_staking = []
    temp_multisig = []
    temp_circ_supply = []
    for ts in lf_start_timestamps:
        if not ts in vesting_start_ts:
            temp_vesting.append({'timestamp': ts, 'funds_in_vesting': 0})
        if not ts in staking_start_ts:
            temp_staking.append({'timestamp': ts, 'funds_in_staking': 0})
        if not ts in multisig_start_ts:
            temp_multisig.append({'timestamp': ts, 'balance': 0})
        if not ts in circ_supply_start_ts:
            temp_circ_supply.append({'timestamp': ts, 'circulating_supply': 0})

    vesting = temp_vesting + vesting
    staking = temp_staking + staking
    multisig_balance = temp_multisig + multisig_balance
    circulating_supply = temp_circ_supply + circulating_supply

    released_funds = copy.deepcopy(multisig_balance)
    for rf in released_funds:
        rf['balance'] = app.config['COVALENT']['FISH_metadata']['total_supply'] - rf['balance']
    released_funds[0]['balance'] = 0

    vote_locked_funds = [{'timestamp': sf['timestamp'], 'balance': sf['funds_in_staking']} for sf in staking]
    for vlf in vote_locked_funds:
        for vstd in vesting:
            if vlf['timestamp'] == vstd['timestamp']:
                vlf['balance'] += vstd['funds_in_vesting']

    # print([ item['timestamp'] for item in vesting[0:10] ])
    # print([ item['timestamp'] for item in staking[0:10] ])
    # print([ item['timestamp'] for item in multisig_balance[0:10] ])


    return render_template('fish_analytics.html', **locals())

from .data_api import data_api_bp
app.register_blueprint(data_api_bp)





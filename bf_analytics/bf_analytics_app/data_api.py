from flask import Blueprint, abort, request, jsonify
from functools import wraps
from .helpers import get_date_from_string
from . import app, db, get_data_from_model
import datetime
from .models.data_models import *

data_api_bp = Blueprint('data_api', __name__, url_prefix='/api/')


def convert_timestamps_to_isoformat(data):
    for d in data:
        d['timestamp'] = d['timestamp'].isoformat()


def api_data_validator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        valid_api_keys = app.config['DATA_API_KEYS']
        if request.method != 'GET':
            abort(405)

        start_date = request.args.get('start-date')
        end_date = request.args.get('end-date')
        limit = request.args.get('limit')
        order = request.args.get('order')
        api_key = request.args.get('api-key')

        if not api_key or api_key not in valid_api_keys:
            abort(401)

        if order and order not in ('asc', 'desc'):
            abort(400)

        try:
            start_date = get_date_from_string(start_date) if start_date else None
            end_date = get_date_from_string(end_date) if end_date else None
            limit = int(limit) if limit else None
        except:
            abort(400)

        return func(**locals())
    return wrapper


@data_api_bp.route('/balances/', methods=('GET', 'POST'))
@api_data_validator
def api_get_balances(*args, **kwargs):
    data = get_data_from_model(Balance, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(data)
    return jsonify(data)


@data_api_bp.route('/net_deposits/', methods=('GET', 'POST'))
@api_data_validator
def api_get_deposits(*args, **kwargs):
    data = get_data_from_model(NetDeposits, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(data)
    return jsonify(data)


@data_api_bp.route('/wallets/unique/', methods=('GET', 'POST'))
@api_data_validator
def api_get_unique_wallets(*args, **kwargs):
    data = get_data_from_model(UniqueWallets, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(data)
    return jsonify(data)


@data_api_bp.route('/wallets/active/', methods=('GET', 'POST'))
@api_data_validator
def api_get_active_wallets(*args, **kwargs):
    data = get_data_from_model(ActiveWallets, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(data)
    return jsonify(data)


@data_api_bp.route('/all/', methods=('GET', 'POST'))
@api_data_validator
def api_get_all_data(*args, **kwargs):
    balances = get_data_from_model(Balance, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(balances)

    net_deposits = get_data_from_model(NetDeposits, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(net_deposits)
    
    unique_wallets = get_data_from_model(UniqueWallets, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(unique_wallets)

    active_wallets = get_data_from_model(ActiveWallets, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(active_wallets)

    return jsonify(balances=balances, net_deposits=net_deposits, unique_wallets=unique_wallets, active_wallets=active_wallets)


@data_api_bp.route('fish/all/', methods=('GET', 'POST'))
@api_data_validator
def api_get_all_fish_data(*args, **kwargs):
    prices = get_data_from_model(Price, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(prices)

    circulating_supply = get_data_from_model(CirculatingSupply, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(circulating_supply)

    market_cap = get_data_from_model(MarketCap, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(market_cap)

    fish_unique_wallets = get_data_from_model(FishUniqueWallets, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(fish_unique_wallets)

    fish_active_wallets = get_data_from_model(FishActiveWallets, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(fish_active_wallets)


    fish_vesting = get_data_from_model(FishVesting, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(fish_vesting)


    fish_staking = get_data_from_model(FishStaking, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(fish_staking)


    fish_multisig = get_data_from_model(FishMultisig, limit=kwargs['limit'], start_date=kwargs['start_date'], 
        end_date=kwargs['end_date'], order=kwargs['order'])
    convert_timestamps_to_isoformat(fish_multisig)

    return jsonify(prices=prices, circulating_supply=circulating_supply, market_cap=market_cap, fish_unique_wallets=fish_unique_wallets,
        fish_active_wallets=fish_active_wallets, fish_vesting=fish_vesting, fish_staking=fish_staking, fish_multisig=fish_multisig)
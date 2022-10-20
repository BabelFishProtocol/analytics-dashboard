from .models.data_models import *
import datetime


def create_record(model, data):
    if model == Balance:
        return Balance(timestamp=data['date'], balance=data['balance'])
    elif model == NetDeposits:
        return NetDeposits(timestamp=data['date'], 
                net_deposits_by_collateral=data['net_deposits_by_collateral'], 
                net_deposits_value=data['net_deposits_total_value'])
    elif model == UniqueWallets:
        return UniqueWallets(timestamp=data['date'], unique_wallets_count=data['unique_wallets_count'])
    elif model == ActiveWallets:
        return ActiveWallets(timestamp=data['date'], daily_active_wallets_count=data['daw_count'])
    elif model == Price:
        return Price(timestamp=data['date'], ticker=data['ticker'], prices=data['prices'])
    elif model == CirculatingSupply:
        return CirculatingSupply(timestamp=data['date'], circulating_supply=data['circulating_supply'])
    elif model == MarketCap:
        return MarketCap(timestamp=data['date'], market_cap=data['market_cap'])
    elif model == FishUniqueWallets:
        return FishUniqueWallets(timestamp=data['date'], unique_wallets_count=data['unique_wallets_count'])
    elif model == FishActiveWallets:
        return FishActiveWallets(timestamp=data['date'], daily_active_wallets_count=data['daw_count'])
    elif model == FishVesting:
        return FishVesting(timestamp=data['date'], funds_in_vesting=data['funds_in_vesting'])
    elif model == FishVestingContract:
        return FishVestingContract(address=data['address'])
    elif model == FishStaking:
        return FishStaking(timestamp=data['date'], funds_in_staking=data['funds_in_staking'])
    elif model == FishMultisig:
        return FishMultisig(timestamp=data['date'], balance=data['balance'])



def save_data(data, model):
    Model = model
    if isinstance(data, dict):
        data = [data]

    if len(data) > 1:
        db_data = Model.query.all()
    elif len(data) == 1:
        if model == FishVestingContract:
            db_data = []
        else:
            dt_start = datetime.datetime.combine(data[0]['date'], datetime.datetime.min.time())
            dt_end = datetime.datetime.combine(data[0]['date'], datetime.datetime.max.time())
            db_data = Model.query.filter(Model.timestamp >= dt_start, Model.timestamp <= dt_end).all()
    else:
        return

    for data_point in data:
        for db_data_point in db_data:
            if 'date' in data_point and data_point['date'] == db_data_point.timestamp.date():
                db.session.delete(db_data_point)
        db.session.commit()

        db.session.add(create_record(Model, data_point))

    db.session.commit()


def save_balances(balances):
    save_data(balances, Balance)


def save_net_deposits(net_deposits):
    save_data(net_deposits, NetDeposits)


def save_unique_wallets_count(wallets_count):
    save_data(wallets_count, UniqueWallets)


def save_daily_active_wallets_count(wallets_count):
    save_data(wallets_count, ActiveWallets)


def save_prices(prices):
    save_data(prices, Price)


def save_circulating_supply(supply):
    save_data(supply, CirculatingSupply)


def save_market_cap(market_cap):
    save_data(market_cap, MarketCap)


def save_fish_unique_wallets_count(wallets_count):
    save_data(wallets_count, FishUniqueWallets)


def save_fish_daily_active_wallets_count(wallets_count):
    save_data(wallets_count, FishActiveWallets)


def save_fish_vesting(vesting):
    save_data(vesting, FishVesting)


def save_fish_vesting_contracts(vesting_contracts):
    save_data(vesting_contracts, FishVestingContract)


def save_fish_staking(staking):
    save_data(staking, FishStaking)


def save_fish_multisig_balance(balance):
    save_data(balance, FishMultisig)
from .. import db

class Balance(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime(), unique=True, nullable=False)
    balance = db.Column(db.JSON(), nullable=False)

    # def to_dict(self):
    #     return {'timestamp': timestamp}


class NetDeposits(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime(), unique=True, nullable=False)
    net_deposits_by_collateral = db.Column(db.JSON(), nullable=False)
    net_deposits_value = db.Column(db.Float(), nullable=False)


class UniqueWallets(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime(), unique=True, nullable=False)
    unique_wallets_count = db.Column(db.Integer(), nullable=False)


class ActiveWallets(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime(), unique=True, nullable=False)
    daily_active_wallets_count = db.Column(db.Integer(), nullable=False)


class Price(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime(), unique=True, nullable=False)
    ticker = db.Column(db.String(), nullable=False)
    prices = db.Column(db.JSON(), nullable=False)


class CirculatingSupply(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime(), unique=True, nullable=False)
    circulating_supply = db.Column(db.Integer(), nullable=False)
    

class MarketCap(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime(), unique=True, nullable=False)
    market_cap = db.Column(db.JSON(), nullable=False)


class FishUniqueWallets(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime(), unique=True, nullable=False)
    unique_wallets_count = db.Column(db.Integer(), nullable=False)


class FishActiveWallets(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime(), unique=True, nullable=False)
    daily_active_wallets_count = db.Column(db.Integer(), nullable=False)


class FishVesting(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime(), unique=True, nullable=False)
    funds_in_vesting = db.Column(db.Float(), nullable=False)


class FishVestingContract(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    address = db.Column(db.String(), unique=True, nullable=False)


class FishStaking(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime(), unique=True, nullable=False)
    funds_in_staking = db.Column(db.Float(), nullable=False)


class FishMultisig(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime(), unique=True, nullable=False)
    balance = db.Column(db.Float(), nullable=False)

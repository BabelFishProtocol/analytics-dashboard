DEBUG = True


COVALENT = {
    'api_url': 'https://api.covalenthq.com/',
    'api_ver': 'v1',
    'chain_id': 30,
    'retry_attempts': 10,
    'retry_wait_time': 15,
    'XUSD_address': '0xb5999795BE0eBb5BAb23144Aa5fD6a02d080299f',
    'basket_address': '0x1440d19436beeaf8517896bffb957a88ec95a00f',
    'XUSD_metadata': {
        'creation_date': '2021-06-07T15:01:30Z'
    },
    'basket_metadata': {
        'creation_date': '2021-06-07T15:11:40Z'
    },
    'FISH_address': '0x055a902303746382Fbb7D18f6aE0df56EFDC5213',
    'FISH_metadata': {
        'total_supply': 420000000,
        'creation_date': '2021-08-21T22:58:29Z'
    },
    'WRBTC_address': '0x542FDA317318eBf1d3DeAF76E0B632741a7e677d',
    'DEX_address': '0x98AcE08d2B759A265ae326f010496BCd63c15Afc',
    'DEX_metadata': {
        'creation_date': '2020-09-30T16:05:35Z'
    },
    'tracked_addresses': {
        # 'vesting_contract': {
        #     'address': '',
        #     'out_of_circulation': True
        # },
        'staking_contract': {
            'address': '0xfd8ea2E5e8591fA791d44731499CDf2e81Cd6A41',
            'out_of_circulation': True,
            'creation_date': '2021-08-24T21:17:51Z'
        },
        'multisig_wallet': {
            'address': '0x26712A09D40F11f34e6C14633eD2C7C34c903eF0',
            'out_of_circulation': True
        },
    },
    'FISH_vesting':{
        'logic_contract': '0x9467785EECFE7199Fa0ceD74EEbFCda11035b147',
        'logic_contract_creation_date': '2021-08-24T21:21:05Z',
        'staking_contract_creation_date': '2021-08-24T21:17:51Z'
    },
    'endpoint_keys': {
        'block': {
            'date_key': 'signed_at',
            'value_key': 'height'
        }
    },
    'daw_to_ignore': [
        '0x0000000000000000000000000000000000000000',
    ],
}

DAYS_INTERVAL_SIZE = None


MODELS_FIELDS = {
    'Balance': ['timestamp', 'balance'],
    'NetDeposits': ['timestamp', 'net_deposits_by_collateral', 'net_deposits_value'],
    'UniqueWallets': ['timestamp', 'unique_wallets_count'],
    'ActiveWallets': ['timestamp', 'daily_active_wallets_count'],
    'Price': ['timestamp', 'ticker', 'prices'],
    'MarketCap': ['timestamp', 'market_cap'],
    'CirculatingSupply': ['timestamp', 'circulating_supply'],
    'FishVesting': ['timestamp', 'funds_in_vesting'],
    'FishStaking': ['timestamp', 'funds_in_staking'],
    'FishMultisig': ['timestamp', 'balance'],
    'FishUniqueWallets': ['timestamp', 'unique_wallets_count'],
    'FishActiveWallets': ['timestamp', 'daily_active_wallets_count'],
}

EXTRACTION_LOCK_KEY = 'data_execution_lock'
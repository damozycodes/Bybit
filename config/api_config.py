BYBIT_CONFIG = {
    'testnet': {
        'api_url': 'https://api-testnet.bybit.com',
        'ws_url': 'wss://stream-testnet.bybit.com',
    },
    'mainnet': {
        'api_url': 'https://api.bybit.com',
        'ws_url': 'wss://stream.bybit.com',
    },
    'endpoints': {
        'account': '/v5/account/wallet-balance',
        'position': '/v5/position/list',
        'leverage': '/v5/position/set-leverage',
        'order': '/v5/order/create',
        'cancel_order': '/v5/order/cancel',
    }
}

def get_exchange_config(exchange_name: str, testnet: bool = True):
    """Get configuration for specific exchange"""
    configs = {
        'bybit': BYBIT_CONFIG,
    }
    
    config = configs.get(exchange_name.lower())
    if not config:
        raise ValueError(f"Unsupported exchange: {exchange_name}")
    
    mode = 'testnet' if testnet else 'mainnet'
    return {**config, **config[mode]}
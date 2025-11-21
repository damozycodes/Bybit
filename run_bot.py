# from bot_controller import TradingBot

# if __name__ == "__main__":
#     bot = TradingBot()

#     bot.open_and_monitor(
#         symbol="BTC/USDT",
#         side="long",          # "long" or "short"
#         quantity=0.001,
#         profit_target=5,       # Take profit at +$5 PnL
#         leverage=10,
#         margin_mode="isolated"
#     )
import ccxt
from pprint import pprint
from config.settings import API_KEY, API_SECRET, EXCHANGE_NAME, TESTNET

exchange_class = getattr(ccxt, EXCHANGE_NAME)
exchange = exchange_class({
    'apiKey': API_KEY,
    'secret': API_SECRET,
})
exchange.set_sandbox_mode(TESTNET)
exchange.options['defaultType'] = 'future'
markets = exchange.load_markets()
exchange.verbose = False

symbol = "BTC/USDT:USDT"
# print(exchange.symbols)

# order = exchange.create_order(
#                 symbol=symbol,
#                 type='Market',
#                 side='Buy',
#                 amount=0.001,
#                 params={}
#             )

positions = exchange.fetch_positions([symbol])
pprint(positions)

# balance = exchange.fetch_balance()
# pprint(balance)
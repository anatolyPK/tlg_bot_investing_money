import aiohttp
from binance.exceptions import BinanceAPIException
# from create_bot import bot
from binance.client import AsyncClient
import os
from keyboards import kb_main_client
from data_base import sqlite_db
from dotenv import load_dotenv

load_dotenv()


async def create_client():
    client = await AsyncClient.create(api_key=os.getenv('API_KEY'), api_secret=os.getenv('SECRET_KEY'))
    return client


# -----------------реализация через aiohttp
async def current_price(token_1: str, token_2: str = 'USDT', user_id: int = None) -> float or int:
    if token_1.lower() == 'usdt':
        token_1 = 'BUSD'
    async with aiohttp.ClientSession() as session:
        params = {'symbol': f'{token_1.upper()}{token_2.upper()}'}
        async with session.get('https://api.binance.com/api/v3/ticker/price', params=params) as res:
            data = await res.json()
            try:
                return float(data['price'])
            except KeyError:
                await bot.send_message(user_id, 'Проверьте токен!')
                return 0


async def post_new_order(state, user_id):
    client = await create_client()
    async with state.proxy() as data:
        symbol = f'{data["symbol_token_buy"]}{data["symbol_token_sell"]}'
        cur_price = await current_price(data["symbol_token_buy"], data["symbol_token_sell"], user_id)
        quantity = f'{round(data["money_usd"] / cur_price)}' if cur_price < 1 else f'{round(data["money_usd"] / cur_price, 1)}'
        try:
            if data['buy_or_sell']:
                order = await client.order_market_buy(symbol=symbol, quantity=quantity)
            else:
                order = await client.order_market_sell(symbol=symbol, quantity=quantity)
            # await bot.send_message(user_id, order) #ответ
            # order = {'symbol': 'XRPUSDT', 'orderId': 5147878144, 'orderListId': -1,
            #     'clientOrderId': 'hkTrH8Rafq9urGk7sKvaDD', 'transactTime': 1682331406711, 'price': '0.00000000',
            # 'origQty': '11.00000000', 'executedQty': '11.00000000', 'cummulativeQuoteQty': '5.09740000',
            # 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'MARKET', 'side': 'SELL', 'workingTime': 1682331406711,
            # 'fills': [{'price': '0.46340000', 'qty': '11.00000000', 'commission': '0.00509740',
            #            'commissionAsset': 'USDT', 'tradeId': 520298793}], 'selfTradePreventionMode': 'NONE'}
            await sqlite_db.sql_add_command(state, user_id, data['buy_or_sell'],
                                            data["symbol_token_buy"].lower(), data["symbol_token_sell"].lower(),
                                            float(order['fills'][0]['qty']), float(order['fills'][0]['price']))
            await sqlite_db.sql_add_command(state, user_id, 0 if data['buy_or_sell'] else 1,
                                            data["symbol_token_sell"].lower(), data["symbol_token_buy"].lower(),
                                            float(order['fills'][0]['qty']) * float(order['fills'][0]['price']),
                                            float(order['fills'][0]['price']))
            await bot.send_message(user_id, 'Успешно!', reply_markup=kb_client)
        except BinanceAPIException as ex:
            await bot.send_message(user_id, f'Ошибка при исполнении ордера!\n{ex}', reply_markup=kb_client)
    await client.close_connection()

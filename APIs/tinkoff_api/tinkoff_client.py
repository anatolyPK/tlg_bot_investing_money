import asyncio
import os
from tinkoff.invest import AsyncClient, Client, InstrumentRequest, InstrumentIdType, SubscriptionInterval, \
    SubscriptionAction, SubscribeCandlesRequest, CandleInstrument, MarketDataRequest
from dotenv import load_dotenv
from data_base import sqlite_db


load_dotenv()

TOKEN = os.getenv("INVEST_TOKEN")


class TinkoffAPI:
    @staticmethod
    def cast_money(v):
        return v.units + v.nano / 1e9

    @classmethod
    async def get_last_price_asset(cls, figi: str) -> float:
        async with AsyncClient(TOKEN) as client:
            value = await client.market_data.get_last_prices(figi=[figi])
            return cls.cast_money(value.last_prices[0].price)

    @staticmethod
    async def get_instrument_info(figi: str = None, ticker: str = None, class_code: str = None):
        async with AsyncClient(TOKEN) as client:
            if figi is None:
                if ticker is None or class_code is None:
                    raise ValueError('figi or both ticker and class_code must be not None')
                return await client.instruments.get_instrument_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                                                                  class_code=class_code, id=ticker)
            return await client.instruments.get_instrument_by(id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI, id=figi)


class CreateAndUpdateAllAssets:
    @staticmethod
    async def __update_all_shares():
        async with AsyncClient(TOKEN) as client:
            values = await client.instruments.shares()
            await sqlite_db.AssetsSQL.add_and_update_shares(values)

    @staticmethod
    async def __update_all_bonds():
        async with AsyncClient(TOKEN) as client:
            values = await client.instruments.bonds()
            await sqlite_db.AssetsSQL.add_and_update_bonds(values)

    @staticmethod
    async def __update_all_etfs():
        async with AsyncClient(TOKEN) as client:
            values = await client.instruments.etfs()
            await sqlite_db.AssetsSQL.add_and_update_etfs(values)

    @staticmethod
    async def __update_all_currencies():
        async with AsyncClient(TOKEN) as client:
            values = await client.instruments.currencies()
            await sqlite_db.AssetsSQL.add_and_update_currencies(values)

    @classmethod
    async def update_all_assets(cls):
        await cls.__update_all_shares()
        await cls.__update_all_bonds()
        await cls.__update_all_etfs()
        await cls.__update_all_currencies()

#
# class MarketStream:
#     @staticmethod
#     async def market_data():
#         async def request_iterator():
#             yield MarketDataRequest(
#                 subscribe_candles_request=SubscribeCandlesRequest(
#                     subscription_action=SubscriptionAction.SUBSCRIPTION_ACTION_SUBSCRIBE,
#                     instruments=[
#                         CandleInstrument(
#                             figi="BBG004730N88",
#                             interval=SubscriptionInterval.SUBSCRIPTION_INTERVAL_FIVE_MINUTES,
#                         )
#                     ],
#                 )
#             )
#             while True:
#                 await asyncio.sleep(1)
#
#         async with AsyncClient(TOKEN) as client:
#             async for marketdata in client.market_data_stream.market_data_stream(
#                     request_iterator()
#             ):
#                 print(marketdata)
#
#
# if __name__ == '__main__':
#     asyncio.run(MarketStream.market_data())

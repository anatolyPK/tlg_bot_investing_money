# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from data_base import sqlite_db
# from datetime import datetime, timedelta
# from create_bot import bot
# from handlers import client
# from binance_api import current_price
#
#
# async def daily_send_currency():
#     unique_id = await sqlite_db.select_all_unique_person_id()
#     tokens_price = ''
#     for token in ('BTC', 'ETH'):
#         price = await current_price(token)
#         tokens_price += f'\n{token}  {price} USD'
#     for id in unique_id:
#         await client.open_portfolio_command(user_id=id)
#         await bot.send_message(id, tokens_price)
#
#
# schedulers = AsyncIOScheduler(timezone='Asia/Vladivostok')
# # schedulers.add_job(daily_send_portfolio, trigger='date', run_date=datetime.now()+timedelta(seconds=3))
# schedulers.add_job(daily_send_currency, trigger='cron', hour=datetime.now().hour,
#                    minute=30, start_date=datetime.now())
# schedulers.start()

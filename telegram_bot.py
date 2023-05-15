from aiogram.utils import executor
from create_bot import dp
from data_base import sqlite_db
from handlers import client, other
from assets.deposits.apsched import schedulers


async def on_startup(*args, **kwargs):
    print('Bot online')
    await sqlite_db.sql_start()


client.register_handlers_clients(dp)
other.register_handlers_other(dp)

schedulers.start()
executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
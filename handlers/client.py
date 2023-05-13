from aiogram import types, Dispatcher
from keyboards import kb_main_client, kb_stop_add
from aiogram.dispatcher import FSMContext
from assets import register_handlers_crypto, register_handlers_deposits
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from data_base import sqlite_db
from create_bot import bot


async def command_start(message: types.Message):
    await message.answer('Hello, man', reply_markup=kb_main_client)


async def cancel_handler(message: types.Message, state=FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.finish()
    await message.reply('okay', reply_markup=kb_main_client)

# --------------------------------------------------------------------


def register_handlers_clients(dp: Dispatcher):#assets hadlers
    dp.register_message_handler(command_start, commands=['start', 'help'])

    dp.register_message_handler(cancel_handler, state='*', commands='отмена')
    dp.register_message_handler(cancel_handler, Text(equals='отмена', ignore_case=True), state='*')

    register_handlers_crypto(dp)
    register_handlers_deposits(dp)



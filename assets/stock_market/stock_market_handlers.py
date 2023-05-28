from aiogram import types, Dispatcher
from keyboards import kb_deposit, kb_stop_add, type_capitalization, generate_inline_keyboards, generate_buttons_assets, kb_stock
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from data_base import sqlite_db
from APIs.tinkoff_api.tinkoff_client import TinkoffAPI, CreateAndUpdateAllAssets
from datetime import datetime


# ----------------------------ADD ASSET---------------------------
class AddAsset(StatesGroup):
    type_of_asset = State()
    num_of_asset = State()
    figi = State()
    is_buy_or_sell = State()
    price_in_rub = State()
    lot = State()
    date_operation = State()


async def start_add_assets(message: types.Message):
    await AddAsset.type_of_asset.set()
    await message.answer('Выберите актив', reply_markup=generate_inline_keyboards([['Акция', 'share'],
                                                                                   ['Облигация', 'bond'],
                                                                                   ['Фонд', 'etf'],
                                                                                   ['Валюта', 'currency']]))


async def get_type_of_asset(callback: types.CallbackQuery, state=FSMContext):
    await callback.message.answer('Введите тикер', reply_markup=kb_stop_add)
    await callback.answer()
    async with state.proxy() as data:
        data['type_of_asset'] = callback.data
    await AddAsset.next()


async def get_assets(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        res = await sqlite_db.AssetsSQL.get_assets_info(assets_type=data['type_of_asset'], ticker=message.text)
        if not res:
            await message.answer('Актив не найден! Введите заново тикер!', reply_markup=kb_stop_add) #как запустить заново хэндлер
        else:
            res = res[0]
            current_price = await TinkoffAPI.get_last_price_asset(res[0])
            data['currency'] = res[2]
            text_inline_kb = [[f'{res[1]}    {current_price} {"USD" if data["currency"] == "usd" else "Руб"}', 'correct'],
                              ['Актив не верный', 'incorrect']]
            await message.answer(f'Выберите нужный инструмент', reply_markup=generate_inline_keyboards(text_inline_kb))
            await AddAsset.next()
            data['assets_price'] = current_price
            data['figi'] = res[0]


async def get_asset(callback: types.CallbackQuery):
    if callback.data == 'correct':
        await callback.message.answer('Выберите операцию', reply_markup=generate_inline_keyboards([['Купить', 'buy'],
                                                                                                  ['Продать', 'sell']]))
        await AddAsset.next()
        await callback.answer()
    elif callback.data == 'incorrect':
        await callback.message.answer('Введите исправленный тикер', reply_markup=kb_stop_add)
        await callback.answer()
        await AddAsset.previous()


async def get_operation_type(callback: types.CallbackQuery, state=FSMContext):
    async with state.proxy() as data:
        if data['currency'] == 'rub':
            await callback.message.answer('Введите стоимость актива в рублях', reply_markup=kb_stop_add)
        elif data['currency'] == 'usd':
            await callback.message.answer('Введите стоимость актива в USD', reply_markup=kb_stop_add)

        data['is_buy_or_sell'] = callback.data
        await AddAsset.next()


async def get_price(message: types.Message, state=FSMContext):
    await message.answer('Введите количество', reply_markup=kb_stop_add)
    async with state.proxy() as data:
        data['price_in_rub'] = int(message.text)
    await AddAsset.next()


async def get_lot(message: types.Message, state=FSMContext):
    date_today = datetime.today().date()
    await message.answer('Введите дату',
                         reply_markup=generate_inline_keyboards([[f'{datetime.strftime(date_today, "%d.%m.%Y")}',
                                                                  f'{datetime.strftime(date_today, "%d.%m.%Y")}']]))
    async with state.proxy() as data:
        data['lot'] = int(message.text)
    await AddAsset.next()


async def get_date_from_callback(callback: types.CallbackQuery, state=FSMContext):
    async with state.proxy() as data:
        await sqlite_db.AssetsSQL.add_assets_transaction(figi=data['figi'],
                                                         person_id=callback.from_user.id,
                                                         is_buy_or_sell=data['is_buy_or_sell'],
                                                         price=data['assets_price'],
                                                         lot=data['lot'],
                                                         date_operation=callback.data
                                                         )

        await callback.message.answer('Готово!', reply_markup=kb_stock)
        await state.finish()


async def get_date_from_message(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        await sqlite_db.AssetsSQL.add_assets_transaction(figi=data['figi'],
                                                person_id=message.from_user.id,
                                                is_buy_or_sell=data['is_buy_or_sell'],
                                                price=data['assets_price'],
                                                lot=data['lot'],
                                                date_operation=message.text
                                                )

        await message.answer('Готово!', reply_markup=kb_stock)
        await state.finish()


async def start_stock_market_window(message: types.Message):
    await message.answer('Выберите операцию!', reply_markup=kb_stock)


async def refresh_assets(message: types.Message): #фикс чтобы не добавлялись еще раз
    await CreateAndUpdateAllAssets.update_all_assets()
    await message.answer('OK', reply_markup=kb_stock)


def register_handlers_stock_market(dp: Dispatcher):
    dp.register_message_handler(start_stock_market_window, Text(equals='фонда', ignore_case=True))

    dp.register_message_handler(start_add_assets, Text(equals='внести операцию', ignore_case=True), state=None)
    dp.register_callback_query_handler(get_type_of_asset, state=AddAsset.type_of_asset)
    dp.register_message_handler(get_assets, state=AddAsset.num_of_asset)
    dp.register_callback_query_handler(get_asset, state=AddAsset.figi)
    dp.register_callback_query_handler(get_operation_type, state=AddAsset.is_buy_or_sell)
    dp.register_message_handler(get_price, state=AddAsset.price_in_rub)
    dp.register_message_handler(get_lot, state=AddAsset.lot)
    dp.register_callback_query_handler(get_date_from_callback, state=AddAsset.date_operation)
    dp.register_message_handler(get_date_from_message, state=AddAsset.date_operation)

    dp.register_message_handler(refresh_assets, Text(equals='Обновить'))


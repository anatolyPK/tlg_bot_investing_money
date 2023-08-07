from aiogram import types, Dispatcher
from keyboards import kb_deposit, kb_stop_add, type_capitalization, generate_inline_keyboards, generate_buttons_assets, kb_stock
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from data_base import sqlite_db
from APIs.tinkoff_api.tinkoff_client import TinkoffAPI, CreateAndUpdateAllAssets
from datetime import datetime


class Decorators:
    @staticmethod
    def retry(description_error):
        def retry_decorator(func):
            async def wrapper(cls, message: types.Message, state: FSMContext):
                try:
                    await func(cls, message, state)
                except ValueError:
                    await message.reply(f'Проверь {description_error}!', reply_markup=kb_stop_add)
            return wrapper
        return retry_decorator


class AddAssets:
    class AddAssetsState(StatesGroup):
        type_of_asset = State()
        num_of_asset = State()
        figi = State()
        is_buy_or_sell = State()
        price_in_rub = State()
        lot = State()
        date_operation = State()

    buttons_for_start_add_assets = [['Акция', 'share'], ['Облигация', 'bond'], ['Фонд', 'etf'], ['Валюта', 'currency']]

    @classmethod
    async def start_add_assets(cls, message: types.Message):
        await cls.AddAssetsState.type_of_asset.set()
        await message.answer('Выберите актив', reply_markup=generate_inline_keyboards(cls.buttons_for_start_add_assets))

    @classmethod
    async def get_type_of_asset(cls, callback: types.CallbackQuery, state=FSMContext):
        await callback.message.answer('Введите тикер', reply_markup=kb_stop_add)
        await callback.answer()
        async with state.proxy() as data:
            data['type_of_asset'] = callback.data
        await cls.AddAssetsState.next()

    @classmethod
    async def get_assets(cls, message: types.Message, state=FSMContext):
        async with state.proxy() as data:
            res = await sqlite_db.AssetsSQL.get_all_assets_info(assets_type=data['type_of_asset'], ticker=message.text)
            if not res:
                await message.answer('Актив не найден! Введите заново тикер!', reply_markup=kb_stop_add)
            else:
                res = res[0]
                current_price = await TinkoffAPI.get_last_price_asset(res[0])
                data['currency'] = res[2]
                text_inline_kb = [[f'{res[1]}    {current_price} {"USD" if data["currency"] == "usd" else "Руб"}', 'correct'],
                                  ['Актив не верный', 'incorrect']]
                await message.answer(f'Выберите нужный инструмент', reply_markup=generate_inline_keyboards(text_inline_kb))
                await cls.AddAssetsState.next()
                data['assets_price'] = current_price
                data['figi'] = res[0]
                data['name'] = res[1]

    @classmethod
    async def get_asset(cls, callback: types.CallbackQuery):
        if callback.data == 'correct':
            await callback.message.answer('Выберите операцию', reply_markup=generate_inline_keyboards([['Купить', 1],
                                                                                                      ['Продать', 0]]))
            await cls.AddAssetsState.next()
            await callback.answer()
        elif callback.data == 'incorrect':
            await callback.message.answer('Введите исправленный тикер', reply_markup=kb_stop_add)
            await callback.answer()
            await cls.AddAssetsState.previous()

    @classmethod
    async def get_operation_type(cls, callback: types.CallbackQuery, state=FSMContext):
        async with state.proxy() as data:
            if data['currency'] == 'rub':
                await callback.message.answer('Введите стоимость актива в рублях', reply_markup=kb_stop_add)
            elif data['currency'] == 'usd':
                await callback.message.answer('Введите стоимость актива в USD', reply_markup=kb_stop_add)

            data['is_buy_or_sell'] = callback.data
            await cls.AddAssetsState.next()

    @classmethod
    @Decorators.retry('стоимость!')
    async def get_price(cls, message: types.Message, state=FSMContext):
        async with state.proxy() as data:
            data['price'] = float(message.text)
        await message.answer('Введите количество', reply_markup=kb_stop_add)
        await cls.AddAssetsState.next()

    @classmethod
    @Decorators.retry('количество!')
    async def get_lot(cls, message: types.Message, state=FSMContext):
        date_today = datetime.today().date()
        async with state.proxy() as data:
            data['lot'] = int(message.text)
        await message.answer('Введите дату',
                             reply_markup=generate_inline_keyboards([[f'{datetime.strftime(date_today, "%d.%m.%Y")}',
                                                                      f'{datetime.strftime(date_today, "%d.%m.%Y")}']]))
        await cls.AddAssetsState.next()

    @classmethod
    async def get_date_from_callback(cls, callback: types.CallbackQuery, state=FSMContext):
        async with state.proxy() as data:
            await sqlite_db.AssetsSQL.add_assets_transaction(name=data['name'],
                                                             figi=data['figi'],
                                                             person_id=callback.from_user.id,
                                                             is_buy_or_sell=data['is_buy_or_sell'],
                                                             price=data['price'],
                                                             lot=data['lot'],
                                                             date_operation=callback.data
                                                             )
            await sqlite_db.AssetsSQL.add_or_update_user_assets(person_id=callback.from_user.id,
                                                                figi=data['figi'],
                                                                lot=data['lot'],
                                                                price=data['price']
                                                                )
            await callback.message.answer('Готово!', reply_markup=kb_stock)
            await state.finish()

    @classmethod
    async def get_date_from_message(cls, message: types.Message, state=FSMContext):
        async with state.proxy() as data:
            await sqlite_db.AssetsSQL.add_assets_transaction(name=data['name'],
                                                             figi=data['figi'],
                                                             person_id=message.from_user.id,
                                                             is_buy_or_sell=data['is_buy_or_sell'],
                                                             price=data['price'],
                                                             lot=data['lot'],
                                                             date_operation=message.text
                                                             )
            await sqlite_db.AssetsSQL.add_or_update_user_assets(person_id=message.from_user.id,
                                                                figi=data['figi'],
                                                                lot=data['lot'],
                                                                price=data['price']
                                                                )
            await message.answer('Готово!', reply_markup=kb_stock)
            await state.finish()


class PersonAssetsPortfolio:

    class CountPriceAsset: #доработать

        def __init__(self, buy_price, lot, current_price, currency):
            self.lot = lot
            self.price_buy = buy_price * self.lot
            self.current_price = current_price
            self.currency = currency

        def get_average_cost(self):
            return round(self.price_buy / self.lot, 1)

        def count_percent_from_average_to_current_price(self):
            average_cost = self.get_average_cost()
            percent_from_average_to_current_price = round((self.current_price / average_cost - 1) * 100, 1)
            if percent_from_average_to_current_price > 0:
                return '+' + str(percent_from_average_to_current_price)
            return percent_from_average_to_current_price

        @staticmethod
        def count_percent_profit(num_1: int, num_2: int):
            average_cost = num_1
            percent_from_average_to_current_price = round((num_2 / average_cost - 1) * 100, 1)
            if percent_from_average_to_current_price > 0:
                return '+' + str(percent_from_average_to_current_price)
            return percent_from_average_to_current_price

        def get_current_price_assets(self):
            return round(self.current_price * self.lot)

    @staticmethod
    async def count_portfolio_cost(values):
        person_assets = {}
        for figi, lot, average_price in values:
            current_price = await TinkoffAPI.get_last_price_asset(figi)
            currency = await sqlite_db.AssetsSQL.get_assets_info(figi, "currency")
            person_assets[figi] = PersonAssetsPortfolio.CountPriceAsset(average_price, lot, current_price, currency)
        return dict(sorted(person_assets.items(), key=lambda item: item[0], reverse=True))

    @classmethod
    async def make_message_answer(cls, person_assets):
        message_answer, investing_summ, total_now_summ = '', 0, 0
        usd_rub_currency = None
        for figi in person_assets.keys():
            now_assets_price = person_assets[figi].get_current_price_assets()
            message_answer += f'{await sqlite_db.AssetsSQL.get_assets_info(figi, "name")}  {now_assets_price} ' \
                              f'{person_assets[figi].currency}  ' \
                              f'{person_assets[figi].count_percent_from_average_to_current_price()} %\n'

            if person_assets[figi].currency == 'rub':
                investing_summ += person_assets[figi].get_average_cost() * person_assets[figi].lot
                total_now_summ += now_assets_price
            elif person_assets[figi].currency == 'usd':
                if not usd_rub_currency:
                    usd_rub_currency = await TinkoffAPI.get_last_price_asset('USD000UTSTOM')
                investing_summ += person_assets[figi].get_average_cost() * usd_rub_currency * person_assets[figi].lot
                total_now_summ += now_assets_price * usd_rub_currency
        profit = PersonAssetsPortfolio.CountPriceAsset.count_percent_profit(investing_summ, total_now_summ)
        return f'Общая сумма - {round(total_now_summ)} Руб {profit} %\n' + message_answer

    @classmethod
    async def get_portfolio_cost(cls, message: types.Message):
        values = await sqlite_db.AssetsSQL.select_all_person_assets(message.from_user.id)
        person_assets = await cls.count_portfolio_cost(values)
        message_answer = await cls.make_message_answer(person_assets)
        await message.answer(message_answer, reply_markup=kb_stock)


async def start_stock_market_window(message: types.Message):
    await message.answer('Выберите операцию!', reply_markup=kb_stock)


async def refresh_assets(message: types.Message):
    await CreateAndUpdateAllAssets.update_all_assets()
    await message.answer('OK', reply_markup=kb_stock)


def register_handlers_stock_market(dp: Dispatcher):
    dp.register_message_handler(start_stock_market_window, Text(equals='фонда', ignore_case=True))

    dp.register_message_handler(PersonAssetsPortfolio.get_portfolio_cost, Text(equals='Активы'))

    dp.register_message_handler(AddAssets.start_add_assets, Text(equals='внести операцию', ignore_case=True), state=None)
    dp.register_callback_query_handler(AddAssets.get_type_of_asset, state=AddAssets.AddAssetsState.type_of_asset)
    dp.register_message_handler(AddAssets.get_assets, state=AddAssets.AddAssetsState.num_of_asset)
    dp.register_callback_query_handler(AddAssets.get_asset, state=AddAssets.AddAssetsState.figi)
    dp.register_callback_query_handler(AddAssets.get_operation_type, state=AddAssets.AddAssetsState.is_buy_or_sell)
    dp.register_message_handler(AddAssets.get_price, state=AddAssets.AddAssetsState.price_in_rub)
    dp.register_message_handler(AddAssets.get_lot, state=AddAssets.AddAssetsState.lot)
    dp.register_callback_query_handler(AddAssets.get_date_from_callback, state=AddAssets.AddAssetsState.date_operation)
    dp.register_message_handler(AddAssets.get_date_from_message, state=AddAssets.AddAssetsState.date_operation)

    dp.register_message_handler(refresh_assets, Text(equals='Обновить'))


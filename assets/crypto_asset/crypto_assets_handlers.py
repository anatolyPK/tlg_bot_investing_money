from aiogram import types, Dispatcher
from keyboards import kb_main_client, kb_stop_add, buy_or_sell_token, token_sell_or_buy, add_history, kb_crypto_client
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from data_base import sqlite_db
from APIs.binance_api import current_price, post_new_order
from create_bot import bot


class AddTransaction(StatesGroup):
    operation = State()
    token_1 = State()
    token_2 = State()
    token_size = State()
    token_price = State()


#check ValueError
def retry(description_error):
    def retry_decorator(func):
        async def wrapper(message: types.Message, state: FSMContext):
            try:
                await func(message, state)
            except ValueError:
                await message.reply(f'Проверь {description_error}!', reply_markup=kb_stop_add)
        return wrapper
    return retry_decorator


# старт машины состояния
async def start_add_transaction(message: types.Message):
    await AddTransaction.operation.set()
    await message.answer('Выбери операцию', reply_markup=buy_or_sell_token)


# ловим первый ответ и т.д.
async def choose_buy_or_sell(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        if message.text == 'Покупка':
            data['operation'] = 1
            await AddTransaction.next()
            await message.answer('Введи первый токен', reply_markup=kb_stop_add)
        elif message.text == 'Продажа':
            data['operation'] = 0
            await AddTransaction.next()
            await message.answer('Введи первый токен', reply_markup=kb_stop_add)
        else:
            await message.reply('Внимательнее! Выбери операцию', reply_markup=buy_or_sell_token)


async def add_token_1(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['token_1'] = message.text.lower()
    await AddTransaction.next()
    await message.answer('Введи второй токен', reply_markup=kb_stop_add)


async def add_token_2(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['token_2'] = message.text.lower()
    await AddTransaction.next()
    await message.answer('Введи количество купленных монет', reply_markup=kb_stop_add)


@retry('количество')
async def add_token_size(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['token_size'] = float(message.text)
    await AddTransaction.next()
    await message.answer('Введи цену за монету', reply_markup=kb_stop_add)


@retry('цену')
async def add_token_price(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
         data['token_price'] = float(message.text)
    #real operation
    await sqlite_db.sql_add_command(state=state, user_id=message.from_user.id)
    #invertion opertaion
    await sqlite_db.sql_add_command(state=state,
                                    user_id=message.from_user.id,
                                    buy_or_sell=0 if data['operation'] else 1,
                                    ticker_1=data['token_2'],
                                    ticker_2=data['token_1'],
                                    size=data['token_price']*data['token_size'],
                                    price=1/data['token_price'])
    await state.finish()
    await message.answer('Готово!', reply_markup=kb_main_client)


async def cancel_handler(message: types.Message, state=FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.finish()
    await message.reply('okay', reply_markup=kb_main_client)


async def command_start(message: types.Message):
    await message.answer('Hello, man', reply_markup=kb_main_client)


# ---------------------------------------------------------------------------------
class BuyOrSellToken(StatesGroup):
    buy_or_sell = State()
    symbol_token_buy = State()
    symbol_token_sell = State()
    money_usd = State()


async def start_buy_or_sell(message: types.Message):
    await BuyOrSellToken.buy_or_sell.set()
    await message.answer('Выбери операцию', reply_markup=token_sell_or_buy)


async def token_buy_or_sell(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['buy_or_sell'] = 1 if message.text.lower() == 'купить' else 0
    await BuyOrSellToken.next()
    await message.answer('Введи токен для покупки', reply_markup=kb_stop_add)


async def choose_symbol_token_buy(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['symbol_token_buy'] = message.text.upper()
    await BuyOrSellToken.next()
    await message.answer('Введи токен для продажи', reply_markup=kb_stop_add)


async def choose_symbol_token_sell(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['symbol_token_sell'] = message.text.upper()
    await BuyOrSellToken.next()
    await message.answer('Введи сумму в $', reply_markup=kb_stop_add)

@retry('сумму')
async def input_usd(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['money_usd'] = float(message.text)
    await post_new_order(state, message.from_user.id)
    await state.finish()


# _________________________________________________________________________________
def percent_count(s: float or int, e: float or int) -> str:
    res = round((e - s) * 100 / s, 1)
    if res >= 0:
        return '+' + str(res) + '%'
    else:
        return str(res) + '%'


async def open_portfolio_command(message: types.Message = None, user_id=None):
    if user_id is None:
        user_id = message.from_user.id
    total_cost, token_size_and_prise = 0, ''
    ticker_cost = await sqlite_db.count_portfolio_cost(user_id=user_id)
    rubusd_current_price = await current_price('busd', 'rub')
    for item in dict(sorted(ticker_cost.items(), key=lambda item: item[1][1] * item[1][0], reverse=True)).items():
        ticker = item[0]
        token_price_current, token_size = item[1]
        total_cost += token_price_current * token_size
        token_size_and_prise += '\n{:8} {:<8.4f} {:<4.1f} USD   {:<6.1f} RUB'.format(ticker.upper(), token_size,
                                token_size * token_price_current,
                                token_size * token_price_current * rubusd_current_price)
    start_rub, start_usd = await sqlite_db.count_all_investing(user_id=message.from_user.id)
    percent_rub, percent_usd = percent_count(start_rub, total_cost * rubusd_current_price), percent_count(start_usd, total_cost)
    await bot.send_message(user_id, f'Портфель - {round(total_cost, 1)} USD {percent_usd} '
                                    f'{round(total_cost * rubusd_current_price)} '
                                    f'RUB {percent_rub}' + token_size_and_prise)


async def add_or_history_transaction(message: types.Message):
    await message.answer('Выбери', reply_markup=add_history)


async def read_history_transaction(message: types.Message):
    mes = await sqlite_db.read_db(user_id=message.from_user.id)
    await message.answer(mes, reply_markup=add_history)


# ___________________________________________________________
class CurrentPrice(StatesGroup):
    symbol_token = State()


async def current_price_token_start(message: types.Message):
    await CurrentPrice.symbol_token.set()
    await message.answer('Введите токен', reply_markup=kb_stop_add)


async def current_price_token(message: types.Message, state=FSMContext):
    token = message.text
    await state.finish()
    price = await current_price(token, user_id=message.from_user.id)
    await message.answer(price, reply_markup=kb_main_client)


# ______________________________________________
class AddMoney(StatesGroup):
    rub_size = State()
    usdt_size = State()


async def add_money_start(message: types.Message):
    await AddMoney.rub_size.set()
    await message.answer('Введите сумму в рублях', reply_markup=kb_stop_add)


@retry('сумму')
async def add_rub_size(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['size_rub'] = float(message.text)
    await AddMoney.next()
    await message.answer('Введите количество USDT', reply_markup=kb_stop_add)


@retry('количество')
async def add_usdt_size(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['usdt_size'] = float(message.text)
        await sqlite_db.add_in_sql_rub_size(user_id=message.from_user.id, state=data)
    await sqlite_db.sql_add_command(state=state, user_id=message.from_user.id, buy_or_sell_token=1, ticker1='usdt',
                                    ticker2='rub', size=float(message.text), price=1)
    await state.finish()
    await message.answer('Операция добавлена!', reply_markup=kb_main_client)


async def start_crypto_operation(message: types.Message):
    await message.answer('Выбери операцию', reply_markup=kb_crypto_client)


def register_handlers_crypto(dp: Dispatcher):#assets hadlers
    dp.register_message_handler(add_or_history_transaction, Text(equals='Операция/история', ignore_case=True))
    dp.register_message_handler(read_history_transaction, Text(equals='История операций', ignore_case=True))
    dp.register_message_handler(add_money_start, Text(equals='Внести средства', ignore_case=True), state=None)
    dp.register_message_handler(add_rub_size, state=AddMoney.rub_size)
    dp.register_message_handler(add_usdt_size, state=AddMoney.usdt_size)
    dp.register_message_handler(start_add_transaction, Text(equals='Добавить операцию', ignore_case=True), state=None)
    dp.register_message_handler(choose_buy_or_sell, state=AddTransaction.operation)
    dp.register_message_handler(add_token_1, state=AddTransaction.token_1)
    dp.register_message_handler(add_token_2, state=AddTransaction.token_2)
    dp.register_message_handler(add_token_size, state=AddTransaction.token_size)
    dp.register_message_handler(add_token_price, state=AddTransaction.token_price)

    dp.register_message_handler(start_buy_or_sell, Text(equals='Купить/продать', ignore_case=True), state=None)
    dp.register_message_handler(token_buy_or_sell, state=BuyOrSellToken.buy_or_sell)
    dp.register_message_handler(choose_symbol_token_buy, state=BuyOrSellToken.symbol_token_buy)
    dp.register_message_handler(choose_symbol_token_sell, state=BuyOrSellToken.symbol_token_sell)
    dp.register_message_handler(input_usd, state=BuyOrSellToken.money_usd)

    dp.register_message_handler(current_price_token_start, Text(equals='курс', ignore_case=True), state=None)
    dp.register_message_handler(current_price_token, state=CurrentPrice)

    dp.register_message_handler(open_portfolio_command, Text(equals='портфель', ignore_case=True))
    dp.register_message_handler(start_crypto_operation, Text(equals='Крипта', ignore_case=True))

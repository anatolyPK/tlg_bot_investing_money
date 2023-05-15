from aiogram import types, Dispatcher
from keyboards import kb_deposit, kb_stop_add, type_capitalization, generate_open_deposits_button, generate_buttons_deposit
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from data_base import sqlite_db


async def get_id_and_description_of_deposit(user_id):
    global id_description
    id_description = await sqlite_db.select_all_person_deposits(user_id)


# --------------------------------ADD OR CHANGE DEPOSIT----------------------
class AddOrChangeDeposit(StatesGroup):
    description = State()
    date_open = State()
    percent = State()
    start_sum = State()
    percent_capitalization = State()


async def start_add_or_change_deposit(message: types.Message):
    await AddOrChangeDeposit.description.set()
    await message.answer('Введите описание вклада', reply_markup=kb_stop_add)


async def get_descriptions(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text
    await AddOrChangeDeposit.next()
    await message.answer('Введите дату открытия вклада  ДД.ММ.ГГГГ', reply_markup=kb_stop_add)


async def get_date_open(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['date_operation'] = message.text
    await AddOrChangeDeposit.next()
    await message.answer('Введите процент', reply_markup=kb_stop_add)


async def get_percent(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['percent'] = float(message.text)
    await AddOrChangeDeposit.next()
    await message.answer('Введите сумму', reply_markup=kb_stop_add)


async def get_start_sum(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['summ'] = float(message.text)
    await AddOrChangeDeposit.next()
    await message.answer('Выберите тип капитализации', reply_markup=type_capitalization)


async def get_percent_capitalization(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        last_row_id = await sqlite_db.add_deposit(message.from_user.id, data['description'], data['date_operation'],
                                                  data['percent'], message.text)
        await sqlite_db.add_deposit_transaction(message.from_user.id, last_row_id, data['summ'], 1,
                                                data['date_operation'])
    await state.finish()
    await message.answer('Готово!', reply_markup=kb_deposit)


# ------------------------------ADD OR TAKE SUM FROM DEPOSIT---------------------
class AddOrTakeSumFromDeposit(StatesGroup):
    deposit_id = State()
    is_add_or_take = State()
    summ = State()
    date_add = State()


async def start_add_or_take_from_deposit(message: types.Message):
    await AddOrTakeSumFromDeposit.deposit_id.set()
    await get_id_and_description_of_deposit(message.from_user.id)
    await message.answer('Выберите вклад', reply_markup=generate_open_deposits_button(id_description))


async def get_deposit_id(message: types.Message, state=FSMContext):
    for row in id_description:
        if message.text == row[1]:
            async with state.proxy() as data:
                data['deposit_id'] = row[0]
                break
    await AddOrTakeSumFromDeposit.next()
    await message.answer('Выберите операцию', reply_markup=generate_buttons_deposit(['Пополнение', 'Снятие']))


async def get_is_add_or_take(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['is_add_or_take'] = 0 if message.text == 'Снятие' else 1
    await AddOrTakeSumFromDeposit.next()
    await message.answer('Введите сумму', reply_markup=kb_stop_add)


async def get_summ(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data['summ'] = float(message.text)
    await AddOrTakeSumFromDeposit.next()
    await message.answer('Введите дату ДД.ММ.ГГГГ', reply_markup=kb_stop_add)


async def get_date_add(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        await sqlite_db.add_deposit_transaction(message.from_user.id, data['deposit_id'], data['summ'],
                                                data['is_add_or_take'], message.text)
    await state.finish()
    await message.answer('Готово!', reply_markup=kb_deposit)


# -----------------------------CHANGE PERCENT---------------------------
class ChangeDepositPercent(StatesGroup):
    deposit_id = State()
    new_percent = State()


async def start_change_deposit_percent(message: types.Message):
    await ChangeDepositPercent.deposit_id.set()
    await get_id_and_description_of_deposit(message.from_user.id)
    await message.answer('Выберите вклад', reply_markup=generate_open_deposits_button(id_description))


async def get_deposit_id_for_new_percent(message: types.Message, state=FSMContext):
    for row in id_description:
        if message.text == row[1]:
            async with state.proxy() as data:
                data['deposit_id'] = row[0]
                break
    await ChangeDepositPercent.next()
    await message.answer('Введите новый процент', reply_markup=kb_stop_add)


async def get_new_percent(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        await sqlite_db.update_new_percent(message.from_user.id, float(message.text), data['deposit_id'])
    await state.finish()
    await message.answer('Готово!', reply_markup=kb_deposit)


# -----------------------------CLOSE DEPOSIT-----------------------------
class CloseDeposit(StatesGroup):
    deposit_id = State()


async def start_close_deposit(message: types.Message):
    await CloseDeposit.deposit_id.set()
    await get_id_and_description_of_deposit(message.from_user.id)
    await message.answer('Выберите вклад', reply_markup=generate_open_deposits_button(id_description))


async def get_deposit_id_for_close(message: types.Message, state=FSMContext):
    for row in id_description:
        if message.text == row[1]:
            await sqlite_db.update_close_deposit(message.from_user.id, row[0])
            break
    await state.finish()
    await message.answer('Вклад закрыт!', reply_markup=kb_deposit)


async def open_deposit_window(message: types.Message):
    depos_descr_and_size = await sqlite_db.count_deposits_money(message.from_user.id)
    mes = ''
    for descr, size in depos_descr_and_size.items():
        mes += f'{descr}    {size} рублей\n'

    await message.answer(mes, reply_markup=kb_deposit)


async def start_deposit_window(message: types.Message):
    total_sum = await sqlite_db.count_deposits_money(message.from_user.id)
    total = sum([size for size in total_sum.values()])
    await message.answer(f'Общая сумма вкладов - {total}', reply_markup=kb_deposit)


def register_handlers_deposits(dp: Dispatcher):#assets hadlers
    dp.register_message_handler(start_deposit_window, Text(equals='вклады', ignore_case=True))

    dp.register_message_handler(open_deposit_window, Text(equals='активные вклады', ignore_case=True))

    dp.register_message_handler(start_add_or_change_deposit, Text(equals='Добавить вклад', ignore_case=True),
                                state=None)
    dp.register_message_handler(get_descriptions, state=AddOrChangeDeposit.description)
    dp.register_message_handler(get_date_open, state=AddOrChangeDeposit.date_open)
    dp.register_message_handler(get_percent, state=AddOrChangeDeposit.percent)
    dp.register_message_handler(get_start_sum, state=AddOrChangeDeposit.start_sum)
    dp.register_message_handler(get_percent_capitalization, state=AddOrChangeDeposit.percent_capitalization)

    dp.register_message_handler(start_add_or_take_from_deposit, Text(equals='внести сумму', ignore_case=True),
                                state=None)
    dp.register_message_handler(get_deposit_id, state=AddOrTakeSumFromDeposit.deposit_id)
    dp.register_message_handler(get_is_add_or_take, state=AddOrTakeSumFromDeposit.is_add_or_take)
    dp.register_message_handler(get_summ, state=AddOrTakeSumFromDeposit.summ)
    dp.register_message_handler(get_date_add, state=AddOrTakeSumFromDeposit.date_add)

    dp.register_message_handler(start_change_deposit_percent, Text(equals='изменить процент', ignore_case=True),
                                state=None)
    dp.register_message_handler(get_deposit_id_for_new_percent, state=ChangeDepositPercent.deposit_id)
    dp.register_message_handler(get_new_percent, state=ChangeDepositPercent.new_percent)

    dp.register_message_handler(start_close_deposit, Text(equals='закрыть вклад', ignore_case=True),
                                state=None)
    dp.register_message_handler(get_deposit_id_for_close, state=CloseDeposit.deposit_id)


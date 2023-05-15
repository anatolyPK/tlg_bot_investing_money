from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


b1 = KeyboardButton('Изменить процент')
b2 = KeyboardButton('Добавить вклад')
b3 = KeyboardButton('Закрыть вклад')
b4 = KeyboardButton('Внести сумму')
b5 = KeyboardButton('Отмена')
b6 = KeyboardButton('Активные вклады')
kb_deposit = ReplyKeyboardMarkup(resize_keyboard=True)
kb_deposit.add(b6).insert(b2).insert(b4).add(b1).insert(b3).insert(b5)

b_1 = KeyboardButton('Ежемесячная')
b_2 = KeyboardButton('Ежегодная')
type_capitalization = ReplyKeyboardMarkup(resize_keyboard=True)
type_capitalization.add(b_1).insert(b_2).insert(b5)


def generate_open_deposits_button(id_and_description):
    kb_open_deposits = ReplyKeyboardMarkup(resize_keyboard=True)
    for row in id_and_description:
        button = KeyboardButton(row[1])
        kb_open_deposits.add(button)
    kb_open_deposits.add(b5)
    return kb_open_deposits


def generate_buttons_deposit(buttons):
    kb_deposits = ReplyKeyboardMarkup(resize_keyboard=True)
    for but in buttons:
        button = KeyboardButton(but)
        kb_deposits.add(button)
    kb_deposits.add(b5)
    return kb_deposits

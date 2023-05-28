from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


b1 = KeyboardButton('Портфель')
b2 = KeyboardButton('Внести операцию')
b5 = KeyboardButton('Отмена')
b3 = KeyboardButton('Обновить')
kb_stock = ReplyKeyboardMarkup(resize_keyboard=True)
kb_stock.add(b1).insert(b2).add(b5).insert(b3)


def generate_buttons_assets(buttons):
    kb_deposits = ReplyKeyboardMarkup(resize_keyboard=True)
    for but in buttons:
        button = KeyboardButton(but)
        kb_deposits.add(button)
    kb_deposits.add(b5)
    return kb_deposits


def generate_inline_keyboards(buttons: [list[str, str]]):
    inl_keyb = InlineKeyboardMarkup(row_width=2)
    for text, callback in buttons:
        button = InlineKeyboardButton(text=text, callback_data=callback)
        inl_keyb.add(button)
    return inl_keyb

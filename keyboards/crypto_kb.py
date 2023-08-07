from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

stop_add_trans = KeyboardButton('Отмена')

buy_token = KeyboardButton('Покупка')
sell_token = KeyboardButton('Продажа')
buy_or_sell_token = ReplyKeyboardMarkup(resize_keyboard=True)
buy_or_sell_token.row(buy_token, sell_token).add(stop_add_trans)


token_buy = KeyboardButton('Купить')
token_sell = KeyboardButton('Продать')
token_sell_or_buy = ReplyKeyboardMarkup(resize_keyboard=True)
token_sell_or_buy.row(token_buy, token_sell).add(stop_add_trans)


key_1 = KeyboardButton('Добавить операцию')
key_2 = KeyboardButton('История операций')
key_3 = KeyboardButton('Внести средства')
add_history = ReplyKeyboardMarkup(resize_keyboard=True)
add_history.row(key_1, key_2, key_3).add(stop_add_trans)



b_1 = KeyboardButton('Портфель')
b_2 = KeyboardButton('Операция/история')
b_3 = KeyboardButton('Купить/Продать')
kb_crypto_client = ReplyKeyboardMarkup(resize_keyboard=True)
kb_crypto_client.add(b_1).insert(b_2).add(b_3).insert(stop_add_trans)

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


b2 = KeyboardButton('Вклады')
b3 = KeyboardButton('Крипта')
b4 = KeyboardButton('Фонда')
kb_main_client = ReplyKeyboardMarkup(resize_keyboard=True)
kb_main_client.add(b3).insert(b4).add(b2)


stop_add_trans = KeyboardButton('Отмена')
kb_stop_add = ReplyKeyboardMarkup(resize_keyboard=True)
kb_stop_add.add(stop_add_trans)

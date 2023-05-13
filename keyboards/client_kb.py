from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


b1 = KeyboardButton('ИИС')
b2 = KeyboardButton('Вклады')
b3 = KeyboardButton('Крипта')
b4 = KeyboardButton('Фонда')
kb_main_client = ReplyKeyboardMarkup(resize_keyboard=True)
kb_main_client.add(b1).insert(b2).add(b3).insert(b4)


stop_add_trans = KeyboardButton('Отмена')
kb_stop_add = ReplyKeyboardMarkup(resize_keyboard=True)
kb_stop_add.add(stop_add_trans)

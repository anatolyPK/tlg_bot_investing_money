from aiogram import types, Dispatcher


async def echo_send(message: types.Message):
    await message.answer(message.text)


def register_handlers_other(dp: Dispatcher):
    dp.register_message_handler(echo_send)

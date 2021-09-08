import logging
import config
import datetime
from pymongo import MongoClient
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters import Text
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,

)





TOKEN = config.token





cluster = MongoClient(
    "mongodb+srv://admin:148xzm58gbo@cluster0.tdbye.mongodb.net/DataBot?retryWrites=true&w=majority", ssl=True, ssl_cert_reqs='CERT_NONE'
)


db = cluster["DataBot"]

workers = db["problem"]


bot = Bot(token=TOKEN)

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)

logging.basicConfig(level=logging.INFO)
dp.middleware.setup(LoggingMiddleware())


reg_button = KeyboardButton("Подать заявку")
reg_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
reg_keyboard.add(reg_button)


cancel_button = KeyboardButton("Отмена")
cancel_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
cancel_keyboard.add(cancel_button)


















class Anketa(StatesGroup):

    name = State()
    company = State()
    phone = State()
    problem = State()



@dp.message_handler(commands=["start"])
async def welcome(message: types.Message):

    if not workers.find_one({"_id": message.chat.id}):
        await bot.send_message(
            message.chat.id,
            f"<b>Здравтсвуйте!</b>\n\n"
            f"Чтобы подать заявку, нажмите на кнопку <b>Подать заявку</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=reg_keyboard,
        )
    else:
        await bot.send_message(
            message.chat.id, "Неизвестная ошибка"
        )



@dp.message_handler(Text(equals="Отмена"), state="*")
async def menu_button(message: types.Message, state: FSMContext):
    await state.finish()
    await bot.send_message(
        message.chat.id, "Заявка отменена.", reply_markup=reg_keyboard
    )



@dp.message_handler(Text(equals="Подать заявку"), state="*")
async def name(message: types.Message, state: FSMContext):
    await bot.send_message(
        message.chat.id, "Введите своё имя:", reply_markup=cancel_keyboard
    )

    await Anketa.name.set()


@dp.message_handler(state=Anketa.name, content_types=types.ContentTypes.TEXT)
async def company(message: types.Message, state: FSMContext):

    await state.update_data(name=message.text)
    await bot.send_message(
        message.chat.id, "Введите название компании:", reply_markup=cancel_keyboard
    )
    await Anketa.company.set()

@dp.message_handler(state=Anketa.company, content_types=types.ContentTypes.TEXT)
async def phone(message: types.Message, state: FSMContext):

    await state.update_data(company=message.text)
    await bot.send_message(
        message.chat.id, "Введите номер телефона:", reply_markup=cancel_keyboard
    )
    await Anketa.phone.set()

@dp.message_handler(state=Anketa.phone, content_types=types.ContentTypes.TEXT)
async def phone(message: types.Message, state: FSMContext):
    
    await state.update_data(phone=message.text)
    await bot.send_message(
        message.chat.id, "Опишите проблему:", reply_markup=cancel_keyboard
    )
    await Anketa.problem.set()


@dp.message_handler(state=Anketa.problem, content_types=types.ContentTypes.TEXT)
async def confirmation(message: types.Message, state: FSMContext):
    await state.update_data(problem=message.text)
    data = await state.get_data()
    await bot.send_message(
        message.chat.id, "Заявка успешно подана."

    )

    workers.insert_one(
        {
            "time": datetime.datetime.now(),
            "name": data.get("name"),
            "company": data.get("company"),
            "phone": data.get("phone"),
            "problem": data.get("problem")

        }
    )
    print("Кто то подал заявку, проврь базу")

if __name__ == "__main__":

    executor.start_polling(dp, skip_updates=True)

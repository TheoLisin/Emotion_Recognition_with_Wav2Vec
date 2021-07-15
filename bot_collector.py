import os
import asyncio
import logging

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, storage, FSMContext
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiohttp.client import request
from audio_parser import save_wav
from dataclasses import dataclass
from enum import Enum
from logger_funcs import start_logging
from typing import List, Optional, Dict


BOT_TOKEN = os.environ['BOT_TOKEN']
COLLECT_PATH = os.environ['COLLECT_PATH']
LOGS_FILE = os.environ['LOGS_FILE']

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN, timeout=5)
dp = Dispatcher(bot, storage=storage)


logger = logging.getLogger(__name__)
f_handler = logging.FileHandler(LOGS_FILE)
f_handler.setLevel(logging.DEBUG)
f_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(f_handler)


class AudioLoad(StatesGroup):
    waiting_label = State()


class Emotions(Enum):
    ANGRY = "angry"
    CALM = "calm"
    DISGUST = "disgust"
    FEARFUL = "fearful"
    HAPPY = "happy"
    NEUTRAL = "neutral"
    SAD = "sad"
    SURPRISED = "surprised"


@dataclass
class ButtonInfo():
    text: str
    callback_data: Optional[str] = None

    def get_button_params(self) -> Dict[str, str]:
        params = {}

        if self.text is not None:
            params["text"] = self.text

        if self.callback_data is not None:
            params["callback_data"] = self.callback_data
        else:
            params["callback_data"] = self.text

        return params


EMOTIONS_BUTTONS_INFO = [ButtonInfo(text=emo.value) for emo in Emotions]
OTVAL = 'https://memepedia.ru/wp-content/uploads/2019/11/15655259183450.jpg'


@dp.message_handler(commands='OTVAL', state="*")
async def send_otval(message: types.Message):
    await message.reply_photo(OTVAL, caption="Тестовый отвал")


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    text = "".join(["Привет! Я бот-коллектор. Пришёл собрать немного данных)",
                    "\nТебе нужно будет прислать эмоциональное голосовое сообщение,",
                    " а затем выбрать одну из восьми эмойций.",
                    " Если хочешь, запиши пару любимых фраз из фильмов.",
                    "\n\nP.S. Желательно записывать не дольше 5 секунд и на английском."])
    await message.reply(text)


@dp.message_handler()
async def echo(message: types.Message):
    text = "\n".join(["Я готов тебя выслушать.",
                      "Можешь записать мне эмоциональное голосовое.",
                      "Или любимую фразу из фильма)",
                      "\nP.S. Желательно записывать не дольше 5 секунд и на английском."])

    await message.answer(text)


@dp.message_handler(content_types=['voice'], state="*")
async def get_audio(message: types.Message, state: FSMContext):
    await AudioLoad.waiting_label.set()
    record_info = await bot.get_file(message.voice.file_id)
    await state.update_data(last_record_info=record_info)
    emo_keyboard = get_keyboard(EMOTIONS_BUTTONS_INFO)
    await message.reply("Теперь выбери эмоцию",
                        reply_markup=emo_keyboard)


@dp.message_handler(text=[emo_info.text for emo_info in EMOTIONS_BUTTONS_INFO],
                    state=AudioLoad.waiting_label)
async def get_label(message: types.Message, state: FSMContext):
    await message.answer(text="Спасибо! Можешь ещё что-нибудь записать")
    user_record = await state.get_data()
    last_record_info = user_record['last_record_info']
    name, ogg_name = create_file_name(message, file_path=COLLECT_PATH)
    try:
        await bot.download_file(last_record_info.file_path, ogg_name)
        save_wav(name, COLLECT_PATH)
    except Exception as unknown_err:
        await bot.send_photo(state.chat, OTVAL, caption="Произошёл отвал. Сообщите @TedFox!")
        start_logging(user_id=message.chat.id, file_name=name,
                      exception=unknown_err, logger=logger)
    await state.finish()


def get_keyboard(buttons_info: List[ButtonInfo],
                 resize=True, one_time_kb=True) -> types.ReplyKeyboardMarkup:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=resize,
                                         one_time_keyboard=one_time_kb)
    for button_info in buttons_info:
        button = types.KeyboardButton(**button_info.get_button_params())
        keyboard.add(button)
    return keyboard


def create_file_name(message: types.Message,
                     file_format: str = ".ogg",
                     file_path: str = None):
    name = "_".join([str(message.chat.id), str(
        message.message_id), message.text])

    if file_path is not None:
        name = file_path + name

    format_name = "_".join([name, file_format])
    return name + '_', format_name


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO)
    # logging.info(f">>>> Start logging <<<<")
    executor.start_polling(dp, skip_updates=True)

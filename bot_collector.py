import os
import asyncio
import logging
from aiogram.types import reply_keyboard
import numpy as np

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, storage, FSMContext
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiohttp.client import request
from numpy.testing._private.utils import measure
from audio_parser import save_wav, ogg_to_wav
from dataclasses import dataclass
from enum import Enum
from logger_funcs import start_logging
from typing import List, Optional, Dict
from model_funcs import load_model, predict, get_emo_msg_and_top


BOT_TOKEN = os.environ['BOT_TOKEN']
COLLECT_PATH = os.environ['COLLECT_PATH']
LOGS_FILE = os.environ['LOGS_FILE']
MODEL_PATH = os.environ['MODEL_PATH']
TEMP_PATH = os.environ['TEMP_PATH']
RES_FILE = os.environ['RES_FILE']

# "jonatasgrosman/wav2vec2-large-xlsr-53-english"
HF_MODEL = os.environ['HF_MODEL']


storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN, timeout=5)
dp = Dispatcher(bot, storage=storage)


model, processor, config, sr, device = load_model(MODEL_PATH,
                                                  pretrained_model_path=HF_MODEL)

err_logger = logging.getLogger(__name__)
res_logger = logging.getLogger(__name__)

err_handler = logging.FileHandler(LOGS_FILE)
err_handler.setLevel(logging.DEBUG)
err_handler.setFormatter(logging.Formatter('%(message)s'))
err_logger.addHandler(err_handler)

res_handler = logging.FileHandler(RES_FILE)
res_handler.setLevel(logging.DEBUG)
res_handler.setFormatter(logging.Formatter('%(message)s'))
res_logger.addHandler(res_handler)


class PredictAndCollect(StatesGroup):
    test_mode = State()
    full_mode = State()
    predict_emo = State()
    rate_prediction = State()


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
OTVAL = ['http://img.picturequotes.com/2/679/678642/sad-emo-quote-3-picture-quote-1.jpg',
         'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTDNI1NI5cqZ9vHdttBwPxLYON6xTwhx_A-1s0nCBY4wLsEx6P5TZdrQjd_zVM3reNOK9M&usqp=CAU',
         'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRFfPVPPW79G-h_2lNldBK4xInuM5wPu0IOKw&usqp=CAU',
         'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRqc9NL4S2cJy5vXjM89YUrrhyESnhbbOUhww&usqp=CAU',
         'https://medportal.ru/pictures/news/c1fcf83a-c36b-4211-8a41-aae685247882/medium.jpg',
         'https://memegenerator.net/img/instances/85179270.jpg']


@dp.message_handler(commands='OTVAL', state="*")
async def send_otval(message: types.Message):
    ind = np.random.randint(0, len(OTVAL))
    await message.reply_photo(OTVAL[ind], caption="Тестовый отвал")


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    text = "".join(["Привет! Я эмобот - чувствительная натура. ",
                    "Запиши мне голосовое и я попробую предсказать эмоцию.",
                    "\nОбязательно оцени мою работу в режиме тестирования!",
                    "\n\nРежим /test для тестирования (в это режими ты поможешь собирать нам данные).",
                    "\nРежим /full для классификации больших сообщений с помощью emoji"])
    await message.reply(text)


@dp.message_handler(commands=['test', 'full'], state='*')
async def change_mode(message: types.Message, state: FSMContext):
    await state.finish()
    if message.text == 'full':
        await message.reply("Пока работает только тест)")
        await PredictAndCollect.test_mode.set()
        # await state.update_data(test=False)
    else:
        await PredictAndCollect.test_mode.set()
        # await state.update_data(test=True)


@dp.message_handler(content_types=['voice'], state=PredictAndCollect.test_mode)
async def get_audio(message: types.Message, state: FSMContext):
    await PredictAndCollect.rate_prediction.set()
    name, ogg_name = create_file_name(
        message, file_path=COLLECT_PATH, text=False)

    try:
        record_info = await bot.get_file(message.voice.file_id)
        await bot.download_file(record_info.file_path, ogg_name)
        audio, _ = ogg_to_wav(name, new_sr=sr, save=True)

        emo_dist = predict(audio, model, processor, config, sr, device)

        msg, top_two, _ = get_emo_msg_and_top(emo_dist)

        await state.update_data(pred=top_two)
        await state.update_data(file_name=name)

        kb = get_keyboard(EMOTIONS_BUTTONS_INFO)
        await message.reply(msg)
        rate_text = "Отметь пожалуйста эмоцию, с которой ты действительно говорил)"
        await bot.send_message(message.chat.id, text=rate_text, reply_markup=kb)

    except Exception as unknown_err:
        ind = np.random.randint(0, len(OTVAL))
        await bot.send_photo(state.chat, OTVAL[ind], caption="Произошёл отвал. Сообщите @TedFox!")
        start_logging(message.chat.id, name,
                      exception=unknown_err,
                      err_mode=True, logger=err_logger)


@dp.message_handler(text=[emo_info.text for emo_info in EMOTIONS_BUTTONS_INFO],
                    state=PredictAndCollect.rate_prediction)
async def get_label(message: types.Message, state: FSMContext):
    await message.answer(text="Спасибо! Можешь ещё что-нибудь записать")
    user_record = await state.get_data()
    start_logging(user_id=message.chat.id,
                  file_name=user_record['file_name'],
                  logger=res_logger,
                  label=message.text,
                  top_two=user_record['pred'])

    await state.finish()
    await PredictAndCollect.test_mode.set()


@dp.message_handler(content_types=['text'])
async def simple_answer(message: types.Message):
    await message.reply("Я тебя могу послушать, котик")


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
                     file_path: str = None, text=True):
    if text:
        message_text = message.text
    else:
        message_text = ""
    name = "_".join([str(message.chat.id), str(
        message.message_id), message_text])

    if file_path is not None:
        name = file_path + name

    format_name = "_".join([name, file_format])
    return name + '_', format_name


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO)
    # logging.info(f">>>> Start logging <<<<")
    executor.start_polling(dp, skip_updates=True)

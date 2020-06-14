import os, json
import redis
import numpy as np

import telebot
from telebot import types

import warnings

warnings.filterwarnings('ignore')

bot = telebot.TeleBot(os.environ['BOT_TOKEN'])
REDIS_URL = os.environ.get('REDIS_URL')
all_user_data = {}

BTN_PICTURE = 'Выбери картинку для трансформации'
BTN_STYLE = 'Выбери картинку со стилем'
BTN_DONE = 'Трансформировать'
GREETINGS = ['hi', 'привет']
GO_TO_TRANSFORM = ['ещё', 'да', '+']
ANSWER_BASE = 'Я тебя не понял :('

from my_models import *


def save_data(key, value):
    """
    Сохранение данных по игроку в базу redis
    """
    if REDIS_URL:
        redis_db = redis.from_url(REDIS_URL)
        redis_db.set(key, value)


def load_data(key):
    """
    Загрузка сохраненных данных по игроку
    :param key: id игрока в базе
    :return: строка со словарем
    """
    if REDIS_URL:
        redis_db = redis.from_url(REDIS_URL)
        if redis_db.get(key):
            return redis_db.get(key).decode("utf-8")
    else:
        return all_user_data.get(key)


@bot.message_handler(func=lambda message: True)
def dispatcher(message):
    """
    Диспетчер перехвата сообщений игрока
    :param message: сообщение игрока
    :return: вызов необходимого обработчика с учетом статуса игрока в дереве вопросов
    """
    user_id = str(message.from_user.id)
    if REDIS_URL:  # если подключена база redis
        val_str = load_data(user_id)
        if val_str:
            all_user_data[str(user_id)] = json.loads(val_str)

    if (user_id not in all_user_data) or (all_user_data[user_id] == None):
        all_user_data[user_id] = {}
        all_user_data[user_id]['id_pic'] = ''
        all_user_data[user_id]['id_style'] = ''
        all_user_data[user_id]['state_pic'] = 0
        all_user_data[user_id]['state_style'] = 0

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(types.KeyboardButton(BTN_PICTURE),
                 types.KeyboardButton(BTN_STYLE),
                 types.KeyboardButton(BTN_DONE))

    if message.text.lower().strip() == '/start':
        bot.reply_to(message, 'Это бот для преобразования картинок и фотографий' + '\n' +
                     'путём переноса стиля с одной картинки на другую', reply_markup=keyboard)

    print(all_user_data)
    if all_user_data[user_id]['state_pic'] == 1 or all_user_data[user_id]['state_style'] == 1:
        bot.reply_to(message, 'Нужно выбрать картинку')
    if all_user_data[user_id]['state_pic'] == 0 and all_user_data[user_id]['state_style'] == 0:
        text_handler(message)
    else:
        try:
            print('ветка docum')
            document_handler(message)
        except:
            print('ветка фото')
            photo_handler(message)


def text_handler(message):
    """
    Обработка сообщений на базовом уровне (вход пользователя или после результата игры)
    :param message: сообщение игрока
    :return: Ответ игроку в зависимости от обработки сообщения
    """
    user_id = str(message.from_user.id)
    if message.text.lower().strip() == '/start':
        pass  # обрабатывается в процедуре диспетчера

    elif message.text == BTN_PICTURE:
        all_user_data[user_id]['state_pic'] = 1
        all_user_data[user_id]['state_style'] = 0
        bot.reply_to(message, 'Выбери картинку (фото) для трансформации')
    elif message.text == BTN_STYLE:
        all_user_data[user_id]['state_pic'] = 0
        all_user_data[user_id]['state_style'] = 1
        bot.reply_to(message, 'Выбери картинку (фото) со стилем')
    elif message.text == BTN_DONE:
        if all_user_data[user_id]['id_pic'] == '':
            bot.reply_to(message, 'Не выбрана картника для трансформации')
        elif all_user_data[user_id]['id_style'] == '':
            bot.reply_to(message, 'Не выбрана картника со стилем')
        elif all_user_data[user_id]['id_pic'] == all_user_data[user_id]['id_style']:
            bot.reply_to(message, 'Выбранные картинки совпадают')
        else:
            bot.reply_to(message, 'Это займет некоторое время', reply_markup=types.ReplyKeyboardRemove())
            # style_transform("my_images/panda.jpg", "my_images/wolf.jpg")
            style_transform(all_user_data[user_id]['id_pic'], all_user_data[user_id]['id_style'])
            res_photo = open('out.png', 'rb')

            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            keyboard.add(types.KeyboardButton(BTN_PICTURE),
                         types.KeyboardButton(BTN_STYLE),
                         types.KeyboardButton(BTN_DONE))
            bot.send_photo(message.from_user.id, res_photo, reply_markup=keyboard)
    else:
        bot.reply_to(message, ANSWER_BASE + '\n' + 'Выбери действие из меню клавиатуры')

    # save_data(user_id, json.dumps(all_user_data[user_id]))


@bot.message_handler(content_types=["photo"])
def photo_handler(message):
    user_id = str(message.from_user.id)
    # file_info = bot.get_file(message.photo[-1].file_id)

    if all_user_data[user_id]['state_pic'] == 1:
        all_user_data[user_id]['id_pic'] = bot.get_file_url(message.photo[-1].file_id)
    if all_user_data[user_id]['state_style'] == 1:
        all_user_data[user_id]['id_style'] = bot.get_file_url(message.photo[-1].file_id)

        # if all_user_data[user_id]['state_pic'] == 1:
        #     file_name = user_id + '_1.png'
        #     downloaded_photo = bot.download_file(file_info.file_path)
        #     with open(file_name, 'wb') as new_file:
        #         new_file.write(downloaded_photo)
        #     all_user_data[user_id]['id_pic'] = file_name
        #
        # if all_user_data[user_id]['state_style'] == 1:
        #     file_name = user_id + '_2.png'
        #     downloaded_photo = bot.download_file(file_info.file_path)
        #     with open(file_name, 'wb') as new_file:
        #         new_file.write(downloaded_photo)
        #     all_user_data[user_id]['id_pic'] = file_name

    all_user_data[user_id]['state_pic'] = 0
    all_user_data[user_id]['state_style'] = 0
    bot.reply_to(message, 'Этa картинка принята для обработки')
    # photo = open(file_name, 'rb')
    # bot.send_photo(message.from_user.id, photo)

    # save_data(user_id, json.dumps(all_user_data[user_id]))
    print(all_user_data)


@bot.message_handler(content_types=["document"])
def document_handler(message):
    user_id = str(message.from_user.id)

    if all_user_data[user_id]['state_pic'] == 1:
        all_user_data[user_id]['id_pic'] = bot.get_file_url(message.document.file_id)
    if all_user_data[user_id]['state_style'] == 1:
        all_user_data[user_id]['id_style'] = bot.get_file_url(message.document.file_id)

    all_user_data[user_id]['state_pic'] = 0
    all_user_data[user_id]['state_style'] = 0
    bot.reply_to(message, 'Этa картинка принята для обработки')
    # docum = open(file_name, 'rb')
    # bot.send_photo(message.from_user.id, docum)

    # save_data(user_id, json.dumps(all_user_data[user_id]))
    print(all_user_data)


def style_transform(img_content, img_style):
    #    content_img = image_loader("my_images/panda.jpg")
    #    style_img = image_loader("my_images/wolf.jpg")
    content_img = image_loader_url(img_content)
    style_img = image_loader_url(img_style)

    input_img = content_img.clone()
    output = run_style_transfer(cnn, cnn_normalization_mean, cnn_normalization_std, content_img, style_img, input_img)
    output = output.squeeze()
    np_out = output.cpu().detach().numpy()
    np_out *= 255
    np_out = np.transpose(np_out, (1, 2, 0))
    PIL_from_np = Image.fromarray(np.uint8(np_out))
    PIL_from_np.save('out.png')
    Image.open('out.png')


if __name__ == '__main__':
    # style_transform("my_images/panda.jpg", "my_images/wolf.jpg")
    # style_transform()

    #    if REDIS_URL:
    #        redis_db = redis.from_url(REDIS_URL)
    #        redis_db.delete('409088886')
    bot.polling()

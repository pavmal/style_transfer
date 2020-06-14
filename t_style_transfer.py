import random, time, os, json
import requests
import redis
import numpy as np

import telebot
from telebot import types
from telebot import apihelper

#import config
# from PIL import Image



#apihelper.proxy = {'http': 'socks5://78.46.218.20:14516'}
#apihelper.proxy = {'http': 'socks5://student:TH8FwlMMwWvbJF8FYcq0@178.128.203.1:1080'}

# bot = telebot.TeleBot(config.token)
bot = telebot.TeleBot(os.environ['BOT_TOKEN'])
#apihelper.proxy = {'http': 'socks5://stepik.akentev.com:1080'}


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
        bot.reply_to(message, 'Это бот для преобразования картинок и фотографий' +'\n'+
                                'путём переноса стиля с одной картинки на другую', reply_markup=keyboard)

    print(all_user_data)
    if all_user_data[user_id]['state_pic'] == 1 or all_user_data[user_id]['state_style'] == 1:
        bot.reply_to(message, 'Нужно выбрать картинку')
    if all_user_data[user_id]['state_pic'] == 0 and all_user_data[user_id]['state_style'] == 0:
        text_handler(message)
    else:
        print('ветка фото')
        photo_handler(message)

    # print('Состояние до вопроса:\n{}'.format(all_user_data))
    # if all_user_data[user_id]['state'] == NEW_USER:
    #     handler_new_member(message)
    # elif all_user_data[user_id]['state'] == BASE_STATE:
    #     base_handler(message)
    # elif all_user_data[user_id]['state'] == ASK_QUESTION_STATE:
    #     ask_question(message)
    # else:
    #     bot.reply_to(message, ANSWER_BASE)
    # """ Оставил для возможной обработки фото и стикетов """
    # #    photo_handler(message)
    # # sticker_handler(message)
    #
    # # def new_user_handler(message):
    # """

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
        #bot.reply_to(message, 'Выбери картинку (фото) для трансформации', reply_markup=types.ReplyKeyboardRemove())
        bot.reply_to(message, 'Выбери картинку (фото) для трансформации')
    elif message.text == BTN_STYLE:
        all_user_data[user_id]['state_pic'] = 0
        all_user_data[user_id]['state_style'] = 1
        #bot.reply_to(message, 'Выбери картинку (фото) со стилем', reply_markup=types.ReplyKeyboardRemove())
        bot.reply_to(message, 'Выбери картинку (фото) со стилем')
    elif message.text == BTN_DONE:
        #all_user_data[user_id]['state'] = 1
        bot.reply_to(message, 'Это займет некоторое время')
        style_transform()
        res_photo = open('out.png', 'rb')
        bot.send_photo(message.from_user.id, res_photo)
        #bot.send_photo(message.from_user.id, message.photo[-1].file_id
    else:
        bot.reply_to(message, ANSWER_BASE + '\n' + 'Если хочешь попробовать, напиши: "+"')

    # save_data(user_id, json.dumps(all_user_data[user_id]))



@bot.message_handler(content_types=["photo"])
def photo_handler(message):
    print('begin photo load')
    user_id = str(message.from_user.id)
    if all_user_data[user_id]['state_pic'] == 1:
        #all_user_data[user_id]['id_pic'] = message.photo[0].file_id
        all_user_data[user_id]['id_pic'] = bot.get_file_url(message.photo[0].file_id)
        all_user_data[user_id]['state_pic'] = 0

        print('загрузка фото для трасформации')
    if all_user_data[user_id]['state_style'] == 1:
        #all_user_data[user_id]['id_style'] = message.photo[0].file_id
        all_user_data[user_id]['id_style'] = bot.get_file_url(message.photo[0].file_id)
        all_user_data[user_id]['state_style'] = 0
        print('загрузка фото со стилем')

    #print(message.from_user.id, message.photo[-1].file_id)
    print(message.from_user.id, message.photo[0].file_id)
    print(all_user_data)
    #bot.send_photo(message.from_user.id, message.photo[0].file_id)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(types.KeyboardButton(BTN_PICTURE),
                    types.KeyboardButton(BTN_STYLE),
                    types.KeyboardButton(BTN_DONE))

    bot.reply_to(message, 'Этa картинка принята для обработки', reply_markup=keyboard)
    file_info = bot.get_file(file_id=message.photo[0].file_id)


    print(file_info.file_path)
    res = bot.get_file_url(file_id=message.photo[0].file_id)
    #f = requests.get(res)
    print(res)

    respon = requests.get(res)
    #print(respon.content)
    #with open('111.jpg', 'wb') as new_file:
    #    new_file.write(res)
    print('respon - ok')

    file_info = bot.get_file(message.photo[0].file_id)
    downloaded_photo = bot.download_file(file_info.file_path)
    file_name = user_id + '_1.png'
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_photo)
    photo = open(file_name, 'rb')
    bot.send_photo(message.from_user.id, photo)
    # src = message.photo[0].file_id


    print('ok')
# save_data(user_id, json.dumps(all_user_data[user_id]))


def base_handler(message):
    """
    Обработка сообщений на базовом уровне (вход пользователя или после результата игры)
    :param message: сообщение игрока
    :return: Ответ игроку в зависимости от обработки сообщения
    """
    user_id = str(message.from_user.id)

    if message.text.lower().strip() == '/start':
        pass  # обрабатывается в процедуре диспетчера
    elif message.text.lower().strip() in GREETINGS:
        bot.reply_to(message, 'Ну, Привет, {}!\nЕсли хочешь поиграть, напиши:\n"давай вопрос" или "+"'.format(
            str(message.from_user.first_name)))


    elif message.text.lower().strip() in GO_TO_TRANSFORM:

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.add(types.KeyboardButton(BTN_PICTURE),
                    types.KeyboardButton(BTN_STYLE),
                    types.KeyboardButton(BTN_DONE))
            # проверка выбранных ранее файлов - сообщение пользователю
        bot.reply_to(message, 'Выбери картинки (фото)', reply_markup=keyboard)

    elif message.text.lower().strip() == BTN_PICTURE or message.text.lower().strip() == BTN_STYLE:
        all_user_data[user_id]['state'] = 0


    else:
        bot.reply_to(message, ANSWER_BASE + '\n' + 'Если хочешь попробовать, напиши: "+"')

    # save_data(user_id, json.dumps(all_user_data[user_id]))

#def style_transform(img_content, img_style):
def style_transform():
    style_img = image_loader("my_images/wolf.jpg")  # as well as here
    content_img = image_loader("my_images/panda.jpg")  # измените путь на тот который у вас.

    #input_img = content_img.clone()
    input_img = content_img.clone()
    # if you want to use white noise instead uncomment the below line:
    # input_img = torch.randn(content_img.data.size(), device=device)

    # add the original input image to the figure:
    #models.imshow(input_img, title='Input Image')
    output = run_style_transfer(cnn, cnn_normalization_mean, cnn_normalization_std, content_img, style_img, input_img)

    output = output.squeeze()
    np_out = output.cpu().detach().numpy()
    np_out *= 255
    np_out = np.transpose(np_out, (1, 2, 0))
    PIL_from_np = Image.fromarray(np.uint8(np_out))
    PIL_from_np.save('out.png')
    Image.open('out.png')



if __name__ == '__main__':
    # style_transform()

    #    if REDIS_URL:
    #        redis_db = redis.from_url(REDIS_URL)
    #        redis_db.delete('409088886')
    bot.polling()
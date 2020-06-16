import os
import numpy as np

import telebot
from telebot import types
import warnings

warnings.filterwarnings('ignore')

bot = telebot.TeleBot(os.environ['BOT_TOKEN'])
all_user_data = {}

BTN_PICTURE = 'Выбери картинку для трансформации'
BTN_STYLE = 'Выбери картинку со стилем'
BTN_DONE = 'Трансформировать'
GREETINGS = ['hi', 'привет']
ANSWER_BASE = 'Я тебя не понял :('

from my_models import *


@bot.message_handler(func=lambda message: True)
def dispatcher(message):
    """
    Диспетчер перехвата сообщений игрока
    :param message: сообщение игрока
    :return: вызов необходимого обработчика с учетом статуса игрока в дереве вопросов
    """
    user_id = str(message.from_user.id)
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

    if all_user_data[user_id]['state_pic'] == 1 or all_user_data[user_id]['state_style'] == 1:
        bot.reply_to(message, 'Нужно выбрать картинку')
    if all_user_data[user_id]['state_pic'] == 0 and all_user_data[user_id]['state_style'] == 0:
        text_handler(message)
    else:
        try:
            document_handler(message)
        except:
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

    elif message.text.lower().strip() in GREETINGS:
        bot.reply_to(message, 'Ну, Привет, {}!\nЗагружай картинки и пробуй перенос стиля'.format(
            str(message.from_user.first_name)))

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
            bot.reply_to(message, 'Это займет некоторое время. Ждите...' + '\n' +
                         'Результат будет направлен в ответном сообщении', reply_markup=types.ReplyKeyboardRemove())
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

    print(all_user_data)


def style_transform(img_content, img_style):
    content_img = image_loader("my_images/panda.jpg")
    style_img = image_loader("my_images/wolf.jpg")
    # content_img = image_loader_url(img_content)
    # style_img = image_loader_url(img_style)

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
    style_transform(' ', ' ') #for local test
    #bot.polling()

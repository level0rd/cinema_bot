"""Simple bot for searching movies. Unofficial Kinopoisk API
 are taken from a repository on GitHub:
https://github.com/Ulbwaa/KinoPoiskAPI
"""
import telebot
from telebot import types
from kinopoisk_api import KP
from kinopoisk_unofficial.kinopoisk_api_client import KinopoiskApiClient
from kinopoisk_unofficial.request.films.film_search_by_filters_request import FilmSearchByFiltersRequest
from config import kinopoisk_token, bot_token

kinopoisk = KP(token=kinopoisk_token)
api_client = KinopoiskApiClient(kinopoisk_token)
bot = telebot.TeleBot(bot_token, parse_mode=None)


class DialogState:
    def __init__(self):
        self.menu = ''
        self.exit = False
        self.name = ''
        self.genre = ''
        self.year = ''
        self.score = ''


dialog_state = DialogState()

# start keyboard
start_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
btn_filter = types.KeyboardButton("⚙️Фильтр")
btn_search = types.KeyboardButton("🔍Найти")
start_keyboard.add(btn_filter, btn_search)


@bot.message_handler(commands=['start'])
def welcome(message):

    bot.send_message(message.chat.id, "👋Добро пожаловать, {0.first_name}!\nЯ - {1.first_name}, "
                                      'бот созданный чтобы помочь выбрать наиболее подходящий для тебя фильм. '
                                      '(Для возвращения к началу в любой момент напишите "Меню")'
                                      ''.format(message.from_user, bot.get_me()), reply_markup=start_keyboard)


@bot.message_handler(content_types = ['text'])
def talk(message):

    # genre keyboard
    genre_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_comedy = types.KeyboardButton("😂Комедия")
    btn_action = types.KeyboardButton("💥Боевик")
    btn_thriller = types.KeyboardButton("🔪Триллер")
    btn_horror = types.KeyboardButton("🎃Хоррор")

    genre_keyboard.add(btn_comedy, btn_action, btn_thriller, btn_horror)

    # final keyboard
    fin_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_information = types.KeyboardButton("📖Информация")

    fin_keyboard.add(btn_information)

    # menu keyboard
    menu_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_menu = types.KeyboardButton("Меню")

    menu_keyboard.add(btn_menu)

    if message.chat.type == 'private':
        if message.text == 'Здравствуй' or message.text == 'Привет' or message.text == 'Hello':
            bot.send_message(message.chat.id, 'Привет! Я помогу выбрать наиболее подходящий для тебя фильм. '
                                              'Также я могу показать информацию о интересующем тебя фильме.')

        elif message.text == 'Меню' and dialog_state.menu == '':
            bot.send_message(message.chat.id, "Что ты хочешь сделать?".format(message.from_user, bot.get_me()), reply_markup=start_keyboard)

        elif dialog_state.menu == '🔍Найти':
            search = kinopoisk.search(message.text)
            for item in search:
                bot.send_message(message.from_user.id,
                                 item.ru_name + " (" + item.name + "), " + item.year + ", " + ", ".join(
                                    item.genres) + ", " + "".join(item.kp_rate))
                break

            dialog_state.menu = ''

        elif dialog_state.menu == 'Жанр' and message.text in ['😂Комедия', '💥Боевик', '🔪Триллер', '🎃Хоррор']:
            dialog_state.genre = message.text.lower()
            bot.send_message(message.chat.id, "Позднее какого года вышел фильм?",
                             reply_markup=types.ReplyKeyboardRemove())
            dialog_state.menu = 'Год'

        elif dialog_state.menu == 'Год':
            dialog_state.year = message.text
            bot.send_message(message.chat.id, "Какая максимальная оценка у фильма?")
            dialog_state.menu = 'Оценка'

        elif dialog_state.menu == 'Оценка':
            dialog_state.score = message.text
            request = FilmSearchByFiltersRequest()
            request.year_from = dialog_state.year
            request.rating_to = dialog_state.score
            request.genres = dialog_state.genre
            response = api_client.films.send_film_search_by_filters_request(request)

            code_string = str(response)
            splited_string = code_string.split(',')
            dialog_state.name = splited_string[2].replace(' name_ru=', '').replace("'", '')

            poster = splited_string[13].replace(" poster_url_preview='", '').replace("')", '')
            bot.send_message(message.chat.id, dialog_state.name + poster, reply_markup=fin_keyboard)

            dialog_state.genre = ''
            dialog_state.year = ''
            dialog_state.score = ''
            dialog_state.exit = True
            dialog_state.menu = ''

        elif message.text == '📖Информация' and dialog_state.exit:
            search = kinopoisk.search(dialog_state.name)
            for item in search:
                bot.send_message(message.from_user.id,
                                 item.ru_name + " (" + item.name + "), " + item.year + ", " + ", ".join(
                                    item.genres) + ", " + "".join(item.kp_rate), reply_markup=menu_keyboard)
                break
            dialog_state.exit = False

        elif message.text == '🔍Найти':
            bot.send_message(message.chat.id, "Введите название фильма.", reply_markup=types.ReplyKeyboardRemove())
            dialog_state.menu = 'Найти'

        elif message.text == '⚙Фильтр':
            bot.send_message(message.chat.id, "Какого жанр вы предпочитаете?", reply_markup=genre_keyboard)
            dialog_state.menu = 'Жанр'

        elif dialog_state.menu == '':
            bot.send_message(message.chat.id, "Я не понял ваш запрос! Пожалуйста, введите корректный запрос"
                                              "(для получения списка команда напишите “Меню”).")


bot.polling(none_stop=True)

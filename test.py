import telebot
from telebot import types
import sqlite3
import requests
from g4f.client import Client

def get_db_connection():
    conn = sqlite3.connect('words.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS user_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, word TEXT)")
    conn.commit()
    return conn

def save_user_request(username, word):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_requests (username, word) VALUES (?, ?)", (username, word))
    conn.commit()
    conn.close()

# def get_user_requests(username):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT word FROM user_requests WHERE username = ?", (username,))
#     requests = cursor.fetchall()
#     conn.close()
#     return requests

def get_words(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM user_requests WHERE username = ?", (username,))
    cities = [city[0] for city in cursor.fetchall()]
    conn.close()
    return cities

TOKEN = '6423338394:AAHKHG9mu6PFSLXmhIzCmUfCkB0NxMZ3368'  # Update your token
bot = telebot.TeleBot(TOKEN)
user_info = {}
@bot.message_handler(func=lambda message: message.text == 'Новый запрос')
def new_request(message):
    send_welcome(message)  # Restart the conversation

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_info[message.from_user.id] = {'username': message.from_user.username}
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button_male = types.KeyboardButton('Добавить новое слово')
    button_female = types.KeyboardButton('Составить предложение со словом')
    markup.add(button_female)
    bot.send_message(message.chat.id, "Выберите нужный вам вариант", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['Составить предложение со словом'])
def gender_chosen(message):
    username = user_info.get(message.from_user.id, {}).get('username')
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    words = get_words(username)
    for word in words:
        markup.add(types.KeyboardButton(word))
    bot.send_message(message.chat.id, "Выберите слово", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['Перевод предложения'])
def translate(message):
    client = Client()
    pog = f'Переведи предложение на русский: {sentence}'
    print(pog)
    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[{"role": "user", "content": pog}]
    )
    print(response.choices[0])
    bot.send_message(message.chat.id, response.choices[0].message.content if response.choices else "Не удалось получить ответ от AI.")

@bot.message_handler(func=lambda message: message.text)
def get_sentence(message):
    word = message.text
    global sentence
    pog = f'Составь предложение на английском со словом {word}'
    save_user_request(user_info[message.from_user.id]['username'], word)
    client = Client()
    print(pog)
    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[{"role": "user", "content": pog}]
    )
    print(response)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('Новый запрос'))
    if response.choices:
        sentence = response.choices[0].message.content
        markup.add(types.KeyboardButton('Перевод предложения'))
        bot.reply_to(message, response.choices[0].message.content, reply_markup=markup)
    else:
        bot.reply_to(message, "Не удалось получить ответ от GPT.", reply_markup=markup)

bot.polling()
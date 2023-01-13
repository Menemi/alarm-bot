import logging
import random
import sqlite3

from aiogram import Bot, Dispatcher, executor, types
from config import token, logs, path_to_db

logging.basicConfig(level=logging.INFO)

bot = Bot(token=token)
dp = Dispatcher(bot)


def log(message: types.Message):
    logs.write(f"{message}\n")


def checker(message: types.Message):
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()
    user_id = message.from_user.id
    expected_user_id = cursor.execute(f"SELECT user_id FROM dicks WHERE user_id = {user_id}").fetchall()

    if not expected_user_id:
        cursor.execute('INSERT INTO dicks(user_id, length) VALUES(?, ?)', (user_id, f"0-{message.from_user.username}"))
        connection.commit()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    log(message)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.InlineKeyboardButton("/dick")
    markup.add(button)
    button = types.InlineKeyboardButton("/top_dick")
    markup.add(button)

    await bot.send_message(message.from_user.id, text="Доступные команды:", reply_markup=markup)
    return


@dp.message_handler(commands=['dick'])
async def start(message: types.Message):
    log(message)
    checker(message)
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()

    random_number = 0
    while random_number == 0:
        random_number = random.randint(-8, 10)

    lucky_chance = random.randint(0, 1000)
    if lucky_chance == 1000:
        random_number = 1000
    if lucky_chance == 0:
        random_number = -1000

    user_id = message.from_user.id

    current_length = cursor.execute(f"SELECT length FROM dicks WHERE user_id = {user_id}").fetchall()[0][0]
    username = current_length.split('-')[1]
    current_length = int(current_length.split('-')[0])
    final_length = current_length + random_number
    if final_length < 0:
        final_length = 0

    cursor.execute(f'UPDATE dicks SET length = "{final_length}-{username}" WHERE user_id = {user_id}')
    connection.commit()

    text = "сократился" if random_number < 0 else "вырос"

    dicks = cursor.execute(f"SELECT length FROM dicks").fetchall()
    dicks_length = []

    for dick in dicks:
        dicks_length.append(int(dick[0].split('-')[0]))

    expected_username = message.from_user.username
    rating = 0
    for i in range(len(dicks_length) - 1):
        for j in range(len(dicks_length) - i - 1):
            if dicks_length[j] < dicks_length[j + 1]:
                dicks_length[j], dicks_length[j + 1] = dicks_length[j + 1], dicks_length[j]
                dicks[j], dicks[j + 1] = dicks[j + 1], dicks[j]

                if expected_username == dicks[j][0].split('-')[1]:
                    rating = j
                elif expected_username == dicks[j + 1][0].split('-')[1]:
                    rating = j + 1

    await message.reply(
        f"@{message.from_user.username}, твой писюн {text} на <b>{abs(random_number)}</b> см.\n"
        f"Теперь он равен <b>{final_length}</b> см.\n"
        f"Ты занимаешь <b>{rating}</b> место в топе\n"
        f"Следующая попытка СЕЙЧАС!", parse_mode="HTML")
    return


@dp.message_handler(commands=['top_dick'])
async def start(message: types.Message):
    log(message)
    checker(message)
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()

    dicks = cursor.execute(f"SELECT length FROM dicks").fetchall()
    dicks_length = []
    for dick in dicks:
        dicks_length.append(int(dick[0].split('-')[0]))

    for i in range(len(dicks_length) - 1):
        for j in range(len(dicks_length) - i - 1):
            if dicks_length[j] < dicks_length[j + 1]:
                dicks_length[j], dicks_length[j + 1] = dicks_length[j + 1], dicks_length[j]
                dicks[j], dicks[j + 1] = dicks[j + 1], dicks[j]

    count = 0
    answer = ""
    for i in range(10):
        length = dicks[i][0].split('-')[0]
        username = dicks[i][0].split('-')[1]
        answer += f"{count}|<b>{username}</b> — <b>{length}</b> см.\n"
        count += 1
    await message.reply(answer, parse_mode="HTML")
    return


@dp.message_handler(content_types=types.ContentType.ANY)
async def echo(message: types.Message):
    checker(message)
    return


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

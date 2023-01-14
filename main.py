import logging
import random
import sqlite3

from aiogram import Bot, Dispatcher, executor, types
from config import token, logs, path_to_db, commands, buttons

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
    for command in buttons:
        button = types.InlineKeyboardButton(command)
        markup.add(button)
    await bot.send_message(message.from_user.id, text=f"Доступные команды:", reply_markup=markup)
    return


@dp.message_handler(commands=['help'])
async def helper(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for command in buttons:
        button = types.InlineKeyboardButton(command)
        markup.add(button)
    answer = ""
    for command in commands:
        answer += f"{command}\n"
    await message.reply(f"Доступные команды:\n{answer}", reply_markup=markup, parse_mode="HTML")
    return


@dp.message_handler(commands=['dick'])
async def dick(message: types.Message):
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
async def top_dick(message: types.Message):
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


@dp.message_handler(commands=['bet'])
async def bet(message: types.Message):
    log(message)
    checker(message)
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()
    args = message.get_args()
    if not args:
        await message.reply("Нужно ввести ставку: /bet <code>N</code>", parse_mode="HTML")
        return

    user_bet = str(args)
    if user_bet.find(' ') != -1:
        await message.reply("Ты че вообще еблан? Введи 1 аргумент, сука", parse_mode="HTML")
        return
    if user_bet.find(';') != -1 \
            or user_bet.find('.') != -1 \
            or user_bet.find(',') != -1 \
            or user_bet.find(':') != -1 \
            or not user_bet.isdigit():
        await message.reply("Ставка должна быть в виде целого неотрицательного числа", parse_mode="HTML")
        return

    current_length = cursor.execute(
        f"SELECT length FROM dicks WHERE user_id = {message.from_user.id}").fetchall()[0][0].split("-")
    length = int(current_length[0])
    username = current_length[1]

    user_bet = int(user_bet)
    if user_bet > length:
        await message.reply(
            f"Ставка не может быть больше твоего нынешнего размера писюна (<code>{length}</code>)", parse_mode="HTML")
        return

    luck = random.randint(0, 1)
    final_length = length
    text = " "
    if luck == 1:
        final_length = length + user_bet
    else:
        final_length = length - user_bet
        text = " не "

    cursor.execute(f'UPDATE dicks SET length = "{final_length}-{username}" WHERE user_id = {message.from_user.id}')
    connection.commit()

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
        f"@{message.from_user.username}, твоя ставка{text}сыграла\n"
        f"Теперь твой писюн равен <b>{final_length}</b> см.\n"
        f"Ты занимаешь <b>{rating}</b> место в топе\n", parse_mode="HTML")
    return


@dp.message_handler(commands=['all_in'])
async def all_in(message: types.Message):
    log(message)
    checker(message)
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()

    current_length = cursor.execute(
        f"SELECT length FROM dicks WHERE user_id = {message.from_user.id}").fetchall()[0][0].split("-")
    length = current_length[0]
    username = current_length[1]

    luck = random.randint(0, 1)
    final_length = int(length)
    if luck == 1:
        final_length *= 2
    else:
        final_length = 0

    cursor.execute(f'UPDATE dicks SET length = "{final_length}-{username}" WHERE user_id = {message.from_user.id}')
    connection.commit()

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

    if luck == 1:
        await message.reply(
            f"@{message.from_user.username}, ебать тебе повезло-повезло, ты удвоил свой писюн\n"
            f"Теперь твой писюн равен <b>{final_length}</b> см.\n"
            f"Ты занимаешь <b>{rating}</b> место в топе\n", parse_mode="HTML")
        return
    else:
        await message.reply(
            f"@{message.from_user.username}, ебать ты лох, ты проебал весь свой писюн, АХАХХАХАХАХАХАХХАХАХАХАХ\n"
            f"Теперь твой писюн равен <b>{final_length}</b> см.\n"
            f"Ты занимаешь <b>{rating}</b> место в топе\n", parse_mode="HTML")
        return


@dp.message_handler(commands=['changesize'])
async def change_size(message: types.Message):
    log(message)
    checker(message)

    if message.from_user.id != 433013981:
        return

    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()

    args = message.get_args()
    if not args:
        return
    args = args.split(" ")
    if len(args) == 1:
        return
    username = cursor.execute(f"SELECT length FROM dicks WHERE user_id = {args[0]}").fetchall()[0][0].split("-")[1]
    cursor.execute(f'UPDATE dicks SET length = "{args[1]}-{username}" WHERE user_id = {args[0]}')
    connection.commit()
    await message.answer(f"Теперь член @{username} - {args[1]} см.")


@dp.message_handler(content_types=types.ContentType.ANY)
async def echo(message: types.Message):
    checker(message)
    return


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

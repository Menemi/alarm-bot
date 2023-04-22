import datetime
import logging
import random
import asyncio
import sqlite3
import json

import aiogram.utils.exceptions
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InputFile

from config import token, path_to_db, commands

logging.basicConfig(level=logging.INFO)

bot = Bot(token=token)
dp = Dispatcher(bot)
tz = datetime.timezone(datetime.timedelta(hours=3), name="МСК")


class User:
    def __init__(self, id, user_id, length, username, plus, minus, flag):
        self.id = id
        self.user_id = user_id
        self.length = length
        self.username = username
        self.plus_try_count = plus
        self.minus_try_count = minus
        self.flag = flag


class DatabaseObject:
    def __init__(self):
        self.users = []

    def addUser(self, user: User):
        self.users.append(user)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


def log(message: types.Message):
    logs = open("logs.json", "a")
    logs.write(f"{message},\n")
    logs.close()


def get_start_checker_flag():
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()
    return cursor.execute("SELECT flag FROM start_flag WHERE id=1").fetchall()[0][0]


def reset_start_checker_flag(flag: bool):
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()
    cursor.execute("UPDATE start_flag SET flag = TRUE WHERE id=1") if flag \
        else cursor.execute("UPDATE start_flag SET flag = FALSE WHERE id=1")
    connection.commit()


async def new_day_stater():
    reset_start_checker_flag(True)
    flag_written = True
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()
    while True:
        if flag_written and \
                (datetime.datetime.now().astimezone(tz).strftime("%H:%M") == "00:00" or
                 datetime.datetime.now().astimezone(tz).strftime("%H:%M") == "00:01"):
            users_id = cursor.execute("SELECT user_id FROM dicks WHERE flag = TRUE").fetchall()
            for user_id in users_id:
                cursor.execute(f"UPDATE dicks SET flag = FALSE WHERE user_id = {user_id[0]}")
            connection.commit()

            await bot.send_message(433013981, f"Можно заново измерить писюн", parse_mode="HTML")
            flag_written = False
            await asyncio.sleep(1200)
        else:
            flag_written = True
            await asyncio.sleep(120)


async def checker(message: types.Message):
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()
    user_id = message.from_user.id
    expected_user_id = cursor.execute(f"SELECT user_id FROM dicks WHERE user_id = {user_id}").fetchall()

    if not expected_user_id:
        cursor.execute('INSERT INTO dicks(user_id, username, chat_ids) VALUES(?, ?, ?)',
                       (user_id, message.from_user.username, f"{user_id}a"))
        connection.commit()

    if not get_start_checker_flag():
        asyncio.create_task(new_day_stater())
        reset_start_checker_flag(True)


def checker2(message: types.Message):
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()
    user_id = message.from_user.id
    return cursor.execute(f"SELECT flag FROM dicks WHERE user_id = {user_id}").fetchall()[0][0]


def print_dick_with_rating1(username, length, rating):
    return f"@{username}, ты уже играл.\n" \
           f"Сейчас он равен <b>{length}</b> см.\n" \
           f"Ты занимаешь <b>{rating}</b> место в топе.\n" \
           f"Следующая попытка завтра!"


def print_dick_without_rating1(username, length):
    return f"@{username}, ты уже играл.\n" \
           f"Сейчас он равен <b>{length}</b> см.\n" \
           f"Следующая попытка завтра!"


def print_dick_with_rating2(username, text, random_number, final_length, rating):
    return f"@{username}, твой писюн {text} на <b>{abs(random_number)}</b> см.\n" \
           f"Теперь он равен <b>{final_length}</b> см.\n" \
           f"Ты занимаешь <b>{rating}</b> место в топе.\n" \
           f"Следующая попытка завтра!"


def print_dick_without_rating2(username, text, random_number, final_length):
    return f"@{username}, твой писюн {text} на <b>{abs(random_number)}</b> см.\n" \
           f"Теперь он равен <b>{final_length}</b> см.\n" \
           f"Следующая попытка завтра!"


def chat_check(message: types.Message):
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()

    chat_ids = cursor.execute(f"SELECT chat_ids FROM dicks WHERE user_id = {message.from_user.id}").fetchall()[0][
        0].split("a")
    flag2 = False
    for chat_id in chat_ids:
        if str(chat_id) == str(message.chat.id):
            flag2 = True
            break

    if not flag2:
        chat_ids = cursor.execute(f"SELECT chat_ids FROM dicks WHERE user_id = {message.from_user.id}").fetchall()[0][0]
        cursor.execute(
            f'UPDATE dicks SET chat_ids = "{chat_ids}{message.chat.id}a" WHERE user_id = {message.from_user.id}')
        connection.commit()


@dp.message_handler(commands=['start', 'help'])
async def helper(message: types.Message):
    log(message)
    await checker(message)
    chat_check(message)
    answer = ""
    for command in commands:
        answer += f"{command}\n"

    answer += "\n<b>Контакты</b>:\n" \
              "Наш канал — @MenemiIsClown\n" \
              'Наш чат — <a href="nahnah.ru">ссылка</a>\n' \
              "Админ — @Menemi"
    await message.reply(f"<b>Команды бота</b>:\n{answer}", parse_mode="HTML")
    return


@dp.message_handler(commands=['dick'])
async def dick(message: types.Message):
    log(message)
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()
    await checker(message)
    flag = checker2(message)
    chat_check(message)

    cursor.execute(f'UPDATE dicks SET username = "{message.from_user.username}" WHERE user_id = {message.from_user.id}')
    connection.commit()
    if flag:
        current_length = \
            cursor.execute(f"SELECT length FROM dicks WHERE user_id = {message.from_user.id}").fetchall()[0][0]

        top = cursor.execute(
            f"SELECT length, username FROM dicks WHERE chat_ids LIKE '%{message.chat.id}%' ORDER BY length DESC").fetchall()

        rating = 0
        for member in top:
            if member[1] == message.from_user.username:
                break
            rating += 1

        if message.chat.id == message.from_user.id:
            await message.reply(print_dick_without_rating1(message.from_user.username, current_length),
                                parse_mode="HTML")
            return
        await message.reply(print_dick_with_rating1(message.from_user.username, current_length, rating),
                            parse_mode="HTML")
        return

    random_number = 0
    while random_number == 0:
        random_number = random.randint(0, 10)

    negative = False
    if random.randint(0, 100) <= 35:
        negative = True

    user_id = message.from_user.id

    current_length = cursor.execute(f"SELECT length FROM dicks WHERE user_id = {user_id}").fetchall()[0][0]
    if negative:
        final_length = current_length - random_number
    else:
        final_length = current_length + random_number

    if final_length < 0:
        final_length = 0

    cursor.execute(f'UPDATE dicks SET length = {final_length} WHERE user_id = {user_id}')
    connection.commit()

    text = "сократился" if negative else "вырос"

    top = cursor.execute(
        f"SELECT length, username FROM dicks WHERE chat_ids LIKE '%{message.chat.id}%' ORDER BY length DESC").fetchall()

    rating = 0
    for member in top:
        if member[1] == message.from_user.username:
            break
        rating += 1

    if negative:
        current_minus_try_count = \
            cursor.execute(f"SELECT minus_try_count FROM dicks WHERE user_id = {user_id}").fetchall()[0][0]
        cursor.execute(f'UPDATE dicks SET minus_try_count = {current_minus_try_count + 1} WHERE user_id = {user_id}')
    else:
        current_plus_try_count = \
            cursor.execute(f"SELECT plus_try_count FROM dicks WHERE user_id = {user_id}").fetchall()[0][0]
        cursor.execute(f'UPDATE dicks SET plus_try_count = {current_plus_try_count + 1} WHERE user_id = {user_id}')

    cursor.execute(f'UPDATE dicks SET flag = TRUE WHERE user_id = {user_id}')
    connection.commit()

    if message.chat.id == message.from_user.id:
        await message.reply(
            print_dick_without_rating2(message.from_user.username, text, abs(random_number), final_length),
            parse_mode="HTML")
        return
    await message.reply(
        print_dick_with_rating2(message.from_user.username, text, abs(random_number), final_length, rating),
        parse_mode="HTML")

    return


@dp.message_handler(commands=['top_dick'])
async def top_dick(message: types.Message):
    log(message)
    await checker(message)
    chat_check(message)
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()

    top10dicks = cursor.execute(f"SELECT length, username "
                                f"FROM dicks "
                                f"WHERE chat_ids "
                                f"LIKE '%{message.chat.id}%' "
                                f"ORDER BY length "
                                f"DESC LIMIT 10").fetchall()

    count = 0
    answer = f"Топ {len(top10dicks)} игроков\n\n"
    for dick in top10dicks:
        answer += f"{count}|<b>{dick[1]}</b> — <b>{dick[0]}</b> см.\n"
        count += 1
    await message.reply(answer, parse_mode="HTML")
    return


@dp.message_handler(commands=['stats'])
async def stats(message: types.Message):
    # 0: id
    # 1: user_id
    # 2: length
    # 3: username
    # 4: plus_try_count
    # 5: minus_try_count
    # 6: flag
    log(message)
    await checker(message)
    chat_check(message)
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()

    user_id = message.from_user.id
    current_user = cursor.execute(f"SELECT * FROM dicks WHERE user_id = {user_id}").fetchall()[0]
    await message.reply(f"@{message.from_user.username}, твоя статистика:\n"
                        f"- Размер писюна: <b>{str(current_user[2]).split('-')[0]}</b>\n"
                        f"- К-во измерений: <b>{int(current_user[4]) + int(current_user[5])}</b>\n"
                        f"- К-во удачных измерений: <b>{int(current_user[4])}</b>\n"
                        f"- К-во лузерских измерений: <b>{int(current_user[5])}</b>\n", parse_mode="HTML")
    return


@dp.message_handler(commands=['changesize'])
async def change_size(message: types.Message):
    log(message)
    await checker(message)

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
    username = cursor.execute(f"SELECT username FROM dicks WHERE user_id = {args[0]}").fetchall()[0][0]
    cursor.execute(f'UPDATE dicks SET length = {args[1]} WHERE user_id = {args[0]}')
    connection.commit()
    await message.answer(f"Теперь член @{username} - {args[1]} см.")


@dp.message_handler(commands=['get'])
async def get(message: types.Message):
    log(message)
    await checker(message)

    if message.from_user.id != 433013981:
        return

    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()

    database_data = cursor.execute("SELECT * FROM dicks").fetchall()
    data = DatabaseObject()
    for row in database_data:
        id = row[0]
        user_id = row[1]
        length = row[2]
        username = row[3]
        plus_try_count = row[4]
        minus_try_count = row[5]
        flag = row[6]
        user = User(id, user_id, length, username, plus_try_count, minus_try_count, flag)
        data.addUser(user)
    result = data.toJSON()
    file = open("get.json", "w")
    file.write(result)
    file.close()
    await bot.send_document(433013981, InputFile("get.json"))


@dp.message_handler(commands=['getFlag1'])
async def getFlag1(message: types.Message):
    log(message)
    await checker(message)

    if message.from_user.id != 433013981:
        return

    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()

    data = cursor.execute("SELECT username FROM dicks WHERE flag = TRUE").fetchall()
    answer = ""
    for user in data:
        answer += f"@{user[0]}\n"
    await message.reply(answer)


@dp.message_handler(commands=['sendMessage'])
async def send_message(message: types.Message):
    try:
        log(message)
        await checker(message)

        if message.from_user.id != 433013981:
            return

        args = message.get_args()
        args = args.split(' ')
        chat_id = args[0]
        args.pop(0)

        message_text = ""
        for arg in args:
            message_text += f"{arg} "

        await bot.send_message(chat_id, message_text)
        await bot.send_message(433013981, f"успешно отправил сообщение {chat_id}")
    except aiogram.utils.exceptions.CantInitiateConversation:
        await bot.send_message(433013981, "бот не может инициировать беседу с этим пользователем")
    except aiogram.utils.exceptions.BotBlocked:
        await bot.send_message(433013981, "бот был заблокирован пользователем")
    except aiogram.utils.exceptions.BotKicked:
        await bot.send_message(433013981, "бот был выгнан из группы")


@dp.message_handler(content_types=types.ContentType.PHOTO)
async def process_photo(message: types.Message):
    new_message = await bot.forward_message(chat_id=433013981,
                                            from_chat_id=message.chat.id,
                                            message_id=message.message_id)
    await new_message.reply(text=f"@{message.from_user.username}\n"
                                 f"chat_id: {message.from_user.id}")


@dp.message_handler(content_types=types.ContentType.ANY)
async def echo(message: types.Message):
    await checker(message)


if __name__ == '__main__':
    reset_start_checker_flag(False)
    executor.start_polling(dp, skip_updates=True)

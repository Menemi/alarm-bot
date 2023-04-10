import datetime
import logging
import random
import asyncio
import sqlite3

from aiogram import Bot, Dispatcher, executor, types
from config import token, path_to_db, commands, buttons

logging.basicConfig(level=logging.INFO)

bot = Bot(token=token)
dp = Dispatcher(bot)
tz = datetime.timezone(datetime.timedelta(hours=3), name="МСК")


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
            users_id = cursor.execute("SELECT user_id FROM dicks").fetchall()
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
        cursor.execute('INSERT INTO dicks(user_id, username) VALUES(?, ?)', (user_id, message.from_user.username))
        connection.commit()

    if not get_start_checker_flag():
        asyncio.create_task(new_day_stater())
        reset_start_checker_flag(True)


def checker2(message: types.Message):
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()
    user_id = message.from_user.id
    return cursor.execute(f"SELECT flag FROM dicks WHERE user_id = {user_id}").fetchall()[0][0]


@dp.message_handler(commands=['start', 'help'])
async def helper(message: types.Message):
    await checker(message)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for command in buttons:
        button = types.InlineKeyboardButton(command)
        markup.add(button)
    answer = ""
    for command in commands:
        answer += f"{command}\n"

    answer += "\n<b>Контакты</b>:\n" \
              "Наш канал — @MenemiIsClown\n" \
              'Наш чат — <a href="nahnah.ru">ссылка</a>\n' \
              "Админ — @Menemi"
    await message.reply(f"<b>Команды бота</b>:\n{answer}", reply_markup=markup, parse_mode="HTML")
    return


@dp.message_handler(commands=['dick'])
async def dick(message: types.Message):
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()
    await checker(message)
    flag = checker2(message)
    cursor.execute(f'UPDATE dicks SET username = "{message.from_user.username}" WHERE user_id = {message.from_user.id}')
    connection.commit()
    if flag:
        current_length = \
        cursor.execute(f"SELECT length FROM dicks WHERE user_id = {message.from_user.id}").fetchall()[0][0]

        top = cursor.execute("SELECT length, username FROM dicks order by length desc").fetchall()

        rating = 0
        for member in top:
            if member[1] == message.from_user.username:
                break
            rating += 1

        await message.reply(
            f"@{message.from_user.username}, ты уже играл.\n"
            f"Сейчас он равен <b>{current_length}</b> см.\n"
            f"Ты занимаешь <b>{rating}</b> место в топе.\n"
            f"Следующая попытка завтра!", parse_mode="HTML")
        return

    random_number = 0
    while random_number == 0:
        random_number = random.randint(0, 10)

    negative = False
    if random.randint(0, 100) <= 35:
        negative = True

    user_id = message.from_user.id

    current_length = cursor.execute(f"SELECT length FROM dicks WHERE user_id = {user_id}").fetchall()[0][0]
    username = message.from_user.username
    if negative:
        final_length = current_length - random_number
    else:
        final_length = current_length + random_number

    if final_length < 0:
        final_length = 0

    cursor.execute(f'UPDATE dicks SET length = {final_length} WHERE user_id = {user_id}')
    connection.commit()

    text = "сократился" if negative else "вырос"

    top = cursor.execute("SELECT length, username FROM dicks order by length desc").fetchall()

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

    await message.reply(
        f"@{message.from_user.username}, твой писюн {text} на <b>{abs(random_number)}</b> см.\n"
        f"Теперь он равен <b>{final_length}</b> см.\n"
        f"Ты занимаешь <b>{rating}</b> место в топе.\n"
        f"Следующая попытка завтра!", parse_mode="HTML")
    return


@dp.message_handler(commands=['top_dick'])
async def top_dick(message: types.Message):
    await checker(message)
    connection = sqlite3.connect(path_to_db)
    cursor = connection.cursor()

    top10dicks = cursor.execute("SELECT length, username FROM dicks order by length desc limit 10").fetchall()

    count = 0
    answer = "Топ 10 игроков\n\n"
    for i in range(10):
        answer += f"{count}|<b>{top10dicks[i][1]}</b> — <b>{top10dicks[i][0]}</b> см.\n"
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
    await checker(message)
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


@dp.message_handler(content_types=types.ContentType.ANY)
async def echo(message: types.Message):
    await checker(message)
    return


if __name__ == '__main__':
    reset_start_checker_flag(False)
    executor.start_polling(dp, skip_updates=True)

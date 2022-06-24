#!/usr/bin/python
# -*- coding: UTF-8 -*-

import telebot
from telebot.async_telebot import AsyncTeleBot
import asyncio

import sqlite3
import json
import time
from datetime import datetime

from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage
from telebot import asyncio_filters



bot = AsyncTeleBot("5405209426:AAFG3h3W7bOe2FUuXexQ3PplOdMWAUc-6AI")



class AddRemind(StatesGroup):
    date = State() # statesgroup should contain states
    time = State()
    text = State()



#Database create
connect = sqlite3.connect("reminds.db")
cursor = connect.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS reminds(
    date DATE,
    time TIME,
    remind TEXT,
    user TEXT
)""")

connect.commit()

#-----------------------------------------HELP/START--Помощь----------------------------------------------#
@bot.message_handler(commands=["help"])
async def help(message):
    bot.send_message(message.chat.id, """Вас приветствует Чат-бот Напоминаний. Данный чат-бот создан для напоминания о предстоящих событиях.
Полный список команд:
/help - команда для ориентации  пользователя по боту.
/add_remind - добавить напоминание.
/del_remind - удалить напоминание по названию.
/edit_reminds - редактировать напоминание.
/show_reminds - показать все мои напоминания.""")
    await asyncio.sleep(0)

@bot.message_handler(commands=["start"])
async def start(message):
    await bot.send_message(message.chat.id, """Вас приветствует Чат-бот Напоминаний. Данный чат-бот создан для напоминания о предстоящих событиях.
Полный список команд:
/help - команда для ориентации  пользователя по боту.
/add_remind - добавить напоминание.
/del_remind - удалить напоминание по названию.
/edit_reminds - редактировать напоминание.
/show_reminds - показать все мои напоминания.""")
    reminds_info[message.chat.id] = []
    await asyncio.sleep(0)


#------------------------------------add_remind---------------------------------------------------------------#
reminds_info = {}
@bot.message_handler(commands=["add_remind"])
async def add_remind(message):
    await bot.send_message(message.chat.id, "Введите дату напоминания в формате DD.MM.YY")
    reminds_info[message.chat.id].append({
        "date": "",
        "time": "",
        "text": ""
    })
    await bot.set_state(message.from_user.id, AddRemind.date, message.chat.id)
    await asyncio.sleep(0)


@bot.message_handler(state=AddRemind.date)
async def add_remind_date(message):
    try:
        date = datetime.strptime(message.text, "%d.%m.%Y")
    except ValueError:
        await bot.send_message(message.chat.id, "Вы ввели дату в неверном формате. Пожалуйста, введите дату в формта DD.MM.YYYY")
        await bot.set_state(message.from_user.id, AddRemind.date, message.chat.id)
        return

    if datetime.now().date() > date.date():
        await bot.send_message(message.chat.id, "Вы ввели прошедшую дату. Пожалуйста, введите будущую или сегодняшнюю дату")
        await bot.set_state(message.from_user.id, AddRemind.date, message.chat.id)
        return

    reminds_info[message.chat.id][-1]["date"] = message.text
    await bot.send_message(message.chat.id, "Введите время напоминания в формате HH.MM")
    await bot.set_state(message.from_user.id, AddRemind.time, message.chat.id)
    await asyncio.sleep(0)

@bot.message_handler(state=AddRemind.time)
async def add_remind_time(message):
    try:
        time = datetime.strptime(message.text, "%H.%M")
    except ValueError:
        await bot.send_message(message.chat.id, "Вы ввели время в неверном формате. Пожалуйста, введите время в формта HH.MM")
        await bot.set_state(message.from_user.id, AddRemind.time, message.chat.id)
        return

    if datetime.now().time() > time.time() and reminds_info[message.chat.id][-1]["date"] == datetime.now().date():
        await bot.send_message(message.chat.id, "Вы ввели прошедшее время. Пожалуйста, введите будущее время")
        await bot.set_state(message.from_user.id, AddRemind.time, message.chat.id)
        return

    reminds_info[message.chat.id][-1]["time"] = message.text
    await bot.send_message(message.chat.id, "Введите текст напоминания")
    await bot.set_state(message.from_user.id, AddRemind.date, message.chat.id)
    await asyncio.sleep(0)

@bot.message_handler(state=AddRemind.text)
async def add_remind_text(message):
    reminds_info[message.chat.id][-1]["text"] = message.text
    await bot.send_message(message.chat.id, str(reminds_info))

    connect = sqlite3.connect("reminds.db")

    payload = f"""INSERT INTO reminds
(date, time, remind, user)
VALUES
(\
"{reminds_info[message.chat.id][-1]["date"]}",\
"{reminds_info[message.chat.id][-1]["time"]}",\
"{reminds_info[message.chat.id][-1]["text"]}",\
"{message.chat.id}"\
);
    """

    connect.execute(
        payload
    )
    connect.commit()

    await bot.send_message(message.chat.id, "Напоминание создано успешно")
    await asyncio.sleep(0)



async def check_reminds():
    while True:
        connect = sqlite3.connect("reminds.db")

        reminds = list(connect.execute(f"SELECT * FROM reminds WHERE date='{datetime.now().date().strftime('%d.%m.%Y')}' AND time<='{datetime.now().time().strftime('%H.%M')}'"))

        for remind in reminds:
            date, time, text, user = remind
            send_remind(date, time, text, user)
            connect.execute(f"DELETE FROM reminds WHERE date='{date}' AND time='{time}' AND user='{user}' AND remind='{text}'")
            connect.commit()
        await asyncio.sleep(0)

def send_remind(date, time, text, user):
    bot.send_message(user, f"Напоминание от {date}: {time}\n{text}")


async def main():
    await asyncio.gather(bot.infinity_polling(), check_reminds())

bot.add_custom_filter(asyncio_filters.StateFilter(bot))
asyncio.run(main())
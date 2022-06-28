#!/usr/bin/python
# -*- coding: UTF-8 -*-

import telebot
from telebot.async_telebot import AsyncTeleBot
import asyncio

import sqlite3
import json
import os
from dotenv import load_dotenv
import time
from datetime import datetime

from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage
from telebot import asyncio_filters

load_dotenv()

bot = AsyncTeleBot(os.getenv("TOKEN"))



class AddRemind(StatesGroup):
    date = State()
    time = State()
    text = State()

class DelRemind(StatesGroup):
     remind = State()

class EditRemind(StatesGroup):
    remind = State()
    date = State()
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
/edit_remind - редактировать напоминание.
/show_reminds - показать все мои напоминания.""")
    await asyncio.sleep(0)

@bot.message_handler(commands=["start"])
async def start(message):
    await bot.send_message(message.chat.id, """Вас приветствует Чат-бот Напоминаний. Данный чат-бот создан для напоминания о предстоящих событиях.
Полный список команд:
/help - команда для ориентации  пользователя по боту.
/add_remind - добавить напоминание.
/del_remind - удалить напоминание по названию.
/edit_remind - редактировать напоминание.
/show_reminds - показать все мои напоминания.""")
    reminds_info[message.chat.id] = []
    await asyncio.sleep(0)


#------------------------------------add_remind---------------------------------------------------------------#
reminds_info = {}
@bot.message_handler(commands=["add_remind"])
async def add_remind(message):
    await bot.send_message(message.chat.id, "Введите дату напоминания в формате DD.MM.YYYY")
    if not message.chat.id in reminds_info:
        reminds_info[message.chat.id] = []
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
        await bot.send_message(message.chat.id, "Вы ввели дату в неверном формате. Пожалуйста, введите дату в формате DD.MM.YYYY")
        await bot.set_state(message.from_user.id, AddRemind.date, message.chat.id)
        return

    if datetime.now().date() > date.date():
        await bot.send_message(message.chat.id, "Вы ввели прошедшую дату. Пожалуйста, введите будущую или сегодняшнюю дату")
        await bot.set_state(message.from_user.id, AddRemind.date, message.chat.id)
        return

    reminds_info[message.chat.id][-1]["date"] = message.text
    await bot.send_message(message.chat.id, "Введите время напоминания в формате HH:MM")
    await bot.set_state(message.from_user.id, AddRemind.time, message.chat.id)
    await asyncio.sleep(0)

@bot.message_handler(state=AddRemind.time)
async def add_remind_time(message):
    try:
        time = datetime.strptime(message.text, "%H:%M")
    except ValueError:
        await bot.send_message(message.chat.id, "Вы ввели время в неверном формате. Пожалуйста, введите время в формате HH:MM")
        await bot.set_state(message.from_user.id, AddRemind.time, message.chat.id)
        return

    if datetime.now().time() > time.time() and reminds_info[message.chat.id][-1]["date"] == datetime.now().date().strftime("%d.%m.%Y"):
        await bot.send_message(message.chat.id, "Вы ввели прошедшее время. Пожалуйста, введите будущее время")
        await bot.set_state(message.from_user.id, AddRemind.time, message.chat.id)
        return

    reminds_info[message.chat.id][-1]["time"] = message.text
    await bot.send_message(message.chat.id, "Введите текст напоминания")
    await bot.set_state(message.from_user.id, AddRemind.text, message.chat.id)
    await asyncio.sleep(0)

@bot.message_handler(state=AddRemind.text)
async def add_remind_text(message):
    reminds_info[message.chat.id][-1]["text"] = message.text

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
    await bot.set_state(message.from_user.id, 0, message.chat.id)
    #await asyncio.sleep(0)


#-------------------------------DEL_REMIND-----------------------------------------------------------------------------#
def get_keyboard_reminds(user):
    connect = sqlite3.connect("reminds.db")
    reminds = list(connect.execute(f"SELECT * FROM reminds WHERE user='{user}'"))
    print(reminds)

    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = []
    for remind in reminds:
        buttons.append(telebot.types.KeyboardButton(f"{remind[0]} в {remind[1]}: {remind[2]}"))
    for button in buttons:
        keyboard.add(button)
    keyboard.add(telebot.types.KeyboardButton("Отмена"))
    return keyboard, reminds

@bot.message_handler(commands=["del_remind"])
async def del_remind(message):
    keyboard, reminds = get_keyboard_reminds(message.chat.id)
    await bot.send_message(message.chat.id, "Выберите напоминание для удаления.", reply_markup=keyboard)
    await bot.set_state(message.from_user.id, DelRemind.remind, message.chat.id)

@bot.message_handler(state=DelRemind.remind)
async def del_remind_remind(message):
    if message.text == "Отмена":
        await bot.send_message(message.chat.id, "Операция отменена.", reply_markup=telebot.types.ReplyKeyboardRemove())
        await bot.set_state(message.from_user.id, 0, message.chat.id)
        return
    date = message.text[0:10]
    time = message.text[13:18]
    text = message.text[20:]

    connect = sqlite3.connect("reminds.db")
    reminds = list(connect.execute(f"SELECT * FROM reminds WHERE date='{date}' AND time='{time}' AND user='{message.chat.id}' AND remind='{text}'"))
    connect.execute(f"DELETE FROM reminds WHERE date='{date}' AND time='{time}' AND user='{message.chat.id}' AND remind='{text}'")
    connect.commit()

    await bot.send_message(message.chat.id, "Напоминание удалено успешно.", reply_markup=telebot.types.ReplyKeyboardRemove())
    await bot.set_state(message.from_user.id, 0, message.chat.id)


#-------------------------------EDIT_REMIND-----------------------------------------------------------------------------#

edit_reminds_info = {}

@bot.message_handler(commands=["edit_remind"])
async def select_edit_remind(message):
    keyboard, reminds = get_keyboard_reminds(message.chat.id)
    await bot.send_message(message.chat.id, "Выберите напоминание для редактирования.", reply_markup=keyboard)
    await bot.set_state(message.from_user.id, EditRemind.remind, message.chat.id)

@bot.message_handler(state=EditRemind.remind)
async def select_edit_remind_remind(message):
    if message.text == "Отмена":
        await bot.send_message(message.chat.id, "Операция отменена.", reply_markup=telebot.types.ReplyKeyboardRemove())
        await bot.set_state(message.from_user.id, 0, message.chat.id)
        return
    date = message.text[0:10]
    time = message.text[13:18]
    text = message.text[20:]

    await bot.send_message(message.chat.id, "Введите новую дату напоминания в формате DD.MM.YYYY (skip для пропуска)")
    if not message.chat.id in edit_reminds_info:
        edit_reminds_info[message.chat.id] = []
    edit_reminds_info[message.chat.id].append({
        "date": "",
        "time": "",
        "text": "",
        "old": {
            "date": date,
            "time": time,
            "text": text
        }
    })
    await bot.set_state(message.from_user.id, EditRemind.date, message.chat.id)

@bot.message_handler(state=EditRemind.date)
async def edit_remind_date(message):
    if "skip" in message.text.lower():
        edit_reminds_info[message.chat.id][-1]["date"] = edit_reminds_info[message.chat.id][-1]["old"]["date"]
    else:
        try:
            date = datetime.strptime(message.text, "%d.%m.%Y")
        except ValueError:
            await bot.send_message(message.chat.id, "Вы ввели дату в неверном формате. Пожалуйста, введите дату в формате DD.MM.YYYY (skip для пропуска)")
            await bot.set_state(message.from_user.id, EditRemind.date, message.chat.id)
            return

        if datetime.now().date() > date.date():
            await bot.send_message(message.chat.id, "Вы ввели прошедшую дату. Пожалуйста, введите будущую или сегодняшнюю дату (skip для пропуска)")
            await bot.set_state(message.from_user.id, EditRemind.date, message.chat.id)
            return

        edit_reminds_info[message.chat.id][-1]["date"] = message.text
    await bot.send_message(message.chat.id, "Введите новое время напоминания в формате HH:MM (skip для пропуска)")
    await bot.set_state(message.from_user.id, EditRemind.time, message.chat.id)
    await asyncio.sleep(0)

@bot.message_handler(state=EditRemind.time)
async def edit_remind_time(message):
    if "skip" in message.text.lower():
        edit_reminds_info[message.chat.id][-1]["time"] = edit_reminds_info[message.chat.id][-1]["old"]["time"]
    else:
        try:
            time = datetime.strptime(message.text, "%H:%M")
        except ValueError:
            await bot.send_message(message.chat.id, "Вы ввели время в неверном формате. Пожалуйста, введите время в формате HH:MM (skip для пропуска)")
            await bot.set_state(message.from_user.id, EditRemind.time, message.chat.id)
            return

        if datetime.now().time() > time.time() and edit_reminds_info[message.chat.id][-1]["date"] == datetime.now().date().strftime("%d.%m.%Y"):
            await bot.send_message(message.chat.id, "Вы ввели прошедшее время. Пожалуйста, введите будущее время (skip для пропуска)")
            await bot.set_state(message.from_user.id, EditRemind.time, message.chat.id)
            return

        edit_reminds_info[message.chat.id][-1]["time"] = message.text
    await bot.send_message(message.chat.id, "Введите новый текст напоминания (skip для пропуска)")
    await bot.set_state(message.from_user.id, EditRemind.text, message.chat.id)
    await asyncio.sleep(0)

@bot.message_handler(state=EditRemind.text)
async def edit_remind_text(message):
    if "skip" in message.text.lower():
        edit_reminds_info[message.chat.id][-1]["text"] = edit_reminds_info[message.chat.id][-1]["old"]["text"]
    else:
        edit_reminds_info[message.chat.id][-1]["text"] = message.text

    connect = sqlite3.connect("reminds.db")

    payload = f"""UPDATE reminds SET \
date="{edit_reminds_info[message.chat.id][-1]["date"]}", \
time="{edit_reminds_info[message.chat.id][-1]["time"]}", \
remind="{edit_reminds_info[message.chat.id][-1]["text"]}"\
WHERE date='{edit_reminds_info[message.chat.id][-1]["old"]["date"]}' AND time='{edit_reminds_info[message.chat.id][-1]["old"]["time"]}' AND remind='{edit_reminds_info[message.chat.id][-1]["old"]["text"]}' AND user='{message.chat.id}';
    """
    print(payload)

    connect.execute(
        payload
    )
    connect.commit()

    await bot.send_message(message.chat.id, "Напоминание изменено успешно")
    await bot.set_state(message.from_user.id, 0, message.chat.id)
    #await asyncio.sleep(0)


#-------------------------------SHOW_REMIND-----------------------------------------------------------------------------#
@bot.message_handler(commands=["show_reminds"])
async def show_reminds(message):
    connect = sqlite3.connect("reminds.db")
    reminds = list(connect.execute(f"SELECT * FROM reminds WHERE user='{message.chat.id}'"))

    for remind in reminds:
        await bot.send_message(message.chat.id, f"{remind[0]} в {remind[1]}:\n{remind[2]}")



async def check_reminds():
    while True:
        connect = sqlite3.connect("reminds.db")

        reminds = list(connect.execute(f"SELECT * FROM reminds WHERE date='{datetime.now().date().strftime('%d.%m.%Y')}' AND time<='{datetime.now().time().strftime('%H:%M')}'"))

        for remind in reminds:
            date, time, text, user = remind
            print(date, time, text, user)
            await bot.send_message(user, f"<b>⏰ Напоминание от {date}: {time}\n{text}</b>", parse_mode='html')
            connect.execute(f"DELETE FROM reminds WHERE date='{date}' AND time='{time}' AND user='{user}' AND remind='{text}'")
            connect.commit()
        await asyncio.sleep(0)


async def main():
    await asyncio.gather(bot.infinity_polling(), check_reminds())

bot.add_custom_filter(asyncio_filters.StateFilter(bot))
asyncio.run(main())

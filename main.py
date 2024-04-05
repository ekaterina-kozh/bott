#@title Полный код бота для самоконтроля
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F
from sqlcode import create_table, get_quiz_index, update_quiz_index, get_player_statistics, get_last_user_score
import json

quiz_data = []
with open('quizedata.json', encoding='utf-8') as file:
    quiz_data = json.load(file)

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Замените "YOUR_BOT_TOKEN" на токен, который вы получили от BotFather
API_TOKEN = '6573032015:AAGP8DXlrj1Di8C3QIjTEXpWTM5Zt-L9ZiE'

# Объект бота
bot = Bot(token=API_TOKEN)
# Диспетчер
dp = Dispatcher()


def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data="right_answer" if option == right_answer else "wrong_answer")
        )

    builder.adjust(1)
    return builder.as_markup()



@dp.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

 # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]['correct_option']
    final_score = await get_last_user_score(callback.from_user.id)
    #SCORE_BY_CORRECT_ANSWER = 12

    final_score += 1
    await callback.message.answer(f"Верно. Ваш ответ: {quiz_data[current_question_index]['options'][correct_option]}")

    
    await callback.message.answer("Верно!")
    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index, final_score)


    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        final_score = await get_last_user_score(callback.from_user.id)
        corrent_answers_count = int(final_score / 12)
        corrent_percent = corrent_answers_count / len(quiz_data)
        incorrent_percent = 1.0 - corrent_percent

        result_text = f"\nФинальный счет: *{final_score}*\n*{corrent_percent:.2%}* правильных ответов, " \
                      f"*{incorrent_percent:.2%}* неправильных ответов"
        
        await callback.message.answer("Это был последний вопрос. Квиз завершен!" + result_text,
                                      parse_mode="Markdown")


@dp.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )


    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]['correct_option']
    final_score = await get_last_user_score(callback.from_user.id)
    SCORE_BY_CORRECT_ANSWER = 12

    final_score += SCORE_BY_CORRECT_ANSWER

    await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index, final_score)


    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        final_score = await get_last_user_score(callback.from_user.id)
        corrent_answers_count = int(final_score / 12)
        corrent_percent = corrent_answers_count / len(quiz_data)
        incorrent_percent = 1.0 - corrent_percent

        result_text = f"\nФинальный счет: *{final_score}*\n*{corrent_percent:.2%}* правильных ответов, " \
                      f"*{incorrent_percent:.2%}* неправильных ответов"

        await callback.message.answer("Это был последний вопрос. Квиз завершен!" + result_text,
                                      parse_mode="Markdown")


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    builder.add(types.KeyboardButton(text="Статистика"))
    await message.answer("Добро пожаловать в квиз! 👋", reply_markup=builder.as_markup(resize_keyboard=True))


# Хэндлер на команду /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):

    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)

 #Хэндлер на команду /stat
@dp.message(F.text == "Статистика")
@dp.message(Command("stat"))
async def send_statistics(message: types.Message):
    statistics = await get_player_statistics()
    stats_message = "Статистика игроков:\n\n" + "\n".join([f"ID пользователя: {user_id}, Последний результат: {score}" for user_id, score in statistics])
    await message.answer(stats_message)


async def get_question(message, user_id):

    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await get_quiz_index(user_id)
    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)


async def new_quiz(message):
    user_id = message.from_user.id
    current_question_index = 0
    user_score = 0
    await update_quiz_index(user_id, current_question_index, user_score)
    await get_question(message, user_id)

# Запуск процесса поллинга новых апдейтов
async def main():

    # Запускаем создание таблицы базы данных
    await create_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
from aiogram import types
from create_bot import bot, dp
from data_base import sqlite_db
from aiogram.dispatcher import FSMContext
from handlers import states
from keyboards import usually_kb
from handlers.admin_side import add_proxy_data
#/start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    all_users_id = [id_[0] for id_ in await sqlite_db.get_all_users()]
    if message.from_user.id not in all_users_id:
        await sqlite_db.add_user(message.from_user.id)

    await bot.send_message(message.chat.id, 'Привет это бот расписание. Помощь по командам /help')
    await bot.send_message(message.chat.id, 'Выберите группу в которой учитесь, либо напишите любой текст'
                                            'что-бы пропустить это',
                           reply_markup=usually_kb.group_keyboard(await sqlite_db.get_all_groups()))
    await states.StartStates.group_name.set()
@dp.message_handler(state=states.StartStates.group_name)
async def start_state(message: types.Message, state: FSMContext):
    all_group_names = [_[0] for _ in await sqlite_db.get_all_groups()]
    if message.text in all_group_names:
        await sqlite_db.change_user_group(message.from_user.id, message.text)
        await bot.send_message(message.chat.id, f'Окей, прикрепил тебя к группе {message.text}',
                               reply_markup=types.ReplyKeyboardRemove())
    else:
        await bot.send_message(message.chat.id, 'Ты пропустил выбор группу, но всегда сможешь'
                                                ' выбрать ее с помощью /select_group',
                               reply_markup=types.ReplyKeyboardRemove())
    await state.finish()
#/select_group выбор группы
@dp.message_handler(commands=['select_group'])
async def select_group_command(message: types.Message):
    all_groups = await sqlite_db.get_all_groups()
    group_kb = usually_kb.group_keyboard(all_groups)
    await message.reply('Выбери группу', reply=False,
                        reply_markup=group_kb)
    await states.SelectGroupStates.group_name.set()
@dp.message_handler(commands=['get_schedule'])
async def get_schedule_command(message: types.Message):
    user_id = message.from_user.id  # Получаем ID пользователя
    group_name = await sqlite_db.get_user_group(user_id)  # Предполагается, что эта функция получает группу, в которой состоит пользователь

    if group_name:
        schedule = await sqlite_db.get_schedule(group_name)  # Предполагается, что вы получаете расписание для данной группы
        if schedule:
            await bot.send_photo(message.chat.id, schedule, caption='РАСПИСАНИЕ ВАШЕЙ ГРУППЫ')
        else:
            await message.reply("Извините, расписание для вашей группы не найдено.")
    else:
        await message.reply("Вы не привязаны к группе. Используйте /select_group, чтобы выбрать группу.")
@dp.message_handler(state=states.SelectGroupStates.group_name)
async def select_group_state(message: types.Message, state: FSMContext):
    all_group_names = [_[0] for _ in await sqlite_db.get_all_groups()]
    if message.text in all_group_names:
        await sqlite_db.change_user_group(message.from_user.id, message.text)
        await bot.send_message(message.chat.id, f'Группа изменена',
                               reply_markup=types.ReplyKeyboardRemove())
    else:
        await bot.send_message(message.chat.id, 'Группу которую ты выбрал, не существует',
                               reply_markup=types.ReplyKeyboardRemove())
    await state.finish()
#/delete_me_from_group Возможность выйти из группы
@dp.message_handler(commands=['delete_me_from_group'])
async def delete_from_group(message: types.Message):
    await sqlite_db.change_user_group(message.from_user.id, None)
    await message.reply('Группа успешно отвязана', reply=False)
#/news Просмотр новостей
@dp.message_handler(commands=['news', 'новости'])
async def news_command(message: types.Message):
    news = await sqlite_db.get_news()
    for i in news[:3]:
        await bot.send_photo(message.chat.id, i[3], f'*{i[1]}*\n\n{i[2]}',
                             parse_mode='Markdown')
#/ask_question Можно задать вопрос админу
@dp.message_handler(commands=['ask_question'])
async def ask_question_command(message: types.Message):
    await message.reply('Напишите свой вопрос', reply=False)
    await states.AskQuestionStates.get_question.set()
@dp.message_handler(state=states.AskQuestionStates.get_question)
async def get_question_state(message: types.Message, state: FSMContext):
    await add_proxy_data(state, {
        'user_id': message.from_user.id,
        'question': message.text,
        'nick': message.from_user.username,
    })
    await sqlite_db.add_question(state)
    await message.reply('Вопрос задан, ждите ответа...', reply=False)
@dp.message_handler(commands=['id'])
async def get_group_id(message: types.Message, state: FSMContext):
    await message.reply(message.chat.id)
#/help список команд
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await bot.send_message(message.chat.id, 'Команды для взаимодействия с ботом:')
    await bot.send_message(message.chat.id, '/select_group(Выбор группы) /delete_me_from_group(Удалить себя из группы) /news(Новости от админа)')


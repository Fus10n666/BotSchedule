from aiogram import types
from keyboards import usually_kb
from create_bot import bot, dp, ADMINS_CHAT_ID
from handlers import states
from aiogram.dispatcher import FSMContext
from data_base import sqlite_db
from keyboards import inline_kb, delete_kb
from aiogram.dispatcher.filters import Text
from handlers import sending_messages
from create_bot import ADMINS_CHAT_ID
from data_base.sqlite_db import get_data_from_proxy


async def add_proxy_data(state, data: dict):
    async with state.proxy() as proxy:
        for k,v in data.items():
            proxy[k] = v

#Удаление группы
@dp.message_handler(commands=['delete_group'], is_chat_admin=True)
async def delete_group_command(message: types.Message):
    all_groups = await sqlite_db.get_all_groups()
    group_kb = usually_kb.group_keyboard(all_groups)
    await message.answer('Выберите группу для удаления', reply=False,
                         reply_markup=group_kb)
    await states.DeleteGroupStates.group_name.set()


@dp.message_handler(state=states.DeleteGroupStates.group_name)
async def delete_group_state(message: types.Message, state: FSMContext):
    all_groups_names = [name[0] for name in await sqlite_db.get_all_groups()]
    if message.text in all_groups_names:
        await sqlite_db.delete_group(message.text)
        await message.reply('Группа удалена!', reply=False,
                            reply_markup=types.ReplyKeyboardRemove())
    else:
        await bot.send_message(message.chat.id, 'Группа которую вы хотите удалить - не существует!')
    await state.finish()

#создание группы
@dp.message_handler(commands=['create_group'], is_chat_admin=True)
async def create_group_command(message: types.Message):
    await message.reply('Введите название группы')
    await states.CreateGroupStates.group_name.set()


@dp.message_handler(state=states.CreateGroupStates.group_name)
async def create_group_state(message: types.Message, state: FSMContext):
    await sqlite_db.add_group(message.text, message)
    await message.reply('Группа создана!', reply=False)
    await state.finish()

#Создание новостей
@dp.message_handler(commands=['create_news'], is_chat_admin=True)
async def create_news(message: types.Message):
    await states.NewsStates.title.set()
    await message.reply('Отправьте заголовок новости', reply=False)


@dp.message_handler(state=states.NewsStates.title)
async def state_title_news(message: types.Message, state: FSMContext):
    await add_proxy_data(state, {'title': message.text})
    await message.reply('Теперь введи содержание новости', reply=False)
    await states.NewsStates.next()


@dp.message_handler(state=states.NewsStates.content)
async def state_content_news(message: types.Message, state: FSMContext):
    await add_proxy_data(state, {'content': message.text})
    await message.reply('Отправьте фото к новости', reply=False)
    await states.NewsStates.next()


@dp.message_handler(state=states.NewsStates.image, content_types=['photo'])
async def state_image_news(message: types.Message, state: FSMContext):
    await add_proxy_data(state, {'image': message.photo[0].file_id})
    await sqlite_db.add_news(state)
    await message.reply('Новость успешно создана!', reply=False)
    await state.finish()

#Удаление новости
@dp.message_handler(commands=['delete_news'], is_chat_admin=True)
async def delete_news(message: types.Message):
    news = await sqlite_db.get_news()
    for i in news:
        await bot.send_photo(message.chat.id, i[3], f'*НОВОСТЬ*\n\n {i[1]}\n{i[2]}',
                             parse_mode='Markdown', reply_markup=inline_kb.create_delete_news_keyboard(i[0]))


@dp.callback_query_handler(Text(startswith='news '))
async def callback_delete_news(callback: types.CallbackQuery):
    cb_data = callback.data.replace('news ', '')
    await sqlite_db.delete_news(cb_data)
    await delete_kb.delete_inline_keyboard(callback.message)
    await callback.answer('Новость удалена!')
    await bot.send_message(callback.message.chat.id, 'Новость успешно удалена!')

#Создание расписания
@dp.message_handler(commands=['create_schedule'], is_chat_admin=True)
async def create_schedule(message: types.Message):
    groups = await sqlite_db.get_all_groups()
    await states.ScheduleStates.select_group.set()
    await message.reply('Выберите группу, которой хотите обновить расписание', reply=False,
                        reply_markup=usually_kb.group_keyboard(groups))


@dp.message_handler(state=states.ScheduleStates.select_group)
async def state_select_group_schedule(message: types.Message, state: FSMContext):
    all_groups_names = [name[0] for name in await sqlite_db.get_all_groups()]
    if message.text in all_groups_names:
        await add_proxy_data(state, {'group': message.text})
        await message.reply('Теперь отправь фотографию расписания', reply=False,
                            reply_markup=types.ReplyKeyboardRemove())
        await states.ScheduleStates.next()
    else:
        await bot.send_message(message.chat.id, 'Такой группы не существует!')
        await state.finish()


@dp.message_handler(state=states.ScheduleStates.image, content_types=['photo'])
async def state_image_schedule(message: types.Message, state: FSMContext):
    await add_proxy_data(state, {'image': message.photo[0].file_id})
    await sqlite_db.create_schedule(state)
    await message.reply('Расписание добавлено', reply=False)
    async with state.proxy() as data:
        await sending_messages.sending_schedule(data['group'])
    await state.finish()

#Удаление расписания
@dp.message_handler(commands=['delete_schedule'], is_chat_admin=True)
async def delete_schedule(message: types.Message):
    groups = await sqlite_db.get_all_groups()
    kb = usually_kb.group_keyboard(groups)
    await message.reply('Выберите группу, которую хотите удалить', reply=False,
                        reply_markup=kb)
    await states.DeleteScheduleStates.select_group.set()


@dp.message_handler(state=states.DeleteScheduleStates.select_group)
async def state_delete_schedule(message: types.Message, state: FSMContext):
    all_groups_names = [name[0] for name in await sqlite_db.get_all_groups()]
    if message.text in all_groups_names:
        await sqlite_db.delete_schedule(message.text)
        await message.reply(f'Расписание группы {message.text} удалено', reply=False,
                            reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
    else:
        await bot.send_message(message.chat.id, 'Такой группы не существует!')
        await state.finish()

#Просмотр вопросов от пользователей
@dp.message_handler(commands=['next_reply'], is_chat_admin=True)
async def next_reply_command(message: types.Message):
    all_qtns = sqlite_db.get_all_questions()
    if all_qtns:
        await states.AnswerTheQuestion.start.set()
        await bot.send_message(ADMINS_CHAT_ID, f'Вопрос от @{all_qtns[0][2]}:\n'
                                               f'{all_qtns[0][1]}',
                               reply_markup=await inline_kb.create_reply_keyboard(all_qtns[0][0]))
    else:
        await bot.send_message(ADMINS_CHAT_ID, 'Вопросы закончились')

#Ответы на вопросы пользователей
@dp.callback_query_handler(Text(startswith='qtn '), state=states.AnswerTheQuestion.start)
async def callback_question_and_start_state(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.data.replace('qtn ', '')
    await add_proxy_data(state, {'user_id': user_id})
    await states.AnswerTheQuestion.next()
    await callback.message.reply('Введите ответ пользователю', reply=False)
    await callback.answer()


@dp.message_handler(state=states.AnswerTheQuestion.answer)
async def answer_the_question(message: types.Message, state: FSMContext):
    dict_from_proxy = await get_data_from_proxy(state)
    await bot.send_message(int(dict_from_proxy['user_id']), 'На ваш вопрос ответили: \n'
                                                            f'{message.text}')
    await message.reply('Пользователь получил ваш ответ!', reply=False)
    await sqlite_db.delete_question(int(dict_from_proxy['user_id']))
    await state.finish()

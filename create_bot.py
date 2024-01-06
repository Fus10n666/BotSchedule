from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
storage= MemoryStorage()
bot=Bot(token='6576491678:AAHXiH8IYws4R1fiNkGIkc5rLE1ncNkpv_A')
ADMINS_CHAT_ID=-4035573279
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

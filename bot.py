#!/usr/bin/env python3
"""
ЛЮМИ БОТ - Персональный помощник
Telegram бот для отслеживания привычек, планирования событий,
ведения дневника, трекера цикла и личных записей.
Технологии:
- Python 3.11+
- aiogram 3.x
- APScheduler
- SQLAlchemy (aiosqlite)
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import settings
from database import init_db
from handlers import router as main_router
from handlers_planner import router as planner_router
from handlers_private import router as private_router
from handlers_cycle import router as cycle_router
from handlers_settings import router as settings_router
from handlers_admin import router as admin_router, setup_schedulers
# Настройка логирования
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)
async def on_startup(bot: Bot, dispatcher: Dispatcher):
    """Действия при запуске бота"""
    logger.info("🚀 Запуск бота ЛЮМИ...")
    
    # Инициализация базы данных
    await init_db()
    logger.info("✅ База данных инициализирована")
    
    # Уведомление админа
    if settings.ADMIN_ID:
        try:
            await bot.send_message(
                settings.ADMIN_ID,
                f"✅ <b>{settings.BOT_NAME} запущен!</b>\n\n"
                f"🤖 Бот готов к работе.\n"
                f"Используй /admin для панели управления."
            )
        except Exception as e:
            logger.warning(f"Не удалось уведомить админа: {e}")
    
    logger.info("🎯 Бот успешно запущен!")
async def on_shutdown(bot: Bot, dispatcher: Dispatcher):
    """Действия при остановке бота"""
    logger.info("🛑 Остановка бота...")
    
    # Уведомление админа
    if settings.ADMIN_ID:
        try:
            await bot.send_message(
                settings.ADMIN_ID,
                f"🛑 <b>{settings.BOT_NAME} остановлен</b>\n\n"
                f"Бот выключен."
            )
        except Exception:
            pass
    
    logger.info("👋 Бот остановлен")
async def cmd_help(message: Message):
    """Команда /help"""
    help_text = (
        "🌟 <b>ЛЮМИ - твой персональный помощник</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Помощь\n"
        "/admin - Панель администратора\n\n"
        "<b>Возможности:</b>\n"
        "• 👤 <b>Профиль</b> - статистика, уровень, XP\n"
        "• ✅ <b>Привычки</b> - создание и отслеживание привычек\n"
        "• 📅 <b>Планировщик</b> - события с уведомлениями\n"
        "• 🔒 <b>Личное</b> - приватные записи с PIN-кодом\n"
        "• 🌙 <b>Цикл</b> - трекер женского цикла\n"
        "• ⚙️ <b>Настройки</b> - уведомления и тихий режим\n\n"
        "<b>Система уровней:</b>\n"
        "За выполнение привычек и задач ты получаешь XP.\n"
        "Накапливай XP для повышения уровня!\n\n"
        "Начни с команды /start 🚀"
    )
    await message.answer(help_text)
async def cmd_cancel(message: Message, state):
    """Отмена текущего действия"""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer(
            "❌ Действие отменено.",
            reply_markup=main_menu_keyboard()
        )
    else:
        await message.answer("Нечего отменять.")
async def main():
    """Главная функция"""
    # Проверка токена
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "your_bot_token_here":
        logger.error("❌ BOT_TOKEN не установлен! Укажи токен в .env файле.")
        sys.exit(1)
    
    # Инициализация бота
    bot = Bot(token=settings.BOT_TOKEN, parse_mode=ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Подключаем роутеры
    dp.include_router(main_router)
    dp.include_router(planner_router)
    dp.include_router(private_router)
    dp.include_router(cycle_router)
    dp.include_router(settings_router)
    dp.include_router(admin_router)
    
    # Регистрируем команды
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_cancel, Command("cancel"))
    
    # Регистрируем хуки жизненного цикла
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Настройка планировщика
    scheduler = AsyncIOScheduler()
    setup_schedulers(scheduler, bot)
    scheduler.start()
    logger.info("⏰ Планировщик запущен")
    
    # Запуск бота
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        scheduler.shutdown()
        await bot.session.close()
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

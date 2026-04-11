from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards.reply import main_kb

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Бот запущен! Используй меню:", reply_markup=main_kb())

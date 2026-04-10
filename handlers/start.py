from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from db.queries import get_user, add_user
from keyboards.main_menu import main_menu

# Создаем "роутер" для этого файла. Он собирает все обработчики отсюда.
router = Router()

# Создаем "чекпоинты" (состояния) для регистрации
class Registration(StatesGroup):
    waiting_for_name = State()


# 1. Реакция на команду /start
@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    # Спрашиваем базу: этот юзер у нас есть?
    user = await get_user(message.from_user.id)
    
    if user:
        # Вариант Б из ТЗ: Если человек УЖЕ есть - просто обновляем меню без лишнего текста
        await message.answer(
            "С возвращением! 🌸", 
            reply_markup=main_menu()
        )
    else:
        # Если человека НЕТ - ставим чекпоинт "ждем имя"
        await state.set_state(Registration.waiting_for_name)
        await message.answer(
            "Привет! Я <b>ЛЮМИ</b>, твой личный помощник.\n\n"
            "Как мне к тебе обращаться?",
            parse_mode="HTML"
        )


# 2. Реакция на введенное имя (срабатывает только если стоит чекпоинт waiting_for_name)
@router.message(Registration.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip() # Убираем пробелы по краям
    
    # ВАРИАНТ Б: Строгая проверка имени
    # Убираем пробелы и дефисы, оставляем только буквы. 
    # Если остались только буквы и длина от 2 до 30 - всё ок.
    clean_name = name.replace(" ", "").replace("-", "")
    
    if not (2 <= len(name) <= 30) or not clean_name.isalpha():
        await message.answer(
            "Пожалуйста, введи корректное имя.\n"
            "(Только буквы, от 2 до 30 символов, без смайликов и цифр) 😊"
        )
        return # Прерываем функцию, ждем новое сообщение


    # Если проверка пройдена - забираем никнейм из Телеграма
    username = message.from_user.username
    
    # Сохраняем в базу
    await add_user(message.from_user.id, username, name)
    
    # Убираем чекпоинт (имя получено)
    await state.clear()
    
    # Выдаем главное меню
    await message.answer(
        f"Приятно познакомиться, <b>{name}</b>! 🌸\n"
        f"Выбирай раздел в меню ниже 👇",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

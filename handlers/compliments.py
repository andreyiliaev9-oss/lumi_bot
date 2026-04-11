import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func
from db.db import async_session
from db.models import Compliment, User
from config import ADMIN_ID

router = Router()

class ComplimentForm(StatesGroup):
    text = State()

@router.message(F.text == "💝 Комплименты")
async def send_random_compliment(message: Message):
    tg_id = message.from_user.id
    async with async_session() as session:
        # Получаем случайный комплимент из активных
        total = await session.scalar(select(func.count(Compliment.id)).where(Compliment.is_active == True))
        if total == 0:
            await message.answer("💜 Пока нет комплиментов. Администратор добавит их позже.")
            return
        random_offset = random.randint(0, total - 1)
        compliment = await session.scalar(select(Compliment).where(Compliment.is_active == True).offset(random_offset).limit(1))
        if compliment:
            await message.answer(f"💜 {compliment.text}")

# Админские функции (только для ADMIN_ID)
@router.message(F.text == "👑 Админ-панель")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💝 Управление комплиментами", callback_data="admin_compliments")],
        [InlineKeyboardButton(text="🌸 Управление советами цикла", callback_data="admin_cycle_tips")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")]
    ])
    await message.answer("👑 Админ-панель", reply_markup=kb)

@router.callback_query(lambda c: c.data == "admin_compliments" and c.from_user.id == ADMIN_ID)
async def manage_compliments(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить комплимент", callback_data="add_compliment")],
        [InlineKeyboardButton(text="📋 Список комплиментов", callback_data="list_compliments")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")]
    ])
    await callback.message.edit_text("Управление комплиментами:", reply_markup=kb)
    await callback.answer()

@router.callback_query(lambda c: c.data == "add_compliment" and c.from_user.id == ADMIN_ID)
async def add_compliment_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите текст комплимента (можно с эмодзи):")
    await state.set_state(ComplimentForm.text)
    await callback.answer()

@router.message(ComplimentForm.text)
async def save_compliment(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    text = message.text.strip()
    async with async_session() as session:
        compliment = Compliment(text=text)
        session.add(compliment)
        await session.commit()
    await message.answer("✅ Комплимент добавлен!")
    await state.clear()
    await admin_panel(message)

@router.callback_query(lambda c: c.data == "list_compliments" and c.from_user.id == ADMIN_ID)
async def list_compliments(callback: CallbackQuery):
    async with async_session() as session:
        compliments = await session.execute(select(Compliment).order_by(Compliment.id))
        comp_list = compliments.scalars().all()
        if not comp_list:
            text = "Нет комплиментов."
        else:
            text = "📋 Список комплиментов:\n\n"
            for c in comp_list:
                status = "✅" if c.is_active else "❌"
                text += f"{status} ID {c.id}: {c.text[:50]}{'...' if len(c.text)>50 else ''}\n"
                text += f"Команды: /del_comp_{c.id} | /toggle_comp_{c.id}\n\n"
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_compliments")]
        ]))
    await callback.answer()

# Команды для админа (можно использовать в чате)
@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text.startswith("/del_comp_"))
async def delete_compliment(message: Message):
    comp_id = int(message.text.split("_")[2])
    async with async_session() as session:
        comp = await session.get(Compliment, comp_id)
        if comp:
            await session.delete(comp)
            await session.commit()
            await message.answer(f"🗑 Комплимент ID {comp_id} удалён.")
        else:
            await message.answer("Не найден.")

@router.message(lambda m: m.from_user.id == ADMIN_ID and m.text.startswith("/toggle_comp_"))
async def toggle_compliment(message: Message):
    comp_id = int(message.text.split("_")[2])
    async with async_session() as session:
        comp = await session.get(Compliment, comp_id)
        if comp:
            comp.is_active = not comp.is_active
            await session.commit()
            await message.answer(f"🔄 Комплимент ID {comp_id} {'активирован' if comp.is_active else 'деактивирован'}.")
        else:
            await message.answer("Не найден.")

@router.callback_query(lambda c: c.data == "back_to_admin" and c.from_user.id == ADMIN_ID)
async def back_to_admin(callback: CallbackQuery):
    await admin_panel(callback.message)
    await callback.answer()

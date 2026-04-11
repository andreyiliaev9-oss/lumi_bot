from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, date
from sqlalchemy import select
from db.db import async_session
from db.models import User, TimeCapsule
from keyboards.inline import back_button

router = Router()

class CapsuleForm(StatesGroup):
    title = State()
    content = State()
    open_date = State()

@router.callback_query(F.data == "time_capsule")
async def time_capsule_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Создать капсулу", callback_data="capsule_new")],
        [InlineKeyboardButton(text="📋 Мои капсулы", callback_data="capsule_list")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="exit_private")]
    ])
    await callback.message.edit_text("📦 Капсула времени — письма в будущее", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "capsule_new")
async def capsule_new_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите заголовок капсулы:")
    await state.set_state(CapsuleForm.title)
    await callback.answer()

@router.message(CapsuleForm.title)
async def capsule_get_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите текст сообщения:")
    await state.set_state(CapsuleForm.content)

@router.message(CapsuleForm.content)
async def capsule_get_content(message: Message, state: FSMContext):
    await state.update_data(content=message.text)
    await message.answer("Введите дату открытия в формате <b>ДД.ММ.ГГГГ</b> (например, 31.12.2026):")
    await state.set_state(CapsuleForm.open_date)

@router.message(CapsuleForm.open_date)
async def capsule_get_date(message: Message, state: FSMContext):
    try:
        open_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        if open_date <= date.today():
            await message.answer("⚠️ Дата открытия должна быть в будущем. Введите корректную дату.")
            return
    except:
        await message.answer("❌ Неверный формат. Используйте <b>ДД.ММ.ГГГГ</b>")
        return
    data = await state.get_data()
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if not user:
            await message.answer("Ошибка")
            return
        capsule = TimeCapsule(
            user_id=user.id,
            title=data['title'],
            content=data['content'],
            open_date=open_date
        )
        session.add(capsule)
        await session.commit()
    await message.answer(f"✅ Капсула создана! Она откроется {open_date.strftime('%d.%m.%Y')}.", reply_markup=back_button("time_capsule"))
    await state.clear()

@router.callback_query(F.data == "capsule_list")
async def capsule_list(callback: CallbackQuery):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == callback.from_user.id))
        if not user:
            await callback.answer("Ошибка")
            return
        capsules = await session.execute(
            select(TimeCapsule).where(TimeCapsule.user_id == user.id)
            .order_by(TimeCapsule.open_date)
        )
        caps_list = capsules.scalars().all()
        if not caps_list:
            text = "У вас нет капсул времени."
            await callback.message.edit_text(text, reply_markup=back_button("time_capsule"))
        else:
            text = "📦 <b>Ваши капсулы времени:</b>\n\n"
            for c in caps_list:
                status = "🔓 Открыта" if c.is_opened else f"🔒 Откроется {c.open_date.strftime('%d.%m.%Y')}"
                text += f"• <b>{c.title}</b> — {status}\n"
                text += f"  ID: {c.id} | Команды: /viewcapsule_{c.id} /delcapsule_{c.id}\n\n"
            await callback.message.edit_text(text, reply_markup=back_button("time_capsule"))
    await callback.answer()

@router.message(lambda m: m.text and m.text.startswith("/viewcapsule_"))
async def view_capsule(message: Message):
    capsule_id = int(message.text.split("_")[1])
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if not user:
            return
        capsule = await session.get(TimeCapsule, capsule_id)
        if capsule and capsule.user_id == user.id:
            if capsule.is_opened or capsule.open_date <= date.today():
                text = f"<b>📦 {capsule.title}</b>\n\n{capsule.content}\n\n📅 Создана: {capsule.created_at.strftime('%d.%m.%Y')}\n🔓 Открыта: {capsule.open_date.strftime('%d.%m.%Y')}"
            else:
                text = f"🔒 Эта капсула откроется {capsule.open_date.strftime('%d.%m.%Y')}. Загляните позже."
            await message.answer(text)
        else:
            await message.answer("Капсула не найдена.")

@router.message(lambda m: m.text and m.text.startswith("/delcapsule_"))
async def delete_capsule(message: Message):
    capsule_id = int(message.text.split("_")[1])
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if not user:
            return
        capsule = await session.get(TimeCapsule, capsule_id)
        if capsule and capsule.user_id == user.id:
            await session.delete(capsule)
            await session.commit()
            await message.answer("🗑 Капсула удалена.")
        else:
            await message.answer("Капсула не найдена.")

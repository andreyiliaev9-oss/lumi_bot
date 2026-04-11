from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.db import async_session
from db.models import User, DiaryEntry
from sqlalchemy import select, update, func
from keyboards.inline import private_main_menu_kb

router = Router()

class DiaryStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_emotion = State()

@router.callback_query(F.data == "p_diary")
async def diary_index(callback: CallbackQuery):
    async with async_session() as session:
        # Считаем количество записей пользователя
        user = await session.scalar(select(User).where(User.tg_id == callback.from_user.id))
        count = await session.scalar(
            select(func.count(DiaryEntry.id)).where(DiaryEntry.user_id == user.id)
        )
    
    text = (
        f"📖 <b>ЛИЧНЫЙ ДНЕВНИК</b>\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"У тебя уже <b>{count}</b> записей.\n"
        f"Дневник — это твой безопасный уголок, где можно выговориться.\n\n"
        f"Чего желаешь?"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Написать мысль", callback_data="diary_add")],
        [InlineKeyboardButton(text="📜 Последние записи", callback_data="diary_view")],
        [InlineKeyboardButton(text="« Назад", callback_data="p_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "diary_add")
async def add_entry_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("О чем ты сейчас думаешь? Просто напиши это одним сообщением:")
    await state.set_state(DiaryStates.waiting_for_text)

@router.message(DiaryStates.waiting_for_text)
async def get_diary_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    
    # Кнопки эмоций
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="😊 Радость", callback_data="emo_happy"),
            InlineKeyboardButton(text="❤️ Любовь", callback_data="emo_love")
        ],
        [
            InlineKeyboardButton(text="😔 Грусть", callback_data="emo_sad"),
            InlineKeyboardButton(text="😤 Гнев", callback_data="emo_angry")
        ],
        [InlineKeyboardButton(text="😐 Спокойствие", callback_data="emo_neutral")]
    ])
    
    await message.answer("Какую эмоцию ты сейчас чувствуешь?", reply_markup=kb)
    await state.set_state(DiaryStates.waiting_for_emotion)

@router.callback_query(F.data.startswith("emo_"))
async def save_diary_entry(callback: CallbackQuery, state: FSMContext):
    emotion_map = {
        "emo_happy": "😊 Радость",
        "emo_love": "❤️ Любовь",
        "emo_sad": "😔 Грусть",
        "emo_angry": "😤 Гнев",
        "emo_neutral": "😐 Спокойствие"
    }
    
    data = await state.get_data()
    emotion = emotion_map.get(callback.data, "😐 Спокойствие")
    
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == callback.from_user.id))
        
        # Добавляем запись
        new_entry = DiaryEntry(
            user_id=user.id,
            text=data['text'],
            emotion=emotion
        )
        session.add(new_entry)
        
        # Обновляем счетчик в профиле
        await session.execute(
            update(User).where(User.id == user.id).values(diary_count=user.diary_count + 1)
        )
        await session.commit()
    
    await state.clear()
    await callback.message.edit_text(
        f"✅ <b>Запись сохранена!</b>\n\nЯ запомнила твои чувства. Теперь ты можешь вернуться в меню.",
        reply_markup=private_main_menu_kb(),
        parse_mode="HTML"
    )

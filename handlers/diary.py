from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import date, datetime
from sqlalchemy import select, delete, func
from db.db import async_session
from db.models import DiaryEntry
from keyboards.inline import back_button

router = Router()

# Состояния для FSM
class DiaryForm(StatesGroup):
    text = State()
    emotion = State()
    entry_date = State()
    tags = State()
    edit_id = State()
    edit_text = State()
    search_type = State()
    search_date = State()
    search_tag = State()

# Эмодзи для эмоций
EMOTIONS = {
    "😊 Радость": "joy",
    "😢 Грусть": "sadness",
    "😠 Гнев": "anger",
    "😨 Страх": "fear",
    "😌 Спокойствие": "calm",
    "❤️ Любовь": "love",
    "🤔 Задумчивость": "thought"
}

# ---------- Главное меню дневника ----------
@router.callback_query(F.data == "diary")
async def diary_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Новая запись", callback_data="diary_new")],
        [InlineKeyboardButton(text="📋 Мои записи", callback_data="diary_list")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="diary_search")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="start")]
    ])
    await callback.message.edit_text("📔 Личный дневник", reply_markup=kb)
    await callback.answer()

# ---------- Создание записи ----------
@router.callback_query(F.data == "diary_new")
async def diary_new_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите текст записи:")
    await state.set_state(DiaryForm.text)
    await callback.answer()

@router.message(DiaryForm.text)
async def diary_get_text(message: Message, state: FSMContext):
    if len(message.text) > 2000:
        await message.answer("Текст слишком длинный (макс. 2000 символов). Сократите.")
        return
    await state.update_data(text=message.text)
    # Клавиатура выбора эмоции
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=emoji, callback_data=f"emotion_{code}") for emoji, code in list(EMOTIONS.items())[i:i+3]]
        for i in range(0, len(EMOTIONS), 3)
    ])
    await message.answer("Выберите эмоцию (можно пропустить):", reply_markup=kb)
    await state.set_state(DiaryForm.emotion)

@router.callback_query(DiaryForm.emotion, F.data.startswith("emotion_"))
async def diary_get_emotion(callback: CallbackQuery, state: FSMContext):
    emotion_code = callback.data.split("_")[1]
    await state.update_data(emotion=emotion_code)
    # Предлагаем изменить дату или оставить сегодня
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Сегодня", callback_data="date_today"),
         InlineKeyboardButton(text="📆 Выбрать другую дату", callback_data="date_other")]
    ])
    await callback.message.edit_text("Выберите дату записи:", reply_markup=kb)
    await state.set_state(DiaryForm.entry_date)
    await callback.answer()

@router.callback_query(DiaryForm.entry_date, F.data == "date_today")
async def diary_date_today(callback: CallbackQuery, state: FSMContext):
    await state.update_data(entry_date=date.today())
    await callback.message.edit_text("Введите теги через пробел (или '-' для пропуска):")
    await state.set_state(DiaryForm.tags)
    await callback.answer()

@router.callback_query(DiaryForm.entry_date, F.data == "date_other")
async def diary_date_other(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите дату в формате ГГГГ-ММ-ДД:")
    await state.set_state(DiaryForm.entry_date)
    await callback.answer()

@router.message(DiaryForm.entry_date)
async def diary_set_date(message: Message, state: FSMContext):
    try:
        entry_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        if entry_date > date.today():
            await message.answer("Дата не может быть в будущем.")
            return
        await state.update_data(entry_date=entry_date)
        await message.answer("Введите теги через пробел (или '-' для пропуска):")
        await state.set_state(DiaryForm.tags)
    except:
        await message.answer("Неверный формат. Используйте ГГГГ-ММ-ДД")

@router.message(DiaryForm.tags)
async def diary_get_tags(message: Message, state: FSMContext):
    tags = None if message.text == "-" else message.text
    data = await state.get_data()
    async with async_session() as session:
        entry = DiaryEntry(
            user_id=message.from_user.id,
            text=data['text'],
            emotion=data.get('emotion'),
            date=data['entry_date'],
            tags=tags
        )
        session.add(entry)
        await session.commit()
    await message.answer("✅ Запись сохранена!", reply_markup=back_button("diary"))
    await state.clear()

# ---------- Список записей с пагинацией ----------
@router.callback_query(F.data == "diary_list")
async def diary_list(callback: CallbackQuery, page: int = 0):
    async with async_session() as session:
        # Получаем общее количество записей
        total = await session.scalar(select(func.count(DiaryEntry.id)).where(DiaryEntry.user_id == callback.from_user.id))
        if total == 0:
            await callback.message.edit_text("У вас пока нет записей.", reply_markup=back_button("diary"))
            await callback.answer()
            return
        offset = page * 5
        entries = await session.execute(
            select(DiaryEntry).where(DiaryEntry.user_id == callback.from_user.id)
            .order_by(DiaryEntry.date.desc())
            .offset(offset).limit(5)
        )
        entries_list = entries.scalars().all()
        text = "📋 <b>Ваши записи:</b>\n\n"
        for e in entries_list:
            emotion_emoji = next((emoji for emoji, code in EMOTIONS.items() if code == e.emotion), "📌")
            text += f"{emotion_emoji} <b>{e.date}</b>\n{e.text[:100]}{'...' if len(e.text)>100 else ''}\n"
            if e.tags:
                text += f"🏷️ {e.tags}\n"
            text += f"[ID: {e.id}] — /edit_{e.id} /del_{e.id}\n\n"
        # Клавиатура пагинации
        kb = InlineKeyboardMarkup(inline_keyboard=[])
        if page > 0:
            kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"diary_page_{page-1}")])
        if (page+1)*5 < total:
            kb.inline_keyboard.append([InlineKeyboardButton(text="Вперед ▶️", callback_data=f"diary_page_{page+1}")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="diary")])
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("diary_page_"))
async def diary_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    await diary_list(callback, page)

# ---------- Редактирование записи ----------
@router.message(F.text.startswith("/edit_"))
async def edit_entry_start(message: Message, state: FSMContext):
    entry_id = int(message.text.split("_")[1])
    async with async_session() as session:
        entry = await session.get(DiaryEntry, entry_id)
        if not entry or entry.user_id != message.from_user.id:
            await message.answer("Запись не найдена.")
            return
        await state.update_data(edit_id=entry_id)
        await message.answer(f"Текущий текст:\n{entry.text}\n\nВведите новый текст:")
        await state.set_state(DiaryForm.edit_text)

@router.message(DiaryForm.edit_text)
async def edit_entry_save(message: Message, state: FSMContext):
    data = await state.get_data()
    entry_id = data['edit_id']
    new_text = message.text
    async with async_session() as session:
        entry = await session.get(DiaryEntry, entry_id)
        if entry and entry.user_id == message.from_user.id:
            entry.text = new_text
            await session.commit()
            await message.answer("✅ Запись обновлена!", reply_markup=back_button("diary"))
        else:
            await message.answer("Ошибка: запись не найдена.")
    await state.clear()

# ---------- Удаление записи ----------
@router.message(F.text.startswith("/del_"))
async def delete_entry(message: Message):
    entry_id = int(message.text.split("_")[1])
    async with async_session() as session:
        entry = await session.get(DiaryEntry, entry_id)
        if entry and entry.user_id == message.from_user.id:
            await session.delete(entry)
            await session.commit()
            await message.answer("🗑 Запись удалена.", reply_markup=back_button("diary"))
        else:
            await message.answer("Запись не найдена.")

# ---------- Поиск ----------
@router.callback_query(F.data == "diary_search")
async def search_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 По дате", callback_data="search_by_date")],
        [InlineKeyboardButton(text="🏷️ По тегу", callback_data="search_by_tag")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="diary")]
    ])
    await callback.message.edit_text("Выберите тип поиска:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "search_by_date")
async def search_by_date_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите дату в формате ГГГГ-ММ-ДД:")
    await state.set_state(DiaryForm.search_date)
    await callback.answer()

@router.message(DiaryForm.search_date)
async def search_by_date_result(message: Message, state: FSMContext):
    try:
        search_date = datetime.strptime(message.text, "%Y-%m-%d").date()
    except:
        await message.answer("Неверный формат.")
        return
    async with async_session() as session:
        entries = await session.execute(
            select(DiaryEntry).where(DiaryEntry.user_id == message.from_user.id, DiaryEntry.date == search_date)
            .order_by(DiaryEntry.date.desc())
        )
        entries_list = entries.scalars().all()
        if not entries_list:
            await message.answer("Записей за эту дату не найдено.", reply_markup=back_button("diary"))
        else:
            text = f"📅 Записи за {search_date}:\n\n"
            for e in entries_list:
                emotion_emoji = next((emoji for emoji, code in EMOTIONS.items() if code == e.emotion), "📌")
                text += f"{emotion_emoji} {e.text}\n"
                if e.tags:
                    text += f"🏷️ {e.tags}\n"
                text += f"[ID: {e.id}] — /edit_{e.id} /del_{e.id}\n\n"
            await message.answer(text, reply_markup=back_button("diary"))
    await state.clear()

@router.callback_query(F.data == "search_by_tag")
async def search_by_tag_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите тег (или часть тега) для поиска:")
    await state.set_state(DiaryForm.search_tag)
    await callback.answer()

@router.message(DiaryForm.search_tag)
async def search_by_tag_result(message: Message, state: FSMContext):
    tag = message.text
    async with async_session() as session:
        entries = await session.execute(
            select(DiaryEntry).where(DiaryEntry.user_id == message.from_user.id, DiaryEntry.tags.contains(tag))
            .order_by(DiaryEntry.date.desc())
        )
        entries_list = entries.scalars().all()
        if not entries_list:
            await message.answer(f"Записей с тегом '{tag}' не найдено.", reply_markup=back_button("diary"))
        else:
            text = f"🏷️ Записи по тегу '{tag}':\n\n"
            for e in entries_list:
                emotion_emoji = next((emoji for emoji, code in EMOTIONS.items() if code == e.emotion), "📌")
                text += f"{emotion_emoji} <b>{e.date}</b>\n{e.text[:100]}{'...' if len(e.text)>100 else ''}\n"
                if e.tags:
                    text += f"🏷️ {e.tags}\n"
                text += f"[ID: {e.id}] — /edit_{e.id} /del_{e.id}\n\n"
            await message.answer(text, reply_markup=back_button("diary"))
    await state.clear()

import hashlib
import time
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from db.db import async_session
from db.models import User, SecretNote
from keyboards.inline import back_button

router = Router()

# Хранилище блокировок: {user_id: (попытки, время_разблокировки)}
blocked_until = {}

class PinState(StatesGroup):
    waiting_pin = State()

class SecretNoteState(StatesGroup):
    title = State()
    content = State()
    edit_id = State()
    edit_title = State()
    edit_content = State()

# ---------- Вспомогательные функции ----------
def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()

async def set_pin_hash(user_id: int, pin: str):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.pin_hash = hash_pin(pin)
            await session.commit()

async def check_pin(user_id: int, pin: str) -> bool:
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user and user.pin_hash:
            return user.pin_hash == hash_pin(pin)
    return False

async def is_authenticated(user_id: int) -> bool:
    # Для простоты используем временную сессию в памяти
    # В реальном проекте можно хранить в Redis или в БД с TTL
    return user_id in auth_sessions and auth_sessions[user_id] > time.time()

# Словарь активных сессий (user_id: время истечения)
auth_sessions = {}

# ---------- Вход по PIN ----------
@router.callback_query(F.data == "secret_notes")
async def secret_auth(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    # Проверяем блокировку
    if user_id in blocked_until and blocked_until[user_id] > time.time():
        remaining = int(blocked_until[user_id] - time.time())
        await callback.answer(f"Доступ заблокирован на {remaining} сек.", show_alert=True)
        return
    await callback.message.edit_text("🔒 Введите PIN-код (4 цифры):")
    await state.set_state(PinState.waiting_pin)
    await callback.answer()

@router.message(PinState.waiting_pin)
async def check_pin_code(message: Message, state: FSMContext):
    user_id = message.from_user.id
    pin = message.text.strip()
    # Удаляем сообщение пользователя с PIN
    await message.delete()

    # Проверяем, не заблокирован ли
    if user_id in blocked_until and blocked_until[user_id] > time.time():
        await message.answer("⛔ Доступ временно заблокирован. Попробуйте позже.")
        await state.clear()
        return

    # Если PIN ещё не установлен (первый вход), устанавливаем его
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user.pin_hash:
            if len(pin) != 4 or not pin.isdigit():
                await message.answer("PIN должен состоять из 4 цифр. Повторите ввод.")
                return
            await set_pin_hash(user_id, pin)
            auth_sessions[user_id] = time.time() + 3600  # сессия на 1 час
            await message.answer("🔐 PIN установлен! Доступ к заметкам открыт.", reply_markup=await secret_menu_kb())
            await state.clear()
            return

    # Проверяем PIN
    if await check_pin(user_id, pin):
        auth_sessions[user_id] = time.time() + 3600
        await message.answer("✅ Доступ разрешён.", reply_markup=await secret_menu_kb())
        await state.clear()
    else:
        # Неверный PIN: увеличиваем счётчик попыток
        attempts = 1
        if user_id in blocked_until:
            # Если уже есть блокировка, но она не истекла, не увеличиваем
            if blocked_until[user_id] > time.time():
                await message.answer("⛔ Доступ заблокирован. Попробуйте позже.")
                await state.clear()
                return
            # Если блокировка истекла, сбрасываем
        # Получаем текущее количество попыток из временного хранилища
        if user_id in blocked_until and blocked_until[user_id] < time.time():
            del blocked_until[user_id]
        # Увеличиваем счётчик
        attempts = blocked_until.get(user_id, (0,0))[0] + 1
        if attempts >= 3:
            blocked_until[user_id] = time.time() + 300  # блокировка на 5 минут
            await message.answer("⛔ Неверный PIN 3 раза. Доступ заблокирован на 5 минут.")
        else:
            blocked_until[user_id] = (attempts, 0)  # не время, а просто счётчик
            await message.answer(f"❌ Неверный PIN. Осталось попыток: {3 - attempts}")
        await state.clear()

# ---------- Клавиатура меню заметок ----------
async def secret_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Новая заметка", callback_data="secret_new")],
        [InlineKeyboardButton(text="📋 Мои заметки", callback_data="secret_list")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="start")]
    ])

# ---------- Проверка аутентификации (middleware или явно) ----------
async def check_auth(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in auth_sessions or auth_sessions[user_id] < time.time():
        await callback.answer("🔒 Требуется повторный вход. Используйте меню 'Приватные заметки'", show_alert=True)
        return False
    return True

# ---------- Создание заметки ----------
@router.callback_query(F.data == "secret_new")
async def secret_new_start(callback: CallbackQuery, state: FSMContext):
    if not await check_auth(callback):
        return
    await callback.message.edit_text("Введите заголовок заметки:")
    await state.set_state(SecretNoteState.title)
    await callback.answer()

@router.message(SecretNoteState.title)
async def secret_get_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите текст заметки (можно с переносами):")
    await state.set_state(SecretNoteState.content)

@router.message(SecretNoteState.content)
async def secret_get_content(message: Message, state: FSMContext):
    content = message.text
    data = await state.get_data()
    async with async_session() as session:
        note = SecretNote(
            user_id=message.from_user.id,
            title=data['title'],
            content=content
        )
        session.add(note)
        await session.commit()
    await message.answer("✅ Заметка сохранена!", reply_markup=await secret_menu_kb())
    await state.clear()

# ---------- Список заметок ----------
@router.callback_query(F.data == "secret_list")
async def secret_list(callback: CallbackQuery, page: int = 0):
    if not await check_auth(callback):
        return
    async with async_session() as session:
        total = await session.scalar(select(SecretNote.id).where(SecretNote.user_id == callback.from_user.id).count())
        if total == 0:
            await callback.message.edit_text("У вас нет приватных заметок.", reply_markup=await secret_menu_kb())
            await callback.answer()
            return
        offset = page * 5
        notes = await session.execute(
            select(SecretNote).where(SecretNote.user_id == callback.from_user.id)
            .order_by(SecretNote.created_at.desc())
            .offset(offset).limit(5)
        )
        notes_list = notes.scalars().all()
        text = "📋 <b>Ваши заметки:</b>\n\n"
        for n in notes_list:
            text += f"📌 <b>{n.title}</b> (ID: {n.id})\n{n.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            text += f"{n.content[:100]}{'...' if len(n.content)>100 else ''}\n"
            text += f"Команды: /view_{n.id} | /edit_{n.id} | /del_{n.id}\n\n"
        # Пагинация
        kb = InlineKeyboardMarkup(inline_keyboard=[])
        if page > 0:
            kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"secret_page_{page-1}")])
        if (page+1)*5 < total:
            kb.inline_keyboard.append([InlineKeyboardButton(text="Вперед ▶️", callback_data=f"secret_page_{page+1}")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="secret_notes")])
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("secret_page_"))
async def secret_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    await secret_list(callback, page)

# ---------- Просмотр заметки ----------
@router.message(F.text.startswith("/view_"))
async def view_secret_note(message: Message):
    if not await check_auth_message(message):
        return
    note_id = int(message.text.split("_")[1])
    async with async_session() as session:
        note = await session.get(SecretNote, note_id)
        if note and note.user_id == message.from_user.id:
            await message.answer(f"<b>{note.title}</b>\n\n{note.content}\n\n📅 {note.created_at}")
        else:
            await message.answer("Заметка не найдена.")

# ---------- Редактирование заметки ----------
@router.message(F.text.startswith("/edit_"))
async def edit_secret_start(message: Message, state: FSMContext):
    if not await check_auth_message(message):
        return
    note_id = int(message.text.split("_")[1])
    async with async_session() as session:
        note = await session.get(SecretNote, note_id)
        if not note or note.user_id != message.from_user.id:
            await message.answer("Заметка не найдена.")
            return
        await state.update_data(edit_id=note_id)
        await message.answer(f"Текущий заголовок: {note.title}\nВведите новый заголовок:")
        await state.set_state(SecretNoteState.edit_title)

@router.message(SecretNoteState.edit_title)
async def edit_secret_title(message: Message, state: FSMContext):
    await state.update_data(edit_title=message.text)
    await message.answer("Введите новый текст заметки:")
    await state.set_state(SecretNoteState.edit_content)

@router.message(SecretNoteState.edit_content)
async def edit_secret_content(message: Message, state: FSMContext):
    data = await state.get_data()
    note_id = data['edit_id']
    new_title = data['edit_title']
    new_content = message.text
    async with async_session() as session:
        note = await session.get(SecretNote, note_id)
        if note and note.user_id == message.from_user.id:
            note.title = new_title
            note.content = new_content
            note.updated_at = datetime.now()
            await session.commit()
            await message.answer("✅ Заметка обновлена!")
        else:
            await message.answer("Ошибка")
    await state.clear()

# ---------- Удаление заметки ----------
@router.message(F.text.startswith("/del_"))
async def delete_secret_note(message: Message):
    if not await check_auth_message(message):
        return
    note_id = int(message.text.split("_")[1])
    async with async_session() as session:
        note = await session.get(SecretNote, note_id)
        if note and note.user_id == message.from_user.id:
            await session.delete(note)
            await session.commit()
            await message.answer("🗑 Заметка удалена.")
        else:
            await message.answer("Заметка не найдена.")

# Вспомогательная функция проверки аутентификации для сообщений
async def check_auth_message(message: Message) -> bool:
    user_id = message.from_user.id
    if user_id not in auth_sessions or auth_sessions[user_id] < time.time():
        await message.answer("🔒 Требуется повторный вход. Нажмите 'Приватные заметки' в меню.")
        return False
    return True

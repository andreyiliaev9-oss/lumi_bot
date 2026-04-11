from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from sqlalchemy import select
from db.db import async_session
from db.models import User, SecretNote
from keyboards.inline import back_button

router = Router()

class NoteForm(StatesGroup):
    title = State()
    content = State()
    edit_id = State()
    edit_title = State()
    edit_content = State()

@router.callback_query(F.data == "secret_notes")
async def secret_notes_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Новая заметка", callback_data="note_new")],
        [InlineKeyboardButton(text="📋 Мои заметки", callback_data="note_list")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="exit_private")]
    ])
    await callback.message.edit_text("📝 Приватные заметки", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "note_new")
async def note_new_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите заголовок заметки:")
    await state.set_state(NoteForm.title)
    await callback.answer()

@router.message(NoteForm.title)
async def note_get_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите текст заметки:")
    await state.set_state(NoteForm.content)

@router.message(NoteForm.content)
async def note_get_content(message: Message, state: FSMContext):
    content = message.text
    data = await state.get_data()
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if not user:
            await message.answer("Ошибка")
            return
        note = SecretNote(
            user_id=user.id,
            title=data['title'],
            content=content
        )
        session.add(note)
        await session.commit()
    await message.answer("✅ Заметка сохранена!", reply_markup=back_button("secret_notes"))
    await state.clear()

@router.callback_query(F.data == "note_list")
async def note_list(callback: CallbackQuery, page: int = 0):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == callback.from_user.id))
        if not user:
            await callback.answer("Ошибка")
            return
        total = await session.scalar(select(SecretNote.id).where(SecretNote.user_id == user.id).count())
        if total == 0:
            await callback.message.edit_text("У вас нет заметок.", reply_markup=back_button("secret_notes"))
            await callback.answer()
            return
        offset = page * 5
        notes = await session.execute(
            select(SecretNote).where(SecretNote.user_id == user.id)
            .order_by(SecretNote.created_at.desc())
            .offset(offset).limit(5)
        )
        notes_list = notes.scalars().all()
        text = "📋 <b>Ваши заметки:</b>\n\n"
        for n in notes_list:
            text += f"📌 <b>{n.title}</b> (ID: {n.id})\n📅 {n.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            text += f"📝 {n.content[:100]}{'...' if len(n.content)>100 else ''}\n"
            text += f"Команды: /viewnote_{n.id} | /editnote_{n.id} | /delnote_{n.id}\n\n"
        kb = InlineKeyboardMarkup(inline_keyboard=[])
        if page > 0:
            kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"note_page_{page-1}")])
        if (page+1)*5 < total:
            kb.inline_keyboard.append([InlineKeyboardButton(text="Вперед ▶️", callback_data=f"note_page_{page+1}")])
        kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="secret_notes")])
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("note_page_"))
async def note_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    await note_list(callback, page)

@router.message(lambda m: m.text and m.text.startswith("/viewnote_"))
async def view_note(message: Message):
    note_id = int(message.text.split("_")[1])
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if not user:
            return
        note = await session.get(SecretNote, note_id)
        if note and note.user_id == user.id:
            await message.answer(f"<b>{note.title}</b>\n\n{note.content}\n\n📅 {note.created_at.strftime('%d.%m.%Y %H:%M')}")
        else:
            await message.answer("Заметка не найдена.")

@router.message(lambda m: m.text and m.text.startswith("/editnote_"))
async def edit_note_start(message: Message, state: FSMContext):
    note_id = int(message.text.split("_")[1])
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if not user:
            return
        note = await session.get(SecretNote, note_id)
        if note and note.user_id == user.id:
            await state.update_data(edit_id=note_id)
            await message.answer(f"Текущий заголовок: {note.title}\nВведите новый заголовок:")
            await state.set_state(NoteForm.edit_title)
        else:
            await message.answer("Заметка не найдена.")

@router.message(NoteForm.edit_title)
async def edit_note_title(message: Message, state: FSMContext):
    await state.update_data(edit_title=message.text)
    await message.answer("Введите новый текст заметки:")
    await state.set_state(NoteForm.edit_content)

@router.message(NoteForm.edit_content)
async def edit_note_content(message: Message, state: FSMContext):
    data = await state.get_data()
    note_id = data['edit_id']
    new_title = data['edit_title']
    new_content = message.text
    async with async_session() as session:
        note = await session.get(SecretNote, note_id)
        if note:
            note.title = new_title
            note.content = new_content
            note.updated_at = datetime.now()
            await session.commit()
            await message.answer("✅ Заметка обновлена!")
        else:
            await message.answer("Ошибка")
    await state.clear()

@router.message(lambda m: m.text and m.text.startswith("/delnote_"))
async def delete_note(message: Message):
    note_id = int(message.text.split("_")[1])
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if not user:
            return
        note = await session.get(SecretNote, note_id)
        if note and note.user_id == user.id:
            await session.delete(note)
            await session.commit()
            await message.answer("🗑 Заметка удалена.")
        else:
            await message.answer("Заметка не найдена.")

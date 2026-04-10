import asyncio
import logging
from datetime import datetime, date
import aiosqlite
import pytz

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db.database import init_db, DB_NAME

API_TOKEN = '8690428738:AAGUuo-V3id99Z-3UsT6twy2bJGmScCXFbA'
MOSCOW_TZ = pytz.timezone("Europe/Moscow")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)

class RegST(StatesGroup):
    name = State()
    gender = State()

class TaskST(StatesGroup):
    t = State()
    dt = State()

class HabST(StatesGroup):
    t = State()
    tm = State()

def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🗓 Планировщик")],
        [KeyboardButton(text="🌸 Комплимент"), KeyboardButton(text="🔄 Привычки")],
        [KeyboardButton(text="🆘 Поддержка"), KeyboardButton(text="🔒 Приватное")]
    ], resize_keyboard=True)

@dp.message(Command("start"))
async def start(m: types.Message, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT is_registered FROM users WHERE user_id = ?", (m.from_user.id,)) as c:
            u = await c.fetchone()
        if not u or u[0] == 0:
            await db.execute("INSERT OR IGNORE INTO users (user_id, username, is_registered) VALUES (?, ?, 0)", (m.from_user.id, m.from_user.username))
            await db.commit()
            await m.answer("✨ Привет! Как мне к тебе обращаться?")
            await state.set_state(RegST.name)
        else:
            await m.answer("Система ЛЮМИ готова.", reply_markup=main_kb())

@dp.message(RegST.name)
async def reg_n(m: types.Message, state: FSMContext):
    await state.update_data(n=m.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Мужской 👨", callback_data="g_m"),
        InlineKeyboardButton(text="Женский 👩", callback_data="g_f")
    ]])
    await m.answer(f"Приятно познакомиться, {m.text}! Укажи свой пол:", reply_markup=kb)
    await state.set_state(RegST.gender)

@dp.callback_query(RegST.gender)
async def reg_g(c: types.CallbackQuery, state: FSMContext):
    g = "m" if c.data == "g_m" else "f"
    data = await state.get_data()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET first_name = ?, gender = ?, is_registered = 1 WHERE user_id = ?", (data['n'], g, c.from_user.id))
        await db.commit()
    await c.answer()
    await c.message.delete()
    await c.message.answer(f"Всё готово, {data['n']}!", reply_markup=main_kb())
    await state.clear()

@dp.message(F.text == "👤 Профиль")
async def profile(m: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT first_name, streak_days, joined_date, gender FROM users WHERE user_id = ?", (m.from_user.id,)) as c:
            r = await c.fetchone()
    if r:
        txt = f"👤 ПРОФИЛЬ: {r[0]}\nПол: {'Мужской' if r[3]=='m' else 'Женский'}\nСерия: {r[1]} дн.\nВ системе с: {r[2][:10]}"
        await m.answer(txt)

@dp.message(F.text == "🔄 Привычки")
async def habits(m: types.Message):
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT habit_id, title, last_completed FROM habits WHERE user_id = ?", (m.from_user.id,)) as c:
            h_list = await c.fetchall()
    kb = []
    for hid, title, l_c in h_list:
        status = "✅" if l_c == today else "🔘"
        kb.append([InlineKeyboardButton(text=f"{status} {title}", callback_data=f"h_done_{hid}"),
                   InlineKeyboardButton(text="🗑", callback_data=f"h_del_{hid}")])
    kb.append([InlineKeyboardButton(text="➕ Добавить", callback_data="h_add")])
    await m.answer("🔄 ПРИВЫЧКИ:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("h_done_"))
async def h_d(c: types.CallbackQuery):
    hid = c.data.split("_")[2]
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE habits SET streak = streak + 1, last_completed = ? WHERE habit_id = ?", (today, hid))
        await db.commit()
    await c.answer("Отлично!")
    await habits(c.message)
    await c.message.delete()

@dp.callback_query(F.data == "h_add")
async def h_a(c: types.CallbackQuery, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM habits WHERE user_id = ?", (c.from_user.id,)) as cur:
            if (await cur.fetchone())[0] >= 5: return await c.answer("Лимит 5!", show_alert=True)
    await c.answer()
    await c.message.answer("Название привычки:")
    await state.set_state(HabST.t)

@dp.message(HabST.t)
async def h_t(m: types.Message, state: FSMContext):
    await state.update_data(t=m.text)
    await m.answer("Время (ЧЧ:ММ):")
    await state.set_state(HabST.tm)

@dp.message(HabST.tm)
async def h_tm(m: types.Message, state: FSMContext):
    try:
        datetime.strptime(m.text, "%H:%M")
        data = await state.get_data()
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO habits (user_id, title, remind_time) VALUES (?, ?, ?)", (m.from_user.id, data['t'], m.text))
            await db.commit()
        await m.answer("✅ Добавлено!")
        await state.clear()
    except: await m.answer("Формат: ЧЧ:ММ")

@dp.message(F.text == "🗓 Планировщик")
async def pl_s(m: types.Message, state: FSMContext):
    await m.answer("Что нужно сделать?")
    await state.set_state(TaskST.t)

@dp.message(TaskST.t)
async def pl_t(m: types.Message, state: FSMContext):
    await state.update_data(t=m.text)
    await m.answer("Время (ДД.ММ ЧЧ:ММ):")
    await state.set_state(TaskST.dt)

@dp.message(TaskST.dt)
async def pl_dt(m: types.Message, state: FSMContext):
    try:
        dt = datetime.strptime(f"{m.text}.{datetime.now().year}", "%d.%m %H:%M.%Y")
        data = await state.get_data()
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO tasks (user_id, title, task_time) VALUES (?, ?, ?)", (m.from_user.id, data['t'], dt.strftime("%Y-%m-%d %H:%M:00")))
            await db.commit()
        await m.answer("✅ Задача создана!")
        await state.clear()
    except: await m.answer("Ошибка формата!")

async def worker():
    now_f = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d %H:%M:00")
    now_t = datetime.now(MOSCOW_TZ).strftime("%H:%M")
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        # Задачи
        async with db.execute("SELECT task_id, user_id, title FROM tasks WHERE task_time <= ? AND is_notified = 0", (now_f,)) as cur:
            for tid, uid, title in await cur.fetchall():
                try:
                    await bot.send_message(uid, f"🔔 НАПОМИНАНИЕ: {title}")
                    await db.execute("UPDATE tasks SET is_notified = 1 WHERE task_id = ?", (tid,))
                except: pass
        # Опрос 19:00
        if now_t == "19:00":
            async with db.execute("SELECT h.habit_id, h.user_id, h.title, u.gender, u.first_name FROM habits h JOIN users u ON h.user_id = u.user_id WHERE h.last_completed != ?", (today,)) as cur:
                for hid, uid, title, gen, name in await cur.fetchall():
                    w = "сделал" if gen == "m" else "сделала"
                    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Да", callback_data=f"h_done_{hid}"), InlineKeyboardButton(text="❌ Нет", callback_data="h_no")]])
                    try: await bot.send_message(uid, f"❓ {name}, ты уже {w} привычку: {title}?", reply_markup=kb)
                    except: pass
        await db.commit()

async def main():
    await init_db()
    scheduler.add_job(worker, "interval", minutes=1)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

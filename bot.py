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

# Глобальная переменная для базы (ускоряет работу в разы)
db_conn = None

class RegST(StatesGroup): name = State(); gender = State()
class TaskST(StatesGroup): t = State(); dt = State()
class HabST(StatesGroup): t = State(); tm = State()

def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🗓 Планировщик")],
        [KeyboardButton(text="🌸 Комплимент"), KeyboardButton(text="🔄 Привычки")],
        [KeyboardButton(text="🆘 Поддержка"), KeyboardButton(text="🔒 Приватное")]
    ], resize_keyboard=True)

# --- ИНИЦИАЛИЗАЦИЯ ---
async def get_db():
    global db_conn
    if db_conn is None:
        db_conn = await aiosqlite.connect(DB_NAME)
    return db_conn

@dp.message(Command("start"))
async def start(m: types.Message, state: FSMContext):
    db = await get_db()
    async with db.execute("SELECT is_registered FROM users WHERE user_id = ?", (m.from_user.id,)) as c:
        u = await c.fetchone()
    if not u or u[0] == 0:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username, is_registered) VALUES (?, ?, 0)", (m.from_user.id, m.from_user.username))
        await db.commit()
        await m.answer("✨ ЛЮМИ приветствует тебя. Как мне к тебе обращаться?")
        await state.set_state(RegST.name)
    else:
        await m.answer("Система готова.", reply_markup=main_kb())

@dp.callback_query(F.data.startswith("g_"))
async def reg_g(c: types.CallbackQuery, state: FSMContext):
    g = c.data.split("_")[1]
    data = await state.get_data()
    db = await get_db()
    await db.execute("UPDATE users SET first_name = ?, gender = ?, is_registered = 1 WHERE user_id = ?", (data['n'], g, c.from_user.id))
    await db.commit()
    await c.answer(); await c.message.delete()
    await c.message.answer(f"Принято, {data['n']}!", reply_markup=main_kb())
    await state.clear()

@dp.message(RegST.name)
async def reg_n(m: types.Message, state: FSMContext):
    await state.update_data(n=m.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Мужской 👨", callback_data="g_m"), InlineKeyboardButton(text="Женский 👩", callback_data="g_f")]])
    await m.answer("Твой пол:", reply_markup=kb)
    await state.set_state(RegST.gender)

# --- ПРОФИЛЬ ---
@dp.message(F.text == "👤 Профиль")
async def profile(m: types.Message):
    db = await get_db()
    async with db.execute("SELECT first_name, streak_days, joined_date, gender FROM users WHERE user_id = ?", (m.from_user.id,)) as c:
        r = await c.fetchone()
    if r:
        await m.answer(f"👤 **ПРОФИЛЬ**\nИмя: {r[0]}\nПол: {'М' if r[3]=='m' else 'Ж'}\nВ системе с: {r[2][:10]}", parse_mode="Markdown")

# --- 🔄 ПРИВЫЧКИ (ЕЖЕДНЕВНЫЕ) ---
@dp.message(F.text == "🔄 Привычки")
async def habits_list(m: types.Message):
    today = date.today().isoformat()
    db = await get_db()
    async with db.execute("SELECT habit_id, title, last_completed FROM habits WHERE user_id = ?", (m.from_user.id,)) as c:
        rows = await c.fetchall()
    
    kb = []
    for hid, title, l_c in rows:
        status = "✅" if l_c == today else "🔘"
        kb.append([InlineKeyboardButton(text=f"{status} {title}", callback_data=f"hck_{hid}"),
                   InlineKeyboardButton(text="🗑", callback_data=f"hdl_{hid}")])
    kb.append([InlineKeyboardButton(text="➕ Добавить привычку", callback_data="h_add")])
    
    await m.answer("🔄 **ЕЖЕДНЕВНЫЕ ПРИВЫЧКИ**\n(Обнуляются в полночь)", 
                   reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("hck_"))
async def h_check(c: types.CallbackQuery):
    hid = c.data.split("_")[1]; today = date.today().isoformat()
    db = await get_db()
    await db.execute("UPDATE habits SET last_completed = ? WHERE habit_id = ?", (today, hid))
    await db.commit()
    await c.answer("Выполнено! 🔥"); await habits_list(c.message); await c.message.delete()

# --- 🗓 ПЛАНИРОВЩИК (ЛЕНТА СОБЫТИЙ) ---
@dp.message(F.text == "🗓 Планировщик")
async def planner_list(m: types.Message):
    db = await get_db()
    # Показываем только будущие задачи
    async with db.execute("SELECT task_id, title, task_time FROM tasks WHERE user_id = ? AND is_notified = 0 ORDER BY task_time ASC", (m.from_user.id,)) as c:
        rows = await c.fetchall()
    
    text = "🗓 **ТВОИ ПЛАНЫ:**\n\n"
    kb = []
    if not rows:
        text += "_Пока планов нет..._"
    else:
        for tid, title, t_time in rows:
            clean_time = datetime.strptime(t_time, "%Y-%m-%d %H:%M:%00").strftime("%d.%m %H:%M")
            text += f"📍 {clean_time} — {title}\n"
            kb.append([InlineKeyboardButton(text=f"🗑 Удалить: {title[:15]}...", callback_data=f"tdl_{tid}")])
    
    kb.append([InlineKeyboardButton(text="➕ Создать план", callback_data="t_add")])
    await m.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("tdl_"))
async def t_del(c: types.CallbackQuery):
    tid = c.data.split("_")[1]
    db = await get_db()
    await db.execute("DELETE FROM tasks WHERE task_id = ?", (tid,))
    await db.commit()
    await c.answer("Удалено"); await planner_list(c.message); await c.message.delete()

# --- ДОБАВЛЕНИЕ (ОБЩЕЕ) ---
@dp.callback_query(F.data == "t_add")
async def t_add(c: types.CallbackQuery, state: FSMContext):
    await c.answer(); await c.message.answer("Что планируем?"); await state.set_state(TaskST.t)

@dp.message(TaskST.t)
async def t_t(m: types.Message, state: FSMContext):
    await state.update_data(t=m.text)
    await m.answer("Когда? (Формат: ДД.ММ ЧЧ:ММ)"); await state.set_state(TaskST.dt)

@dp.message(TaskST.dt)
async def t_dt(m: types.Message, state: FSMContext):
    try:
        dt = datetime.strptime(f"{m.text}.{datetime.now().year}", "%d.%m %H:%M.%Y")
        db = await get_db(); data = await state.get_data()
        await db.execute("INSERT INTO tasks (user_id, title, task_time) VALUES (?, ?, ?)", (m.from_user.id, data['t'], dt.strftime("%Y-%m-%d %H:%M:00")))
        await db.commit()
        await m.answer("✅ План добавлен!", reply_markup=main_kb()); await state.clear()
    except: await m.answer("Ошибка! Пиши так: 12.04 15:00")

@dp.callback_query(F.data == "h_add")
async def h_add(c: types.CallbackQuery, state: FSMContext):
    await c.answer(); await c.message.answer("Название привычки:"); await state.set_state(HabST.t)

@dp.message(HabST.t)
async def h_t(m: types.Message, state: FSMContext):
    await state.update_data(t=m.text); await m.answer("Время напоминания (ЧЧ:ММ):"); await state.set_state(HabST.tm)

@dp.message(HabST.tm)
async def h_tm(m: types.Message, state: FSMContext):
    try:
        datetime.strptime(m.text, "%H:%M")
        db = await get_db(); data = await state.get_data()
        await db.execute("INSERT INTO habits (user_id, title, remind_time) VALUES (?, ?, ?)", (m.from_user.id, data['t'], m.text))
        await db.commit()
        await m.answer("✅ Привычка добавлена!", reply_markup=main_kb()); await state.clear()
    except: await m.answer("Ошибка! Пиши так: 08:00")

@dp.callback_query(F.data.startswith("hdl_"))
async def h_del(c: types.CallbackQuery):
    hid = c.data.split("_")[1]
    db = await get_db()
    await db.execute("DELETE FROM habits WHERE habit_id = ?", (hid,))
    await db.commit()
    await c.answer("Удалено"); await habits_list(c.message); await c.message.delete()

# --- ВОРКЕР ---
async def worker():
    db = await get_db()
    now_f = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d %H:%M:00")
    now_t = datetime.now(MOSCOW_TZ).strftime("%H:%M")
    
    # Уведомления планировщика
    async with db.execute("SELECT task_id, user_id, title FROM tasks WHERE task_time <= ? AND is_notified = 0", (now_f,)) as cur:
        for tid, uid, title in await cur.fetchall():
            try:
                await bot.send_message(uid, f"🔔 **ПОРА СДЕЛАТЬ:**\n{title}", parse_mode="Markdown")
                await db.execute("UPDATE tasks SET is_notified = 1 WHERE task_id = ?", (tid,))
            except: pass
    
    # Напоминания по привычкам (19:00)
    if now_t == "19:00":
        today = date.today().isoformat()
        async with db.execute("SELECT h.user_id, h.title, u.gender, u.first_name FROM habits h JOIN users u ON h.user_id = u.user_id WHERE h.last_completed != ?", (today,)) as cur:
            for uid, title, gen, name in await cur.fetchall():
                w = "сделал" if gen == "m" else "сделала"
                try: await bot.send_message(uid, f"❓ {name}, ты уже {w} сегодня: {title}?")
                except: pass
    await db.commit()

async def main():
    await init_db()
    scheduler.add_job(worker, "interval", minutes=1)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

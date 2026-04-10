async def calculate_streak(session, user_id) -> int:
    from datetime import date, timedelta
    streak = 0
    current = date.today()
    while True:
        habit = await session.scalar(
            select(HabitLog).where(HabitLog.user_id == user_id, HabitLog.date == current, HabitLog.completed == True)
        )
        cycle = await session.scalar(
            select(CycleLog).where(CycleLog.user_id == user_id, CycleLog.date == current)
        )
        event = await session.scalar(
            select(Event).where(Event.user_id == user_id, Event.date == current)
        )
        diary = await session.scalar(
            select(DiaryEntry).where(DiaryEntry.user_id == user_id, DiaryEntry.date == current)
        )
        if habit or cycle or event or diary:
            streak += 1
            current -= timedelta(days=1)
        else:
            break
    return streak

async def calculate_streak(session, user_id) -> int:
    """Возвращает количество дней подряд с активностью (выполненные привычки или записи цикла)"""
    from datetime import date, timedelta
    streak = 0
    current = date.today()
    while True:
        # Проверяем, была ли активность в этот день
        habit_log = await session.scalar(
            select(HabitLog).where(HabitLog.user_id == user_id, HabitLog.date == current, HabitLog.completed == True)
        )
        cycle_log = await session.scalar(
            select(CycleLog).where(CycleLog.user_id == user_id, CycleLog.date == current)
        )
        if habit_log or cycle_log:
            streak += 1
            current -= timedelta(days=1)
        else:
            break
    return streak

from .start import router as start_router
from .profile import router as profile_router
from .settings import router as settings_router
from .compliments import router as compliments_router
from .private import router as private_router
from .planner import router as planner_router
from .cycle import router as cycle_router
from .diary import router as diary_router
from .secret_notes import router as secret_notes_router
from .time_capsule import router as time_capsule_router
from .admin import router as admin_router
from .habits import router as habits_router

def register_all_handlers(dp):
    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(settings_router)
    dp.include_router(compliments_router)
    dp.include_router(private_router)
    dp.include_router(planner_router)
    dp.include_router(cycle_router)
    dp.include_router(diary_router)
    dp.include_router(secret_notes_router)
    dp.include_router(time_capsule_router)
    dp.include_router(admin_router)
    dp.include_router(habits_router)

from .start import router as start_router
from .profile import router as profile_router
from .habits import router as habits_router
from .planner import router as planner_router
from .cycle import router as cycle_router
from .diary import router as diary_router
from .secret import router as secret_router
from .admin import router as admin_router

def register_all_handlers(dp):
    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(habits_router)
    dp.include_router(planner_router)
    dp.include_router(cycle_router)
    dp.include_router(diary_router)
    dp.include_router(secret_router)
    dp.include_router(admin_router)

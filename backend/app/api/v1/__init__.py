from fastapi import APIRouter
from .employee import router as employee_router
from .agent import router as agent_router
from .auth import router as auth_router
from .admin import router as admin_router
from .feedback import router as feedback_router
from .feedback_ws import router as feedback_ws_router
from .analytics import router as analytics_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(employee_router, prefix="/employee", tags=["employee"])
router.include_router(agent_router, prefix="/agent", tags=["agent"])
router.include_router(admin_router, prefix="/admin", tags=["admin"])
router.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
router.include_router(feedback_ws_router, tags=["feedback_ws"])
router.include_router(analytics_router, tags=["analytics"])
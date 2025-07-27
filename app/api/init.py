
from fastapi import APIRouter
from . import auth, vendor, supplier, products, chat, video_call

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(vendor.router, prefix="/vendors", tags=["vendors"])
router.include_router(supplier.router, prefix="/suppliers", tags=["suppliers"])
router.include_router(products.router, prefix="/products", tags=["products"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(video_call.router, prefix="/video-calls", tags=["video-calls"])

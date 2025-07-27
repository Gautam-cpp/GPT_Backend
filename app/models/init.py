# Import models in the correct order to avoid circular dependencies
from .user import Vendor, Supplier
from .product import Product, ProductImage
from .order import Order, OrderItem
from .video_call import VideoCall
from .chat import ChatSession, ChatMessage

# Make sure all models are imported before create_all() is called
__all__ = [
    "Vendor", "Supplier", 
    "Product", "ProductImage",
    "Order", "OrderItem",
    "VideoCall",
    "ChatSession", "ChatMessage"
]

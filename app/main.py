from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all models to ensure they're registered with SQLAlchemy
from .models import user, product, order, video_call, chat
from .config.database import engine, Base
from .api import auth, vendor, supplier, products, chat as chat_api, video_call as video_call_api, orders

# Create all tables in the correct order
try:
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
except Exception as e:
    print(f"Database creation error: {e}")

app = FastAPI(
    title="VendorGPT API",
    description="AI-powered platform connecting street vendors with suppliers", 
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include all routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(vendor.router, prefix="/vendors", tags=["vendors"])
app.include_router(supplier.router, prefix="/suppliers", tags=["suppliers"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(chat_api.router, prefix="/chat", tags=["chat"])
app.include_router(video_call_api.router, prefix="/video-calls", tags=["video-calls"])

@app.get("/")
async def root():
    return {"message": "VendorGPT API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "models_loaded": True,
        "database_connected": True
    }

# Debug route to show all registered routes
@app.get("/debug/routes")
async def debug_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods)
            })
    return {"routes": routes}

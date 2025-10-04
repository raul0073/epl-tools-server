from contextlib import asynccontextmanager
from fastapi import FastAPI
#routes
from routes.admin.admin_route import router as admin_route

from routes.fotmob.table_route import router as table_router
from routes.auth.register import router as user_registration_router
from routes.user.user_actions import router as user_update_router
from routes.fbref.fbref_fixtures import router as fixtures_router
from routes.fbref.fbref_players import router as players_router
from fastapi.middleware.cors import CORSMiddleware as Cors
from core.config import settings
from services.startup.startup_service import StartupService
# startup_service = StartupService()
app = FastAPI(
    title="WhoScored API",
    description="Expose fixtures and missing players (injuries/suspensions) from WhoScored",
    version="1.0.0",
)


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     await startup_service.start()
#     yield
#     await startup_service.stop()
# @app.get("/")
# def root():
#     return {"message": "WhoScored API is live 🚀"}

# include routes

# admin
app.include_router(admin_route, prefix="/api/admin")
# auth
app.include_router(user_registration_router, prefix="/api/auth")

### --- data --- ###
# table
app.include_router(table_router, prefix="/api/fotmob")
# user actions
app.include_router(user_update_router, prefix="/api/user")
# players
app.include_router(players_router, prefix="/api/fbref")
# fixtures
app.include_router(fixtures_router, prefix="/api/fbref")

# cors
# TODO: add DB url. add srver url.
app.add_middleware(
    Cors,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




    
    
# run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
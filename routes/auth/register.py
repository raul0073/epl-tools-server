from fastapi import APIRouter, HTTPException
from models.user.register_models import UserCreate, UserRead
from services.users.auth.register.register_service import UserService

router = APIRouter(tags=["Register"])

# -----------------------------
# Register user route
# -----------------------------
@router.post("/register", response_model=UserRead)
async def register_user(user: UserCreate):
    """
    Create a new user if not exists. 
    If user with same email exists, return existing user.
    """
    try:
        # Check if user exists
        existing_user = await UserService.get_user_by_email(user.email)
        if existing_user:
            return existing_user  

        # Otherwise, create user
        created_user = await UserService.create_user(user)
        return created_user

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



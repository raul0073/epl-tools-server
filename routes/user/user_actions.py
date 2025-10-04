from fastapi import APIRouter, HTTPException, Path
from models.user.register_models import UserRead
from fastapi import Body
from services.users.auth.register.register_service import UserService
from services.users.update.user_service import UserUpdateService

router = APIRouter(tags=["User Actions"])

@router.post("/update/{id}", response_model=UserRead)
async def update_user(user: dict = Body(...), id: str = Path(...)):
    user_id = user.get("id") == id
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user id or not matching")
    print(f"SERVER GOT USER: {user} ")
    try:
        updated = await UserUpdateService.update_user_full(id, user)
        print(f"SERVER UPDATED USER: {updated} ")
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    

@router.get("/get/{id}", response_model=UserRead)
async def get_user_by_id(id: str = Path(..., description="The ID of the user to retrieve")):
    """
    Retrieve a user by ID, including their predictions and points.
    """
    try:
        # Assuming you have a service method to fetch a user by id
        user = await UserService.get_user_by_id(id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all", response_model=list[UserRead])
async def get_all_users():
    """
    Retrieve all users, including their predictions and points.
    """
    try:
        users = await UserService.get_all_users()  
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
from fastapi import APIRouter, Depends
from backend.core.security import require_role

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/profile")
def get_profile(current_user: dict = Depends(require_role("user"))):
    return {"message": f"Welcome User {current_user['id']}. Here is your profile."}

@router.get("/orders")
def get_order_history(current_user: dict = Depends(require_role("user"))):
    return {"message": "Order history retrieved.", "orders": []}
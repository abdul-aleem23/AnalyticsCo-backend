from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_database
from ..models import AdminUser
from ..schemas import UserLogin, Token, UserResponse
from ..utils import verify_password, create_access_token, verify_token, get_password_hash
from ..config import settings

router = APIRouter()
security = HTTPBearer()

@router.post("/admin/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_database)
):
    # Find user by email
    result = await db.execute(
        select(AdminUser).where(AdminUser.email == login_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.jwt_expire_hours * 3600
    }

@router.post("/admin/logout")
async def logout():
    # Since we're using stateless JWT, logout is handled client-side
    return {"message": "Successfully logged out"}

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_database)
) -> AdminUser:
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    result = await db.execute(
        select(AdminUser).where(AdminUser.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

@router.get("/admin/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: AdminUser = Depends(get_current_user)
):
    return current_user

# Utility function to create initial admin user
async def create_initial_admin(db: AsyncSession):
    result = await db.execute(select(AdminUser))
    existing_admin = result.first()
    
    if not existing_admin:
        admin_user = AdminUser(
            email=settings.admin_email,
            password_hash=get_password_hash(settings.admin_password)
        )
        db.add(admin_user)
        await db.commit()
        print(f"Initial admin user created: {settings.admin_email}")
    else:
        print(f"Admin user already exists: {existing_admin[0].email}")

# Temporary endpoint to reset admin password (remove after use)
@router.post("/admin/reset-password-temp")
async def reset_admin_password_temp(
    new_password: str,
    db: AsyncSession = Depends(get_database)
):
    """Temporary endpoint to reset admin password. Remove after use!"""
    result = await db.execute(select(AdminUser))
    admin_user = result.scalar_one_or_none()

    if not admin_user:
        raise HTTPException(status_code=404, detail="No admin user found")

    # Update password
    admin_user.password_hash = get_password_hash(new_password)
    await db.commit()

    return {
        "message": "Admin password updated successfully",
        "email": admin_user.email,
        "note": "Remove this endpoint after use!"
    }
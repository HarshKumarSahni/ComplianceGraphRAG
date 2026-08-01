from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.schemas.response import ApiResponse
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService
from app.dependencies.auth_deps import get_auth_service, get_current_user
from app.db.database import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Creates a new user account with hashed password and returns JWT authentication access token."
)
async def signup(
    req: SignupRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    result = auth_service.register_user(db, req)
    return ApiResponse(
        success=True,
        message="Account created successfully! Welcome to GraphGuard AI.",
        data=result
    )


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates user credentials and returns JWT authentication access token."
)
async def login(
    req: LoginRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    result = auth_service.authenticate_user(db, req)
    return ApiResponse(
        success=True,
        message="Login successful!",
        data=result
    )


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Current Authenticated User Profile",
    description="Returns the profile details of the currently authenticated user."
)
async def get_me(current_user: User = Depends(get_current_user)):
    return ApiResponse(
        success=True,
        message="User profile retrieved successfully",
        data=UserResponse.model_validate(current_user)
    )

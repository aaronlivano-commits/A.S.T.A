"""Auth verification endpoint (Firebase JWT)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import CurrentUser, get_current_user
from ..schemas import AuthVerifyResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/verify", response_model=AuthVerifyResponse)
def verify_token(user: CurrentUser = Depends(get_current_user)) -> AuthVerifyResponse:
    """Verify a Firebase ID token and bootstrap the user profile."""
    return AuthVerifyResponse(
        uid=user.uid,
        email=user.email,
        name=user.name,
        picture=user.picture,
        initialized=True,
    )

from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import Cookie, Depends
from sqlmodel import select

from appserver.db import DbSessionDep
from .exceptions import (
    ExpiredTokenError,
    InvalidTokenError,
    UserNotFoundError,
)
from .models import User
from .utils import ACCESS_TOKEN_EXPIRE_MINUTES, decode_token

async def get_current_user(
    auth_token: Annotated[str, Cookie()],
    db_session: DbSessionDep,
):
    # 쿠키에 토큰이 없으면 인증 실패
    if auth_token is None:
        raise InvalidTokenError()
    
    # 토큰 디코딩 (실패 시 인증 오류로 변환)
    try:
        decoded = decode_token(auth_token)
    except Exception as e:
        raise InvalidTokenError() from e
    
    # 토큰의 만료 여부 확인
    expires_at = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    if now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) < expires_at:
        raise ExpiredTokenError()
    
    # 토큰의 subject(username)으로 사용자 조회
    stmt = select(User).where(User.username == decoded["sub"])
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise UserNotFoundError()
    
    return user

# 의존성 주입용 타입 별칭
CurrentUserDep = Annotated[User, Depends(get_current_user)]


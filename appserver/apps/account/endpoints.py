from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from sqlmodel import select, SQLModel
from appserver.db import DbSessionDep
# .models에서 User 모델을 가져옴 (현재 코드에서 직접 쓰이지 않지만 확장을 위한 존재)
from .models import User
# 데이터베이스 중복 확인을 위한 select, func
from sqlmodel import select, func
# 중복 사용자명 예외
from .exceptions import DuplicatedUsernameError, DuplicatedEmailError
from sqlalchemy.exc import IntegrityError

# /account 경로로 시작하는 API 그룹 생성
router = APIRouter(prefix="/account")

@router.get("/users/{username}")
async def user_detail(username: str, session: DbSessionDep) -> User:
    """
    데이터베이스에서 특정 사용자 정보를 조회합니다.
    
    주의: 현재 dsn이 함수 내부에 있어 매 요청마다 엔진을 생성합니다.
    실제 서비스에서는 글로벌하게 선언된 엔진을 사용하는 것이 성능상 유리합니다.
    """
    # [Tip] 경로 이슈를 방지하려면 절대 경로를 쓰거나 환경 변수를 활용하세요.
    stmt = select(User).where(User.username == username)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is not None:
        return user
    
    # DB에 해당 조건의 유저가 없는 경우
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="User not found"
    )

@router.post("/signup")
async def signup(payload: dict, session: DbSessionDep) -> User:
    # username 중복 체크
    stmt = select(func.count()).select_from(User).where(User.username == payload["username"])
    result = await session.execute(stmt)
    count = result.scalar_one()
    if count > 0:
        raise DuplicatedUsernameError
    
    # email 중복 체크
    stmt = select(func.count()).select_from(User).where(User.email == payload["email"])
    result = await session.execute(stmt)
    count = result.scalar_one()
    if count > 0:
        raise DuplicatedEmailError
    
    # 사용자 입력을 Pydantic 모델 규칙으로 검증하여 안전한 모델로 변환
    user = User.model_validate(payload)
    session.add(user) # 세션에 모델 객체 등록
    
    try:
        await session.commit() # 모든 객체의 변경 사항을 데이터베이스에 반영
    except IntegrityError as e:
        # 혹시 모를 race condition 대비
        if "email" in str(e.orig):
            raise DuplicatedEmailError
        else:
            raise DuplicatedUsernameError
    
    return user
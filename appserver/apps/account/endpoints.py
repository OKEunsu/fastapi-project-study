from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from sqlmodel import select, SQLModel
from appserver.db import create_async_engine, create_session
# .models에서 User 모델을 가져옴 (현재 코드에서 직접 쓰이지 않지만 확장을 위한 존재)
from .models import User

# /account 경로로 시작하는 API 그룹 생성
router = APIRouter(prefix="/account")

@router.get("/users/{username}")
async def user_detail(username: str) -> User:
    """
    데이터베이스에서 특정 사용자 정보를 조회합니다.
    
    주의: 현재 dsn이 함수 내부에 있어 매 요청마다 엔진을 생성합니다.
    실제 서비스에서는 글로벌하게 선언된 엔진을 사용하는 것이 성능상 유리합니다.
    """
    # [Tip] 경로 이슈를 방지하려면 절대 경로를 쓰거나 환경 변수를 활용하세요.
    dsn = "sqlite+aiosqlite:///./test.db" 
    engine = create_async_engine(dsn)
    session_factory = create_session(engine)

    async with session_factory() as session:
        # SQLModel select 구문을 사용하여 유저 조회
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none() # 단일 객체 혹은 None 반환

        if user:
            return user
    
    # DB에 해당 조건의 유저가 없는 경우
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="User not found"
    )
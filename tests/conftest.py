import pytest
from appserver.db import create_async_engine, create_session
# 모델들이 metadata에 등록되도록 반드시 import
from appserver.apps.account import models
from appserver.apps.calendar import models
from sqlmodel import SQLModel
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from appserver.db import create_engine, create_session, use_session
from appserver.app import include_routers

@pytest.fixture(autouse=True)
async def db_session():
    """테스트마다 독립된 트랜잭션을 제공하는 세션 피쳐"""
    dsn = "sqlite+aiosqlite:///./:memory:"
    engine = create_async_engine(dsn)
    
    # 세션 생성
    async with engine.connect() as conn:
        # 비동기 함수 안에서 동기 방식의 함수를 안전하게 실행할 수 있는 역할
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
        
        session_factory = create_session(engine)
        async with session_factory() as session:
            yield session

        await conn.run_sync(SQLModel.metadata.drop_all)
        # commit 이후 발생한 모든 변경 사항을 취소하고 데이터베이스 이전 상태로 되돌리기
        await conn.rollback()
    # 연결 완전히 닫기
    await engine.dispose()

@pytest.fixture()
def fastapi_app(db_sessionq: AsyncSession):
    """
    테스트용 FastAPI 애플리케이션 인스턴스를 생성하는 피처입니다.
    실제 DB 세션 생성 로직을 테스트용 세션으로 교체합니다.
    """
    # 1. 테스트를 위한 독립적인 FastAPI 객체 생성
    app = FastAPI()
    
    # 2. 정의된 모든 API 경로(Router)를 앱에 등록
    include_routers(app)
    
    # 3. 의존성 오버라이드 함수
    # app.dependency_overrides[원래함수] = 교체할함수
    # 이제 API 엔드포인트에서 use_session을 호출하면 override_use_session이 실행됩니다.
    async def override_use_session():
        yield db_session
    
    app.dependency_overrides[use_session] = override_use_session
    return app
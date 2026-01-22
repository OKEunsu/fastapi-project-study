import pytest
import asyncio
from appserver.db import create_async_engine, create_session
# 모델들이 metadata에 등록되도록 반드시 import
from appserver.apps.account import models as account_models
from appserver.apps.calendar import models as calendar_models  # ensure Calendar model is registered
from sqlmodel import SQLModel
from fastapi import FastAPI, status
from appserver.apps.account.schemas import LoginPayload
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from appserver.db import create_engine, create_session, use_session
from appserver.app import include_routers
from fastapi.testclient import TestClient
from appserver.apps.account.utils import hash_password

@pytest.fixture(scope="function")
async def db_engine():
    """테스트용 비동기 엔진을 생성하는 fixture"""
    dsn = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(dsn)
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine: AsyncEngine):
    """테스트마다 독립된 트랜잭션을 제공하는 세션 fixture"""
    session_factory = create_session(db_engine)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture()
def fastapi_app(db_engine: AsyncEngine):
    """
    테스트용 FastAPI 애플리케이션 인스턴스를 생성하는 fixture입니다.
    실제 DB 세션 생성 로직을 테스트용 세션으로 교체합니다.
    """
    # 1. 테스트를 위한 독립적인 FastAPI 객체 생성
    app = FastAPI()
    
    # 2. 정의된 모든 API 경로(Router)를 앱에 등록
    include_routers(app)
    
    # 3. 의존성 오버라이드 함수
    # TestClient는 동기이므로, 비동기 세션을 동기적으로 사용할 수 있도록 해야 함
    async def override_use_session():
        session_factory = create_session(db_engine)
        async with session_factory() as session:
            yield session
    
    app.dependency_overrides[use_session] = override_use_session
    return app


@pytest.fixture()
def client(fastapi_app: FastAPI):
    """
    테스트용 HTTP 클라이언트를 생성하는 fixture입니다.
    생성된 fastapi_app(의존성이 교체된 앱)을 실행하여 요청을 보낼 준비를 합니다.
    """
    # TestClient는 내부적으로 비동기 함수를 동기적으로 실행해줍니다
    with TestClient(fastapi_app) as client:
        yield client

@pytest.fixture()
async def host_user(db_session: AsyncSession):
    """
    테스트용 호스트 사용자 fixture
    """
    user = account_models.User(
        username="puddingcamp",
        hashed_password=hash_password("testtest"),
        password=hash_password("testtest"),
        email="puddingcamp@example.com",
        display_name="푸딩캠프",
        is_host=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.flush(user)
    return user

@pytest.fixture()
def client_with_auth(fastapi_app: FastAPI, host_user: account_models.User):
    """
    host_user로 로그인한 상태의 TestClient를 반환한다. (auth_token 쿠키 포함)
    """
    payload = LoginPayload(
        username=host_user.username,
        password="testtest",
    )
    
    with TestClient(fastapi_app) as client:
        response = client.post("/account/login", json=payload.model_dump())
        assert response.status_code == status.HTTP_200_OK
        
        auth_token = response.cookies.get("auth_token")
        assert auth_token is not None
        
        client.cookies["auth_token"] = auth_token
        yield client
        
@pytest.fixture()
async def guest_user(db_session: AsyncSession):
    user = account_models.User(
        username = "puddingcafe",
        hashed_password=hash_password("testtest"),
        email="puddingcafe@example.com",
        display_name="푸딩카페",
        is_host=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.flush()
    return user

@pytest.fixture()
async def host_user_calendar(db_session: AsyncSession, host_user: account_models.User):
    calendar = calendar_models.Calendar(
        host_id=host_user.id,
        topics=["푸딩캠프", "푸딩캠프2"],
        google_calendar_id="1234567890",
    )
    db_session.add(calendar)
    await db_session.commit()
    await db_session.refresh(host_user)
    await db_session.flush()
    return calendar

from typing import TYPE_CHECKING
from fastapi import HTTPException
from appserver.apps.account.endpoints import user_detail
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from appserver.app import app
from appserver.apps.account.models import User
from appserver.apps.calendar.models import Calendar
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from appserver.db import create_async_engine, create_session


async def test_user_detail_successfully():
    """정상적인 사용자 조회 시 데이터가 정확한지 확인"""
    result = await user_detail("test") # async 함수이므로 await 필수
    assert result["id"] == 1
    assert result["username"] == "test"
    assert result["email"] == "test@example.com"
    assert result["display_name"] == "test"
    assert result["is_host"] is True
    assert result["created_at"] is not None
    assert result["updated_at"] is not None
    
async def test_user_detail_not_found():
    """사용자가 없을 때 HTTPException이 발생하는지 확인"""
    # pytest.raises: 예외가 발생하는지 체크하는 컨텍스트 매니저
    with pytest.raises(HTTPException) as exc_info:
        await user_detail("not_found")
    # 발생한 에러의 상태 코드가 404인지 검증
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

def test_user_detail_by_http_not_found():
    """HTTP 클라이언트를 통해 실제 라우팅과 응답을 확인"""
    client = TestClient(app)
    # 실제 API 경로로 GET 요청 전송
    response = client.get("/account/users/not_found")
    # HTTP 상태 코드 검증
    assert response.status_code == status.HTTP_404_NOT_FOUND

# 2. Integration Test (E2E): 실제 HTTP 요청/응답 과정을 테스트
def test_user_detail_by_http():
    client = TestClient(app)
    
    response = client.get("/account/users/test")
    
    assert response.status_code == status.HTTP_200_OK
    # API 응답은 JSON 형식이므로 .json()으로 파싱하여 검증
    data = response.json()
    assert data["id"] == 1
    assert data["username"] == "test"
    assert data["email"] == "test@example.com"
    assert data["display_name"] == "test"
    assert data["is_host"] is True
    assert data["created_at"] is not None
    assert data["updated_at"] is not None
    
dsn = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(dsn)

async def test_user_detail_for_real_user(db_session):
    user = User(
        username="test",
        password="test",
        email="test@example.com",
        display_name="test",
        is_host=True,
    )
    db_session.add(user)
    await db_session.commit()
    
    client = TestClient(app)
    response = client.get(f"/account/users/{user.username}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "test"
    assert data["email"] == "test@example.com"
    assert data["display_name"] == "test"
    
    response = client.get("/account/users/not_found")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # async with engine.begin() as conn:
    #     await conn.run_sync(SQLModel.metadata.drop_all)
    # # 이걸 안 하면 test.db 파일이 "사용 중" 상태로 남아 삭제가 안 될 수 있음
    # await engine.dispose()
    
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


async def test_user_detail_successfully(db_session: AsyncSession):
    """정상적인 사용자 조회 시 데이터가 정확한지 확인"""
    host_user = User(
        username="test-hostuser",
        password="test",
        email="test.hostuser@example.com",
        display_name="test",
        is_host=True,
    )
    db_session.add(host_user)
    await db_session.commit()
    await db_session.refresh(host_user)  # DB에서 생성된 ID 등을 가져오기
    
    # user_detail 함수 호출
    result = await user_detail(host_user.username, db_session)
    
    # 결과 검증
    assert result.username == "test-hostuser"
    assert result.email == "test.hostuser@example.com"
    assert result.display_name == "test"
    assert result.is_host is True

    
async def test_user_detail_not_found(db_session: AsyncSession):
    """사용자가 없을 때 HTTPException이 발생하는지 확인"""
    # pytest.raises: 예외가 발생하는지 체크하는 컨텍스트 매니저
    with pytest.raises(HTTPException) as exc_info:
        await user_detail("not_found", db_session)
    # 발생한 에러의 상태 코드가 404인지 검증
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


def test_user_detail_by_http_not_found(client: TestClient):
    """HTTP 클라이언트를 통해 실제 라우팅과 응답을 확인"""
    # 실제 API 경로로 GET 요청 전송
    response = client.get("/account/users/not_found")
    # HTTP 상태 코드 검증
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_user_detail_by_http(client: TestClient, db_session: AsyncSession):
    """Integration Test (E2E): 실제 HTTP 요청/응답 과정을 테스트"""
    # 1. 먼저 테스트용 사용자를 DB에 생성
    user = User(
        username="test-http-user",
        password="test",
        email="test-http@example.com",
        display_name="HTTP Test User",
        is_host=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 2. HTTP 클라이언트로 사용자 조회
    response = client.get(f"/account/users/{user.username}")
    
    # 3. 응답 검증
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == user.username
    assert data["email"] == user.email
    assert data["display_name"] == user.display_name
    assert data["is_host"] is True
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


async def test_user_detail_for_real_user(db_session: AsyncSession):
    """실제 DB 세션을 사용하여 사용자 생성 후 조회 테스트"""
    # 1. 사용자 생성
    user = User(
        username="test-real-user",
        password="test",
        email="test-real@example.com",
        display_name="Real Test User",
        is_host=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # 2. user_detail 함수로 조회
    result = await user_detail(user.username, db_session)
    
    # 3. 검증
    assert result.username == user.username
    assert result.email == user.email
    assert result.display_name == user.display_name
    assert result.is_host is True
    
    # 4. 존재하지 않는 사용자 조회 시 404 확인
    with pytest.raises(HTTPException) as exc_info:
        await user_detail("not_found_user", db_session)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

from sqlalchemy.ext.asyncio import AsyncSession
from appserver.apps.account.endpoints import signup
from appserver.apps.account.models import User
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

async def test_모든_입력_항목을_유효한_값으로_입력하면_계정이_생성된다(
    client: TestClient,
    db_session: AsyncSession
    ):
    payload = {
        "username": "test",
        "email": "test@example.com",
        "display_name": "test",
        "password": "test테스트1234",
    }

    result = await signup(payload, db_session)

    assert isinstance(result, User)
    assert result.username == payload["username"]
    assert result.email == payload["email"]
    assert result.display_name == payload["display_name"]
    assert result.is_host is False

@pytest.mark.parametrize(
    "username",
    [
        "puddingcamppuddingcamppuddingcamppuddingcamppuddingcamp",
        12345678,
        "x",
    ]
)

async def test_사용자명이_유효하지_않으면_사용자명이_유효하지_않다는_메세지를_담은_오류를_일으킨다(
    client: TestClient,
    db_session: AsyncSession,
    username: str
):
    payload = {
        "username": username,
        "email": "test@example.com",
        "display_name": "test",
        "password": "test테스트1234",
    }
    
    with pytest.raises(ValidationError) as exc_info:
        await signup(payload, db_session)
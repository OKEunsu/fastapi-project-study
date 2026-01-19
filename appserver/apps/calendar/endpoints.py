from fastapi import APIRouter, status
from sqlmodel import select
from appserver.apps.account.models import User
from appserver.apps.calendar.models import Calendar
from appserver.db import DbSessionDep
from appserver.apps.account.deps import CurrentUserOptionalDep
from .schemas import CalendarDetailOut, CalendarOut

async def host_calendar_detail(
    host_username: str,
    user: CurrentUserOptionalDep,
    session: DbSessionDep
) -> CalendarOut | CalendarDetailOut:
    """
    데이터베이스에서 특정 사용자 정보를 조회합니다.

    Args:
        host_username (str): 조회할 사용자의 username
        user (CurrentUserOptionalDep): 현재 로그인한 사용자 정보
        session (DbSessionDep): 데이터베이스 세션

    Returns:
        CalendarOut | CalendarDetailOut: 조회된 사용자 정보
    """
    stmt = select(User).where(User.username == host_username)
    result = await session.execute(stmt)
    host = result.scalar_one_or_none()

    stmt = select(Calendar).where(Calendar.host_id == host.id)
    result = await session.execute(stmt)
    calendar = result.scalar_one_or_none()
    if user is not None and user.id == host_id:
        return CalendarDetailOut.model_validate(calendar)

    return CalendarOut.model_validate(calendar)
    
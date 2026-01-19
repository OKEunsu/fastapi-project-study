import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from appserver.apps.calendar.models import Calendar
from appserver.apps.calendar.schemas import CalendarDetailOut, CalendarOut
from appserver.apps.calendar.endpoints import host_calendar_detail

async def test_호스트인_사용자의_username_으로_캘린더_정보를_가져온다(
    host_user: User,
    host_user_calendar: Calendar,
    guest_user: User,
    db_session: AsyncSession,
):
    user = None
    expected_type = CalendarOut

    result = await host_calendar_detail(host_user.username, db_session)

    assert isinstance(result, expected_type)
    result_keys = frozenset(result.model_dump().keys())

    expected_keys = frozenset(expected_type.model_fields.keys())
    assert result_keys == expected_keys

    assert result.topics == host_user_calendar.topics
    assert result.description == host_user_calendar.description

    user = guest_user
    expected_type = CalendarOut
    # 반복 되는 코드
    result = await host_calendar_detail(host_user.username, user, db_session)

    assert isinstance(result, expected_type)
    result_keys = frozenset(result.model_dump().keys())

    expected_keys = frozenset(expected_type.model_fields.keys())
    assert result_keys == expected_keys

    assert result.topics == host_user_calendar.topics
    assert result.description == host_user_calendar.description

    # 반복 되는 코드
    result = await host_calendar_detail(host_user.username, user, db_session)

    assert isinstance(result, expected_type)
    result_keys = frozenset(result.model_dump().keys())

    expected_keys = frozenset(expected_type.model_fields.keys())
    assert result_keys == expected_keys

    assert result.topics == host_user_calendar.topics
    assert result.description == host_user_calendar.description
    assert result.google_calendar_id == host_user_calendar.google_calendar_id

@pytest.mark.parametrize("user_key, expected_type", [
    ("host_user", CalendarDetailOut),
    ("guest_user", CalendarOut),
    (None, CalendarOut),
])
async def test_호스트인_사용자의_username으로_캘린더_정보를_가져온다(
    user_key: str | None,
    expected_type: type[CalendarOut | CalendarDetailOut],
    host_user: User,
    host_user_calendar: Calendar,
    guest_user: User,
    db_session: AsyncSession,
):
    users = {
        "host_user": host_user,
        "guest_user": guest_user,
        None: None,
    }
    user = users[user_key]

    result = await host_calendar_detail(host_user.username, user, db_session)

    assert isinstance(result, expected_type)
    result_keys = frozenset(result.model_dump().keys())
    expected_keys = frozenset(expected_type.model_fields.keys())
    assert result_keys == expected_keys

    assert result.topics == host_user_calendar.topics
    assert result.description == host_user_calendar.description
    if expected_type is CalendarDetailOut:
        assert result.google_calendar_id == host_user_calendar.google_calendar_id
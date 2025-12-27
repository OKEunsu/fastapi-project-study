from datetime import date, time, timezone, datetime
from typing import TYPE_CHECKING
from pydantic import AwareDatetime
from sqlalchemy_utc import UtcDateTime
from sqlmodel import SQLModel, Field, Relationship, Text, JSON, func, String, Column
from sqlalchemy.dialects.postgresql import JSONB
if TYPE_CHECKING:
    from appserver.apps.account.models import User
# TYPE_CHECKING은 코드가 실행될 때는 무시하고, 타입 검사(IDE 등) 시에만 사용됨
# User와 Calendar가 서로를 import하며 발생하는 순화 참조 에러 방지

class Calendar(SQLModel, table=True):
    __tablename__ = "calendars"
    
    id: int = Field(default=None, primary_key=True)
    # list[str]: ["FastAPI", "Python", "SQLModel"]
    # DB 저장 시 문자열 '["A", "B"] JSON 형태로 변환하여 들어갑니다.
    topics: list[str] = Field(
        sa_type=JSON().with_variant(JSONB(astext_type=Text()), "postgresql"), 
        default_factory=list, 
        description="게스트와 나눌 주제들")
    # PostgreSQL JSONB 자료형, 특별한 이유 없으면 JSONB 사용 권장
    # JSONB: 바이너리 형식, 공백제거, 키 순서 변경, 빠름, 인덱싱 지원, 쓰기비용 상대적으로 높음
    # 읽기 비용 낮음, 공간 효율성 높음, 중복키: 마지막 키로 대체, 빠른 질의 및 데이터 처리가 필요할 때
    # 기본적으로는 표준 JSON 타입을 쓰되, DB가 PostgresSQL일 경우에만
    # 더 빠르고 검색에 유리한 JSONB 형식을 사용하도록 유연하게 설계함.
    
    description: str = Field(sa_type=Text, description="게스트에게 보여 줄 설명")
    google_calendar_id: str = Field(max_length=1024, description="Google Calandar")
    
    created_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
        },
    )
    updated_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": lambda: datetime.now(timezone.utc),
        },
    )
    
    # 1:1 관계 한 명의 호스트(User)는 하나의 캘린더만 가짐
    host_id: int = Field(foreign_key="users.id", unique=True)
    host: "User" = Relationship(
        back_populates="calendar", # 이 객체는 단 하나의 부모에게만 종속됨을 명시
        sa_relationship_kwargs={"uselist": False, "single_parent": True},
    )
    # 부모가 삭제되거나 관계가 끊기면 자식 객체도 삭제함
    # 유저가 탈퇴하면 그 유저의 개인 캘린더 설정도 함꼐 지워져야 하므로 이 설정을 추가
    
    time_slots: list["TimeSlot"] = Relationship(back_populates="calendar")
    
    
class TimeSlot(SQLModel, table=True):
    __tablename__ = "time_slots"
    
    id: int = Field(default=None, primary_key=True)
    start_time: time # 예약 가능한 시작 시간
    end_time: time # 예약 가능 종료 시간
    # 요일 설정 0(월) ~ 6(일) 숫자를 리스트로 저장하여 다중 요일 선택 기능
    weekdays: list[int] = Field(
        sa_type=JSON().with_variant(JSONB(astext_type=Text()), "postgresql"),
        description="예약 가능한 요일들"
    )
    
    calendar_id: int = Field(foreign_key="calendars.id")
    calendar: Calendar = Relationship(back_populates="time_slots")
    bookings: list["Booking"] = Relationship(back_populates="time_slot")
    created_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
        },
    )
    updated_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": lambda: datetime.now(timezone.utc),
        },
    )

class Booking(SQLModel, table=True):
    __tablename__ = "bookings"
    
    id: int = Field(default=None, primary_key=True)
    when: date
    topic: str
    description: str = Field(sa_type=Text, description="예약 설명")
    
    time_slot_id: int = Field(foreign_key="time_slots.id")
    time_slot: TimeSlot = Relationship(back_populates="bookings")
    
    guest_id: int = Field(foreign_key="users.id")
    guest: "User" = Relationship(back_populates="bookings")
    
    created_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
        },
    )
    updated_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime, 
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": lambda: datetime.now(timezone.utc),
        },
    )
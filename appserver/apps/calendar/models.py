from datetime import timezone, datetime
from typing import TYPE_CHECKING
from pydantic import AwareDatetime
from sqlalchemy_utc import UtcDateTime
from sqlmodel import SQLModel, Field, Relationship, Text, JSON, func
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
    
    host_id: int = Field(foreign_key="users.id", unique=True)
    host: "User" = Relationship(
        back_populates="calendar", # 이 객체는 단 하나의 부모에게만 종속됨을 명시
        sa_relationship_kwargs={"single_parent": True},
    )
    # 부모가 삭제되거나 관계가 끊기면 자식 객체도 삭제함
    # 유저가 탈퇴하면 그 유저의 개인 캘린더 설정도 함꼐 지워져야 하므로 이 설정을 추가
    

from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, func, Column, AutoString
from pydantic import EmailStr, AwareDatetime # 이메일 형식이 유효한지(@ 포함 등) 자동으로 검사해주는 도구
from sqlalchemy import UniqueConstraint # 특정 컬럼의 값이 중복되지 않도록 DB 레벨에서 강제하는 
from sqlalchemy_utc import UtcDateTime
from typing import TYPE_CHECKING, Union
import random
import string
from pydantic import model_validator

if TYPE_CHECKING:
    from appserver.apps.calendar.models import Calendar, Booking

class User(SQLModel, table=True): 
    __tablename__ = "users" # 데이터베이스 테이블의 이름 지정 # table=True 인자를 지정한 경유 유효
    
    # DB 제약 조건 설정: "email" 컬럼에 중복된 값이 들어올 수 없도록 이름(uq_email)을 붙여 설정함
    __table_args__ = (
        UniqueConstraint("email", name="uq_email"),
    )
    
    # ID: 기본키(PK). 처음 객체 생성시 None이지만 DB 저장 시 자동 생성됨
    id: int = Field(default=None, primary_key=True) 
    
    # username: 고유해야 하며, 최대 40자 제한, description은 Swagger 문성에 설명으로 표시됨
    username: str = Field(min_length=4,unique=True, max_length=40, description="사용자 계정 ID")
    
    # email: Pydantic의 EamilStr을 사용해 문자열이 아닌 진짜 이메일 형식인지 검증함
    email: EmailStr = Field(max_length=128, description="사용자 이메일")
    
    # display_name: 서비스에서 보여질 별명, 길이를 제한하여 DB 공간 효율 증대
    display_name: str = Field(min_length=4, max_length=40, description="사용자 표시 이름")
    
    # password: 실제 비밀번호가 저장될 곳, 나중에 해싱(암호화)된 문자열이 저장될 예정
    password: str = Field(min_length=4, max_length=128, description="사용자 비밀번호")
    # is_host: 호스트/게스트 구분용, 기본값 False(게스트)로 설정
    
    is_host: bool = Field(default=False, description="사용자가 호스트인지 여부")
    # 생성/ 수정 시간: 데이터의 이력을 추적하기 위한 필수 필드
    created_at: AwareDatetime = Field(
        default=None, # 파이썬에서 처리하는 default
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(), # 데이터베이스에서 처리하는 server_default
        }, # func는 SQLAlchemy에서 제공하는 객체로, 각 데이터베이스에서 현재 일시 값을 만드는 함수
    )
    updated_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime,
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": lambda: datetime.now(timezone.utc),
            # ORM의 객체 데이터가 갱신될 때 호출될 파이썬 객체를 받음
        },
    )
    
    oauth_accounts: list["OAuthAccount"] = Relationship(back_populates="user")
    # list["OAuthAccount"]: 한 명의 여러 개의 소셜 계정을 가질 수 있는 1:N(일대 다) 관계를 의미
    # 따옴표(" "): OAuthAccount 클래스가 아래의 정의되어 있어, 파이썬이 미리 알 수있게 '문자열'로 타입을 명시 한 것 (Forward Refrence)
    # back_populates: 양방향 연결 설정. OAuthAccount 쪽에서도 .user를 통해 이 사용자를 바로 조회할 수 있게 함.
    
    calendar: Union["Calendar", None] = Relationship(
        back_populates="host",
        sa_relationship_kwargs={"uselist": False, "single_parent": True},
    )
    bookings: list["Booking"] = Relationship(back_populates="guest")

    @model_validator(mode="before") # 데이터 검증 전에 실행, Pydantic 모델 생성 전에 실행
    @classmethod
    def generate_display_name(cls, data: dict):
        if not data.get("display_name"):
            data["display_name"] = "".join(
                random.choices(
                    string.ascii_letters + string.digits,
                    k=8,
                )
            )
        return data

    # @model_validator(mode="after")
    # pydantic이 데이터를 검증하고 모델 객체를 만들기 직전에 이 함수를 실행하라는 뜻
    # mode = "after" 일 때는 입력받은 데이터가 아직 딕셔너리 형태입니다. 데이터 타입을 맞추거나,
    # 빠진 값을 채워넣는 전처리 단계에서 주로 사용
    # 함수가 특정 인스턴스가 아니라 클래스 자체에 속함

class OAuthAccount(SQLModel, table=True):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_account_id",
            name="uq_provider_provider_account_id",
        ), # 쉼표(,) 추가 튜플
    )
    # 한 명의 사용자가 동일한 제공자(예: 카카오)의 동일한 게정으로
    # 중복 가입되는 것을 DB 레벨에서 원천 봉쇄함 (보안 및 데이터 무결성)
    
    id: int = Field(default=None, primary_key=True)
    provider: str = Field(max_length=10, description="OAuth 제공자")
    # google, kakao, github 등 소셜 로그인 서비스 이름을 저장
    provider_account_id: str = Field(max_length=128, description="OAuth 제공자 계정 ID")
    # 외부 서비스에서 우리에게 넘겨주는 해당 사용자의 고유 식별 번호
    user_id: int = Field(foreign_key="users.id")
    # users 테이블의 id 컬럼을 참조하는 외래키
    # 이 계정이 어떤 유저의 소유인지 물리적으로 연결
    
    user: User = Relationship(back_populates="oauth_accounts")
    
    created_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDateTime, # DB 저장 시 타임존 정보를 포함하여 항상 UTC 기준으로 저장되도록 강제.
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
            "onupdate": lambda: datetime.now(timezone.utc), # 데이터가 수정될 떄마다 파이썬이 실행 시점의 UTC 시간을 계산해서 넣어줌.
        },
    )
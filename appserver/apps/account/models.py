from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, func
from pydantic import EmailStr, AwareDatetime # 이메일 형식이 유효한지(@ 포함 등) 자동으로 검사해주는 도구
from sqlalchemy import UniqueConstraint # 특정 컬럼의 값이 중복되지 않도록 DB 레벨에서 강제하는 
from sqlalchemy_utc import UtcDatetime

class User(SQLModel, table=True): 
    __tablename__ = "users" # 데이터베이스 테이블의 이름 지정 # table=True 인자를 지정한 경유 유효
    
    # DB 제약 조건 설정: "email" 컬럼에 중복된 값이 들어올 수 없도록 이름(uq_email)을 붙여 설정함
    __table_args__ = (
        UniqueConstraint("email", name="uq_email"),
    )
    
    # ID: 기본키(PK). 처음 객체 생성시 None이지만 DB 저장 시 자동 생성됨
    id: int = Field(default=None, primary_key=True) 
    
    # username: 고유해야 하며, 최대 40자 제한, description은 Swagger 문성에 설명으로 표시됨
    username: str = Field(unique=True, max_length=40, description="사용자 계정 ID")
    
    # email: Pydantic의 EamilStr을 사용해 문자열이 아닌 진짜 이메일 형식인지 검증함
    email: EmailStr = Field(max_length=128, description="사용자 이메일")
    
    # display_name: 서비스에서 보여질 별명, 길이를 제한하여 DB 공간 효율 증대
    display_name: str = Field(max_length=40, description="사용자 표시 이름")
    
    # password: 실제 비밀번호가 저장될 곳, 나중에 해싱(암호화)된 문자열이 저장될 예정
    password: str = Field(max_length=128, description="사용자 비밀번호")
    # is_host: 호스트/게스트 구분용, 기본값 False(게스트)로 설정
    
    is_host: bool = Field(default=False, description="사용자가 호스트인지 여부")
    # 생성/ 수정 시간: 데이터의 이력을 추적하기 위한 필수 필드
    created_at: AwareDatetime = Field(
        default=None, # 파이썬에서 처리하는 default
        nullable=False,
        sa_type=UtcDatetime,
        sa_column_kwargs={
            "server_default": func.now(), # 데이터베이스에서 처리하는 server_default
        }, # func는 SQLAlchemy에서 제공하는 객체로, 각 데이터베이스에서 현재 일시 값을 만드는 함수
    )
    updated_at: AwareDatetime = Field(
        default=None,
        nullable=False,
        sa_type=UtcDatetime,
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": lambda: datetime.now(timezone.utc),
            # ORM의 객체 데이터가 갱신될 때 호출될 파이썬 객체를 받음
        },
    )
    

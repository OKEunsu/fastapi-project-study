import random
import string
from typing_extensions import Self  # Python 3.10 호환성
from pydantic import model_validator, EmailStr
from sqlmodel import SQLModel, Field

# ============ 회원가입 입력 스키마 ============
# 클라이언트로부터 받는 회원가입 데이터의 형식을 정의
# Field()로 각 필드의 검증 규칙 설정
class SignupPayload(SQLModel):
    username: str = Field(min_length=4, unique=True, max_length=40, description="사용자 계정 ID")
    email: EmailStr = Field(unique=True, max_length=128, description="사용자 이메일")  # EmailStr: 이메일 형식 자동 검증
    display_name: str = Field(min_length=4, max_length=40, description="사용자 표시 이름")
    password: str = Field(min_length=8, max_length=128, description="사용자 비밀번호")
    password_again: str = Field(min_length=8, max_length=128, description="사용자 비밀번호 확인")

    # ========== Validator 1: 비밀번호 일치 검증 ==========
    # mode="after": 모든 필드 검증이 끝난 후 실행 (이미 SignupPayload 객체가 생성된 상태)
    # Self: 자기 자신의 타입(SignupPayload)을 반환한다는 의미
    @model_validator(mode="after")
    def verify_password(self) -> Self:
        if self.password != self.password_again:
            raise ValueError("Passwords do not match")
        return self

    # ========== Validator 2: display_name 자동 생성 ==========
    # mode="before": 필드 검증 전에 실행 (아직 dict 상태)
    # @classmethod: 인스턴스가 아닌 클래스 자체를 받음 (cls = SignupPayload)
    @model_validator(mode="before")
    @classmethod
    def generate_display_name(cls, data: dict) -> dict:
        """display_name이 없으면 랜덤 8자리 문자열 생성."""
        if not data.get("display_name"):
            # string.ascii_letters: 'abcd...xyzABC...XYZ'
            # string.digits: '0123456789'
            # random.choices(pool, k=8): pool에서 8개 랜덤 선택 (중복 허용)
            data["display_name"] = "".join(
                random.choices(
                    string.ascii_letters + string.digits,
                    k=8,
                )
            )
        return data

# ============ 회원가입 응답 스키마 ============
# API 응답 시 클라이언트에게 보여줄 필드만 정의
# password, email 등 민감정보는 제외
class UserOut(SQLModel):
    username: str
    display_name: str
    is_host: bool

class LoginPayload(SQLModel):
    """로그인 API에서 받는 페이로드"""
    username: str = Field(min_length=4, max_length=40)
    password: str = Field(min_length=8, max_length=128)
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from sqlmodel import select, SQLModel
from appserver.db import DbSessionDep
# .models에서 User 모델을 가져옴 (현재 코드에서 직접 쓰이지 않지만 확장을 위한 존재)
from .models import User
# 데이터베이스 중복 확인을 위한 select, func
from sqlmodel import select, func
# 중복 사용자명 예외
from .exceptions import DuplicatedUsernameError, DuplicatedEmailError
from sqlalchemy.exc import IntegrityError
from .schemas import SignupPayload, UserOut

# /account 경로로 시작하는 API 그룹 생성
router = APIRouter(prefix="/account")

@router.get("/users/{username}")
async def user_detail(username: str, session: DbSessionDep) -> User:
    """
    데이터베이스에서 특정 사용자 정보를 조회합니다.
    
    주의: 현재 dsn이 함수 내부에 있어 매 요청마다 엔진을 생성합니다.
    실제 서비스에서는 글로벌하게 선언된 엔진을 사용하는 것이 성능상 유리합니다.
    """
    # [Tip] 경로 이슈를 방지하려면 절대 경로를 쓰거나 환경 변수를 활용하세요.
    stmt = select(User).where(User.username == username)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is not None:
        return user
    
    # DB에 해당 조건의 유저가 없는 경우
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, 
        detail="User not found"
    )

# ============ 회원가입 API ============
# response_model=UserOut: 응답 시 UserOut 스키마로 필터링 (password 등 민감정보 제외)
# status_code=201: 리소스 생성 성공 시 HTTP 201 반환
@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def signup(payload: SignupPayload, session: DbSessionDep) -> User:
    """
    회원가입 엔드포인트.
    
    처리 순서:
    1. 입력 검증 (SignupPayload에서 자동 처리)
    2. username 중복 체크
    3. email 중복 체크
    4. User 모델로 변환 및 DB 저장
    5. UserOut 형태로 응답 (민감정보 제외)
    """
    # ========== 1. username 중복 체크 ==========
    # func.count(): SQL의 COUNT(*) 함수
    # select_from(User): User 테이블에서 조회
    # where(): 조건 필터링 (SQL의 WHERE절)
    stmt = select(func.count()).select_from(User).where(User.username == payload.username)
    result = await session.execute(stmt)  # 비동기로 쿼리 실행
    count = result.scalar_one()  # 단일 값(숫자) 추출
    if count > 0:
        raise DuplicatedUsernameError()  # 커스텀 예외 발생
    
    # ========== 2. email 중복 체크 ==========
    stmt = select(func.count()).select_from(User).where(User.email == payload.email)
    result = await session.execute(stmt)
    count = result.scalar_one()
    if count > 0:
        raise DuplicatedEmailError()
    
    # ========== 3. 데이터 변환 및 저장 ==========
    # payload.model_dump(): SignupPayload 객체 → dict 변환
    # User.model_validate(): dict → User 모델 변환 (검증 포함)
    # from_attributes=True: 객체의 속성에서도 값을 가져올 수 있게 함
    user = User.model_validate(payload.model_dump(), from_attributes=True) 
    session.add(user)  # 세션에 추가 (아직 DB에 저장 안 됨)
    
    try:
        # commit(): 세션의 모든 변경사항을 DB에 실제로 반영
        # 이 시점에 INSERT 쿼리가 실행됨
        await session.commit()
    except IntegrityError as e:
        # Race Condition 대비: 중복 체크와 저장 사이에 다른 요청이 끼어들 수 있음
        # DB의 UNIQUE 제약조건 위반 시 IntegrityError 발생
        if "email" in str(e.orig):
            raise DuplicatedEmailError()
        else:
            raise DuplicatedUsernameError()
    
    # ========== 4. 응답 반환 ==========
    # User 객체를 반환하지만, response_model=UserOut 때문에
    # 실제로는 UserOut 형태로 필터링되어 응답됨 (password 제외)
    return user

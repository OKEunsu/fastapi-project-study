from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlmodel import func, select, update

from appserver.db import DbSessionDep
from .constants import AUTH_TOKEN_COOKIE_NAME
from .deps import CurrentUserDep
from .exceptions import (
    DuplicatedEmailError,
    DuplicatedUsernameError,
    PasswordMismatchError,
    UserNotFoundError,
)
from .models import User
from .schemas import (
    LoginPayload,
    SignupPayload,
    UserDetailOut,
    UserOut,
)
from .utils import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    verify_password,
)
from .schemas import UpdateUserPayload


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

@router.post("/login", status_code=status.HTTP_200_OK)
async def login(payload: LoginPayload, session: DbSessionDep) -> JSONResponse:
    """
    로그인 요청을 수신하고, 자격이 확인되면 토큰과 쿠키를 반환합니다.
    
    1. 사용자 조회
    2. 비밀번호 검증
    3. JWT 액세스 토큰 생성 (신분증 발급)
    4. 쿠키에 토큰 설정 (신분증을 지갑에 넣기)
    """
    # ========== 1. 사용자 조회 ==========
    stmt = select(User).where(User.username == payload.username)
    result = await session.execute(stmt)
    # scalar_one_or_none(): 
    # - 결과가 1개면 해당 객체 반환 
    # - 없으면 None 반환
    # - 2개 이상이면 에러 발생 (Unique 조건이 있어서 2개일 수는 없음)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise UserNotFoundError()
    
    # ========== 2. 비밀번호 검증 ==========
    # 입력한 평문 비밀번호(payload.password)와 DB에 저장된 해시(user.hashed_password) 비교
    # verify_password 내부에서 Argon2/Bcrypt 등을 사용하여 검증함
    is_valid = verify_password(payload.password, user.hashed_password)
    if not is_valid:
        raise PasswordMismatchError()
    
    # ========== 3. 토큰 생성 (신분증 발급) ==========
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # payload(내용물)에는 식별 가능한 최소한의 정보를 담습니다.
    # 비밀번호 같은 민감 정보는 절대 담으면 안 됩니다.
    access_token = create_access_token(
        data={
            "sub": user.username,        # sub (Subject): 토큰의 주인 (보통 ID 사용)
            "displayname": user.display_name,
            "is_host": user.is_host,
        },
        expires_delta=access_token_expires,
    )
    
    # 응답 본문(Body)에 담을 데이터 구성
    response_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.model_dump(mode="json", exclude={"hashed_password", "email"})
    }
    
    # ========== 4. 쿠키 설정 및 응답 (지갑에 넣기) ==========
    # JSONResponse 객체를 직접 생성해야 쿠키(Header)를 조작할 수 있습니다.
    res = JSONResponse(response_data, status_code=status.HTTP_200_OK)
    
    # 현재 시간 (쿠키 만료 계산용)
    now = datetime.now(timezone.utc)
    
    # set_cookie: 브라우저에게 "이 데이터를 쿠키 저장소에 저장해!"라고 명령
    res.set_cookie(
        key=AUTH_TOKEN_COOKIE_NAME,       # 쿠키 이름 (예: "access_token")
        value=access_token,               # 쿠키 값 (JWT 문자열)
        
        # 만료 시간 설정 (이 시간이 지나면 브라우저가 알아서 쿠키를 삭제함)
        expires=now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        
        # [보안 중요] httponly=True: 
        # 자바스크립트(document.cookie)로 이 쿠키에 접근할 수 없게 막음.
        # XSS(교차 사이트 스크립팅) 공격 시 토큰 탈취를 방지하는 핵심 옵션.
        httponly=True,
        
        # [보안 중요] secure=True:
        # HTTPS(암호화된 연결)인 경우에만 쿠키를 서버로 전송함.
        # 네트워크 스니핑(패킷 가로채기)으로부터 토큰을 보호함. (로컬 개발에선 http여도 동작하게 설정 필요할 수 있음)
        secure=True,
        
        # [보안 중요] samesite="strict":
        # 다른 사이트에서 우리 사이트로 요청을 보낼 때 쿠키를 전송하지 않음.
        # CSRF(사이트 간 요청 위조) 공격을 방지함.
        samesite="strict"
    )
    return res

@router.get("/@me", response_model=UserDetailOut)
async def me(user: CurrentUserDep) -> User:
    """
    현재 로그인한 사용자의 정보를 반환합니다.
    
    Args:
        user (CurrentUserDep): 
            FastAPI의 Dependency Injection 시스템이 동작합니다.
            1. 요청의 쿠키에서 토큰을 꺼냅니다.
            2. 토큰을 검증하고 디코딩하여 username을 얻습니다.
            3. DB에서 해당 username을 조회하여 User 객체를 만들어 여기에 주입해줍니다.
            (이 모든 과정은 deps.py의 get_current_user 함수에서 처리됩니다)
    """
    return user

@router.patch("/@me", response_model=UserDetailOut)
async def update_user(
    user: CurrentUserDep,
    payload: UpdateUserPayload,
    session: DbSessionDep
) -> User:
    updated_data = payload.model_dump(exclude_unset=True, exclude={"password", "password_again"})
    stmt = update(User).where(User.username == user.username).values(**updated_data)
    await session.execute(stmt)
    await session.commit()
    return user


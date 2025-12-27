from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)

# 1. Engine 생성: 데이터베이스로 가는 '고속도로'를 건설하는 함수
def create_engine(dsn: str):
    # create_async_engine: 비동기 방식으로 DB에 접속하는 엔진을 만듦
    # dsn: Database Source Name (DB 주소. 예: postgresql+asyncpg://...)
    # echo=True: 실행되는 모든 SQL 쿼리를 터미널에 출력 (디버깅용 필수 설정)
    return create_async_engine(
        dsn,
        echo=True,
    )

# 2. Session Factory 생성: DB와 대화할 일꾼(Session)을 찍어내는 공장
def create_session(async_engine: AsyncEngine | None = None):
    # 만약 엔진이 전달되지 않았다면 새로 생성 (보통은 미리 만든 엔진을 재사용함)
    if async_engine is None:
        async_engine = create_engine()

    # async_sessionmaker: 세션을 관리하기 쉽게 만들어주는 팩토리 클래스
    return async_sessionmaker(
        async_engine,
        expire_on_commit=False, # commit 후에도 객체의 데이터를 메모리에 유지 (비동기 효율성)
        autoflush=False, # 의도하지 않은 시점에 DB에 데이터가 반영되는 것을 방지
        class_=AsyncSession, # 이 팩토리가 찍어낼 일꾼의 타입은 비동기 세션임을 명시
    )

# 3. Dependency Injection용 함수: API 요청이 들어올 때마다 세션을 빌려주는 역할
async def use_session():
    # async with: 작업이 끝나면 자동으로 세션을 닫아줌 (안전한 자원 관리)
    async with async_session_factory() as session:
        yield session # FastAPI의 Depends()를 통해 세션을 API 핸들러로 전달

# --- 실제 실행 및 초기화 ---

DSN = "sqlite+aiosqlite:///./local.db"
# 프로젝트 전역에서 사용할 단 하나의 엔진
engine = create_engine(DSN)

# 프로젝트 전역에서 상용할 세션 공장
async_session_factory = create_session(engine)
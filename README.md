# fastapi-project-study

## 📚 Pytest Fixture 완벽 가이드

### 🤔 Fixture란?

**Fixture**는 테스트를 실행하기 전에 필요한 **준비 작업(setup)**과 테스트 후 **정리 작업(teardown)**을 자동으로 처리해주는 **pytest의 테스트 전용 기능**입니다.

쉽게 말하면:
- 테스트에 필요한 **재료(데이터, 객체, 연결 등)**를 미리 준비해주는 함수
- 테스트가 끝나면 자동으로 **정리**까지 해줌
- 여러 테스트에서 **재사용** 가능

> ⚠️ **중요**: Fixture는 **테스트 코드(`tests/` 디렉토리)에서만** 사용됩니다. 실제 프로덕션 코드(`appserver/`)에서는 사용하지 않습니다!

---

### 🎯 왜 Fixture를 사용하나?

#### ❌ Fixture 없이 테스트 작성하면:

```python
def test_user_creation():
    # 매번 DB 연결 설정
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    
    # 실제 테스트
    user = User(username="test")
    session.add(user)
    session.commit()
    
    # 정리
    session.close()
    engine.dispose()

def test_user_query():
    # 또 똑같이 DB 연결 설정 (중복!)
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    
    # 실제 테스트
    user = session.query(User).first()
    
    # 정리
    session.close()
    engine.dispose()
```

**문제점:**
- 코드 중복이 심함
- 테스트 코드가 길고 복잡함
- 정리 작업을 깜빡하면 리소스 누수 발생

---

#### ✅ Fixture 사용하면:

```python
@pytest.fixture
def db_session():
    # Setup: 준비 작업
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    
    yield session  # 테스트에 session 제공
    
    # Teardown: 정리 작업 (자동 실행)
    session.close()
    engine.dispose()

# 테스트 함수에서 fixture 이름을 파라미터로 받으면 자동 주입!
def test_user_creation(db_session):
    user = User(username="test")
    db_session.add(user)
    db_session.commit()
    # 정리는 자동으로 됨!

def test_user_query(db_session):
    user = db_session.query(User).first()
    # 정리는 자동으로 됨!
```

**장점:**
- 코드 중복 제거
- 테스트 코드가 간결해짐
- 정리 작업 자동화 (리소스 누수 방지)

---

### 🔧 Fixture 기본 사용법

#### 1️⃣ **기본 Fixture 정의**

```python
import pytest

@pytest.fixture
def sample_data():
    """간단한 데이터를 제공하는 fixture"""
    return {"name": "Alice", "age": 30}

def test_sample(sample_data):
    # sample_data fixture가 자동으로 주입됨
    assert sample_data["name"] == "Alice"
    assert sample_data["age"] == 30
```

**작동 방식:**
1. pytest가 `test_sample` 함수를 발견
2. 파라미터 `sample_data`를 확인
3. 같은 이름의 fixture를 찾아서 실행
4. fixture의 반환값을 테스트 함수에 전달

---

#### 2️⃣ **Setup/Teardown이 있는 Fixture**

```python
@pytest.fixture
def temp_file():
    # Setup: 파일 생성
    file_path = "test_temp.txt"
    with open(file_path, "w") as f:
        f.write("test data")
    
    yield file_path  # 테스트에 파일 경로 제공
    
    # Teardown: 파일 삭제 (테스트 후 자동 실행)
    import os
    os.remove(file_path)

def test_file_read(temp_file):
    with open(temp_file, "r") as f:
        content = f.read()
    assert content == "test data"
    # 테스트 끝나면 파일이 자동으로 삭제됨!
```

**`yield` 키워드:**
- `yield` 앞: Setup (테스트 전 실행)
- `yield` 값: 테스트 함수에 전달
- `yield` 뒤: Teardown (테스트 후 실행)

---

#### 3️⃣ **Fixture가 다른 Fixture를 사용**

```python
@pytest.fixture
def database_engine():
    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()

@pytest.fixture
def database_session(database_engine):  # 다른 fixture를 파라미터로!
    session = Session(database_engine)
    yield session
    session.close()

def test_with_session(database_session):
    # database_engine → database_session → test 순서로 실행
    user = User(username="test")
    database_session.add(user)
```

**의존성 체인:**
```
database_engine (먼저 실행)
    ↓
database_session (engine을 받아서 실행)
    ↓
test_with_session (session을 받아서 실행)
```

---

### 🎨 Fixture Scope (범위)

Fixture가 **언제 생성되고 언제 정리되는지** 제어할 수 있습니다.

```python
@pytest.fixture(scope="function")  # 기본값: 각 테스트마다 새로 생성
def function_scope():
    print("Setup")
    yield "data"
    print("Teardown")

@pytest.fixture(scope="module")  # 모듈(파일)당 1번만 생성
def module_scope():
    print("Setup once per module")
    yield "data"
    print("Teardown once per module")

@pytest.fixture(scope="session")  # 전체 테스트 세션당 1번만 생성
def session_scope():
    print("Setup once per session")
    yield "data"
    print("Teardown once per session")
```

| Scope | 생성 시점 | 정리 시점 | 사용 예시 |
|-------|----------|----------|----------|
| `function` | 각 테스트 함수마다 | 각 테스트 종료 후 | DB 세션, 임시 파일 |
| `class` | 각 테스트 클래스마다 | 클래스 테스트 종료 후 | 클래스별 설정 |
| `module` | 각 테스트 파일마다 | 파일 테스트 종료 후 | DB 연결 풀 |
| `session` | 전체 테스트 시작 시 | 모든 테스트 종료 후 | 테스트 서버 |

---

### 🎨 Fixture 고급 옵션

#### 1️⃣ **`autouse=True` - 자동 실행**

모든 테스트에서 **자동으로 실행**되어야 하는 fixture가 있다면 이 옵션을 사용합니다.
파라미터로 명시하지 않아도 자동으로 실행됩니다.

```python
@pytest.fixture(autouse=True)
def setup_log():
    """모든 테스트 전에 자동으로 실행"""
    print("\n[LOG] 테스트를 시작합니다...")
    yield
    print("[LOG] 테스트를 종료합니다...")

def test_something():
    # setup_log를 파라미터로 받지 않아도 자동 실행됨!
    assert True
```

**사용 예시:**
- 로깅 설정
- 환경 변수 초기화
- 테스트 데이터베이스 초기화 (우리 프로젝트의 `db_session`처럼)

```python
# 우리 프로젝트의 실제 예시
@pytest.fixture(autouse=True)  # 모든 테스트에서 자동으로 DB 세션 생성
async def db_session():
    # ...
```

---

#### 2️⃣ **`name` - Fixture 이름 지정**

Fixture 함수 이름이 너무 길거나, 테스트 코드에서 더 직관적인 이름을 쓰고 싶을 때 사용합니다.

```python
@pytest.fixture(name="db")
def a_very_long_database_session_fixture_name():
    """함수명은 길지만, 'db'라는 짧은 이름으로 사용 가능"""
    engine = create_engine("sqlite:///:memory:")
    session = Session(engine)
    yield session
    session.close()

def test_user(db):  # 함수명 대신 'db'라는 이름으로 주입!
    user = User(username="test")
    db.add(user)
    assert db is not None
```

**언제 사용하나:**
- 함수명이 너무 길 때
- 더 직관적인 이름을 사용하고 싶을 때
- 레거시 코드와의 호환성을 위해

---

#### 3️⃣ **비동기 Fixture 주의사항**

FastAPI는 비동기(`async/await`)를 많이 사용하므로, Fixture에서도 비동기를 사용할 때 주의가 필요합니다.

**필수 설정:**

1. **`pytest-asyncio` 설치**
   ```bash
   pip install pytest-asyncio
   ```

2. **`pyproject.toml` 설정**
   ```toml
   [tool.pytest.ini_options]
   asyncio_mode = "auto"  # 비동기 테스트 자동 감지
   ```

3. **비동기 Fixture 작성**
   ```python
   @pytest.fixture
   async def async_client():
       """비동기 fixture는 async def로 정의"""
       async with AsyncClient(app=app, base_url="http://test") as client:
           yield client
   
   async def test_api(async_client):
       """비동기 테스트 함수도 async def로 정의"""
       response = await async_client.get("/users/test")
       assert response.status_code == 200
   ```

**주의사항:**

| 구분 | 동기 Fixture | 비동기 Fixture |
|------|-------------|---------------|
| 정의 | `def fixture()` | `async def fixture()` |
| 사용 | 동기 테스트에서 사용 | 비동기 테스트에서 사용 |
| 의존성 | 동기 fixture만 의존 가능 | 비동기/동기 모두 의존 가능 |

**우리 프로젝트 예시:**
```python
# ✅ 올바른 사용
@pytest.fixture
async def db_session(db_engine):  # 비동기 fixture
    async with session_factory() as session:
        yield session

async def test_user(db_session):  # 비동기 테스트
    user = User(username="test")
    db_session.add(user)
    await db_session.commit()  # await 사용

# ❌ 잘못된 사용
def test_user(db_session):  # 동기 테스트에서 비동기 fixture 사용 불가
    await db_session.commit()  # SyntaxError!
```

**동기/비동기 혼용 시 해결책:**
```python
# 비동기 엔진을 동기 fixture에서 사용하려면
@pytest.fixture
def fastapi_app(db_engine: AsyncEngine):  # 동기 fixture가 비동기 엔진 의존
    app = FastAPI()
    
    # 내부에서 비동기 함수 정의 (클로저)
    async def override_use_session():
        session_factory = create_session(db_engine)
        async with session_factory() as session:
            yield session
    
    app.dependency_overrides[use_session] = override_use_session
    return app
```

---

### 🚀 실제 프로젝트 Fixture 구조

우리 프로젝트의 `tests/conftest.py`:

```python
# 1. 최상위: DB 엔진 (모듈당 1번 생성)
@pytest.fixture(scope="function")
async def db_engine():
    """인메모리 SQLite 엔진 생성"""
    dsn = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(dsn)
    
    # 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine  # 엔진 제공
    
    # 정리: 테이블 삭제, 엔진 종료
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


# 2. DB 세션 (비동기 테스트용)
@pytest.fixture(scope="function")
async def db_session(db_engine):
    """각 테스트마다 독립적인 세션 제공"""
    session_factory = create_session(db_engine)
    async with session_factory() as session:
        yield session
        await session.rollback()  # 테스트 후 롤백


# 3. FastAPI 앱 (HTTP 테스트용)
@pytest.fixture()
def fastapi_app(db_engine):
    """테스트용 FastAPI 앱 생성"""
    app = FastAPI()
    include_routers(app)
    
    # 의존성 오버라이드: 실제 DB 대신 테스트 DB 사용
    async def override_use_session():
        session_factory = create_session(db_engine)
        async with session_factory() as session:
            yield session
    
    app.dependency_overrides[use_session] = override_use_session
    return app


# 4. HTTP 클라이언트
@pytest.fixture()
def client(fastapi_app):
    """테스트용 HTTP 클라이언트"""
    with TestClient(fastapi_app) as client:
        yield client
```

---

### 🔄 실행 흐름 예시

```python
async def test_user_detail_by_http(client: TestClient, db_session: AsyncSession):
    # 1. 테스트 데이터 준비
    user = User(username="test")
    db_session.add(user)
    await db_session.commit()
    
    # 2. HTTP API 호출
    response = client.get(f"/account/users/{user.username}")
    assert response.status_code == 200
```

**실행 순서:**

```
1. db_engine fixture 실행
   ├─ 엔진 생성
   └─ 테이블 생성 (users, calendars 등)

2. db_session fixture 실행
   ├─ db_engine을 받아서 세션 생성
   └─ 테스트에 세션 제공

3. fastapi_app fixture 실행
   ├─ db_engine을 받아서 앱 생성
   └─ 의존성 오버라이드 설정

4. client fixture 실행
   ├─ fastapi_app을 받아서 TestClient 생성
   └─ 테스트에 client 제공

5. 테스트 실행
   ├─ db_session으로 사용자 생성
   └─ client로 API 호출

6. Teardown (역순으로 정리)
   ├─ client 정리
   ├─ fastapi_app 정리
   ├─ db_session 롤백
   └─ db_engine 정리 (테이블 삭제, 엔진 종료)
```

---

### 💡 핵심 개념 정리

1. **Fixture = 테스트 재료 준비 + 자동 정리**
   - `yield` 앞: Setup
   - `yield` 값: 테스트에 전달
   - `yield` 뒤: Teardown

2. **의존성 주입**
   - 테스트 함수 파라미터에 fixture 이름 작성
   - pytest가 자동으로 fixture 실행 후 결과 전달

3. **Fixture 체인**
   - Fixture가 다른 fixture를 사용 가능
   - 의존성 순서대로 자동 실행

4. **Scope로 생명주기 제어**
   - `function`: 매 테스트마다 (기본값)
   - `module`: 파일당 1번
   - `session`: 전체 테스트당 1번

5. **`conftest.py`**
   - 여러 테스트 파일에서 공유할 fixture 정의
   - pytest가 자동으로 인식

---

### 🎓 학습 팁

1. **간단한 fixture부터 시작**
   ```python
   @pytest.fixture
   def simple_data():
       return [1, 2, 3]
   ```

2. **print로 실행 순서 확인**
   ```python
   @pytest.fixture
   def my_fixture():
       print("Setup!")
       yield "data"
       print("Teardown!")
   ```

3. **실제 사용 사례 연습**
   - 파일 생성/삭제
   - DB 연결/종료
   - API 서버 시작/종료

4. **공식 문서 참고**
   - https://docs.pytest.org/en/stable/fixture.html

---

## 🔀 Fixture vs 프로덕션 코드

### ⚡ 핵심 차이점

| 구분 | 테스트 코드 | 프로덕션 코드 |
|------|------------|--------------|
| **사용 기술** | Pytest Fixture | FastAPI Dependency Injection |
| **사용 위치** | `tests/` 디렉토리 | `appserver/` 디렉토리 |
| **목적** | 테스트 환경 준비 | 실제 서비스 로직 |
| **DB** | 인메모리 SQLite | 실제 DB (PostgreSQL 등) |
| **생명주기** | 테스트마다 생성/삭제 | 앱 실행 중 유지 |

---

### 📝 비교 예시

#### 1️⃣ **테스트 코드에서 DB 세션 사용** (Pytest Fixture)

```python
# tests/conftest.py
@pytest.fixture
async def db_session(db_engine):
    """테스트용 DB 세션 - 인메모리 SQLite 사용"""
    session_factory = create_session(db_engine)
    async with session_factory() as session:
        yield session
        await session.rollback()  # 테스트 후 롤백

# tests/test_user.py
async def test_create_user(db_session: AsyncSession):
    """Fixture로 세션 주입받음"""
    user = User(username="test")
    db_session.add(user)
    await db_session.commit()
```

---

#### 2️⃣ **프로덕션 코드에서 DB 세션 사용** (FastAPI Dependency)

```python
# appserver/db.py
async def use_session():
    """실제 서비스용 DB 세션 - 실제 DB 사용"""
    async with session_factory() as session:
        yield session

# appserver/apps/account/endpoints.py
@router.get("/users/{username}")
async def user_detail(
    username: str,
    session: AsyncSession = Depends(use_session)  # FastAPI 의존성 주입
):
    """FastAPI Depends로 세션 주입받음"""
    user = await session.get(User, username)
    if not user:
        raise HTTPException(status_code=404)
    return user
```

---

### 🎯 왜 테스트에서는 Fixture를 사용하나?

1. **격리된 환경**
   - 실제 DB를 건드리지 않음
   - 인메모리 DB로 빠른 테스트
   - 테스트마다 깨끗한 상태

2. **의존성 오버라이드**
   ```python
   # 프로덕션: 실제 DB 사용
   app.dependency_overrides[use_session] = 실제_세션
   
   # 테스트: 테스트 DB 사용
   app.dependency_overrides[use_session] = 테스트_세션
   ```

3. **자동 정리**
   - 테스트 후 자동으로 데이터 삭제
   - 리소스 누수 방지

---

### 📂 디렉토리 구조로 이해하기

```
fastapi-project-study/
├── appserver/              # 프로덕션 코드
│   ├── db.py              # use_session (FastAPI Depends)
│   └── apps/
│       └── account/
│           └── endpoints.py  # Depends(use_session) 사용
│
└── tests/                 # 테스트 코드
    ├── conftest.py        # db_session (Pytest Fixture)
    └── apps/
        └── account/
            └── test_endpoints.py  # db_session fixture 사용
```

---

### 💡 정리

- **Pytest Fixture** = 테스트 전용 도구
  - `tests/` 디렉토리에서만 사용
  - `@pytest.fixture` 데코레이터
  - 테스트 환경 준비 및 정리

- **FastAPI Dependency** = 프로덕션 코드의 의존성 주입
  - `appserver/` 디렉토리에서 사용
  - `Depends()` 함수
  - 실제 서비스 로직

**둘 다 "의존성 주입" 개념을 사용하지만, 목적과 사용 위치가 다릅니다!** 🎯
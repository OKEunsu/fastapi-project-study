import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlmodel import SQLModel
from sqlalchemy.engine import Connection

# -------------------------------------------------------------------
# 1. 모델 및 설정 로드 (Alembic이 "무엇을" "어디에" 적용할지 정의)
# -------------------------------------------------------------------

# 설계도(Model) 로드: Alembic이 테이블 구조를 파악할 수 있게 메모리에 올림
from appserver.apps.account import models  # noqa
from appserver.apps.calendar import models  # noqa
# 연결 주소: 프로젝트 설정 파일에서 실제 DB 주소(DSN)를 가져옴
from appserver.db import DSN
# Alembic 설정 객체: alembic.ini 파일의 내용에 접근할 수 있게 해줌
from alembic import context

config = context.config

# 로깅 설정: alembic.ini의 설정을 바탕으로 로그를 출력합니다 (콘솔에 찍히는 내용들).
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata: Alembic이 추적할 "기준" 설계도입니다.
target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    """오프라인 모드: 실제 DB 연결 없이 SQL 스크립트 파일만 생성할 때 생성"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url or DSN, # ini 파일에 주소가 없으면 우리 프로젝트의 DSN 사용
        target_metadata=target_metadata,
        literal_binds=True, # SQL을 텍스트 형태로 출력
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """온라인 모드: 실제 DB에 접속하여 테이블을 생성하거나 수정할 때 실행 (비동기 방식)"""
    configuration = config.get_section(config.config_ini_section, {})

    # 실제 DB 주소 주입: ini 설정보다 코드상의 DSN을 우선시함
    configuration["sqlalchemy.url"] = DSN

    # 비동기 엔진 생성: SQLAlchemy 설정을 바탕으로 DB 통로를 개설
    connectable = AsyncEngine(
        engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool, # 마이그레이션 시에는 커넥션 풀을 사용하지 않음
        ),
    )
    # 실제 DB 접속 후 'do_run_migrations' 함수를 동기적으로 실행(run_sync)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    # 작업 완료 후 엔진 자원 해제
    await connectable.dispose()

# --- 실행부 ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    # 비동기 함수인 run_migrations_online을 이벤트 루프에서 실행
    asyncio.run(run_migrations_online())
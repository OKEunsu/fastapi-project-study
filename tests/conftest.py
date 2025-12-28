import pytest
from appserver.db import create_async_engine, create_session
from appserver.apps.account import models
from appserver.apps.calendar import models
from sqlmodel import SQLModel

@pytest.fixture()
async def db_session():
    dsn = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(dsn)
    
    async with engine.connect() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
        
        session_factory = create_session(engine)
        async with session_factory() as session:
            yield session

        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.rollback()
    await engine.dispose()


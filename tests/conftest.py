import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base, SessionLocal


@pytest.fixture
def in_memory_session(monkeypatch):
    """テスト用インメモリSQLiteセッション。テストごとに独立したDBを使う。"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    monkeypatch.setattr("db.models.SessionLocal", TestSession)
    monkeypatch.setattr("db.repository.SessionLocal", TestSession)

    yield TestSession

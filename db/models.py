import json
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "sqlite:///api_explorer.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    method = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    request_headers = Column(Text, default="{}")
    request_params = Column(Text, default="{}")
    request_body = Column(Text, default="{}")
    response_status = Column(Integer)
    response_headers = Column(Text, default="{}")
    response_body = Column(Text, default="{}")
    timestamp = Column(DateTime, default=datetime.utcnow)

    def request_headers_dict(self) -> dict:
        return json.loads(self.request_headers or "{}")

    def request_params_dict(self) -> dict:
        return json.loads(self.request_params or "{}")

    def request_body_dict(self) -> dict:
        return json.loads(self.request_body or "{}")

    def response_headers_dict(self) -> dict:
        return json.loads(self.response_headers or "{}")

    def response_body_dict(self) -> dict:
        return json.loads(self.response_body or "{}")


def init_db():
    Base.metadata.create_all(bind=engine)

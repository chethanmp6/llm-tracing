from sqlalchemy import Column, String, Text, DateTime, Float, Integer
from sqlalchemy.dialects.postgresql import JSONB
from database import Base

class LiteLLMSpendLogs(Base):
    __tablename__ = "LiteLLM_SpendLogs"

    request_id = Column(String, primary_key=True)
    call_type = Column(String)
    model = Column(String)
    user = Column(String)
    team = Column(String)
    startTime = Column(DateTime)
    endTime = Column(DateTime)
    total_tokens = Column(Integer)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    request_tags = Column(JSONB)
    end_user = Column(String)
    api_key = Column(String)
    spend = Column(Float)
    metadata = Column(JSONB)

class LiteLLMRequestTable(Base):
    __tablename__ = "LiteLLM_RequestTable"

    request_id = Column(String, primary_key=True)
    call_type = Column(String)
    model = Column(String)
    user = Column(String)
    team = Column(String)
    startTime = Column(DateTime)
    endTime = Column(DateTime)
    total_tokens = Column(Integer)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    request_tags = Column(JSONB)
    end_user = Column(String)
    api_key = Column(String)
    spend = Column(Float)
    metadata = Column(JSONB)
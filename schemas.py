from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Literal

class AnalyticsRequest(BaseModel):
    agent_name: str = Field(..., description="Name of the agent to analyze")
    agent_version: str = Field(..., description="Version of the agent to analyze")
    days: Literal[1, 2, 7, 15, 20] = Field(..., description="Number of days to look back")

    @validator('days')
    def validate_days(cls, v):
        if v not in [1, 2, 7, 15, 20]:
            raise ValueError('days must be one of: 1, 2, 7, 15, 20')
        return v

class DateRange(BaseModel):
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")

class Metrics(BaseModel):
    total_sessions: int = Field(..., description="Count of unique agent_session_id values")
    total_messages: int = Field(..., description="Count of all messages/requests")
    avg_daily_messages: float = Field(..., description="Average messages per day in the date range")
    total_users: int = Field(..., description="Count of unique agent_user_id values")

class AnalyticsResponse(BaseModel):
    agent_name: str
    agent_version: str
    metrics: Metrics
    date_range: DateRange

class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime

class ErrorResponse(BaseModel):
    detail: str
    error_code: str

class DailySessionActivity(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    sessions: int = Field(..., description="Number of sessions on this date")

class ActivityTimelineResponse(BaseModel):
    agent_name: str
    agent_version: str
    date_range: DateRange
    daily_sessions: list[DailySessionActivity]

class DailyTokenUsage(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    prompt_tokens: int = Field(..., description="Number of prompt tokens used on this date")
    completion_tokens: int = Field(..., description="Number of completion tokens used on this date")

class TokensUsageResponse(BaseModel):
    agent_name: str
    agent_version: str
    date_range: DateRange
    daily_tokens: list[DailyTokenUsage]

class TotalTokensResponse(BaseModel):
    agent_name: str
    agent_version: str
    date_range: DateRange
    total_prompt_tokens: int = Field(..., description="Total prompt tokens consumed in the date range")
    total_completion_tokens: int = Field(..., description="Total completion tokens consumed in the date range")

class DetailedUsageLog(BaseModel):
    timestamp: datetime = Field(..., description="Request timestamp")
    agent_name: str = Field(..., description="Name of the agent")
    total_tokens: int = Field(..., description="Total tokens for this request")
    prompt_tokens: int = Field(..., description="Prompt tokens for this request")
    completion_tokens: int = Field(..., description="Completion tokens for this request")
    duration_seconds: float = Field(..., description="Request duration in seconds")

class DetailedUsageResponse(BaseModel):
    agent_name: str
    agent_version: str
    date_range: DateRange
    usage_logs: list[DetailedUsageLog]

class RecentMessage(BaseModel):
    timestamp: datetime = Field(..., description="Message timestamp")
    session_id: str = Field(..., description="Agent session ID")
    message_length: int = Field(..., description="Length of the message content")
    agent_name: str = Field(..., description="Name of the agent")
    model_name: str = Field(..., description="Name of the model used")
    message: str = Field(..., description="Message content")

class RecentMessagesResponse(BaseModel):
    agent_name: str
    agent_version: str
    date_range: DateRange
    messages: list[RecentMessage]
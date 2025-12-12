from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging
import os

from database import get_database, close_database
from schemas import AnalyticsResponse, HealthResponse, ErrorResponse, Metrics, DateRange, ActivityTimelineResponse, DailySessionActivity, TokensUsageResponse, DailyTokenUsage, TotalTokensResponse, DetailedUsageResponse, DetailedUsageLog, RecentMessagesResponse, RecentMessage, UpdateMessagesRequest, UpdateMessagesResponse
from crud import get_agent_analytics, check_database_connection, get_agent_activity_timeline, get_agent_tokens_usage, get_agent_total_tokens, get_agent_detailed_usage, get_recent_messages, update_messages_column

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LiteLLM Analytics API",
    description="FastAPI service for analyzing LiteLLM proxy analytics data stored in PostgreSQL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Starting LiteLLM Analytics API")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Shutting down LiteLLM Analytics API")
    await close_database()

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            error_code=f"HTTP_{exc.status_code}"
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unexpected errors."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="Internal server error",
            error_code="INTERNAL_ERROR"
        ).dict()
    )

@app.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_database)):
    """
    Health check endpoint to verify API and database connectivity.

    Returns:
        HealthResponse: Status and timestamp
    """
    try:
        db_connected = await check_database_connection(db)
        if not db_connected:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed"
            )

        return HealthResponse(
            status="healthy",
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service unavailable"
        )


@app.get("/analytics/agent", response_model=AnalyticsResponse)
async def get_analytics(
    agent_name: str = Query(..., description="Filter by agent name"),
    agent_version: str = Query(..., description="Filter by agent version"),
    days: int = Query(..., description="Number of days to look back (1, 2, 7, 15, 20)"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get analytics metrics for a specific agent and version within a date range.

    Args:
        agent_name: Name of the agent to analyze
        agent_version: Version of the agent to analyze
        days: Number of days to look back (must be one of: 1, 2, 7, 15, 20)

    Returns:
        AnalyticsResponse: Agent analytics including sessions, messages, users, and date range

    Raises:
        HTTPException: 422 for invalid parameters, 404 if no data found, 500 for server errors
    """
    
    try:
        logger.info(f"Fetching analytics for agent: {agent_name}, version: {agent_version}, days: {days}")

        # Get analytics data from database
        analytics_data = await get_agent_analytics(
            db=db,
            agent_name=agent_name,
            agent_version=agent_version,
            days=days
        )

        if analytics_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for agent '{agent_name}' version '{agent_version}' in the last {days} days"
            )

        # Create response
        metrics = Metrics(
            total_sessions=analytics_data['total_sessions'],
            total_messages=analytics_data['total_messages'],
            avg_daily_messages=analytics_data['avg_daily_messages'],
            total_users=analytics_data['total_users']
        )

        date_range = DateRange(
            start_date=analytics_data['start_date'].strftime('%Y-%m-%d'),
            end_date=analytics_data['end_date'].strftime('%Y-%m-%d')
        )

        response = AnalyticsResponse(
            agent_name=agent_name,
            agent_version=agent_version,
            metrics=metrics,
            date_range=date_range
        )

        logger.info(f"Successfully fetched analytics for {agent_name} v{agent_version}")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch analytics data"
        )

@app.get("/activitytimeline", response_model=ActivityTimelineResponse)
async def get_activity_timeline(
    agent_name: str = Query(..., description="Filter by agent name"),
    agent_version: str = Query(..., description="Filter by agent version"),
    days: int = Query(..., description="Number of days to look back"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get daily session activity timeline for a specific agent and version within a date range.

    Args:
        agent_name: Name of the agent to analyze
        agent_version: Version of the agent to analyze
        days: Number of days to look back (must be one of: 1, 2, 7, 15, 20)

    Returns:
        ActivityTimelineResponse: Daily session counts with date range

    Raises:
        HTTPException: 422 for invalid parameters, 404 if no data found, 500 for server errors
    """

    try:
        logger.info(f"Fetching activity timeline for agent: {agent_name}, version: {agent_version}, days: {days}")

        # Get activity timeline data from database
        timeline_data = await get_agent_activity_timeline(
            db=db,
            agent_name=agent_name,
            agent_version=agent_version,
            days=days
        )

        if timeline_data is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate activity timeline"
            )

        # Create response
        daily_sessions = [
            DailySessionActivity(
                date=session['date'],
                sessions=session['sessions']
            )
            for session in timeline_data['daily_sessions']
        ]

        date_range = DateRange(
            start_date=timeline_data['start_date'].strftime('%Y-%m-%d'),
            end_date=timeline_data['end_date'].strftime('%Y-%m-%d')
        )

        response = ActivityTimelineResponse(
            agent_name=agent_name,
            agent_version=agent_version,
            date_range=date_range,
            daily_sessions=daily_sessions
        )

        logger.info(f"Successfully fetched activity timeline for {agent_name} v{agent_version}")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error fetching activity timeline: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch activity timeline data"
        )

@app.get("/tokens-usage", response_model=TokensUsageResponse)
async def get_tokens_usage(
    agent_name: str = Query(..., description="Filter by agent name"),
    agent_version: str = Query(..., description="Filter by agent version"),
    days: int = Query(..., description="Number of days to look back (1, 2, 7, 15, 20)"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get daily token usage (prompt and completion tokens) for a specific agent and version within a date range.

    Args:
        agent_name: Name of the agent to analyze
        agent_version: Version of the agent to analyze
        days: Number of days to look back (must be one of: 1, 2, 7, 15, 20)

    Returns:
        TokensUsageResponse: Daily token usage counts with date range

    Raises:
        HTTPException: 422 for invalid parameters, 500 for server errors
    """

    try:
        logger.info(f"Fetching tokens usage for agent: {agent_name}, version: {agent_version}, days: {days}")

        # Get tokens usage data from database
        tokens_data = await get_agent_tokens_usage(
            db=db,
            agent_name=agent_name,
            agent_version=agent_version,
            days=days
        )

        if tokens_data is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate tokens usage data"
            )

        # Create response
        daily_tokens = [
            DailyTokenUsage(
                date=token['date'],
                prompt_tokens=token['prompt_tokens'],
                completion_tokens=token['completion_tokens']
            )
            for token in tokens_data['daily_tokens']
        ]

        date_range = DateRange(
            start_date=tokens_data['start_date'].strftime('%Y-%m-%d'),
            end_date=tokens_data['end_date'].strftime('%Y-%m-%d')
        )

        response = TokensUsageResponse(
            agent_name=agent_name,
            agent_version=agent_version,
            date_range=date_range,
            daily_tokens=daily_tokens
        )

        logger.info(f"Successfully fetched tokens usage for {agent_name} v{agent_version}")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error fetching tokens usage: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch tokens usage data"
        )

@app.get("/total-tokens", response_model=TotalTokensResponse)
async def get_total_tokens(
    agent_name: str = Query(..., description="Filter by agent name"),
    agent_version: str = Query(..., description="Filter by agent version"),
    days: int = Query(..., description="Number of days to look back (1, 2, 7, 15, 20)"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get total token consumption (prompt and completion tokens) for a specific agent and version within a date range.

    Args:
        agent_name: Name of the agent to analyze
        agent_version: Version of the agent to analyze
        days: Number of days to look back (must be one of: 1, 2, 7, 15, 20)

    Returns:
        TotalTokensResponse: Total token consumption with date range

    Raises:
        HTTPException: 422 for invalid parameters, 500 for server errors
    """

    try:
        logger.info(f"Fetching total tokens for agent: {agent_name}, version: {agent_version}, days: {days}")

        # Get total tokens data from database
        total_data = await get_agent_total_tokens(
            db=db,
            agent_name=agent_name,
            agent_version=agent_version,
            days=days
        )

        if total_data is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate total tokens data"
            )

        # Create response
        date_range = DateRange(
            start_date=total_data['start_date'].strftime('%Y-%m-%d'),
            end_date=total_data['end_date'].strftime('%Y-%m-%d')
        )

        response = TotalTokensResponse(
            agent_name=agent_name,
            agent_version=agent_version,
            date_range=date_range,
            total_prompt_tokens=total_data['total_prompt_tokens'],
            total_completion_tokens=total_data['total_completion_tokens']
        )

        logger.info(f"Successfully fetched total tokens for {agent_name} v{agent_version}: prompt={total_data['total_prompt_tokens']}, completion={total_data['total_completion_tokens']}")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error fetching total tokens: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch total tokens data"
        )

@app.get("/detailed-usage", response_model=DetailedUsageResponse)
async def get_detailed_usage(
    agent_name: str = Query(..., description="Filter by agent name"),
    agent_version: str = Query(..., description="Filter by agent version"),
    days: int = Query(..., description="Number of days to look back (1, 2, 7, 15, 20)"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get detailed usage logs for a specific agent and version within a date range.

    Args:
        agent_name: Name of the agent to analyze
        agent_version: Version of the agent to analyze
        days: Number of days to look back (must be one of: 1, 2, 7, 15, 20)

    Returns:
        DetailedUsageResponse: Individual request logs with timestamps, token counts, and durations

    Raises:
        HTTPException: 422 for invalid parameters, 500 for server errors
    """

    # Validate days parameter
    if days not in [1, 2, 7, 15, 20]:
        raise HTTPException(
            status_code=422,
            detail="days parameter must be one of: 1, 2, 7, 15, 20"
        )

    try:
        logger.info(f"Fetching detailed usage for agent: {agent_name}, version: {agent_version}, days: {days}")

        # Get detailed usage data from database
        detailed_data = await get_agent_detailed_usage(
            db=db,
            agent_name=agent_name,
            agent_version=agent_version,
            days=days
        )

        if detailed_data is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate detailed usage data"
            )

        # Create response
        usage_logs = [
            DetailedUsageLog(
                timestamp=log['timestamp'],
                agent_name=log['agent_name'],
                total_tokens=log['total_tokens'],
                prompt_tokens=log['prompt_tokens'],
                completion_tokens=log['completion_tokens'],
                duration_seconds=log['duration_seconds']
            )
            for log in detailed_data['usage_logs']
        ]

        date_range = DateRange(
            start_date=detailed_data['start_date'].strftime('%Y-%m-%d'),
            end_date=detailed_data['end_date'].strftime('%Y-%m-%d')
        )

        response = DetailedUsageResponse(
            agent_name=agent_name,
            agent_version=agent_version,
            date_range=date_range,
            usage_logs=usage_logs
        )

        logger.info(f"Successfully fetched detailed usage for {agent_name} v{agent_version}: {len(usage_logs)} logs")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error fetching detailed usage: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch detailed usage data"
        )

@app.get("/recentmessages", response_model=RecentMessagesResponse)
async def get_recent_messages_endpoint(
    agent_name: str = Query(..., description="Filter by agent name"),
    agent_version: str = Query(..., description="Filter by agent version"),
    days: int = Query(..., description="Number of days to look back (1, 2, 7, 15, 20)"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get recent messages for a specific agent and version within a date range.

    Args:
        agent_name: Name of the agent to analyze
        agent_version: Version of the agent to analyze
        days: Number of days to look back (must be one of: 1, 2, 7, 15, 20)

    Returns:
        RecentMessagesResponse: Individual message logs with timestamps, content, and metadata

    Raises:
        HTTPException: 422 for invalid parameters, 500 for server errors
    """

    # Validate days parameter
    if days not in [1, 2, 7, 15, 20]:
        raise HTTPException(
            status_code=422,
            detail="days parameter must be one of: 1, 2, 7, 15, 20"
        )

    try:
        logger.info(f"Fetching recent messages for agent: {agent_name}, version: {agent_version}, days: {days}")

        # Get recent messages data from database
        messages_data = await get_recent_messages(
            db=db,
            agent_name=agent_name,
            agent_version=agent_version,
            days=days
        )

        if messages_data is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate recent messages data"
            )

        # Create response
        messages = [
            RecentMessage(
                timestamp=msg['timestamp'],
                session_id=msg['session_id'],
                message_length=msg['message_length'],
                agent_name=msg['agent_name'],
                model_name=msg['model_name'],
                message=msg['message']
            )
            for msg in messages_data['messages']
        ]

        date_range = DateRange(
            start_date=messages_data['start_date'].strftime('%Y-%m-%d'),
            end_date=messages_data['end_date'].strftime('%Y-%m-%d')
        )

        response = RecentMessagesResponse(
            agent_name=agent_name,
            agent_version=agent_version,
            date_range=date_range,
            messages=messages
        )

        logger.info(f"Successfully fetched recent messages for {agent_name} v{agent_version}: {len(messages)} messages")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error fetching recent messages: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch recent messages data"
        )

@app.post("/update-messages", response_model=UpdateMessagesResponse)
async def update_messages_endpoint(
    request: UpdateMessagesRequest,
    db: AsyncSession = Depends(get_database)
):
    """
    Update the messages column in LiteLLM_SpendLogs table with agent metadata.

    Args:
        request: UpdateMessagesRequest containing request_id and agent_metadata

    Returns:
        UpdateMessagesResponse: Status of the update operation

    Raises:
        HTTPException: 400 for invalid request_id, 500 for server errors
    """
    try:
        logger.info(f"Updating messages column for request_id: {request.request_id}")

        # Convert agent metadata to dictionary
        agent_metadata_dict = {
            "agent_name": request.agent_metadata.agent_name,
            "agent_user_id": request.agent_metadata.agent_user_id,
            "agent_version": request.agent_metadata.agent_version,
            "agent_app_name": request.agent_metadata.agent_app_name,
            "agent_session_id": request.agent_metadata.agent_session_id
        }

        # Call CRUD function to update messages column
        result = await update_messages_column(
            db=db,
            request_id=request.request_id,
            agent_metadata=agent_metadata_dict
        )

        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to update messages column"
            )

        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error")
            if "not found" in error_msg:
                raise HTTPException(
                    status_code=404,
                    detail=f"Request ID {request.request_id} not found"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update messages: {error_msg}"
                )

        # Create success response
        response = UpdateMessagesResponse(
            status="success",
            request_id=request.request_id,
            message=f"Successfully updated messages column for request_id: {request.request_id}"
        )

        logger.info(f"Successfully updated messages for request_id: {request.request_id}")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error updating messages column: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while updating messages"
        )

@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "LiteLLM Analytics API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
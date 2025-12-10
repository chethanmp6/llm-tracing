from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

async def get_agent_analytics(
    db: AsyncSession,
    agent_name: str,
    agent_version: str,
    days: int
) -> Optional[Dict[str, Any]]:
    """
    Get analytics metrics for a specific agent and version within a date range.

    This function queries LiteLLM_SpendLogs table and uses JSONB operators to extract
    agent proxy_server_request fields: agent_name, agent_version, agent_user_id, agent_session_id, agent_app_name.

    Recommended indexes for performance:
    - CREATE INDEX idx_spend_logs_proxy_server_request_agent ON "LiteLLM_SpendLogs" USING GIN (proxy_server_request);
    - CREATE INDEX idx_spend_logs_starttime ON "LiteLLM_SpendLogs" ("startTime");
    - CREATE INDEX idx_spend_logs_agent_name ON "LiteLLM_SpendLogs" ((proxy_server_request->>'agent_name'));
    - CREATE INDEX idx_spend_logs_agent_version ON "LiteLLM_SpendLogs" ((proxy_server_request->>'agent_version'));
    """

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Query LiteLLM_SpendLogs table for agent analytics
    agent_query = text("""
        SELECT
            COUNT(DISTINCT proxy_server_request->'metadata'->'requester_metadata'->>'agent_session_id') AS total_sessions,
            SUM(
                CASE
                    WHEN response::text != '{}' AND response IS NOT NULL
                    THEN jsonb_array_length(response->'choices')
                    ELSE 0
                END
            ) AS total_messages,
            ROUND(
                COUNT(*)::numeric / NULLIF(COUNT(DISTINCT DATE("startTime")), 0),
                2
            ) AS average_daily_actions,
            COUNT(DISTINCT proxy_server_request->'metadata'->'requester_metadata'->>'agent_user_id') AS total_users
        FROM "LiteLLM_SpendLogs"
        WHERE proxy_server_request::text != '{}'
          AND proxy_server_request->'metadata'->'requester_metadata'->>'agent_name' = :agent_name
          AND proxy_server_request->'metadata'->'requester_metadata'->>'agent_version' = :agent_version
          AND "startTime" >= :start_date
          AND "startTime" <= :end_date
    """)

    try:
        logger.info(f"Executing query with params: agent_name={agent_name}, agent_version={agent_version}, start_date={start_date}, end_date={end_date}")
        result = await db.execute(agent_query, {
            'agent_name': agent_name,
            'agent_version': agent_version,
            'start_date': start_date,
            'end_date': end_date
        })

        row = result.fetchone()
        logger.info(f"Query result: {row}")

        if row and row.total_messages > 0:
            return _process_analytics_result(row, start_date, end_date, days)

        return None

    except Exception as e:
        logger.error(f"Database error in get_agent_analytics: {e}")
        raise

def _process_analytics_result(row, start_date: datetime, end_date: datetime, days: int) -> Dict[str, Any]:
    """Process the raw analytics result from database."""

    return {
        'total_sessions': row.total_sessions or 0,
        'total_messages': row.total_messages or 0,
        'total_users': row.total_users or 0,
        'avg_daily_messages': row.average_daily_actions or 0,
        'start_date': start_date,
        'end_date': end_date
    }

async def check_database_connection(db: AsyncSession) -> bool:
    """Check if database connection is working."""
    try:
        result = await db.execute(text('SELECT 1'))
        row = result.first()
        return row is not None
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

async def get_agent_activity_timeline(
    db: AsyncSession,
    agent_name: str,
    agent_version: str,
    days: int
) -> Optional[Dict[str, Any]]:
    """
    Get daily session activity timeline for a specific agent and version within a date range.

    Returns a list of daily session counts for the specified time period.
    """

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Generate the date range manually in Python
    date_list = []
    current_date = start_date.date()
    end_date_only = end_date.date()

    while current_date <= end_date_only:
        date_list.append(current_date)
        current_date += timedelta(days=1)

    try:
        # Query for actual session data
        session_query = text("""
            SELECT
                DATE("startTime") AS date,
                COUNT(DISTINCT proxy_server_request->'metadata'->'requester_metadata'->>'agent_session_id') AS sessions
            FROM "LiteLLM_SpendLogs"
            WHERE proxy_server_request::text != '{}'
                AND proxy_server_request->'metadata'->'requester_metadata'->>'agent_name' = :agent_name
                AND proxy_server_request->'metadata'->'requester_metadata'->>'agent_version' = :agent_version
                AND "startTime" >= :start_date
                AND "startTime" <= :end_date
            GROUP BY DATE("startTime")
        """)

        logger.info(f"Executing activity timeline query with params: agent_name={agent_name}, agent_version={agent_version}")
        result = await db.execute(session_query, {
            'agent_name': agent_name,
            'agent_version': agent_version,
            'start_date': start_date,
            'end_date': end_date
        })

        # Convert result to dictionary for easy lookup
        session_data = {row.date: row.sessions for row in result.fetchall()}

        # Create daily sessions list with actual data or 0
        daily_sessions = [
            {
                'date': date.strftime('%Y-%m-%d'),
                'sessions': session_data.get(date, 0)
            }
            for date in date_list
        ]

        return {
            'daily_sessions': daily_sessions,
            'start_date': start_date,
            'end_date': end_date
        }

    except Exception as e:
        logger.error(f"Database error in get_agent_activity_timeline: {e}")
        # If database query fails, return all dates with 0 sessions
        daily_sessions = [
            {
                'date': date.strftime('%Y-%m-%d'),
                'sessions': 0
            }
            for date in date_list
        ]

        return {
            'daily_sessions': daily_sessions,
            'start_date': start_date,
            'end_date': end_date
        }

async def get_agent_tokens_usage(
    db: AsyncSession,
    agent_name: str,
    agent_version: str,
    days: int
) -> Optional[Dict[str, Any]]:
    """
    Get daily token usage (prompt and completion) for a specific agent and version within a date range.

    Returns a list of daily token counts for the specified time period.
    """

    # Use date-only calculations to avoid time-based issues
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # For SQL query, make end_date inclusive by going to next day
    end_date_inclusive = end_date + timedelta(days=1)

    # Convert back to datetime for SQL query compatibility
    end_date_dt = datetime.combine(end_date_inclusive, datetime.min.time())
    start_date_dt = datetime.combine(start_date, datetime.min.time())

    # Debug logging to see what date range we're actually using
    logger.info(f"Tokens usage date range: start_date={start_date}, end_date={end_date}")

    # Generate the date range manually in Python
    date_list = []
    current_date = start_date

    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)

    try:
        # Use the exact same query structure that worked in the debug endpoint
        start_date_str = start_date_dt.strftime('%Y-%m-%d')
        end_date_str = end_date_dt.strftime('%Y-%m-%d')

        tokens_query = text(f"""
            SELECT
                DATE("startTime") AS date,
                SUM(prompt_tokens::numeric) AS prompt_tokens,
                SUM(completion_tokens::numeric) AS completion_tokens
            FROM "LiteLLM_SpendLogs"
            WHERE proxy_server_request::text != '{{}}'
                AND proxy_server_request->'metadata'->'requester_metadata'->>'agent_name' = :agent_name
                AND proxy_server_request->'metadata'->'requester_metadata'->>'agent_version' = :agent_version
                AND "startTime" >= '{start_date_str}'
                AND "startTime" <= '{end_date_str}'
            GROUP BY DATE("startTime")
            ORDER BY DATE("startTime")
        """)

        params = {
            'agent_name': agent_name,
            'agent_version': agent_version
        }
        logger.info(f"Executing tokens usage query with params: {params}")
        logger.info(f"Query: {tokens_query}")

        result = await db.execute(tokens_query, params)
        rows = result.fetchall()
        logger.info(f"Tokens usage query returned {len(rows)} rows")

        # Convert query results to dictionary for lookup
        token_data = {}
        for row in rows:
            date_key = row.date
            token_data[date_key] = {
                'prompt_tokens': int(row.prompt_tokens or 0),
                'completion_tokens': int(row.completion_tokens or 0)
            }
            logger.info(f"Found data for {date_key}: prompt={row.prompt_tokens}, completion={row.completion_tokens}")

        # Create daily tokens list with actual data or 0
        daily_tokens = [
            {
                'date': date.strftime('%Y-%m-%d'),
                'prompt_tokens': token_data.get(date, {}).get('prompt_tokens', 0),
                'completion_tokens': token_data.get(date, {}).get('completion_tokens', 0)
            }
            for date in date_list
        ]

        return {
            'daily_tokens': daily_tokens,
            'start_date': datetime.combine(start_date, datetime.min.time()),
            'end_date': datetime.combine(end_date, datetime.min.time())
        }

    except Exception as e:
        logger.error(f"Database error in get_agent_tokens_usage: {e}")
        # If database query fails, return all dates with 0 tokens
        daily_tokens = [
            {
                'date': date.strftime('%Y-%m-%d'),
                'prompt_tokens': 0,
                'completion_tokens': 0
            }
            for date in date_list
        ]

        return {
            'daily_tokens': daily_tokens,
            'start_date': datetime.combine(start_date, datetime.min.time()),
            'end_date': datetime.combine(end_date, datetime.min.time())
        }

async def get_agent_total_tokens(
    db: AsyncSession,
    agent_name: str,
    agent_version: str,
    days: int
) -> Optional[Dict[str, Any]]:
    """
    Get total token consumption (prompt and completion) for a specific agent and version within a date range.

    Returns the sum of all tokens consumed in the specified time period.
    """

    # Use date-only calculations to avoid time-based issues
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # For SQL query, make end_date inclusive by going to next day
    end_date_inclusive = end_date + timedelta(days=1)

    # Convert back to datetime for SQL query compatibility
    end_date_dt = datetime.combine(end_date_inclusive, datetime.min.time())
    start_date_dt = datetime.combine(start_date, datetime.min.time())

    # Debug logging to see what date range we're actually using
    logger.info(f"Total tokens date range: start_date={start_date}, end_date={end_date}")

    try:
        # Use the exact same query structure with hardcoded dates (like tokens-usage)
        start_date_str = start_date_dt.strftime('%Y-%m-%d')
        end_date_str = end_date_dt.strftime('%Y-%m-%d')

        total_tokens_query = text(f"""
            SELECT
                COALESCE(SUM(prompt_tokens::numeric), 0) AS total_prompt_tokens,
                COALESCE(SUM(completion_tokens::numeric), 0) AS total_completion_tokens
            FROM "LiteLLM_SpendLogs"
            WHERE proxy_server_request::text != '{{}}'
                AND proxy_server_request->'metadata'->'requester_metadata'->>'agent_name' = :agent_name
                AND proxy_server_request->'metadata'->'requester_metadata'->>'agent_version' = :agent_version
                AND "startTime" >= '{start_date_str}'
                AND "startTime" <= '{end_date_str}'
        """)

        params = {
            'agent_name': agent_name,
            'agent_version': agent_version
        }
        logger.info(f"Executing total tokens query with params: {params}")

        result = await db.execute(total_tokens_query, params)
        row = result.fetchone()
        logger.info(f"Total tokens query result: prompt={row.total_prompt_tokens}, completion={row.total_completion_tokens}")

        return {
            'total_prompt_tokens': int(row.total_prompt_tokens or 0),
            'total_completion_tokens': int(row.total_completion_tokens or 0),
            'start_date': datetime.combine(start_date, datetime.min.time()),
            'end_date': datetime.combine(end_date, datetime.min.time())
        }

    except Exception as e:
        logger.error(f"Database error in get_agent_total_tokens: {e}")
        # If database query fails, return 0 totals
        return {
            'total_prompt_tokens': 0,
            'total_completion_tokens': 0,
            'start_date': datetime.combine(start_date, datetime.min.time()),
            'end_date': datetime.combine(end_date, datetime.min.time())
        }

async def get_agent_detailed_usage(
    db: AsyncSession,
    agent_name: str,
    agent_version: str,
    days: int
) -> Optional[Dict[str, Any]]:
    """
    Get detailed usage logs for a specific agent and version within a date range.

    Returns individual request logs with timestamps, token counts, and duration.
    """

    # Use date-only calculations to avoid time-based issues
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # For SQL query, make end_date inclusive by going to next day
    end_date_inclusive = end_date + timedelta(days=1)

    # Convert back to datetime for SQL query compatibility
    end_date_dt = datetime.combine(end_date_inclusive, datetime.min.time())
    start_date_dt = datetime.combine(start_date, datetime.min.time())

    # Debug logging to see what date range we're actually using
    logger.info(f"Detailed usage date range: start_date={start_date}, end_date={end_date}")

    try:
        # Use the exact same query structure with hardcoded dates
        start_date_str = start_date_dt.strftime('%Y-%m-%d')
        end_date_str = end_date_dt.strftime('%Y-%m-%d')

        detailed_logs_query = text(f"""
            SELECT
                "startTime" AS timestamp,
                proxy_server_request->'metadata'->'requester_metadata'->>'agent_name' AS agent_name,
                total_tokens::numeric AS total_tokens,
                prompt_tokens::numeric AS prompt_tokens,
                completion_tokens::numeric AS completion_tokens,
                EXTRACT(EPOCH FROM ("endTime" - "startTime")) AS duration_seconds
            FROM "LiteLLM_SpendLogs"
            WHERE proxy_server_request::text != '{{}}'
                AND proxy_server_request->'metadata'->'requester_metadata'->>'agent_name' = :agent_name
                AND proxy_server_request->'metadata'->'requester_metadata'->>'agent_version' = :agent_version
                AND "startTime" >= '{start_date_str}'
                AND "startTime" <= '{end_date_str}'
            ORDER BY "startTime" DESC
        """)

        params = {
            'agent_name': agent_name,
            'agent_version': agent_version
        }
        logger.info(f"Executing detailed usage query with params: {params}")

        result = await db.execute(detailed_logs_query, params)
        rows = result.fetchall()
        logger.info(f"Detailed usage query returned {len(rows)} rows")

        # Convert results to list of usage logs
        usage_logs = [
            {
                'timestamp': row.timestamp,
                'agent_name': row.agent_name or agent_name,  # fallback to parameter if null
                'total_tokens': int(row.total_tokens or 0),
                'prompt_tokens': int(row.prompt_tokens or 0),
                'completion_tokens': int(row.completion_tokens or 0),
                'duration_seconds': float(row.duration_seconds or 0.0)
            }
            for row in rows
        ]

        return {
            'usage_logs': usage_logs,
            'start_date': datetime.combine(start_date, datetime.min.time()),
            'end_date': datetime.combine(end_date, datetime.min.time())
        }

    except Exception as e:
        logger.error(f"Database error in get_agent_detailed_usage: {e}")
        # If database query fails, return empty logs
        return {
            'usage_logs': [],
            'start_date': datetime.combine(start_date, datetime.min.time()),
            'end_date': datetime.combine(end_date, datetime.min.time())
        }

async def get_recent_messages(
    db: AsyncSession,
    agent_name: str,
    agent_version: str,
    days: int
) -> Optional[Dict[str, Any]]:
    """
    Get recent messages for a specific agent and version within a date range.

    Returns individual message logs with timestamps, content, and metadata.
    """

    # Use date-only calculations to avoid time-based issues
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # For SQL query, make end_date inclusive by going to next day
    end_date_inclusive = end_date + timedelta(days=1)

    # Convert back to datetime for SQL query compatibility
    end_date_dt = datetime.combine(end_date_inclusive, datetime.min.time())
    start_date_dt = datetime.combine(start_date, datetime.min.time())

    # Debug logging to see what date range we're actually using
    logger.info(f"Recent messages date range: start_date={start_date}, end_date={end_date}")

    try:
        # Use the exact same query structure with hardcoded dates
        start_date_str = start_date_dt.strftime('%Y-%m-%d')
        end_date_str = end_date_dt.strftime('%Y-%m-%d')

        recent_messages_query = text(f"""
            SELECT
                "startTime" AS timestamp,
                proxy_server_request->'metadata'->'requester_metadata'->>'agent_session_id' AS session_id,
                LENGTH(response->'choices'->0->'message'->>'content') AS message_length,
                proxy_server_request->'metadata'->'requester_metadata'->>'agent_name' AS agent_name,
                response->>'model' AS model_name,
                response->'choices'->0->'message'->>'content' AS message
            FROM "LiteLLM_SpendLogs"
            WHERE proxy_server_request::text != '{{}}'
                AND response::text != '{{}}'
                AND proxy_server_request->'metadata'->'requester_metadata'->>'agent_name' = :agent_name
                AND proxy_server_request->'metadata'->'requester_metadata'->>'agent_version' = :agent_version
                AND "startTime" >= '{start_date_str}'
                AND "startTime" <= '{end_date_str}'
            ORDER BY "startTime" DESC
        """)

        params = {
            'agent_name': agent_name,
            'agent_version': agent_version
        }
        logger.info(f"Executing recent messages query with params: {params}")

        result = await db.execute(recent_messages_query, params)
        rows = result.fetchall()
        logger.info(f"Recent messages query returned {len(rows)} rows")

        # Convert results to list of message logs
        messages = [
            {
                'timestamp': row.timestamp,
                'session_id': row.session_id or '',
                'message_length': int(row.message_length or 0),
                'agent_name': row.agent_name or agent_name,
                'model_name': row.model_name or '',
                'message': row.message or ''
            }
            for row in rows
        ]

        return {
            'messages': messages,
            'start_date': datetime.combine(start_date, datetime.min.time()),
            'end_date': datetime.combine(end_date, datetime.min.time())
        }

    except Exception as e:
        logger.error(f"Database error in get_recent_messages: {e}")
        # If database query fails, return empty messages
        return {
            'messages': [],
            'start_date': datetime.combine(start_date, datetime.min.time()),
            'end_date': datetime.combine(end_date, datetime.min.time())
        }

async def get_available_tables(db: AsyncSession) -> list:
    """Get list of available LiteLLM tables for debugging."""
    try:
        result = await db.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE '%LiteLLM%'
        """))

        return [row.table_name for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Error getting table list: {e}")
        return []


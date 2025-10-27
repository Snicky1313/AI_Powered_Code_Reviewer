#!/usr/bin/env python3
"""
AI-Powered Python Code Reviewer - Logging Query & Analytics Service

Provides query and analytics endpoints for retrieving and analyzing logged events.

Author: Code Review Enhancement Team
Created: 2025-01-XX
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Logging Query & Analytics Service",
    description="Query and analytics endpoints for log events",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DATABASE_HOST', 'localhost'),
    'port': int(os.getenv('DATABASE_PORT', 5432)),
    'database': os.getenv('DATABASE_NAME', 'code_reviewer_logs'),
    'user': os.getenv('DATABASE_USER', 'logging_service_user'),
    'password': os.getenv('DATABASE_PASSWORD', 'SagorAhmmed22')
}


# Pydantic models
class LogQueryResponse(BaseModel):
    """Response model for log queries."""
    total: int
    events: List[Dict[str, Any]]
    page: int = 1
    page_size: int = 100


class AnalyticsResponse(BaseModel):
    """Response model for analytics queries."""
    metrics: Dict[str, Any]
    timestamp: str


class DatabaseManager:
    """Manages database connections and queries."""
    
    def __init__(self):
        self.config = DB_CONFIG
        
    def get_connection(self):
        """Get a database connection."""
        try:
            return psycopg2.connect(**self.config, cursor_factory=RealDictCursor)
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")
    
    def query_events(
        self,
        event_type: Optional[str] = None,
        session_id: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict], int]:
        """
        Query log events with filters.
        
        Returns:
            Tuple of (events list, total count)
        """
        try:
            conn = self.get_connection()
            
            # Build WHERE clause
            conditions = []
            params = []
            
            if event_type:
                conditions.append("event_type = %s")
                params.append(event_type)
            
            if session_id:
                conditions.append("session_id = %s")
                params.append(session_id)
            
            if start_time:
                conditions.append("timestamp >= %s")
                params.append(start_time)
            
            if end_time:
                conditions.append("timestamp <= %s")
                params.append(end_time)
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            # Get total count
            count_query = f"SELECT COUNT(*) as count FROM log_events{where_clause}"
            
            # Get events
            query = f"""
                SELECT * FROM log_events
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            
            with conn.cursor() as cursor:
                # Get count
                cursor.execute(count_query, params[:-2])
                total = cursor.fetchone()['count']
                
                # Get events
                cursor.execute(query, params)
                events = cursor.fetchall()
                
            conn.close()
            
            return [dict(event) for event in events], total
            
        except psycopg2.Error as e:
            logger.error(f"Database query error: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def get_event_types(self) -> List[Dict[str, Any]]:
        """Get list of all event types with counts."""
        try:
            conn = self.get_connection()
            
            query = """
                SELECT event_type, COUNT(*) as count
                FROM log_events
                GROUP BY event_type
                ORDER BY count DESC
            """
            
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
            
            conn.close()
            return [dict(row) for row in results]
            
        except psycopg2.Error as e:
            logger.error(f"Database query error: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def get_usage_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get usage analytics for the last N days."""
        try:
            conn = self.get_connection()
            
            since = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get total events
            query_total = "SELECT COUNT(*) as count FROM log_events WHERE timestamp >= %s"
            
            # Get events by type
            query_by_type = """
                SELECT event_type, COUNT(*) as count
                FROM log_events
                WHERE timestamp >= %s
                GROUP BY event_type
                ORDER BY count DESC
            """
            
            # Get daily breakdown
            query_daily = """
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM log_events
                WHERE timestamp >= %s
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """
            
            # Get unique sessions
            query_sessions = """
                SELECT COUNT(DISTINCT session_id) as count
                FROM log_events
                WHERE timestamp >= %s
            """
            
            with conn.cursor() as cursor:
                cursor.execute(query_total, (since,))
                total_events = cursor.fetchone()['count']
                
                cursor.execute(query_by_type, (since,))
                events_by_type = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute(query_daily, (since,))
                daily_breakdown = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute(query_sessions, (since,))
                unique_sessions = cursor.fetchone()['count']
            
            conn.close()
            
            return {
                "period_days": days,
                "total_events": total_events,
                "unique_sessions": unique_sessions,
                "events_by_type": events_by_type,
                "daily_breakdown": daily_breakdown,
                "since": since
            }
            
        except psycopg2.Error as e:
            logger.error(f"Database query error: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def get_llm_usage_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get LLM usage analytics."""
        try:
            conn = self.get_connection()
            
            since = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get LLM query events
            query_llm = """
                SELECT payload->>'model' as model,
                       COUNT(*) as query_count,
                       SUM((payload->>'tokens_used')::int) as total_tokens
                FROM log_events
                WHERE event_type = 'llm_query_sent' AND timestamp >= %s
                GROUP BY payload->>'model'
                ORDER BY query_count DESC
            """
            
            # Get total LLM costs
            query_costs = """
                SELECT SUM((payload->>'cost')::float) as total_cost
                FROM log_events
                WHERE event_type = 'llm_query_sent' AND timestamp >= %s
            """
            
            with conn.cursor() as cursor:
                cursor.execute(query_llm, (since,))
                llm_usage = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute(query_costs, (since,))
                total_cost = cursor.fetchone()['total_cost'] or 0.0
            
            conn.close()
            
            return {
                "period_days": days,
                "total_queries": sum(usage.get('query_count', 0) for usage in llm_usage),
                "total_tokens": sum(usage.get('total_tokens', 0) or 0 for usage in llm_usage),
                "total_cost": float(total_cost),
                "model_breakdown": llm_usage,
                "since": since
            }
            
        except psycopg2.Error as e:
            logger.error(f"Database query error: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    def get_performance_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get performance analytics (review durations, etc.)."""
        try:
            conn = self.get_connection()
            
            since = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get session durations
            query_durations = """
                SELECT 
                    session_id,
                    MIN(CASE WHEN event_type = 'review_started' THEN timestamp END) as started,
                    MAX(CASE WHEN event_type = 'review_completed' THEN timestamp END) as completed,
                    COUNT(DISTINCT event_type) as event_count
                FROM log_events
                WHERE session_id IN (
                    SELECT DISTINCT session_id
                    FROM log_events
                    WHERE event_type IN ('review_started', 'review_completed')
                    AND timestamp >= %s
                )
                GROUP BY session_id
                HAVING MIN(CASE WHEN event_type = 'review_started' THEN timestamp END) IS NOT NULL
                ORDER BY started DESC
                LIMIT 100
            """
            
            with conn.cursor() as cursor:
                cursor.execute(query_durations, (since,))
                sessions = cursor.fetchall()
            
            conn.close()
            
            # Calculate average duration
            durations = []
            for session in sessions:
                started = session.get('started')
                completed = session.get('completed')
                if started and completed:
                    start_dt = datetime.fromisoformat(str(started))
                    end_dt = datetime.fromisoformat(str(completed))
                    duration = (end_dt - start_dt).total_seconds()
                    durations.append(duration)
            
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                "period_days": days,
                "total_sessions": len(sessions),
                "average_duration_seconds": round(avg_duration, 2),
                "average_duration_minutes": round(avg_duration / 60, 2),
                "since": since
            }
            
        except psycopg2.Error as e:
            logger.error(f"Database query error: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Global database manager
db_manager = DatabaseManager()


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Logging Query & Analytics Service",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "query": "/query",
            "events": "/events",
            "event_types": "/events/types",
            "analytics": "/analytics",
            "analytics_usage": "/analytics/usage",
            "analytics_llm": "/analytics/llm",
            "analytics_performance": "/analytics/performance",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        conn = db_manager.get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        conn.close()
        
        return {
            "status": "healthy",
            "service": "query-analytics",
            "timestamp": datetime.now().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "query-analytics",
            "timestamp": datetime.now().isoformat(),
            "database": "disconnected",
            "error": str(e)
        }


@app.get("/events", response_model=LogQueryResponse)
async def query_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    session_id: Optional[int] = Query(None, description="Filter by session ID"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Page size")
):
    """
    Query log events with filters and pagination.
    
    Example:
        GET /events?event_type=review_started&limit=50&page=1
    """
    # Calculate offset from page and page_size
    actual_offset = (page - 1) * page_size if page > 1 else offset
    
    events, total = db_manager.query_events(
        event_type=event_type,
        session_id=session_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=actual_offset
    )
    
    return LogQueryResponse(
        total=total,
        events=events,
        page=page,
        page_size=page_size
    )


@app.get("/events/types")
async def get_event_types():
    """Get list of all event types with counts."""
    types = db_manager.get_event_types()
    return {
        "event_types": types,
        "total_types": len(types)
    }


@app.get("/analytics/usage", response_model=AnalyticsResponse)
async def get_usage_analytics(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze")
):
    """Get usage analytics for the specified time period."""
    metrics = db_manager.get_usage_analytics(days=days)
    
    return AnalyticsResponse(
        metrics=metrics,
        timestamp=datetime.now().isoformat()
    )


@app.get("/analytics/llm", response_model=AnalyticsResponse)
async def get_llm_analytics(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze")
):
    """Get LLM usage analytics (queries, tokens, costs)."""
    metrics = db_manager.get_llm_usage_analytics(days=days)
    
    return AnalyticsResponse(
        metrics=metrics,
        timestamp=datetime.now().isoformat()
    )


@app.get("/analytics/performance", response_model=AnalyticsResponse)
async def get_performance_analytics(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze")
):
    """Get performance analytics (review durations, etc.)."""
    metrics = db_manager.get_performance_analytics(days=days)
    
    return AnalyticsResponse(
        metrics=metrics,
        timestamp=datetime.now().isoformat()
    )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv('QUERY_SERVICE_HOST', '0.0.0.0')
    port = int(os.getenv('QUERY_SERVICE_PORT', 8002))
    
    logger.info(f"Starting query service on {host}:{port}")
    
    uvicorn.run(
        "query_service:app",
        host=host,
        port=port,
        reload=os.getenv('ENVIRONMENT') == 'development',
        log_level=os.getenv('LOG_LEVEL', 'info').lower()
    )


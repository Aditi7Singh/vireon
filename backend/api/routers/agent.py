from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

import models
import schemas
import database
import auth
from agent.cfo_agent import run_cfo_query, build_graph
from agent.memory import build_config
from langchain_core.messages import HumanMessage, AIMessage

router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/chat", response_model=dict)
async def chat_with_cfo(
    request: schemas.ChatRequest,
    db: Session = Depends(database.get_db),
    current_user: Optional[models.User] = Depends(auth.get_current_user)
):
    # Get session ID or generate one
    session_id = request.session_id or f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Get context from DB if possible, otherwise use fresh context from agent
    latest_metric = None
    if request.company_id:
        latest_metric = db.query(models.MonthlyMetric).filter(
            models.MonthlyMetric.company_id == request.company_id
        ).order_by(models.MonthlyMetric.metric_month.desc()).first()

    company_context = None
    if latest_metric:
        company_context = {
            "name": "SeedlingLabs",
            "cash": float(latest_metric.ending_cash),
            "monthly_burn": float(latest_metric.total_expenses),
            "runway_months": float(latest_metric.runway_months),
            "mrr": float(latest_metric.total_revenue),
            "arr": float(latest_metric.total_revenue) * 12,
            "last_updated": latest_metric.metric_month.strftime("%Y-%m-%d")
        }

    # Run the query through LangGraph CFO agent
    answer = run_cfo_query(
        user_message=request.message,
        session_id=session_id,
        company_context=company_context
    )
    
    return {
        "response": answer,
        "session_id": session_id,
        "query_type": "complex", # Can be more dynamic if needed
        "timestamp": datetime.now().isoformat()
    }

@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    db: Session = Depends(database.get_db),
    current_user: Optional[models.User] = Depends(auth.get_current_user)
):
    try:
        graph = build_graph()
        config = build_config(session_id)
        state = graph.get_state(config)
        
        messages = []
        if state and state.values and "messages" in state.values:
            for msg in state.values["messages"]:
                role = "user" if isinstance(msg, HumanMessage) else "assistant" if isinstance(msg, AIMessage) else None
                if role and msg.content:
                    messages.append({
                        "role": role,
                        "content": msg.content,
                        "timestamp": datetime.now().isoformat() # Ideally get from msg if available
                    })
        
        return {"session_id": session_id, "messages": messages}
    except Exception as e:
        print(f"Error fetching history: {e}")
        return {"session_id": session_id, "messages": []}

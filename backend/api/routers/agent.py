from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

import models
import schemas
import database
import auth
from agent.cfo_agent import run_cfo_query
from agent.finance_agent import run_finance_query
from agent.finance_manager_agent import run_finance_manager_query
from agent.memory import build_enhanced_context, load_session_messages
from agent.routing import classify_query
from langchain_core.messages import HumanMessage, AIMessage
try:
    from services.memory_service import ConversationMemory, MemoryService
except ImportError:
    from backend.services.memory_service import ConversationMemory, MemoryService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/chat", response_model=dict)
async def chat_with_cfo(
    request: schemas.ChatRequest,
    db: Session = Depends(database.get_db),
    current_user: Optional[models.User] = Depends(auth.get_current_user)
):
    try:
        query_type = classify_query(request.message)

        # Get session ID or generate one
        session_id = request.session_id or f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Initialize memory service with database session
        memory_service = MemoryService(db_session=db)
        conversation_memory = ConversationMemory(db_session=db)
        
        # Get or create session with user/company context
        user_id = str(current_user.id) if current_user else None
        company_id = request.company_id
        session = conversation_memory.get_or_create_session(
            session_id=session_id,
            user_id=user_id or "anonymous",
            company_id=str(company_id) if company_id else "default_company",
        )
        
        # Get context from DB if possible, otherwise use fresh context from agent
        latest_metric = None
        company = None
        if request.company_id:
            company = db.query(models.Company).filter(models.Company.id == request.company_id).first()
            latest_metric = db.query(models.MonthlyMetric).filter(
                models.MonthlyMetric.company_id == request.company_id
            ).order_by(models.MonthlyMetric.metric_month.desc()).first()
        elif current_user is not None:
            company = db.query(models.Company).first()
            if company:
                latest_metric = db.query(models.MonthlyMetric).filter(
                    models.MonthlyMetric.company_id == company.id
                ).order_by(models.MonthlyMetric.metric_month.desc()).first()

        company_context = None
        financial_metrics = {}
        
        if latest_metric:
            base_context = {
                "name": company.name if company else "SeedlingLabs",
                "cash": float(latest_metric.ending_cash),
                "monthly_burn": float(latest_metric.total_expenses),
                "runway_months": float(latest_metric.runway_months),
                "mrr": float(latest_metric.total_revenue),
                "arr": float(latest_metric.total_revenue) * 12,
                "last_updated": latest_metric.metric_month.strftime("%Y-%m-%d")
            }
            financial_metrics = base_context.copy()
            # Enhance with additional financial metrics
            company_context = build_enhanced_context(base_context, company_id=str(company.id) if company else None)
        elif company:
            company_context = build_enhanced_context({"name": company.name}, company_id=str(company.id))
        else:
            company_context = build_enhanced_context({"name": "SeedlingLabs"})
        
        # Add financial context to conversation memory
        if financial_metrics:
            memory_service.add_financial_context(session, financial_metrics)
        
        # Store user message in memory
        conversation_memory.add_user_message(session.session_id, request.message)
        
        # Get conversation context for LLM (includes history + metrics)
        llm_context = conversation_memory.get_context_for_llm(session.session_id)

        # Run the query through LangGraph CFO agent
        answer = run_cfo_query(
            user_message=request.message,
            session_id=session_id,
            company_context=company_context,
            company_id=str(company.id) if company else (str(request.company_id) if request.company_id else None),
            conversation_context=llm_context  # Pass conversation history to agent
        )
        
        # Store assistant response in memory
        conversation_memory.add_assistant_message(session.session_id, answer)
        
        logger.info(f"Chat processed for session {session_id}: {query_type}")
        
        return {
            "response": answer,
            "session_id": session_id,
            "query_type": query_type,
            "timestamp": datetime.now().isoformat(),
            "memory_status": "stored"
        }
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    db: Session = Depends(database.get_db),
    current_user: Optional[models.User] = Depends(auth.get_current_user)
):
    try:
        messages = []
        for msg in load_session_messages(session_id):
            role = "user" if isinstance(msg, HumanMessage) else "assistant" if isinstance(msg, AIMessage) else None
            if role and msg.content:
                messages.append({
                    "role": role,
                    "content": msg.content,
                    "timestamp": datetime.now().isoformat()
                })
        
        return {"session_id": session_id, "messages": messages}
    except Exception as e:
        print(f"Error fetching history: {e}")
        return {"session_id": session_id, "messages": []}


@router.post("/finance/chat", response_model=dict)
async def chat_with_finance_agent(
    request: schemas.ChatRequest,
    db: Session = Depends(database.get_db),
    current_user: Optional[models.User] = Depends(auth.get_current_user),
):
    session_id = request.session_id or f"finance_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    company = db.query(models.Company).filter(models.Company.id == request.company_id).first() if request.company_id else db.query(models.Company).first()
    context = build_enhanced_context({"name": company.name if company else "SeedlingLabs"}, company_id=str(company.id) if company else None)
    answer = run_finance_query(
        user_message=request.message,
        session_id=session_id,
        company_context=context,
        company_id=str(company.id) if company else None,
    )
    return {
        "response": answer,
        "session_id": session_id,
        "query_type": classify_query(request.message),
        "agent_mode": "finance_operations",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/finance-manager/chat", response_model=dict)
async def chat_with_finance_manager_agent(
    request: schemas.ChatRequest,
    db: Session = Depends(database.get_db),
    current_user: Optional[models.User] = Depends(auth.get_current_user),
):
    session_id = request.session_id or f"finmgr_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    company = db.query(models.Company).filter(models.Company.id == request.company_id).first() if request.company_id else db.query(models.Company).first()
    context = build_enhanced_context({"name": company.name if company else "SeedlingLabs"}, company_id=str(company.id) if company else None)
    answer = run_finance_manager_query(
        user_message=request.message,
        session_id=session_id,
        company_context=context,
        company_id=str(company.id) if company else None,
    )
    return {
        "response": answer,
        "session_id": session_id,
        "query_type": classify_query(request.message),
        "agent_mode": "finance_manager",
        "timestamp": datetime.now().isoformat(),
    }

"""
Forecast Monitoring Router
Track forecast accuracy and trigger auto-retraining
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/forecast-monitoring", tags=["forecast-monitoring"])


@router.post("/models", response_model=dict)
def create_forecast_model(
    company_id: uuid.UUID,
    model_type: str,
    metric_name: str,
    model_params: dict,
    training_data_start: date,
    training_data_end: date,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Register a new forecast model"""
    
    model = models.ForecastModel(
        company_id=company_id,
        model_type=model_type,
        metric_name=metric_name,
        model_params=model_params,
        training_data_start=training_data_start,
        training_data_end=training_data_end,
        is_active=True
    )
    
    db.add(model)
    db.commit()
    db.refresh(model)
    
    return {
        "model_id": str(model.id),
        "model_type": model_type,
        "metric_name": metric_name,
        "trained_at": model.last_trained_at.isoformat()
    }


@router.get("/models", response_model=List[dict])
def list_forecast_models(
    company_id: uuid.UUID,
    metric_name: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List forecast models"""
    query = db.query(models.ForecastModel).filter(
        models.ForecastModel.company_id == company_id
    )
    
    if metric_name:
        query = query.filter(models.ForecastModel.metric_name == metric_name)
    
    if is_active is not None:
        query = query.filter(models.ForecastModel.is_active == is_active)
    
    models_list = query.order_by(models.ForecastModel.last_trained_at.desc()).all()
    
    result = []
    for m in models_list:
        result.append({
            "id": str(m.id),
            "model_type": m.model_type,
            "metric_name": m.metric_name,
            "mape_score": float(m.mape_score) if m.mape_score else None,
            "rmse_score": float(m.rmse_score) if m.rmse_score else None,
            "prediction_count": m.prediction_count,
            "is_active": m.is_active,
            "last_trained_at": m.last_trained_at.isoformat()
        })
    
    return result


@router.get("/models/{model_id}", response_model=dict)
def get_forecast_model(
    model_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get forecast model details"""
    model = db.query(models.ForecastModel).filter(
        models.ForecastModel.id == model_id
    ).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Forecast model not found")
    
    return {
        "id": str(model.id),
        "company_id": str(model.company_id),
        "model_type": model.model_type,
        "metric_name": model.metric_name,
        "model_params": model.model_params,
        "training_data_start": model.training_data_start.isoformat() if model.training_data_start else None,
        "training_data_end": model.training_data_end.isoformat() if model.training_data_end else None,
        "mape_score": float(model.mape_score) if model.mape_score else None,
        "rmse_score": float(model.rmse_score) if model.rmse_score else None,
        "mae_score": float(model.mae_score) if model.mae_score else None,
        "prediction_count": model.prediction_count,
        "is_active": model.is_active,
        "last_trained_at": model.last_trained_at.isoformat(),
        "created_at": model.created_at.isoformat()
    }


@router.post("/models/{model_id}/retrain", response_model=dict)
def retrain_model(
    model_id: uuid.UUID,
    training_data_end: Optional[date] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Retrain forecast model with updated data"""
    model = db.query(models.ForecastModel).filter(
        models.ForecastModel.id == model_id
    ).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Forecast model not found")
    
    # Update training data end date
    if training_data_end:
        model.training_data_end = training_data_end
    else:
        model.training_data_end = date.today()
    
    # In production, trigger actual model retraining
    # For now, just update metadata
    model.last_trained_at = datetime.utcnow()
    model.prediction_count = 0  # Reset prediction count
    
    db.commit()
    
    return {
        "message": "Model retrained successfully",
        "model_id": str(model_id),
        "training_data_end": model.training_data_end.isoformat(),
        "retrained_at": model.last_trained_at.isoformat()
    }


@router.post("/accuracy", response_model=dict)
def record_forecast_accuracy(
    model_id: uuid.UUID,
    forecast_date: date,
    forecast_value: Decimal,
    actual_value: Decimal,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Record forecast vs actual for accuracy tracking"""
    
    # Calculate errors
    absolute_error = abs(actual_value - forecast_value)
    percentage_error = (absolute_error / actual_value * 100) if actual_value != 0 else Decimal("0.0")
    
    accuracy = models.ForecastAccuracy(
        model_id=model_id,
        forecast_date=forecast_date,
        forecast_value=forecast_value,
        actual_value=actual_value,
        absolute_error=absolute_error,
        percentage_error=percentage_error
    )
    
    db.add(accuracy)
    
    # Update model statistics
    model = db.query(models.ForecastModel).filter(
        models.ForecastModel.id == model_id
    ).first()
    
    if model:
        model.prediction_count += 1
        
        # Recalculate MAPE (Mean Absolute Percentage Error)
        all_accuracy = db.query(models.ForecastAccuracy).filter(
            models.ForecastAccuracy.model_id == model_id
        ).all()
        
        if all_accuracy:
            mape = sum(float(a.percentage_error or 0) for a in all_accuracy) / len(all_accuracy)
            model.mape_score = Decimal(str(mape))
            
            # Check if retraining is needed
            if mape > 20:  # MAPE > 20% suggests model degradation
                trigger_retrain_alert(db, model)
    
    db.commit()
    
    return {
        "message": "Forecast accuracy recorded",
        "absolute_error": float(absolute_error),
        "percentage_error": float(percentage_error),
        "model_mape": float(model.mape_score) if model and model.mape_score else None
    }


@router.get("/accuracy/{model_id}", response_model=List[dict])
def get_forecast_accuracy(
    model_id: uuid.UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get forecast accuracy records"""
    query = db.query(models.ForecastAccuracy).filter(
        models.ForecastAccuracy.model_id == model_id
    )
    
    if start_date:
        query = query.filter(models.ForecastAccuracy.forecast_date >= start_date)
    
    if end_date:
        query = query.filter(models.ForecastAccuracy.forecast_date <= end_date)
    
    accuracy_records = query.order_by(
        models.ForecastAccuracy.forecast_date.desc()
    ).limit(limit).all()
    
    result = []
    for record in accuracy_records:
        result.append({
            "id": str(record.id),
            "forecast_date": record.forecast_date.isoformat(),
            "forecast_value": float(record.forecast_value),
            "actual_value": float(record.actual_value) if record.actual_value else None,
            "absolute_error": float(record.absolute_error) if record.absolute_error else None,
            "percentage_error": float(record.percentage_error) if record.percentage_error else None,
            "recorded_at": record.recorded_at.isoformat()
        })
    
    return result


@router.get("/accuracy/{model_id}/summary", response_model=dict)
def get_accuracy_summary(
    model_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get accuracy summary statistics"""
    model = db.query(models.ForecastModel).filter(
        models.ForecastModel.id == model_id
    ).first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Forecast model not found")
    
    accuracy_records = db.query(models.ForecastAccuracy).filter(
        models.ForecastAccuracy.model_id == model_id
    ).all()
    
    if not accuracy_records:
        return {
            "model_id": str(model_id),
            "total_predictions": 0,
            "mape": None,
            "rmse": None,
            "mae": None
        }
    
    # Calculate statistics
    percentage_errors = [float(r.percentage_error or 0) for r in accuracy_records if r.percentage_error]
    absolute_errors = [float(r.absolute_error or 0) for r in accuracy_records if r.absolute_error]
    
    mape = sum(percentage_errors) / len(percentage_errors) if percentage_errors else 0
    mae = sum(absolute_errors) / len(absolute_errors) if absolute_errors else 0
    
    # RMSE calculation
    squared_errors = [e ** 2 for e in absolute_errors]
    rmse = (sum(squared_errors) / len(squared_errors)) ** 0.5 if squared_errors else 0
    
    # Get recent trend (last 10 predictions)
    recent_records = sorted(accuracy_records, key=lambda x: x.forecast_date, reverse=True)[:10]
    recent_mape = sum(float(r.percentage_error or 0) for r in recent_records) / len(recent_records) if recent_records else 0
    
    # Determine if accuracy is improving or degrading
    trend = "stable"
    if len(accuracy_records) >= 10:
        old_records = sorted(accuracy_records, key=lambda x: x.forecast_date)[:-10]
        if old_records:
            old_mape = sum(float(r.percentage_error or 0) for r in old_records) / len(old_records)
            if recent_mape < old_mape * 0.9:
                trend = "improving"
            elif recent_mape > old_mape * 1.1:
                trend = "degrading"
    
    return {
        "model_id": str(model_id),
        "model_type": model.model_type,
        "metric_name": model.metric_name,
        "total_predictions": len(accuracy_records),
        "mape": round(mape, 2),
        "rmse": round(rmse, 2),
        "mae": round(mae, 2),
        "recent_mape": round(recent_mape, 2),
        "accuracy_trend": trend,
        "needs_retraining": mape > 20 or trend == "degrading",
        "last_trained_at": model.last_trained_at.isoformat()
    }


@router.post("/check-retraining", response_model=dict)
def check_retraining_needed(
    company_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Check all models and identify those needing retraining"""
    
    models_list = db.query(models.ForecastModel).filter(
        and_(
            models.ForecastModel.company_id == company_id,
            models.ForecastModel.is_active == True
        )
    ).all()
    
    needs_retraining = []
    
    for model in models_list:
        # Check MAPE threshold
        if model.mape_score and model.mape_score > 20:
            needs_retraining.append({
                "model_id": str(model.id),
                "model_type": model.model_type,
                "metric_name": model.metric_name,
                "reason": "High MAPE score",
                "mape": float(model.mape_score),
                "last_trained": model.last_trained_at.isoformat()
            })
            continue
        
        # Check if not trained recently
        days_since_training = (datetime.utcnow() - model.last_trained_at).days
        if days_since_training > 90:  # Not trained in 90 days
            needs_retraining.append({
                "model_id": str(model.id),
                "model_type": model.model_type,
                "metric_name": model.metric_name,
                "reason": "Stale model",
                "days_since_training": days_since_training,
                "last_trained": model.last_trained_at.isoformat()
            })
    
    return {
        "total_active_models": len(models_list),
        "models_needing_retraining": len(needs_retraining),
        "models": needs_retraining
    }


@router.post("/auto-retrain", response_model=dict)
def auto_retrain_models(
    company_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Automatically retrain models that need it"""
    
    models_list = db.query(models.ForecastModel).filter(
        and_(
            models.ForecastModel.company_id == company_id,
            models.ForecastModel.is_active == True
        )
    ).all()
    
    retrained_count = 0
    
    for model in models_list:
        should_retrain = False
        
        # Check MAPE threshold
        if model.mape_score and model.mape_score > 20:
            should_retrain = True
        
        # Check staleness
        days_since_training = (datetime.utcnow() - model.last_trained_at).days
        if days_since_training > 90:
            should_retrain = True
        
        if should_retrain:
            # In production, trigger actual retraining job
            model.training_data_end = date.today()
            model.last_trained_at = datetime.utcnow()
            model.prediction_count = 0
            retrained_count += 1
    
    db.commit()
    
    return {
        "message": f"Auto-retrained {retrained_count} models",
        "retrained_count": retrained_count,
        "retrained_at": datetime.utcnow().isoformat()
    }


# Helper functions

def trigger_retrain_alert(db: Session, model: models.ForecastModel):
    """Trigger alert that model needs retraining"""
    # In production, create notification or alert
    # For now, just log it
    print(f"Model {model.id} ({model.metric_name}) needs retraining - MAPE: {model.mape_score}")

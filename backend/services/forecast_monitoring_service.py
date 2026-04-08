"""
ML Forecast Monitoring Service
Tracks forecast accuracy and triggers auto-retraining
"""
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import uuid

from statsmodels.tsa.statespace.sarimax import SARIMAX
from prophet import Prophet
import logging

import models

logger = logging.getLogger(__name__)


class ForecastMonitor:
    """Monitor forecast accuracy and trigger retraining"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def track_forecast_vs_actual(
        self,
        company_id: uuid.UUID,
        metric_name: str,
        forecast_date: date,
        forecast_value: Decimal,
        actual_value: Decimal
    ) -> Dict:
        """Record forecast vs actual and calculate errors"""
        # Find active model for this metric
        model = self.db.query(models.ForecastModel).filter(
            and_(
                models.ForecastModel.company_id == company_id,
                models.ForecastModel.metric_name == metric_name,
                models.ForecastModel.is_active == True
            )
        ).first()
        
        if not model:
            logger.warning(f"No active model found for {metric_name}")
            return {"error": "No active model"}
        
        # Calculate errors
        absolute_error = abs(float(actual_value) - float(forecast_value))
        percentage_error = (absolute_error / float(actual_value) * 100) if actual_value != 0 else 0
        
        # Record accuracy
        accuracy = models.ForecastAccuracy(
            model_id=model.id,
            forecast_date=forecast_date,
            forecast_value=forecast_value,
            actual_value=actual_value,
            absolute_error=Decimal(str(absolute_error)),
            percentage_error=Decimal(str(percentage_error))
        )
        self.db.add(accuracy)
        self.db.commit()
        
        # Update model metrics
        self._update_model_metrics(model.id)
        
        # Check if retraining needed
        if self._should_retrain(model.id):
            logger.info(f"Model {model.id} requires retraining")
            return {
                "accuracy_recorded": True,
                "retrain_required": True,
                "model_id": str(model.id)
            }
        
        return {
            "accuracy_recorded": True,
            "retrain_required": False
        }
    
    def _update_model_metrics(self, model_id: uuid.UUID):
        """Update model performance metrics"""
        # Get recent accuracy records (last 30 days)
        records = self.db.query(models.ForecastAccuracy).filter(
            and_(
                models.ForecastAccuracy.model_id == model_id,
                models.ForecastAccuracy.actual_value.isnot(None)
            )
        ).order_by(models.ForecastAccuracy.forecast_date.desc()).limit(30).all()
        
        if not records:
            return
        
        # Calculate MAPE (Mean Absolute Percentage Error)
        mape = sum(float(r.percentage_error) for r in records) / len(records)
        
        # Calculate RMSE (Root Mean Squared Error)
        squared_errors = [(float(r.absolute_error) ** 2) for r in records]
        rmse = (sum(squared_errors) / len(squared_errors)) ** 0.5
        
        # Calculate MAE (Mean Absolute Error)
        mae = sum(float(r.absolute_error) for r in records) / len(records)
        
        # Update model
        model = self.db.query(models.ForecastModel).filter(
            models.ForecastModel.id == model_id
        ).first()
        
        if model:
            model.mape_score = Decimal(str(mape))
            model.rmse_score = Decimal(str(rmse))
            model.mae_score = Decimal(str(mae))
            self.db.commit()
    
    def _should_retrain(self, model_id: uuid.UUID) -> bool:
        """Determine if model should be retrained"""
        model = self.db.query(models.ForecastModel).filter(
            models.ForecastModel.id == model_id
        ).first()
        
        if not model:
            return False
        
        # Retrain if MAPE > 20% (poor accuracy)
        if model.mape_score and float(model.mape_score) > 20:
            return True
        
        # Retrain if last trained > 90 days ago
        days_since_training = (datetime.utcnow() - model.last_trained_at).days
        if days_since_training > 90:
            return True
        
        # Retrain if recent accuracy declining
        recent_records = self.db.query(models.ForecastAccuracy).filter(
            models.ForecastAccuracy.model_id == model_id
        ).order_by(models.ForecastAccuracy.forecast_date.desc()).limit(10).all()
        
        if len(recent_records) >= 10:
            recent_mape = sum(float(r.percentage_error) for r in recent_records[:5]) / 5
            older_mape = sum(float(r.percentage_error) for r in recent_records[5:10]) / 5
            
            # If recent MAPE is 50% worse than older MAPE
            if recent_mape > older_mape * 1.5:
                return True
        
        return False
    
    def auto_retrain_model(
        self,
        company_id: uuid.UUID,
        metric_name: str
    ) -> Dict:
        """Automatically retrain forecast model"""
        logger.info(f"Starting auto-retrain for {metric_name}")
        
        # Get historical data
        historical_data = self._get_historical_data(company_id, metric_name)
        
        if len(historical_data) < 24:  # Need at least 2 years
            return {"error": "Insufficient historical data"}
        
        # Try SARIMA
        sarima_result = self._train_sarima(historical_data, company_id, metric_name)
        
        # Try Prophet as fallback
        prophet_result = self._train_prophet(historical_data, company_id, metric_name)
        
        # Choose best model
        if sarima_result and prophet_result:
            if sarima_result['mape'] < prophet_result['mape']:
                best_model = sarima_result
            else:
                best_model = prophet_result
        elif sarima_result:
            best_model = sarima_result
        elif prophet_result:
            best_model = prophet_result
        else:
            return {"error": "All models failed"}
        
        # Deactivate old models
        self.db.query(models.ForecastModel).filter(
            and_(
                models.ForecastModel.company_id == company_id,
                models.ForecastModel.metric_name == metric_name,
                models.ForecastModel.is_active == True
            )
        ).update({"is_active": False})
        
        # Save new model
        new_model = models.ForecastModel(
            company_id=company_id,
            model_type=best_model['model_type'],
            metric_name=metric_name,
            model_params=best_model['params'],
            training_data_start=historical_data[0]['date'],
            training_data_end=historical_data[-1]['date'],
            mape_score=Decimal(str(best_model['mape'])),
            rmse_score=Decimal(str(best_model['rmse'])),
            mae_score=Decimal(str(best_model['mae'])),
            is_active=True
        )
        self.db.add(new_model)
        self.db.commit()
        
        logger.info(f"Model retrained successfully: {best_model['model_type']}")
        
        return {
            "success": True,
            "model_id": str(new_model.id),
            "model_type": best_model['model_type'],
            "mape": best_model['mape'],
            "rmse": best_model['rmse']
        }
    
    def _get_historical_data(
        self,
        company_id: uuid.UUID,
        metric_name: str
    ) -> List[Dict]:
        """Get historical data for training"""
        # Get monthly metrics
        metrics = self.db.query(models.MonthlyMetric).filter(
            models.MonthlyMetric.company_id == company_id
        ).order_by(models.MonthlyMetric.metric_month).all()
        
        data = []
        for m in metrics:
            if metric_name == "burn_rate":
                value = float(m.burn_rate)
            elif metric_name == "revenue":
                value = float(m.total_revenue)
            elif metric_name == "runway":
                value = float(m.runway_months)
            elif metric_name == "cash":
                value = float(m.ending_cash)
            else:
                value = 0
            
            data.append({
                "date": m.metric_month,
                "value": value
            })
        
        return data
    
    def _train_sarima(
        self,
        data: List[Dict],
        company_id: uuid.UUID,
        metric_name: str
    ) -> Optional[Dict]:
        """Train SARIMA model"""
        try:
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Auto SARIMA with best params
            # Order (p,d,q) and seasonal (P,D,Q,s)
            model = SARIMAX(
                df['value'],
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 12),
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            
            fitted = model.fit(disp=False)
            
            # Calculate in-sample metrics
            predictions = fitted.fittedvalues
            actuals = df['value']
            
            mape = np.mean(np.abs((actuals - predictions) / actuals)) * 100
            rmse = np.sqrt(np.mean((actuals - predictions) ** 2))
            mae = np.mean(np.abs(actuals - predictions))
            
            return {
                "model_type": "SARIMA",
                "params": {
                    "order": [1, 1, 1],
                    "seasonal_order": [1, 1, 1, 12]
                },
                "mape": float(mape),
                "rmse": float(rmse),
                "mae": float(mae)
            }
        except Exception as e:
            logger.error(f"SARIMA training failed: {e}")
            return None
    
    def _train_prophet(
        self,
        data: List[Dict],
        company_id: uuid.UUID,
        metric_name: str
    ) -> Optional[Dict]:
        """Train Prophet model"""
        try:
            df = pd.DataFrame(data)
            df.columns = ['ds', 'y']
            
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False
            )
            model.fit(df)
            
            # In-sample predictions
            forecast = model.predict(df[['ds']])
            actuals = df['y']
            predictions = forecast['yhat']
            
            mape = np.mean(np.abs((actuals - predictions) / actuals)) * 100
            rmse = np.sqrt(np.mean((actuals - predictions) ** 2))
            mae = np.mean(np.abs(actuals - predictions))
            
            return {
                "model_type": "Prophet",
                "params": {
                    "yearly_seasonality": True,
                    "changepoint_prior_scale": 0.05
                },
                "mape": float(mape),
                "rmse": float(rmse),
                "mae": float(mae)
            }
        except Exception as e:
            logger.error(f"Prophet training failed: {e}")
            return None
    
    def get_model_performance_report(
        self,
        company_id: uuid.UUID
    ) -> Dict:
        """Get comprehensive model performance report"""
        models_list = self.db.query(models.ForecastModel).filter(
            and_(
                models.ForecastModel.company_id == company_id,
                models.ForecastModel.is_active == True
            )
        ).all()
        
        report = []
        for model in models_list:
            # Get recent accuracy
            recent = self.db.query(models.ForecastAccuracy).filter(
                models.ForecastAccuracy.model_id == model.id
            ).order_by(models.ForecastAccuracy.forecast_date.desc()).limit(10).all()
            
            recent_mape = sum(float(r.percentage_error) for r in recent) / len(recent) if recent else 0
            
            report.append({
                "model_id": str(model.id),
                "metric_name": model.metric_name,
                "model_type": model.model_type,
                "mape": float(model.mape_score) if model.mape_score else 0,
                "rmse": float(model.rmse_score) if model.rmse_score else 0,
                "recent_mape": recent_mape,
                "last_trained": model.last_trained_at.isoformat(),
                "days_since_training": (datetime.utcnow() - model.last_trained_at).days,
                "needs_retraining": self._should_retrain(model.id)
            })
        
        return {
            "company_id": str(company_id),
            "models": report,
            "total_models": len(report)
        }

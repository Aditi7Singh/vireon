"""
Scenario Comparison Router
Side-by-side scenario analysis with Monte Carlo simulation
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal
import uuid
import random
import statistics

import database
import models
from auth import get_current_user

router = APIRouter(prefix="/scenario-comparison", tags=["scenario-comparison"])


@router.post("/", response_model=dict)
def create_scenario_comparison(
    company_id: uuid.UUID,
    comparison_name: str,
    scenarios: List[Dict],
    run_monte_carlo: bool = False,
    monte_carlo_iterations: int = 1000,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create and run scenario comparison"""
    
    # Validate scenarios
    if len(scenarios) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 scenarios to compare")
    
    # Run comparison analysis
    results = compare_scenarios(db, company_id, scenarios)
    
    # Run sensitivity analysis
    sensitivity = run_sensitivity_analysis(scenarios)
    
    # Run Monte Carlo if requested
    monte_carlo_results = None
    if run_monte_carlo:
        monte_carlo_results = run_monte_carlo_simulation(
            db, company_id, scenarios, monte_carlo_iterations
        )
    
    comparison = models.ScenarioComparison(
        company_id=company_id,
        comparison_name=comparison_name,
        scenarios=scenarios,
        results=results,
        sensitivity_analysis=sensitivity,
        monte_carlo_results=monte_carlo_results,
        created_by=current_user.username
    )
    
    db.add(comparison)
    db.commit()
    db.refresh(comparison)
    
    return {
        "comparison_id": str(comparison.id),
        "comparison_name": comparison_name,
        "scenario_count": len(scenarios),
        "results_summary": summarize_results(results),
        "monte_carlo_run": run_monte_carlo
    }


@router.get("/", response_model=List[dict])
def list_scenario_comparisons(
    company_id: uuid.UUID,
    limit: int = 20,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List scenario comparisons"""
    comparisons = db.query(models.ScenarioComparison).filter(
        models.ScenarioComparison.company_id == company_id
    ).order_by(models.ScenarioComparison.created_at.desc()).limit(limit).all()
    
    result = []
    for comp in comparisons:
        result.append({
            "id": str(comp.id),
            "comparison_name": comp.comparison_name,
            "scenario_count": len(comp.scenarios) if comp.scenarios else 0,
            "has_monte_carlo": comp.monte_carlo_results is not None,
            "created_by": comp.created_by,
            "created_at": comp.created_at.isoformat()
        })
    
    return result


@router.get("/{comparison_id}", response_model=dict)
def get_scenario_comparison(
    comparison_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get detailed scenario comparison"""
    comparison = db.query(models.ScenarioComparison).filter(
        models.ScenarioComparison.id == comparison_id
    ).first()
    
    if not comparison:
        raise HTTPException(status_code=404, detail="Scenario comparison not found")
    
    return {
        "id": str(comparison.id),
        "company_id": str(comparison.company_id),
        "comparison_name": comparison.comparison_name,
        "scenarios": comparison.scenarios,
        "results": comparison.results,
        "sensitivity_analysis": comparison.sensitivity_analysis,
        "monte_carlo_results": comparison.monte_carlo_results,
        "created_by": comparison.created_by,
        "created_at": comparison.created_at.isoformat()
    }


@router.get("/{comparison_id}/summary", response_model=dict)
def get_comparison_summary(
    comparison_id: uuid.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get executive summary of comparison"""
    comparison = db.query(models.ScenarioComparison).filter(
        models.ScenarioComparison.id == comparison_id
    ).first()
    
    if not comparison:
        raise HTTPException(status_code=404, detail="Scenario comparison not found")
    
    summary = {
        "comparison_name": comparison.comparison_name,
        "scenario_count": len(comparison.scenarios),
        "scenarios": [],
        "best_case": None,
        "worst_case": None,
        "recommended": None
    }
    
    # Analyze each scenario
    for i, scenario in enumerate(comparison.scenarios):
        scenario_result = comparison.results.get(f"scenario_{i}", {})
        summary["scenarios"].append({
            "name": scenario.get("name", f"Scenario {i+1}"),
            "runway_months": scenario_result.get("runway_months", 0),
            "ending_cash": scenario_result.get("ending_cash", 0),
            "total_burn": scenario_result.get("total_burn", 0),
            "risk_score": scenario_result.get("risk_score", 0)
        })
    
    # Identify best/worst cases
    if summary["scenarios"]:
        summary["best_case"] = max(summary["scenarios"], key=lambda x: x["runway_months"])
        summary["worst_case"] = min(summary["scenarios"], key=lambda x: x["runway_months"])
        
        # Recommend scenario with best risk-adjusted runway
        summary["recommended"] = min(
            summary["scenarios"],
            key=lambda x: x["risk_score"] / max(x["runway_months"], 1)
        )
    
    return summary


@router.post("/{comparison_id}/rerun-monte-carlo", response_model=dict)
def rerun_monte_carlo(
    comparison_id: uuid.UUID,
    iterations: int = 1000,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Re-run Monte Carlo simulation with different parameters"""
    comparison = db.query(models.ScenarioComparison).filter(
        models.ScenarioComparison.id == comparison_id
    ).first()
    
    if not comparison:
        raise HTTPException(status_code=404, detail="Scenario comparison not found")
    
    monte_carlo_results = run_monte_carlo_simulation(
        db, comparison.company_id, comparison.scenarios, iterations
    )
    
    comparison.monte_carlo_results = monte_carlo_results
    db.commit()
    
    return {
        "message": "Monte Carlo simulation completed",
        "iterations": iterations,
        "results": monte_carlo_results
    }


@router.post("/quick-compare", response_model=dict)
def quick_scenario_compare(
    company_id: uuid.UUID,
    base_scenario: Dict,
    variations: List[Dict],
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Quick comparison without saving"""
    scenarios = [base_scenario] + variations
    results = compare_scenarios(db, company_id, scenarios)
    
    return {
        "scenarios": scenarios,
        "results": results,
        "summary": summarize_results(results)
    }


# Helper functions

def compare_scenarios(
    db: Session,
    company_id: uuid.UUID,
    scenarios: List[Dict]
) -> Dict:
    """Run comparison analysis on scenarios"""
    results = {}
    
    # Get current company state
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        return results
    
    latest_metric = db.query(models.MonthlyMetric).filter(
        models.MonthlyMetric.company_id == company_id
    ).order_by(models.MonthlyMetric.metric_month.desc()).first()
    
    starting_cash = float(latest_metric.ending_cash) if latest_metric else float(company.initial_cash or 0)
    
    for i, scenario in enumerate(scenarios):
        scenario_key = f"scenario_{i}"
        
        # Extract scenario parameters
        revenue_growth_rate = scenario.get("revenue_growth_rate", 0) / 100
        expense_reduction = scenario.get("expense_reduction", 0) / 100
        new_funding = scenario.get("new_funding", 0)
        projection_months = scenario.get("projection_months", 12)
        
        # Calculate monthly projection
        cash = starting_cash + new_funding
        monthly_revenue = float(latest_metric.total_revenue) if latest_metric else 0
        monthly_expenses = float(latest_metric.total_expenses) if latest_metric else 0
        monthly_expenses *= (1 - expense_reduction)
        
        monthly_projections = []
        for month in range(projection_months):
            monthly_revenue *= (1 + revenue_growth_rate / 12)
            net_cash_flow = monthly_revenue - monthly_expenses
            cash += net_cash_flow
            
            monthly_projections.append({
                "month": month + 1,
                "revenue": monthly_revenue,
                "expenses": monthly_expenses,
                "net_cash_flow": net_cash_flow,
                "ending_cash": cash
            })
            
            if cash <= 0:
                break
        
        # Calculate summary metrics
        total_burn = sum(p["expenses"] - p["revenue"] for p in monthly_projections if p["net_cash_flow"] < 0)
        runway_months = len([p for p in monthly_projections if p["ending_cash"] > 0])
        ending_cash = monthly_projections[-1]["ending_cash"] if monthly_projections else starting_cash
        
        # Calculate risk score
        risk_score = calculate_risk_score(
            runway_months,
            ending_cash,
            revenue_growth_rate,
            expense_reduction
        )
        
        results[scenario_key] = {
            "scenario_name": scenario.get("name", f"Scenario {i+1}"),
            "starting_cash": starting_cash,
            "ending_cash": ending_cash,
            "runway_months": runway_months,
            "total_burn": total_burn,
            "average_monthly_burn": total_burn / max(runway_months, 1),
            "risk_score": risk_score,
            "monthly_projections": monthly_projections
        }
    
    return results


def run_sensitivity_analysis(scenarios: List[Dict]) -> Dict:
    """Analyze sensitivity to key parameters"""
    sensitivity = {
        "revenue_growth": [],
        "expense_reduction": [],
        "funding_amount": []
    }
    
    for scenario in scenarios:
        # Test revenue growth sensitivity
        base_growth = scenario.get("revenue_growth_rate", 0)
        sensitivity["revenue_growth"].append({
            "base": base_growth,
            "plus_5": {"growth_rate": base_growth + 5, "impact": "positive"},
            "minus_5": {"growth_rate": base_growth - 5, "impact": "negative"}
        })
        
        # Test expense reduction sensitivity
        base_reduction = scenario.get("expense_reduction", 0)
        sensitivity["expense_reduction"].append({
            "base": base_reduction,
            "plus_10": {"reduction": base_reduction + 10, "impact": "positive"},
            "minus_10": {"reduction": base_reduction - 10, "impact": "negative"}
        })
        
        # Test funding amount sensitivity
        base_funding = scenario.get("new_funding", 0)
        sensitivity["funding_amount"].append({
            "base": base_funding,
            "plus_500k": {"funding": base_funding + 500000, "impact": "positive"},
            "minus_500k": {"funding": max(0, base_funding - 500000), "impact": "negative"}
        })
    
    return sensitivity


def run_monte_carlo_simulation(
    db: Session,
    company_id: uuid.UUID,
    scenarios: List[Dict],
    iterations: int
) -> Dict:
    """Run Monte Carlo simulation for each scenario"""
    results = {}
    
    for i, scenario in enumerate(scenarios):
        scenario_key = f"scenario_{i}"
        simulation_runs = []
        
        for _ in range(iterations):
            # Add randomness to key parameters
            revenue_variance = random.uniform(-0.2, 0.2)  # ±20%
            expense_variance = random.uniform(-0.1, 0.1)  # ±10%
            
            adjusted_scenario = scenario.copy()
            base_growth = scenario.get("revenue_growth_rate", 0)
            adjusted_scenario["revenue_growth_rate"] = base_growth * (1 + revenue_variance)
            
            base_expense = scenario.get("expense_reduction", 0)
            adjusted_scenario["expense_reduction"] = base_expense * (1 + expense_variance)
            
            # Run single simulation
            sim_result = compare_scenarios(db, company_id, [adjusted_scenario])
            if sim_result and "scenario_0" in sim_result:
                simulation_runs.append({
                    "runway_months": sim_result["scenario_0"]["runway_months"],
                    "ending_cash": sim_result["scenario_0"]["ending_cash"]
                })
        
        # Calculate statistics
        if simulation_runs:
            runway_values = [r["runway_months"] for r in simulation_runs]
            cash_values = [r["ending_cash"] for r in simulation_runs]
            
            results[scenario_key] = {
                "iterations": iterations,
                "runway": {
                    "mean": statistics.mean(runway_values),
                    "median": statistics.median(runway_values),
                    "std_dev": statistics.stdev(runway_values) if len(runway_values) > 1 else 0,
                    "min": min(runway_values),
                    "max": max(runway_values),
                    "percentile_10": sorted(runway_values)[int(len(runway_values) * 0.1)],
                    "percentile_90": sorted(runway_values)[int(len(runway_values) * 0.9)]
                },
                "ending_cash": {
                    "mean": statistics.mean(cash_values),
                    "median": statistics.median(cash_values),
                    "std_dev": statistics.stdev(cash_values) if len(cash_values) > 1 else 0,
                    "min": min(cash_values),
                    "max": max(cash_values)
                },
                "probability_of_runway_12m": sum(1 for r in runway_values if r >= 12) / len(runway_values) * 100
            }
    
    return results


def calculate_risk_score(
    runway_months: int,
    ending_cash: float,
    revenue_growth: float,
    expense_reduction: float
) -> float:
    """Calculate risk score (0-100, higher = riskier)"""
    risk = 0
    
    # Runway risk
    if runway_months < 6:
        risk += 40
    elif runway_months < 12:
        risk += 20
    elif runway_months < 18:
        risk += 10
    
    # Cash position risk
    if ending_cash < 0:
        risk += 30
    elif ending_cash < 500000:
        risk += 15
    
    # Growth assumption risk
    if revenue_growth > 0.5:  # 50% annual growth is aggressive
        risk += 15
    
    # Cost cutting risk
    if expense_reduction > 0.3:  # 30% cuts are risky
        risk += 15
    
    return min(risk, 100)


def summarize_results(results: Dict) -> Dict:
    """Create summary of scenario results"""
    if not results:
        return {}
    
    scenarios = []
    for key, result in results.items():
        scenarios.append({
            "name": result.get("scenario_name", key),
            "runway_months": result.get("runway_months", 0),
            "ending_cash": result.get("ending_cash", 0),
            "risk_score": result.get("risk_score", 0)
        })
    
    # Sort by runway
    scenarios.sort(key=lambda x: x["runway_months"], reverse=True)
    
    return {
        "best_runway": scenarios[0] if scenarios else None,
        "worst_runway": scenarios[-1] if scenarios else None,
        "average_runway": statistics.mean([s["runway_months"] for s in scenarios]) if scenarios else 0,
        "scenarios_passing_12m": sum(1 for s in scenarios if s["runway_months"] >= 12)
    }

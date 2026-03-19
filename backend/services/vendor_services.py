from typing import List, Dict, Any
import models
from sqlalchemy.orm import Session
from sqlalchemy import func

COMMON_SAAS_VENDORS = {
    "AWS": "Cloud Infrastructure",
    "Amazon Web Services": "Cloud Infrastructure",
    "Slack": "Communication",
    "Google Workspace": "Productivity",
    "GitHub": "Development",
    "Vercel": "Hosting",
    "Zoom": "Communication",
    "Salesforce": "CRM",
    "HubSpot": "Marketing",
    "Atlassian": "Development",
    "Jira": "Development",
    "Canva": "Design",
    "Figma": "Design",
    "Stripe": "Payments",
    "Plaid": "Financial Services",
    "Gusto": "Payroll",
    "Rippling": "Payroll",
    "Microsoft 365": "Productivity",
    "DigitalOcean": "Cloud Infrastructure",
    "Clerk": "Authentication",
    "PostHog": "Analytics",
    "Mixpanel": "Analytics"
}

def detect_saas_vendors(db: Session, company_id: UUID = None) -> List[Dict[str, Any]]:
    """
    Search banking transactions for known SaaS vendors and categorize them.
    
    Returns:
        List of detected SaaS vendors with their total spend.
    """
    from models import BankingTransaction, BankFeed
    
    # Simple keyword-based detection
    # In production, this would use a more sophisticated fuzzy matching or a third-party API
    
    query = db.query(
        BankingTransaction.merchant_name,
        func.sum(BankingTransaction.amount).label("total_spend"),
        func.count(BankingTransaction.id).label("transaction_count")
    )
    
    if company_id:
        query = query.join(BankFeed).filter(BankFeed.company_id == company_id)
    
    results = query.group_by(BankingTransaction.merchant_name).all()
    
    saas_list = []
    for merchant, spend, count in results:
        # Check if merchant is in our known SaaS dictionary
        detected_category = None
        for vendor_key, category in COMMON_SAAS_VENDORS.items():
            if vendor_key.lower() in str(merchant or "").lower():
                detected_category = category
                break
        
        if detected_category:
            saas_list.append({
                "vendor": merchant,
                "category": detected_category,
                "total_spend": float(spend),
                "transaction_count": count
            })
            
    return sorted(saas_list, key=lambda x: x["total_spend"], reverse=True)

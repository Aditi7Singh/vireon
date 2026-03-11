import os
import json
from openai import OpenAI
from typing import List, Dict, Any, Optional, Union
from analytics import metrics, scenarios

class AgentRunner:
    """
    AI Agent responsible for financial analysis and tool orchestration.
    Enhanced to handle more enterprise features like anomalies and budget variance.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_financial_summary",
                    "description": "Get current financial metrics like cash balance, revenue, gross burn, net burn, and runway.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "company_id": {"type": "string", "description": "The UUID of the company"}
                        },
                        "required": ["company_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recent_anomalies",
                    "description": "Fetch recent financial anomalies or unusual spending detected.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "company_id": {"type": "string", "description": "The UUID of the company"},
                            "limit": {"type": "integer", "description": "Max number of anomalies to return", "default": 5}
                        },
                        "required": ["company_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_budget_variance",
                    "description": "Analyze variance between actual spending and budgeted amounts for a specific month.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "company_id": {"type": "string", "description": "The UUID of the company"},
                            "month": {"type": "string", "description": "Month in YYYY-MM-DD format"}
                        },
                        "required": ["company_id", "month"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "simulate_hiring",
                    "description": "Simulate the impact of hiring new employees on the company's financial runway.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "company_id": {"type": "string", "description": "The UUID of the company"},
                            "num_employees": {"type": "integer", "description": "Number of new hires"},
                            "avg_salary": {"type": "number", "description": "Average annual salary per hire"}
                        },
                        "required": ["company_id", "num_employees", "avg_salary"]
                    }
                }
            }
        ]

    async def run_query(self, query: str, context_data: Dict[str, Any]) -> str:
        messages = [
            {"role": "system", "content": """
            You are a professional AI CFO for a company using ERPNext. 
            You have access to real-time financial data, anomalies, and budget analysis.
            Always use provided tools to fetch data. 
            If asked about synchronization, mention that ERPNext webhooks are active for real-time updates.
            """},
            {"role": "user", "content": query}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.get_tools_schema(),
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            messages.append(response_message)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "get_financial_summary":
                    result = context_data.get("summary", {})
                
                elif function_name == "get_recent_anomalies":
                    result = context_data.get("anomalies", [])[:function_args.get("limit", 5)]
                
                elif function_name == "get_budget_variance":
                    # For demo, we use simulated budget data if not provided in context
                    actual = context_data.get("revenue", 0)
                    budget = context_data.get("budgeted_revenue", actual * 0.95) # mock
                    result = metrics.calculate_budget_variance(actual, budget)
                
                elif function_name == "simulate_hiring":
                    result = scenarios.simulate_hiring(
                        current_cash=context_data["cash"],
                        current_revenue=context_data["revenue"],
                        current_gross_burn=context_data["gross_burn"],
                        new_salary_annual=function_args["avg_salary"],
                        count=function_args["num_employees"]
                    )
                else:
                    result = {"error": "Tool not found"}

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(result),
                })
            
            second_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            return second_response.choices[0].message.content

        return response_message.content

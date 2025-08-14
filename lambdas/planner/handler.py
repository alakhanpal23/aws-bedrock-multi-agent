import json
import sys
import os
import uuid
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common.bedrock_client import call_llm

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SYSTEM = """You are an intelligent task planning agent. Given a user goal, decompose it into executable tasks.

Return STRICT JSON with this structure:
{
  "tasks": [
    {
      "id": "unique_task_id",
      "type": "knowledge|data|action",
      "description": "what this task does",
      "inputs": {"key": "value"},
      "deps": ["list_of_dependency_task_ids"]
    }
  ]
}

Task types:
- knowledge: Search documents/knowledge base
- data: Fetch real-time data from APIs
- action: Execute actions, generate recommendations

Create 2-5 tasks that logically accomplish the goal."""

def handler(event, _):
    try:
        goal = event.get("goal", "Analyze current AWS pricing trends")
        logger.info(f"Planning for goal: {goal}")
        
        # Use LLM to generate intelligent plan
        context = {
            "available_data_sources": ["aws_pricing", "hackernews", "aws_blogs", "reddit_aws"],
            "available_actions": ["recommend", "analyze", "compare", "summarize"]
        }
        
        response = call_llm(
            system=SYSTEM,
            context_obj=context,
            user_msg=f"Create a task plan to accomplish: {goal}",
            max_tokens=800
        )
        
        # Parse LLM response
        try:
            plan = json.loads(response)
            
            # Validate and enhance plan
            if "tasks" not in plan:
                raise ValueError("No tasks in plan")
            
            # Add unique IDs if missing
            for i, task in enumerate(plan["tasks"]):
                if "id" not in task:
                    task["id"] = f"task_{uuid.uuid4().hex[:8]}"
                
                # Validate task type
                if task.get("type") not in ["knowledge", "data", "action"]:
                    task["type"] = "knowledge"  # default fallback
            
            logger.info(f"Generated plan with {len(plan['tasks'])} tasks")
            return {"plan": plan}
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response: {response}")
            # Fallback to simple plan
            return generate_fallback_plan(goal)
            
    except Exception as e:
        logger.error(f"Planning error: {str(e)}")
        return generate_fallback_plan(goal)

def generate_fallback_plan(goal):
    """Fallback plan if LLM fails"""
    return {
        "plan": {
            "tasks": [
                {
                    "id": "t1",
                    "type": "knowledge",
                    "description": "Search knowledge base",
                    "inputs": {"query": goal},
                    "deps": []
                },
                {
                    "id": "t2",
                    "type": "data",
                    "description": "Fetch current data",
                    "inputs": {"feeds": ["aws_pricing", "hackernews"]},
                    "deps": ["t1"]
                },
                {
                    "id": "t3",
                    "type": "action",
                    "description": "Generate recommendations",
                    "inputs": {"action": "recommend"},
                    "deps": ["t1", "t2"]
                }
            ]
        }
    }
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import re
import time
from agent import mainLLM
from helper import AsyncHelper  # Changed import
from compressor import Compressor
from browser_use import Agent, BrowserProfile, ChatOllama

app = FastAPI(title="Agentic Surfer API",
              description="Web automation and data extraction API")

# Allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    mode: int  # 0 = single_task, 1 = multi_task
    query: str

class QueryResponse(BaseModel):
    status: str
    message: str
    result: dict | None = None
    error: str | None = None


# ---------- Single Task Agent ----------
class SimpleAgent(AsyncHelper):  # Now inherits from AsyncHelper
    def __init__(self):
        super().__init__()
        self.tools = {
            "search_google_safely": {
                "method": self.search_google_safely,
                "description": "Search Google for a query and return top results."
            },
            "click_result": {
                "method": self.smart_click,
                "description": "Click on a search result by context."
            },
            "extract_data": {
                "method": self.extract_visible_content,
                "description": "Extract visible text from the current page."
            },
            "close_browser": {
                "method": self.close,
                "description": "Close browser and cleanup."
            },
            "get_page_info": {
                "method": self.get_page_info,
                "description": "Get current page URL, title and content preview."
            },
            "save_results": {
                "method": self.save_results,
                "description": "Append results to a local file."
            }
        }

    def get_tools_prompt(self) -> str:
        return "\n".join(
            f"• {name}: {info['description']}"
            for name, info in self.tools.items()
        )

    @staticmethod
    def parse_json(text: str):
        """Extract JSON from an LLM response string."""
        try:
            clean_text = re.sub(r"[^\x00-\x7F]+", "", text)
            match = re.search(r"\{[^{}]*\{[^{}]*\}[^{}]*\}|\{[^{}]*\}", clean_text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"error": "No valid JSON found in response"}
        except json.JSONDecodeError as e:
            return {"error": f"JSON parsing failed: {e}"}
        except Exception as e:
            return {"error": f"Unexpected error: {e}"}


async def run_single_task(query: str) -> dict:
    """Run single task mode."""
    agent = SimpleAgent()
    await agent.setup()
    await agent.clear_cookies_and_cache()
    await agent.rotate_user_agent()
    mainllm = mainLLM()
    try:
        available_tools = agent.get_tools_prompt()
        plan_json = mainllm.get_action_plan(query, available_tools)
        action_plan = agent.parse_json(plan_json)

        if "error" in action_plan:
            return {"error": f"Failed to create action plan: {action_plan['error']}"}

        results = []
        for idx, step in enumerate(action_plan.get("steps", []), start=1):
            print(f"\n{idx}. Executing: {step.get('description', 'Unknown step')}")
            action = step.get("action", "")
            
            if action not in agent.tools:
                print(f"❌ Unknown action: {action}")
                results.append({"index": idx, "error": f"Unknown action: {action}"})
                continue

            method = agent.tools[action]["method"]
            params = {
                k: v for k, v in step.items()
                if k not in {"order", "action", "description", "executed"}
            }

            try:
                # Execute the method and ALWAYS capture the result
                if params:
                    result = await method(**params)
                else:
                    result = await method()
                
                # Always add the result to our tracking list
                results.append({"index": idx, "action": action, "result": result})
                print(f"✅ Step {idx} completed")
                
            except Exception as e:
                print(f"❌ Error in step {idx}: {e}")
                results.append({"index": idx, "action": action, "error": str(e)})

        print("\nAnalyzing final results...")
        final_content = await agent.extract_visible_content()
        
        if not final_content:
            return {"error": "No content extracted", "steps_executed": len(results), "step_results": results}

        # Build results string from ALL steps, not just specific ones
        results_str = "\n".join(
            f"Step {r['index']} ({r.get('action', 'unknown')}): {r.get('result', r.get('error', 'No result'))}" 
            for r in results
        )
        
        final_response = mainllm.extract_final_data(results_str, query)
        
        return {
            "response": final_response, 
            "steps_executed": len(results),
            "detailed_results": results,
            "final_content": final_content
        }

    except Exception as e:
        return {"error": f"Error during execution: {e}"}
    finally:
        await agent.close()
# ---------- Multi Task Agent ----------
async def run_multi_task(query: str) -> dict:
    """Run multi task mode."""
    try:
        llm2 = ChatOllama(model="gpt-oss:20b-cloud")
        browser_profile = BrowserProfile(
            minimum_wait_page_load_time=0.1,
            wait_between_actions=0.1,
            headless=False,
        )
        compressor = Compressor()

        print(f"Original Task: {query}")
        compressed_task = compressor.compress_prompt(query)
        print(f"Compressed Task: {compressed_task}")

        task = query + (
            " results in strict JSON format, no text I just strictly need JSON Outputs,"
            " Use google to check relevance and up to date info"
        )

        agent = Agent(
            task=task,
            llm=llm2,
            flash_mode=True,
            browser_profile=browser_profile,
        )

        history = await agent.run()
        extracted_content = history.extracted_content()
        
        if not extracted_content:
            return {"error": "No content extracted from multi-task agent"}
            
        history = extracted_content[-1]
        
        try:
            return json.loads(history)
        except json.JSONDecodeError:
            return {"raw_response": history}

    except Exception as e:
        return {"error": f"Error in multi-task execution: {e}"}


# ---------- Routes ----------
@app.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """Handle user queries for web automation tasks."""
    try:
        if request.mode == 0:
            result = await run_single_task(request.query)
            if "error" in result:
                return QueryResponse(status="error", message=result["error"])
            return QueryResponse(status="success",
                               message="Single task completed successfully",
                               result=result)
        elif request.mode == 1:
            result = await run_multi_task(request.query)
            if "error" in result:
                return QueryResponse(status="error", message=result["error"])
            return QueryResponse(status="success",
                               message="Multi task completed successfully",
                               result=result)
        else:
            raise HTTPException(status_code=400,
                              detail="Invalid mode. Use 0 for single_task or 1 for multi_task")
    except Exception as e:
        return QueryResponse(status="error",
                           message="An error occurred during processing",
                           error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
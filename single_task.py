import asyncio
import requests
import json
from playwright.sync_api import sync_playwright
import time
import random
from agent import mainLLM
from helper import Helper
import re
class SimpleAgent(Helper):
    def __init__(self):
        super().__init__() 
        self.tools = {
            "search_google_safely": {
                "method": self.search_google_safely,
                "description": "Search Google for a query and return top results takes the target query as input string",
            },
            "click_result": {
                "method": self.smart_click,
                "description": "To click on a search result based on the context provided takes a target as input string",
            },
            "extract_data": {
                "method": self.extract_visible_content,
                "description": "Extract visible text content from the current page and filters out unnecessary content of the raw webpage"
            },
            "close_browser": {
                "method": self.close,
                "description": "Close the browser and cleanup resources"
            },
            "get_page_info": {
                "method": self.get_page_info,
                "description": "Get current page information such as URL, title, and a preview of the content"
            },
            "save_results": {
                "method": self.save_results,
                "description": "Append results to a local file for record-keeping of current context"
            }
        }

    def get_tools_prompt(self):
        tools_text = ""
        for tool_name, tool_info in self.tools.items():
            tools_text += f"• {tool_name}: {tool_info['description']}\n"
        return tools_text
    def parse_json(self, text: str):
        """Extract JSON from LLM response"""
        try:
            clean_text = re.sub(r'[^\x00-\x7F]+', '', text)
            json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"error": "No JSON found in response"}
        except Exception as e:
            return {"error": f"JSON parsing failed: {e}"}
    
def main():
    agent = SimpleAgent()
    agent.clear_cookies_and_cache()
    agent.rotate_user_agent()
    mainllm = mainLLM()
    try:
        while True:
            input_query = input(">>>")
            if input_query.lower() in ["exit", "quit", "q"]:
                print("Thank you for using the agent. Goodbye!")
                break  
            
            available_tools = agent.get_tools_prompt()
            action_plan_json = mainllm.get_action_plan(input_query, available_tools)
            action_plan = agent.parse_json(action_plan_json)
            print("Action Plan:", json.dumps(action_plan, indent=4))
            try:
                results = []
                ind=0
                for i, step in enumerate(action_plan.get("steps", [])):
                    print(f"\n{i+1}. ⚡ Executing: {step.get('description', 'Unknown step')}")
                    
                    action = step.get("action", "")
                    if action in agent.tools:
                        method = agent.tools[action]["method"]
                        params = {k: v for k, v in step.items() if k not in ["order", "action", "description","executed"]}
                        print(f"Executing Step {step['order']}: {action} with params {params}")
                        
                        if action =="extract_data" or action =="get_page_info":
                            result=method()
                            results.append({"index":ind+1,"result": result})
                            ind+=1
                        elif action =="save_results":
                            results.append({"index":ind+1,"result": results})
                            ind+=1
                        else:
                            result = method(**params) if params else method()
                        print(f"✅ Step {i+1} completed")
                        page_content = str(result).lower()
                        if "unusual traffic" in page_content or "blocked" in page_content or "captcha" in page_content:
                            print("\n🚫 We've been blocked! Please solve the CAPTCHA manually.")
                            print("Press Enter to continue after solving...")
                            input()
                    else:
                        print(f"❌ Unknown action: {action}")
                
                print("\n📊 Analyzing final results...")
                final_content = agent.extract_visible_content()

                if not final_content:
                    print("❌ No final content extracted")
                    final_results = {"error": "No content extracted"}
                else:
                    results_str = "\n".join([f"Step {r['index']} : {r['result']}" for r in results])
                    final_response = mainllm.extract_final_data( results_str, input_query)
                    print(final_response)
                
            except Exception as e:
                print(f"❌ Error during execution: {e}")
    except KeyboardInterrupt:
        print("Exiting...")
    finally:    
        agent.close()
if __name__ == "__main__":
    main()
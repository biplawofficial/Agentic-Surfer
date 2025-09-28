import ollama
import re

class mainLLM:
    def __init__(self):
        self.model = "gpt-oss:20b-cloud"
    
    def call_llm(self, prompt: str):
        try:
            response = ollama.generate(model=self.model, prompt=prompt)
            result = response['response']
            return result
        except Exception as e:
            return f"Error: {e}"
    
    def get_action_plan(self, user_input: str, available_tools: str):
        prompt = f"""
        you have access to those tools for web navigation and data extraction from the browser environment:
        {available_tools}
        User wants to: {user_input}
        Create a complete web navigation plan To get the required information from the web. Return ONLY JSON:
        {{
            "goal": "{user_input}",
            "steps": [
                {{  
                    "order": 1,
                    "action": "search_google_safely",
                    "query": "search query",
                    "description": "What to look for in the search results"
                }},
                {{
                    "order": 2,
                    "action": "click_result", 
                    "target": "which result to click",
                    "description": "navigate to specific site"
                }},
                {{
                    "order": 3,
                    "action": "extract_data",
                    "what": "what information to extract",
                    "description": "final data extraction"
                }}
                ... and so on up to 7 steps max.
            ]
        }}
        note:
        -The target in the click_result should be an element that should be available on the page after the search or an element that is likely to be present on the page.
        -make use of save_results action to store intermediate results if needed.
        -You should even go to new page and again search for something else if needed to achieve the goal.
        Keep it to min 3-7 steps max. Be specific about search queries and targets.
        """
        return self.call_llm(prompt)
    
    def extract_final_data(self, content: str, original_goal: str):
        """Final call to extract structured data"""
        prompt = f"""
        - You are an very useful agent that gives humanized and summarised outputs to users based on the contents provided as results.
        - Prompt by user (Original goal): {original_goal}
        - Resutls we have by browsing the web: {content[:1500]}
        - This will be the last output that will be directly given to the user based on the question and the response collected from the web.
          The content in the text format, results should be humanized properly okay 
        - It should be point to point nothing extra needed just what is asked in as short as possible but everythign should be clear 
        - eg : - iphone 12 listed on amazon for price 20,000 INR 
               - Top 5 phones on amazon below 10000 are 
                - samsung m12
                - vivo k20
                -... etc
        - and please summarize it and write in your own ways please filter out unnecessary symbols like phone/moto//% filter those please
         """
        #return 
        return self.call_llm(prompt)
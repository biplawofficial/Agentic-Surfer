import asyncio
import os
import json
from browser_use import Agent, BrowserProfile
from browser_use import ChatOllama
from compressor import Compressor
async def main():
    #llm2=ChatOllama(model='gpt-oss:20b-cloud')
    llm2=ChatOllama(model='llama3.1:8b')
    browser_profile = BrowserProfile(
        minimum_wait_page_load_time=0.1,
        wait_between_actions=0.1,
        headless=False,
    )
    compressor=Compressor()

    while True:
        task=input(">>> ")
        print(f"Compressed Task: {compressor.compress_prompt(task)}")
        task+=(f" results in strict JSON format, no text I just strictly need JSON Outputs, Use google to check relevance and up to date info")
        agent = Agent(
            task=task,
            llm=llm2,
            flash_mode=True,
            browser_profile=browser_profile,
        )
        history = await agent.run()
        history = history.extracted_content()[-1]
        history = json.loads(history)
        print(f"Final result: {history}")
if __name__ == '__main__':
	asyncio.run(main())

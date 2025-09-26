import asyncio
import os
from browser_use import Agent, BrowserProfile
from browser_use import ChatOllama
async def main():
	llm2=ChatOllama(model='gpt-oss:20b-cloud')
	browser_profile = BrowserProfile(
		minimum_wait_page_load_time=0.1,
		wait_between_actions=0.1,
		headless=True,
	)
	while True:
		task=input("Enter your query: ")
		agent = Agent(
			task=task,
			llm=llm2,
			flash_mode=True,
			browser_profile=browser_profile,
		)
		await agent.run()
if __name__ == '__main__':
	asyncio.run(main())

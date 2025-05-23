
#pip install aiohttp
import asyncio
import time

from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

import os

from dotenv import load_dotenv
load_dotenv()

async def main() -> None:
    async with DefaultAzureCredential() as creds:
        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(), conn_str=os.environ["PROJECT_CONNECTION_STRING"]
        )
    
    async with project_client:
            agent = await project_client.agents.create_agent(
                model=os.environ["MODEL_DEPLOYMENT_NAME"], name="my-assistant", instructions="You are helpful assistant"
            )
            print(f"Created agent, agent ID: {agent.id}")

            thread = await project_client.agents.create_thread()
            print(f"Created thread, thread ID: {thread.id}")

            message = await project_client.agents.create_message(
                thread_id=thread.id, role="user", content="Hello, tell me a joke"
            )
            print(f"Created message, message ID: {message.id}")

            run = await project_client.agents.create_run(thread_id=thread.id, agent_id=agent.id)

            # Poll the run as long as run status is queued or in progress
            while run.status in ["queued", "in_progress", "requires_action"]:
                run = await project_client.agents.get_run(thread_id=thread.id, run_id=run.id)

                print(f"Run status: {run.status}")

            print(f"Run completed with status: {run.status}")

            await project_client.agents.delete_agent(agent.id)
            print("Deleted agent")

            messages = await project_client.agents.list_messages(thread_id=thread.id)
            print(f"Messages: {messages}")


if __name__ == "__main__":
    asyncio.run(main())
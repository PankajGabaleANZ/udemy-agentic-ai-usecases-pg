import os, asyncio
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.models import AsyncAgentEventHandler, MessageDeltaChunk, ThreadRun, ThreadMessage, RunStep
from opentelemetry import trace
from dotenv import load_dotenv
import time
load_dotenv()

from azure.monitor.opentelemetry import configure_azure_monitor

scenario = os.path.basename(__file__)
tracer = trace.get_tracer(__name__)

async def main() -> None:

    async with DefaultAzureCredential() as creds:
        project_client = AIProjectClient.from_connection_string(
            credential=creds, conn_str=os.environ["PROJECT_CONNECTION_STRING"]
        )

        # Enable Azure Monitor tracing
        application_insights_connection_string = await project_client.telemetry.get_connection_string()
        if not application_insights_connection_string:
            print("Application Insights was not enabled for this project.")
            print("Enable it via the 'Tracing' tab in your AI Foundry project page.")
            exit()
        configure_azure_monitor(connection_string=application_insights_connection_string)

        # enable additional instrumentations
        project_client.telemetry.enable()

        with tracer.start_as_current_span(scenario):
            async with project_client:
                agent = await project_client.agents.create_agent(
                    model=os.environ["MODEL_DEPLOYMENT_NAME"],
                    name="my-assistant",
                    instructions="You are helpful assistant",
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
                    # Wait for a second
                    time.sleep(1)
                    run = await project_client.agents.get_run(thread_id=thread.id, run_id=run.id)

                    print(f"Run status: {run.status}")

                print(f"Run completed with status: {run.status}")

                await project_client.agents.delete_agent(agent.id)
                print("Deleted agent")

                messages = await project_client.agents.list_messages(thread_id=thread.id)
                print(f"Messages: {messages}")


if __name__ == "__main__":
    asyncio.run(main())
import os
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchTool, CodeInterpreterTool, ToolSet, FunctionTool
from user_functions import user_functions
from azure.identity import DefaultAzureCredential
from pathlib import Path
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
conn_str=os.environ["PROJECT_CONNECTION_STRING"]
model_deployment_name = os.environ["MODEL_DEPLOYMENT_NAME"]
bing_connection_name = os.environ["BING_CONNECTION_NAME"]


project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(), conn_str=conn_str
)

# [START enable_tracing]
from opentelemetry import trace
from azure.monitor.opentelemetry import configure_azure_monitor

# Enable Azure Monitor tracing
application_insights_connection_string = project_client.telemetry.get_connection_string()
if not application_insights_connection_string:
    print("Application Insights was not enabled for this project.")
    print("Enable it via the 'Tracing' tab in your AI Foundry project page.")
    exit()
print(application_insights_connection_string)
configure_azure_monitor(connection_string=application_insights_connection_string)

# enable additional instrumentations
project_client.telemetry.enable()

scenario = os.path.basename(__file__)
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span(scenario):
    with project_client:
        # [END enable_tracing]
        agent = project_client.agents.create_agent(
            model=os.environ["MODEL_DEPLOYMENT_NAME"], name="my-assistant", instructions="You are helpful assistant"
        )
        print(f"Created agent, agent ID: {agent.id}")

        thread = project_client.agents.create_thread()
        print(f"Created thread, thread ID: {thread.id}")

        message = project_client.agents.create_message(
            thread_id=thread.id, role="user", content="Hello, tell me a hilarious joke"
        )
        print(f"Created message, message ID: {message.id}")

        run = project_client.agents.create_run(thread_id=thread.id, agent_id=agent.id)

        # Poll the run as long as run status is queued or in progress
        while run.status in ["queued", "in_progress", "requires_action"]:
            # Wait for a second
            time.sleep(1)
            run = project_client.agents.get_run(thread_id=thread.id, run_id=run.id)

            print(f"Run status: {run.status}")

        project_client.agents.delete_agent(agent.id)
        print("Deleted agent")

        messages = project_client.agents.list_messages(thread_id=thread.id)
        print(f"messages: {messages}")
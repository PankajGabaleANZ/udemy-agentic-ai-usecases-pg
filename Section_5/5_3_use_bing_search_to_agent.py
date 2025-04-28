from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import MessageTextContent, FileSearchTool, BingGroundingTool
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
    credential=DefaultAzureCredential(),
    conn_str=conn_str,
)

bing_connection = project_client.connections.get(connection_name=bing_connection_name)
conn_id = bing_connection.id
bing = BingGroundingTool(connection_id=conn_id)


with project_client:
    # [START create_agent]
    agent = project_client.agents.create_agent(
        model=model_deployment_name,
        name="my-assistant",
        instructions="You are helpful assistant, Only use Bing Connection to answer user questions",
        tools = bing.definitions,
    )
    # [END create_agent]
    print(f"Created agent, agent ID: {agent.id}")

    # [START create_thread]
    thread = project_client.agents.create_thread()
    # [END create_thread]
    print(f"Created thread, thread ID: {thread.id}")

    threads = project_client.agents.list_threads()

    message = project_client.agents.create_message(thread_id=thread.id, role="user", content = "Hi, tell me current weather information in Melbourne")

    print(f"Created message, message ID: {message.id}")

    run = project_client.agents.create_run(thread_id=thread.id, agent_id=agent.id)

    while run.status in ["queued", "in_progress", "requires_action"]:
        # Wait for a second
        time.sleep(1)
        run = project_client.agents.get_run(thread_id=thread.id, run_id=run.id)
        # [END create_run]
        print(f"Run status: {run.status}")
    
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")

    messages = project_client.agents.list_messages(thread_id=thread.id)

    for data_point in reversed(messages.data):
        last_message_content = data_point.content[-1]
        if isinstance(last_message_content, MessageTextContent):
            print(f"{data_point.role}: {last_message_content.text.value}")
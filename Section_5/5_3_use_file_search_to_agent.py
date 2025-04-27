from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import MessageTextContent, FileSearchTool,
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
conn_str=os.environ["PROJECT_CONNECTION_STRING"]
model_deployment_name = os.environ["MODEL_DEPLOYMENT_NAME"]

model_name = "gpt-4o-mini"
endpoint = "https://azureaiagenthu0928310936.openai.azure.com/openai/deployments/gpt-4o-mini"

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=conn_str,
)

with project_client:

    file = project_client.agents.upload_file_and_poll(file_path = "Section_5/files/product_info_1.md", purpose = "assistants")
    print("File uploaded with file id", file.id)

    vector_store = project_client.agents.create_vector_store_and_poll(file_ids=[file.id], name="my_vectorstore")

    file_search = FileSearchTool(vector_store_ids=[vector_store.id])

    # [START create_agent]
    agent = project_client.agents.create_agent(
        model=model_deployment_name,
        name="my-assistant",
        instructions="You are helpful assistant, You answer only from the files provided to you. If no info is present in the files you answer 'DO NOT HAVE THAT INFORMATION'",
        tools = file_search.definitions,
        tool_resources = file_search.resources,
    )
    # [END create_agent]
    print(f"Created agent, agent ID: {agent.id}")

    # [START create_thread]
    thread = project_client.agents.create_thread()
    # [END create_thread]
    print(f"Created thread, thread ID: {thread.id}")

    threads = project_client.agents.list_threads()

    message = project_client.agents.create_message(thread_id=thread.id, role="user", content = "Hi, tell me a information about Smart Eyewear")

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
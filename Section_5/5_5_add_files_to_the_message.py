from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import MessageTextContent, FileSearchTool, BingGroundingTool, FilePurpose
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
with project_client:

    # Upload a file and wait for it to be processed
    file = project_client.agents.upload_file_and_poll(file_path="Section_5/files/product_info_1.md", purpose=FilePurpose.AGENTS)
    print(f"Uploaded file, file ID: {file.id}")

    # Create a vector store with no file and wait for it to be processed
    vector_store = project_client.agents.create_vector_store_and_poll(file_ids=[file.id], name="sample_vector_store")
    print(f"Created vector store, vector store ID: {vector_store.id}")

    # Create a file search tool
    file_search_tool = FileSearchTool(vector_store_ids=[vector_store.id])

    # Notices that FileSearchTool as tool and tool_resources must be added or the assistant unable to search the file
    agent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="my-assistant",
        instructions="You are helpful assistant",
        tools=file_search_tool.definitions,
        tool_resources=file_search_tool.resources,
    )
    print(f"Created agent, agent ID: {agent.id}")

    thread = project_client.agents.create_thread()
    print(f"Created thread, thread ID: {thread.id}")

    message = project_client.agents.create_message(
        thread_id=thread.id, role="user", content="What feature does Smart Eyewear offer?"
    )
    print(f"Created message, message ID: {message.id}")

    run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
    print(f"Created run, run ID: {run.id}")

    project_client.agents.delete_vector_store(vector_store.id)
    print("Deleted vector store")

    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")

    messages = project_client.agents.list_messages(thread_id=thread.id)

    for message in reversed(messages.data):
        # To remove characters, which are not correctly handled by print, we will encode the message
        # and then decode it again.
        clean_message = "\n".join(
            text_msg.text.value.encode("ascii", "ignore").decode("utf-8") for text_msg in message.text_messages
        )
        print(f"Role: {message.role}  Message: {clean_message}")
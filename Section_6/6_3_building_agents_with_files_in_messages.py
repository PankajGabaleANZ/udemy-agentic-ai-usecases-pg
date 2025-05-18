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

with project_client:

    # Upload file and create vector store
    # [START create_agent_and_thread_for_file_search]
    file = project_client.agents.upload_file_and_poll(file_path="Section_5/files/product_info_1.md", purpose="assistants")
    print(f"Uploaded file, file ID: {file.id}")
    
    vector_store = project_client.agents.create_vector_store_and_poll(file_ids=[file.id], name="my_vectorstore")
    print(f"Created vector store, vector store ID: {vector_store.id}")

    # Create file search tool with resources followed by creating agent
    file_search = FileSearchTool(vector_store_ids=[vector_store.id])

    functions = FunctionTool(user_functions)
    code_interpreter = CodeInterpreterTool()

    toolset = ToolSet()
    toolset.add(functions)
    toolset.add(code_interpreter)

    agent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="my-assistant",
        instructions="Hello, you are helpful assistant and can search information from uploaded files. Create a summary file by using the create_text_file_from_string tools from the functions by supplying string values as input",
        tools=file_search.definitions,
        toolset=toolset,
    )

    print(f"Created agent, ID: {agent.id}")

    # Create thread with file resources.
    # If the agent has multiple threads, only this thread can search this file.
    thread = project_client.agents.create_thread(tool_resources=file_search.resources)
    # [END create_agent_and_thread_for_file_search]
    print(f"Created thread, ID: {thread.id}")

    # Create message to thread
    message = project_client.agents.create_message(
        thread_id=thread.id, role="user", content="Hello, what Contoso products do you know? Create a summary document with answer of this questions"
    )
    print(f"Created message, ID: {message.id}")
    time.sleep(5)
    # Create and process assistant run in thread with tools
    run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
    print(f"Run finished with status: {run.status}")
    time.sleep(5)
    if run.status == "failed":
        # Check if you got "Rate limit is exceeded.", then you want to get more quota
        print(f"Run failed: {run.last_error}")
    time.sleep(3)
    # [START teardown]
    # Delete the file when done
    project_client.agents.delete_vector_store(vector_store.id)
    print("Deleted vector store")

    project_client.agents.delete_file(file_id=file.id)
    print("Deleted file")

    # Delete the agent when done
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")
    # [END teardown]

    # Fetch and log all messages
    messages = project_client.agents.list_messages(thread_id=thread.id)
    print(f"Messages: {messages}")
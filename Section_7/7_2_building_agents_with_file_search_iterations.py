import os
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchTool, AgentStreamEvent, MessageDeltaChunk, RunStep, RunStepDeltaChunk, ThreadMessage, ThreadRun, MessageRole, BingGroundingTool, MessageDeltaTextContent, MessageDeltaTextUrlCitationAnnotation
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
    # [START upload_file_create_vector_store_and_agent_with_file_search_tool]
    file = project_client.agents.upload_file_and_poll(file_path="Section_7/files/product_info_1.md", purpose="assistants")
    print(f"Uploaded file, file ID: {file.id}")

    vector_store = project_client.agents.create_vector_store_and_poll(file_ids=[file.id], name="my_vectorstore")
    print(f"Created vector store, vector store ID: {vector_store.id}")

    # Create file search tool with resources followed by creating agent
    file_search = FileSearchTool(vector_store_ids=[vector_store.id])

    agent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="my-assistant",
        instructions="Hello, you are helpful assistant and can search information from uploaded files",
        tools=file_search.definitions,
        tool_resources=file_search.resources,
    )
    print(f"Created agent, agent ID: {agent.id}")

    thread = project_client.agents.create_thread()
    print(f"Created thread, thread ID {thread.id}")

    message = project_client.agents.create_message(
        thread_id=thread.id, role="user", content="What feature does Smart Eyewear offer?"
    )
    print(f"Created message, message ID {message.id}")

    with project_client.agents.create_stream(thread_id=thread.id, agent_id=agent.id) as stream:

        for event_type, event_data, _ in stream:

            if isinstance(event_data, MessageDeltaChunk):
                print(f"Text delta received: {event_data.text}")

            elif isinstance(event_data, RunStepDeltaChunk):
                print(f"RunStepDeltaChunk received. ID: {event_data.id}.")

            elif isinstance(event_data, ThreadMessage):
                print(f"ThreadMessage created. ID: {event_data.id}, Status: {event_data.status}")
                for annotation in event_data.file_citation_annotations:
                    print(
                        f"Citation {annotation.text} from file ID: {annotation.file_citation.file_id}, start index: {annotation.start_index}, end index: {annotation.end_index}"
                    )

            elif isinstance(event_data, ThreadRun):
                print(f"ThreadRun status: {event_data.status}")

                if event_data.status == "failed":
                    print(f"Run failed. Error: {event_data.last_error}")

            elif isinstance(event_data, RunStep):
                print(f"RunStep type: {event_data.type}, Status: {event_data.status}")

            elif event_type == AgentStreamEvent.ERROR:
                print(f"An error occurred. Data: {event_data}")

            elif event_type == AgentStreamEvent.DONE:
                print("Stream completed.")

            else:
                print(f"Unhandled Event Type: {event_type}, Data: {event_data}")

    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")

    response_message = project_client.agents.list_messages(thread_id=thread.id)
    print(f"Messages: {response_message}")
    
    if response_message:
        for text_message in response_message.text_messages:
            print(f"Agent response: {text_message.text.value}")
        for annotation in response_message.file_citation_annotations:
            print(f"File Citation: [{annotation.file_citation.file_id}]")
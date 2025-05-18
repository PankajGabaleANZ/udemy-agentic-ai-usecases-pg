import os
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentStreamEvent, MessageDeltaChunk, RunStep, RunStepDeltaChunk, ThreadMessage, ThreadRun, MessageRole, BingGroundingTool, MessageDeltaTextContent, MessageDeltaTextUrlCitationAnnotation
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
    bing_connection = project_client.connections.get(connection_name=bing_connection_name)
    bing = BingGroundingTool(connection_id=bing_connection.id)
    print(f"Bing Connection ID: {bing_connection.id}")

    agent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="my-assistant",
        instructions="You are a helpful assistant",
        tools=bing.definitions,
    )
    print(f"Created agent, agent ID: {agent.id}")

    thread = project_client.agents.create_thread()
    print(f"Created thread, thread ID {thread.id}")

    message = project_client.agents.create_message(
        thread_id=thread.id, role=MessageRole.USER, content="How does wikipedia explain Euler's Identity?"
    )
    print(f"Created message, message ID {message.id}")

    with project_client.agents.create_stream(thread_id=thread.id, agent_id=agent.id) as stream:

        for event_type, event_data, _ in stream:

            if isinstance(event_data, MessageDeltaChunk):
                print(f"Text delta received: {event_data.text}")
                if event_data.delta.content and isinstance(event_data.delta.content[0], MessageDeltaTextContent):
                    delta_text_content = event_data.delta.content[0]
                    if delta_text_content.text and delta_text_content.text.annotations:
                        for delta_annotation in delta_text_content.text.annotations:
                            if isinstance(delta_annotation, MessageDeltaTextUrlCitationAnnotation):
                                print(
                                    f"URL citation delta received: [{delta_annotation.url_citation.title}]({delta_annotation.url_citation.url})"
                                )

            elif isinstance(event_data, RunStepDeltaChunk):
                print(f"RunStepDeltaChunk received. ID: {event_data.id}.")

            elif isinstance(event_data, ThreadMessage):
                print(f"ThreadMessage created. ID: {event_data.id}, Status: {event_data.status}")

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

    response_message = project_client.agents.list_messages(thread_id=thread.id).get_last_message_by_role(
        MessageRole.AGENT
    )
    if response_message:
        for text_message in response_message.text_messages:
            print(f"Agent response: {text_message.text.value}")
        for annotation in response_message.url_citation_annotations:
            print(f"URL Citation: [{annotation.url_citation.title}]({annotation.url_citation.url})")
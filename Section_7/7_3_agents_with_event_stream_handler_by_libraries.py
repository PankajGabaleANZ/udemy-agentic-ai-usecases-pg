import os
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentEventHandler, MessageDeltaChunk, RunStep, RunStepDeltaChunk, ThreadMessage, ThreadRun, MessageRole, BingGroundingTool, MessageDeltaTextContent, MessageDeltaTextUrlCitationAnnotation
from user_functions import user_functions
from azure.identity import DefaultAzureCredential
from pathlib import Path
from dotenv import load_dotenv
import os
import time

from typing import Any, Optional

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
conn_str=os.environ["PROJECT_CONNECTION_STRING"]
model_deployment_name = os.environ["MODEL_DEPLOYMENT_NAME"]
bing_connection_name = os.environ["BING_CONNECTION_NAME"]

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(), conn_str=conn_str
)

class MyEventHandler(AgentEventHandler[str]):

    def on_message_delta(self, delta: "MessageDeltaChunk") -> Optional[str]:
        return f"Text delta received: {delta.text}"

    def on_thread_message(self, message: "ThreadMessage") -> Optional[str]:
        return f"ThreadMessage created. ID: {message.id}, Status: {message.status}"

    def on_thread_run(self, run: "ThreadRun") -> Optional[str]:
        return f"ThreadRun status: {run.status}"

    def on_run_step(self, step: "RunStep") -> Optional[str]:
        return f"RunStep type: {step.type}, Status: {step.status}"

    def on_error(self, data: str) -> Optional[str]:
        return f"An error occurred. Data: {data}"

    def on_done(self) -> Optional[str]:
        return "Stream completed."

    def on_unhandled_event(self, event_type: str, event_data: Any) -> Optional[str]:
        return f"Unhandled Event Type: {event_type}, Data: {event_data}"


# [END stream_event_handler]


with project_client:
    # Create an agent and run stream with event handler
    agent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"], name="my-assistant", instructions="You are a helpful assistant"
    )
    print(f"Created agent, agent ID {agent.id}")

    thread = project_client.agents.create_thread()
    print(f"Created thread, thread ID {thread.id}")

    message = project_client.agents.create_message(thread_id=thread.id, role="user", content="Hello, tell me a joke")
    print(f"Created message, message ID {message.id}")

    # [START create_stream]
    with project_client.agents.create_stream(
        thread_id=thread.id, agent_id=agent.id, event_handler=MyEventHandler()
    ) as stream:
        for event_type, event_data, func_return in stream:
            print(f"Received data.")
            print(f"Streaming receive Event Type: {event_type}")
            print(f"Event Data: {str(event_data)[:100]}...")
            print(f"Event Function return: {func_return}\n")
    # [END create_stream]

    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")

    messages = project_client.agents.list_messages(thread_id=thread.id)
    print(f"Messages: {messages}")
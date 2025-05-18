import os
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool, ToolSet, AgentEventHandler, BaseAgentEventHandler, AgentStreamEvent, MessageDeltaChunk, RunStep, RunStepDeltaChunk, ThreadMessage, ThreadRun, MessageRole, FileSearchTool, MessageDeltaTextContent, MessageDeltaTextUrlCitationAnnotation
from user_functions import user_functions
from azure.identity import DefaultAzureCredential
from pathlib import Path
from dotenv import load_dotenv
import os
import time
import json
from typing import Optional, Any, Generator

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
conn_str=os.environ["PROJECT_CONNECTION_STRING"]
model_deployment_name = os.environ["MODEL_DEPLOYMENT_NAME"]
bing_connection_name = os.environ["BING_CONNECTION_NAME"]

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(), conn_str=conn_str
)

class MyEventHandler(BaseAgentEventHandler[Optional[str]]):

    def _process_event(self, event_data_str: str) -> Optional[str]:  # type: ignore[return]
        event_lines = event_data_str.strip().split("\n")
        event_type: Optional[str] = None
        event_data = ""
        for line in event_lines:
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                event_data = line.split(":", 1)[1].strip()

        if not event_type:
            raise ValueError("Event type not specified in the event data.")

        if event_type == AgentStreamEvent.THREAD_MESSAGE_DELTA.value:

            event_obj: MessageDeltaChunk = MessageDeltaChunk(**json.loads(event_data))

            for content_part in event_obj.delta.content:
                if isinstance(content_part, MessageDeltaTextContent):
                    if content_part.text is not None:
                        return content_part.text.value
        return None

    def get_stream_chunks(self) -> Generator[str, None, None]:
        for chunk in self:
            if chunk:
                yield chunk


project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(), conn_str=os.environ["PROJECT_CONNECTION_STRING"]
)

with project_client:
    agent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"], name="my-assistant", instructions="You are helpful assistant"
    )
    print(f"Created agent, agent ID: {agent.id}")

    thread = project_client.agents.create_thread()
    print(f"Created thread, thread ID {thread.id}")

    message = project_client.agents.create_message(thread_id=thread.id, role="user", content="Hello, tell me a joke")
    print(f"Created message, message ID {message.id}")

    with project_client.agents.create_stream(
        thread_id=thread.id, agent_id=agent.id, event_handler=MyEventHandler()
    ) as stream:
        for chunk in stream.get_stream_chunks():
            print(chunk)

    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")

    messages = project_client.agents.list_messages(thread_id=thread.id)
    print(f"Messages: {messages}")
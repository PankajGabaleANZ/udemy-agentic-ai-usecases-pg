from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import AzureAISearchQueryType, AzureAISearchTool, ListSortOrder, MessageRole
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
conn_str=os.environ["PROJECT_CONNECTION_STRING"]
model_deployment_name = os.environ["MODEL_DEPLOYMENT_NAME"]
bing_connection_name = os.environ["BING_CONNECTION_NAME"]
AI_SEARCH_CONNECTION_NAME = os.environ["AI_SEARCH_CONNECTION_NAME"]

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(), conn_str=conn_str
)

# [START create_agent_with_azure_ai_search_tool]
connection = project_client.connections.get(connection_name=os.environ["AI_SEARCH_CONNECTION_NAME"])
conn_id = connection.id

print(conn_id)

# Initialize agent AI search tool and add the search index connection id
ai_search = AzureAISearchTool(
    index_connection_id=conn_id, index_name="sample_index", query_type=AzureAISearchQueryType.SIMPLE, top_k=3, filter=""
)

with project_client:
    agent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="my-assistant",
        instructions="You are a helpful assistant",
        tools=ai_search.definitions,
        tool_resources=ai_search.resources,
    )
    # [END create_agent_with_azure_ai_search_tool]
    print(f"Created agent, ID: {agent.id}")

    # Create thread for communication
    thread = project_client.agents.create_thread()
    print(f"Created thread, ID: {thread.id}")

    # Create message to thread
    message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content="What is the temperature rating of the cozynights sleeping bag?",
    )
    print(f"Created message, ID: {message.id}")

    # Create and process agent run in thread with tools
    run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
    print(f"Run finished with status: {run.status}")

    if run.status == "failed":
        print(f"Run failed: {run.last_error}")

    # Fetch run steps to get the details of the agent run
    run_steps = project_client.agents.list_run_steps(thread_id=thread.id, run_id=run.id)
    for step in run_steps.data:
        print(f"Step {step['id']} status: {step['status']}")
        step_details = step.get("step_details", {})
        tool_calls = step_details.get("tool_calls", [])

        if tool_calls:
            print("  Tool calls:")
            for call in tool_calls:
                print(f"    Tool Call ID: {call.get('id')}")
                print(f"    Type: {call.get('type')}")

                azure_ai_search_details = call.get("azure_ai_search", {})
                if azure_ai_search_details:
                    print(f"    azure_ai_search input: {azure_ai_search_details.get('input')}")
                    print(f"    azure_ai_search output: {azure_ai_search_details.get('output')}")
        print()  # add an extra newline between steps

    # Delete the assistant when done
    #project_client.agents.delete_agent(agent.id)
    print("Deleted agent")

    # [START populate_references_agent_with_azure_ai_search_tool]
    # Fetch and log all messages
    messages = project_client.agents.list_messages(thread_id=thread.id, order=ListSortOrder.ASCENDING)
    for message in messages.data:
        if message.role == MessageRole.AGENT and message.url_citation_annotations:
            placeholder_annotations = {
                annotation.text: f" [see {annotation.url_citation.title}] ({annotation.url_citation.url})"
                for annotation in message.url_citation_annotations
            }
            for message_text in message.text_messages:
                message_str = message_text.text.value
                for k, v in placeholder_annotations.items():
                    message_str = message_str.replace(k, v)
                print(f"{message.role}: {message_str}")
        else:
            for message_text in message.text_messages:
                print(f"{message.role}: {message_text.text.value}")
    # [END populate_references_agent_with_azure_ai_search_tool]
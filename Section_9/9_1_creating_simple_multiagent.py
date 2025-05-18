# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    This sample demonstrates how to use multiple agents using AgentTeam with traces.

USAGE:
    python sample_agents_agent_team.py

    Before running the sample:

    pip install azure-ai-projects azure-identity

    Set these environment variables with your own values:
    PROJECT_CONNECTION_STRING - the Azure AI Project connection string, as found in your AI Foundry project.
    MODEL_DEPLOYMENT_NAME - the name of the model deployment to use.
"""

import os
import asyncio
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
load_dotenv()
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

#pip install azure-identity
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")

API_KEY = os.getenv("API_KEY")
PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
BING_CONNECTION_NAME = os.getenv("BING_CONNECTION_NAME")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
API_VERSION = os.getenv("MODEL_API_VERSION")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")

az_model_client = AzureOpenAIChatCompletionClient(
    azure_deployment=MODEL_DEPLOYMENT_NAME,
    model=MODEL_DEPLOYMENT_NAME,
    api_version=API_VERSION,
    azure_endpoint=AZURE_ENDPOINT,
    api_key=API_KEY
)


project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=PROJECT_CONNECTION_STRING,
)


async def web_ai_agent(query: str) -> str:
    # with project_client:
    agent = project_client.agents.create_agent(
            model=os.getenv("MODEL_DEPLOYMENT_NAME"),
            name="my-assistant",
            instructions="""        
                You are a summary tool. Based on the user question you attempt to best summarize and expand user topic with facts and statistics known to you.
                Once you have the results, you never do calculations based on them.
            """,
            headers={"x-ms-enable-preview": "true"}
        )
    print(f"Created agent, ID: {agent.id}")

    # Create thread for communication
    thread = project_client.agents.create_thread()
    print(f"Created thread, ID: {thread.id}")

    # Create message to thread
    message = project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=query,
    )
    print(f"SMS: {message}")
        # Create and process agent run in thread with tools
    run = project_client.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent.id)
    print(f"Run finished with status: {run.status}")

    if run.status == "failed":
        print(f"Run failed: {run.last_error}")

        # Delete the assistant when done
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")

        # Fetch and log all messages
    messages = project_client.agents.list_messages(thread_id=thread.id)
    print("Messages:"+ messages["data"][0]["content"][0]["text"]["value"])

        # project_client.close()

    return messages["data"][0]["content"][0]["text"]["value"]


async def save_blog_agent(blog_content: str) -> str:

    agent = project_client.agents.create_agent(
            model=os.getenv("MODEL_DEPLOYMENT_NAME"),
            name="my-agent",
            instructions="You are helpful agent",
    )

    thread = project_client.agents.create_thread()

    message = project_client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content="""
        
                    You are my Python programming assistant. Generate code,save """+ blog_content +
                    
                """    
                    and execute it according to the following requirements

                    1. Save blog content to blog-{YYMMDDHHMMSS}.md

                    2. give me the download this file link
                """,
    )
    # create and execute a run
    run = project_client.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent.id)
    print(f"Run finished with status: {run.status}")

    if run.status == "failed":
            # Check if you got "Rate limit is exceeded.", then you want to get more quota
        print(f"Run failed: {run.last_error}")

    messages = project_client.agents.get_messages(thread_id=thread.id)
    print(f"Messages: {messages}")
        
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")

    return "Saved"

async def main():
    summary_search_agent = AssistantAgent(
        name="summary_search_agent",
        model_client=az_model_client,
        tools=[web_ai_agent],
        system_message="You are a summary expert, help me use tools to find relevant knowledge",
    )

    save_blog_content_agent = AssistantAgent(
        name="save_blog_content_agent",
        model_client=az_model_client,
        tools=[save_blog_agent],
        system_message="""Save blog content. Respond with 'Saved' to when your blogs are saved."""
    )

    write_agent = AssistantAgent(
        name="write_agent",
        model_client=az_model_client,
        system_message="""You are a blog writer, please help me write a blog based on bing search content."""
    )

    termination = TextMentionTermination("Saved") | MaxMessageTermination(10)

    reflection_team = RoundRobinGroupChat(
        [summary_search_agent, write_agent, save_blog_content_agent],
        termination_condition=termination
    )

    # ✅ Await the run_stream
    async for output in reflection_team.run_stream(task="""
        I am writing a blog about machine learning. Write a Hindi blog based on the search results and save it.
        1. What is Machine Learning?
        2. The difference between AI and ML
        3. The history of Machine Learning
    """):
        print(output)

# ✅ Use asyncio to run
if __name__ == "__main__":
    asyncio.run(main())
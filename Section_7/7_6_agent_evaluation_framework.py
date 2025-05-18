import os
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool, ToolSet, CodeInterpreterTool
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



with project_client:
    # Initialize agent toolset with user functions and code interpreter
    # [START create_agent_toolset]
    functions = FunctionTool(user_functions)
    code_interpreter = CodeInterpreterTool()

    toolset = ToolSet()
    toolset.add(functions)
    toolset.add(code_interpreter)

    # To enable tool calls executed automatically
    project_client.agents.enable_auto_function_calls(toolset=toolset)

    agent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="my-assistant",
        instructions="You are a helpful assistant",
        toolset=toolset,
    )
    # [END create_agent_toolset]
    print(f"Created agent, ID: {agent.id}")

    # Create thread for communication
    thread = project_client.agents.create_thread()
    print(f"Created thread, ID: {thread.id}")

    # Create message to thread
    message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content="Hello, send an email with the datetime and weather information in New York?",
    )
    print(f"Created message, ID: {message.id}")

    # Create and process agent run in thread with tools
    # [START create_and_process_run]
    run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
    # [END create_and_process_run]
    print(f"Run finished with status: {run.status}")

    if run.status == "failed":
        print(f"Run failed: {run.last_error}")

    # Fetch and log all messages
    messages = project_client.agents.list_messages(thread_id=thread.id)

    for message in project_client.agents.list_messages(thread.id, order="asc").data:
        print(f"Role: {message.role}")
        print(f"Content: {message.content[0].text.value}")
        print("-" * 40)


    import json, os
    from azure.ai.evaluation import AIAgentConverter, IntentResolutionEvaluator, TaskAdherenceEvaluator, ToolCallAccuracyEvaluator
    from azure.ai.projects.models import ConnectionType
    
    # Initialize the converter for Azure AI agents
    converter = AIAgentConverter(project_client)

    # Specify the thread and run id
    thread_id = thread.id
    run_id = run.id

    converted_data = converter.convert(thread_id, run_id)



    model_config = project_client.connections.get_default(
                                                connection_type=ConnectionType.AZURE_OPEN_AI,
                                                include_credentials=True) \
                                                .to_evaluator_model_config(
                                                deployment_name="gpt-4o",
                                                api_version="2023-05-15",
                                                include_credentials=True
                                            )

        # Specify a file path to save agent output (which is evaluation input data)
    filename = os.path.join(os.getcwd(), "evaluation_input_data.jsonl")

    evaluation_data = converter.prepare_evaluation_data(thread_ids=thread_id, filename=filename) 

    print(f"Evaluation data saved to {filename}")
    for evaluator in [IntentResolutionEvaluator, TaskAdherenceEvaluator, ToolCallAccuracyEvaluator]:
        evaluator = evaluator(model_config)
        try:
            result = evaluator(**converted_data)
            print(json.dumps(result, indent=4)) 
        except:
            print("Note: if there is no tool call to evaluate in the run history, ToolCallAccuracyEvaluator will raise an error")
            pass
    
    # Select evaluators of your choice
    intent_resolution = IntentResolutionEvaluator(model_config=model_config)
    task_adherence = TaskAdherenceEvaluator(model_config=model_config)
    tool_call_accuracy = ToolCallAccuracyEvaluator(model_config=model_config)

    # Batch evaluation API (local)
    from azure.ai.evaluation import evaluate

    response = evaluate(
        data=filename,
        evaluation_name="agent demo - batch run",
        evaluators={
            "intent_resolution": intent_resolution,
            "task_adherence": task_adherence,
            "tool_call_accuracy": tool_call_accuracy,
        },
        # optionally, log your results to your Azure AI Foundry project for rich visualization 
        azure_ai_project={
            "subscription_id": os.environ["AZURE_SUBSCRIPTION_ID"],
            "project_name": os.environ["PROJECT_NAME"],
            "resource_group_name": os.environ["RESOURCE_GROUP_NAME"],
        }
    )
    # Inspect the average scores at a high-level
    print(response["metrics"])
    # Use the URL to inspect the results on the UI
    print(f'AI Foundary URL: {response.get("studio_url")}')
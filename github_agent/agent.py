import uuid

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from dotenv import load_dotenv
from google.genai import types
from google.adk.models.google_llm import Gemini

from google.adk.models.lite_llm import LiteLlm

from github_agent.system_prompts import issue_reader_agent_prompt, orchestrator_agent_prompt, repo_navigator_agent_prompt, code_fix_agent_prompt, summary_agent_prompt
from github_agent.functions import call_agent
from github_agent.tools import github_mcp, get_github_owner
from github_agent.schemas import IssueReaderAgentOutput, RepoNavigatorAgentOutput, CodeFixAgentOutput

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest


import httpx
import os
import asyncio

load_dotenv()

github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")


APP_NAME = "GitHub Agent"
USER_ID = "agent_user"

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

model = Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config)

# model = LiteLlm(
#     model="openrouter/z-ai/glm-4.5-air:free",
#     api_key=openrouter_api_key
# )


# def repo_nav_before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest):
#     """
#     Validates that the 'issue' state variable exists before proceeding.
#     If missing, raises an error to halt agent execution.
#     """
#     print("Repo navigator agent before model callback")
#     print(f"Session state: {callback_context.session.state}")

#     if 'issue' not in callback_context.session.state:
#         error_message = (
#             "Error: Missing required context variable 'issue'. "
#             "The Issue Reader Agent must complete successfully before the Repo Navigator Agent can proceed. "
#             "Ensure the issue data is populated in session state with output_key='issue'."
#         )
#         print(f"❌ {error_message}")
#         raise ValueError(error_message)


# Issue Reader Agent
issue_reader_agent = LlmAgent(
    model=model,
    name="issue_reader_agent",
    instruction=issue_reader_agent_prompt,
    tools=[github_mcp],
    # output_schema=IssueReaderAgentOutput,
    output_key="issue"
)

# Repo Navigator Agent
repo_navigator_agent = LlmAgent(
    model=model,
    name="repo_navigator_agent",
    instruction=repo_navigator_agent_prompt,
    tools=[github_mcp],
    # input_schema=IssueReaderAgentOutput,
    # output_schema=RepoNavigatorAgentOutput,
    output_key="repo_navigation",
)


code_fix_agent = LlmAgent(
    model=model,
    name="code_fix_agent",
    instruction=code_fix_agent_prompt,
    tools=[github_mcp],
    # output_schema=CodeFixAgentOutput,
    output_key="code_fix"
)
summary_agent = LlmAgent(
    model=model,
    name="summary_agent_agent",
    instruction=summary_agent_prompt,
    tools=[github_mcp],
    output_key="summary",
)


chain_agent = SequentialAgent(
    name="chain_agent",
    description="Chain of agents",
    sub_agents=[issue_reader_agent, repo_navigator_agent, code_fix_agent,summary_agent],
)

# Orchestrator Agent
orchestrator_agent = LlmAgent(
    model=model,
    name="orchestrator_agent",
    instruction=orchestrator_agent_prompt,
    tools=[get_github_owner],
    sub_agents=[chain_agent],
    output_key="response"
)

service = InMemorySessionService()
root_agent = orchestrator_agent


async def fetch_github_owner() -> str:
    """Fetch GitHub username from API (for initial session setup)"""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {github_token}"}
        )
        r.raise_for_status()
        user = r.json()["login"]
        return user


async def run_session():
    result = await service.list_sessions(app_name=APP_NAME, user_id=USER_ID)

    if result.sessions:
        session_id = result.sessions[0].id
        session = await service.get_session(
            session_id=session_id,
            app_name=APP_NAME,
            user_id=USER_ID
        )
    else:
        session_id = str(uuid.uuid4())
        github_user = await fetch_github_owner()

        await service.create_session(
            session_id=session_id,
            app_name=APP_NAME,
            user_id=USER_ID,
            state={"github_user": github_user},
        )

        await service.get_session(
            session_id=session_id,
            app_name=APP_NAME,
            user_id=USER_ID
        )
        print(f"✓ GitHub user initialized: {github_user}")

    runner = Runner(
        agent=root_agent,
        session_service=service,
        app_name=APP_NAME,
    )

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break

        await call_agent(
            runner=runner,
            session_id=session_id,
            user_id=USER_ID,
            query=user_input,
        )


if __name__ == "__main__":
    asyncio.run(run_session())

# I have some error in my repo Agent-Testing-Capstone-GenAI.. Please use appropriate tools and check the error

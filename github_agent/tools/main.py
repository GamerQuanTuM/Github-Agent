import os
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
import httpx
from dotenv import load_dotenv
from google.adk.tools.tool_context import ToolContext


load_dotenv()

# Get your GitHub PAT from environment
github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
if not github_token:
    raise ValueError("Set GITHUB_PERSONAL_ACCESS_TOKEN in env")


# Create MCPToolset for GitHub MCP server
github_mcp = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://api.githubcopilot.com/mcp/",
        headers={
            "Authorization": f"Bearer {github_token}"
        }
    ),
    tool_filter=[
        "search_repositories",
        "get_file_contents",
        "list_commits",
        "get_commit",
        "create_or_update_file",
        "create_branch",
        "delete_file",
        "list_issues",
        "list_pull_requests",
        "create_pull_request",
        "update_pull_request",
        "get_me"
    ]
)


async def get_github_owner(tool_context: ToolContext) -> str:
    """Fetch GitHub username from API"""

    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {github_token}"}
        )

        r.raise_for_status()
        user = r.json()["login"]

    # Update session state only when called as a tool
    if tool_context is not None:
        tool_context.state["github_user"] = user

    return user

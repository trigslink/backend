import requests
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_community.chat_models import ChatOpenAI


def load_tool_from_mcp(mcp_metadata_url: str, env_vars: dict):
    try:
        response = requests.get(mcp_metadata_url, timeout=5)
        response.raise_for_status()
        metadata = response.json()
    except Exception as e:
        raise ValueError(f"❌ Failed to fetch MCP metadata from {mcp_metadata_url}: {e}")

    def dynamic_func(input: str):
        payload = {"input": input, **env_vars}
        try:
            res = requests.post(metadata["endpoint"], json=payload, timeout=10)
            res.raise_for_status()
            return res.json().get("output", "No response from MCP.")
        except Exception as e:
            return f"❌ MCP Error: {str(e)}"

    return Tool.from_function(
        name=metadata.get("name", "MCP Tool"),
        description=metadata.get("description", "Interact with MCP using natural language."),
        func=dynamic_func,
    )


def run_agent_with_tool(openai_api_key: str, user_prompt: str, mcp_metadata_url: str, env_vars: dict, openai_model: str = "gpt-4o"):
    try:
        tool = load_tool_from_mcp(mcp_metadata_url, env_vars)
        llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0.3, model=openai_model)
        agent = initialize_agent([tool], llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
        return agent.run(user_prompt)
    except Exception as e:
        return f"❌ Agent Error: {str(e)}"
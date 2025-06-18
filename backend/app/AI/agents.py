import requests
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_community.chat_models import ChatOpenAI

def load_tool_from_mcp(mcp_metadata_url: str, env_vars: dict):
    metadata = requests.get(mcp_metadata_url).json()

    def dynamic_func(input: str):
        payload = {"input": input, **env_vars}
        response = requests.post(metadata["endpoint"], json=payload)
        return response.json().get("output", "No response")

    return Tool.from_function(
        name=metadata["name"],
        description=metadata.get("description", "MCP Tool"),
        func=dynamic_func,
    )

def run_agent_with_tool(openai_api_key, user_prompt, mcp_metadata_url, env_vars):
    tool = load_tool_from_mcp(mcp_metadata_url, env_vars)
    llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0)
    agent = initialize_agent([tool], llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION)
    return agent.run(user_prompt)
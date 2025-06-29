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
        raise ValueError(f"❌ Failed to fetch MCP metadata: {e}")

    def dynamic_func(user_input: str):
        # ✅ Extract wallet and chain from user input
        parts = user_input.strip().split()
        wallet = next((p for p in parts if p.lower().startswith("0x")), None)
        chain = next(
            (p.lower() for p in parts if p.lower() in ["ethereum", "avalanche", "arbitrum", "optimism", "base", "solana"]),
            None
        )

        # ✅ Build payload
        if wallet and chain:
            payload = {
                "wallet": wallet,
                "chain": chain
            }
        else:
            payload = {
                "input": user_input
            }

        # ✅ No headers needed (pass API keys in body)
        payload["openai_api_key"] = env_vars.get("OPENAI_API_KEY")
        payload["model"] = env_vars.get("MODEL", "gpt-4o")

        try:
            print(f"🔗 MCP Endpoint: {metadata['endpoint']}")
            print(f"📦 Payload Sent: {payload}")

            res = requests.post(metadata["endpoint"], json=payload, timeout=60)
            res.raise_for_status()
            return res.json().get("output", "❌ No response from MCP.")
        except Exception as e:
            return f"❌ MCP Error: {str(e)}"

    return Tool.from_function(
        name=metadata.get("service_name", "MCP Tool"),
        description=metadata.get("description", "Interact with MCP."),
        func=dynamic_func,
    )


def run_agent_with_tool(
    openai_api_key: str,
    user_prompt: str,
    mcp_metadata_url: str,
    env_vars: dict,
    openai_model: str = "gpt-4o"
):
    try:
        tool = load_tool_from_mcp(mcp_metadata_url, env_vars)
        llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0.3, model=openai_model)
        agent = initialize_agent([tool], llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
        return agent.run(user_prompt)
    except Exception as e:
        return f"❌ Agent Error: {str(e)}"
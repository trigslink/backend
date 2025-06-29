import requests
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType, AgentExecutor
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

        # ✅ Add headers or API keys into payload
        payload["openai_api_key"] = env_vars.get("OPENAI_API_KEY")
        payload["model"] = env_vars.get("MODEL", "gpt-4o")

        try:
            print(f"🔗 MCP Endpoint: {metadata['endpoint']}")
            print(f"📦 Payload Sent: {payload}")

            res = requests.post(metadata["endpoint"], json=payload, timeout=60)
            res.raise_for_status()

            data = res.json()
            # ✅ If the API returns 'output' key (text), fallback, else use raw JSON
            output = data.get("output") or data

            # ✅ Optional: Format it nicely as human-readable string
            if isinstance(output, dict):
                summary = format_output(output)
                return summary
            else:
                return output

        except Exception as e:
            return f"❌ MCP Error: {str(e)}"

    return Tool.from_function(
        name=metadata.get("service_name", "MCP Tool"),
        description=metadata.get("description", "Interact with MCP."),
        func=dynamic_func,
    )


def format_output(data: dict) -> str:
    """Format the JSON response to human-readable output."""
    try:
        wallet = data.get("wallet", "N/A")
        chain = data.get("chain", "N/A")
        total_value = data.get("total_value_usd", 0)

        summary = f"📊 **Wallet:** {wallet} on **{chain.capitalize()}**\n"
        summary += f"💰 **Total Value:** ${total_value:,.2f}\n"

        positions = data.get("positions", [])
        if not positions:
            summary += "No assets found.\n"
        else:
            summary += "\n🔍 **Top Holdings:**\n"
            for pos in positions[:5]:  # Show top 5
                summary += (
                    f"- **{pos.get('asset', 'Unknown')}**: "
                    f"${pos.get('value_usd', 0):,.2f} | "
                    f"APY: {pos.get('apy', 0)}% via {pos.get('best_protocol', 'N/A')}\n"
                )

        return summary
    except Exception as e:
        return f"⚠️ Error formatting output: {e}"


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

        agent = initialize_agent(
            tools=[tool],
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True  # ✅ Added to prevent parsing failures
        )

        return agent.run(user_prompt)

    except Exception as e:
        return f"❌ Agent Error: {str(e)}"
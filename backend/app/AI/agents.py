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

        payload = {
            "wallet": wallet,
            "chain": chain
        } if wallet and chain else {
            "input": user_input
        }

        payload["openai_api_key"] = env_vars.get("OPENAI_API_KEY")
        payload["model"] = env_vars.get("MODEL", "gpt-4o")

        try:
            print(f"🔗 MCP Endpoint: {metadata['endpoint']}")
            print(f"📦 Payload Sent: {payload}")

            res = requests.post(metadata["endpoint"], json=payload, timeout=60)
            res.raise_for_status()

            data = res.json()

            # 🟦 Check if it's a wallet yield response
            if is_wallet_yield_response(data):
                return format_wallet_yield_response(data)

            # 🟦 Or generic structured output
            if "output" in data:
                return data["output"]

            return "❌ MCP returned an unknown response format."

        except Exception as e:
            return f"❌ MCP Error: {str(e)}"

    return Tool.from_function(
        name=metadata.get("service_name", "MCP Tool"),
        description=metadata.get("description", "Interact with MCP."),
        func=dynamic_func,
    )


def is_wallet_yield_response(data: dict) -> bool:
    return all(key in data for key in ["wallet", "chain", "total_value_usd", "positions"])


def format_wallet_yield_response(data: dict) -> str:
    wallet = data.get("wallet")
    chain = data.get("chain")
    total_value = data.get("total_value_usd", 0)
    positions = data.get("positions", [])

    top_positions = sorted(
        [p for p in positions if p.get("apy", 0) > 0],
        key=lambda x: x.get("estimated_yield_per_year_usd", 0),
        reverse=True
    )[:5]  # Top 5

    if top_positions:
        table = "| Asset | Amount | Value (USD) | APY (%) | Best Protocol | Est. Yearly Yield (USD) |\n"
        table += "|-------|--------|-------------|---------|----------------|--------------------------|\n"
        for p in top_positions:
            table += (
                f"| {p.get('asset')} "
                f"| {round(p.get('amount', 0), 6)} "
                f"| {round(p.get('value_usd', 0), 2)} "
                f"| {round(p.get('apy', 0), 2)} "
                f"| {p.get('best_protocol', 'N/A')} "
                f"| {round(p.get('estimated_yield_per_year_usd', 0), 2)} |\n"
            )
    else:
        table = "_No yield-bearing positions found._"

    output = f"""
**Wallet:** `{wallet}`  
**Chain:** `{chain}`  
**Total Wallet Value:** **${round(total_value, 2):,}**

### 🔥 Top Yield-Generating Positions:
{table}
"""
    return output.strip()


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
            [tool],
            llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True  # ✅ Handle parsing errors safely
        )
        return agent.run(user_prompt)
    except Exception as e:
        return f"❌ Agent Error: {str(e)}"
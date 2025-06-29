# Trigslink Backend

This is the backend for **Trigslink**, a decentralized network for Model Context Protocols (MCPs). 

## Architecture Overview

The backend includes:

- **Agent Runtime**: Handles user queries via `agents.py` using OpenAI or custom logic  
- **Blockchain Layer**: Interfaces with MCP Provider and Consumer smart contracts (using `web3.py`)  
- **Event Listeners**: Reacts to onchain MCP requests and subscription events  
- **MCP Manager**: Manages MCP metadata and routing  
- **API Server**: Offers endpoints for query handling

# Requirements

- Docker & Docker Compose
- An OpenAI API key (or equivalent) if using the AI agent
- Avalanche wallet and RPC (e.g. Fuji testnet) configured for smart contract interaction

## 🚀 Getting Started

### 1. Clone & Install

```bash
git clone https://github.com/trigslink/blockend.git
```

### 2. Set Up Environment Variables

```bash
cp .env.examples backend/.env
Edit with the required values

# Deploy the Backend
```bash
docker-compose up --build
```

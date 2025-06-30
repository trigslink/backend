# 🚀 MCP Backend Service 

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Cloudinary](https://img.shields.io/badge/Cloudinary-3448C5?logo=cloudinary)](https://cloudinary.com/)

## About

The MCP Backend is the central nervous system of the Modular Contract Providers ecosystem, featuring:

-  Real-time blockchain event processing
-  AI-powered decision automation
-  Multi-chain smart contract integration
-  Scalable microservice architecture

##  Core Capabilities

### Blockchain Integration Layer
- Event-driven architecture for contract interactions
- Support for multiple contract standards
- Transaction verification and validation

### AI Decision Engine
- Natural language processing for queries
- Dynamic tool selection based on MCP capabilities
- Context-aware response generation

### Service Management
- End-to-end MCP lifecycle support
- Subscription management system
- Provider reputation tracking

## 🛠️ Technical Stack

**Backend**
- FastAPI (Python 3.8+)
- Uvicorn ASGI server
- Cloudinary media storage

**Infrastructure**
- Docker containerization
- Compose-based orchestration
- Trigslink tunneling

**Data**
- Blockchain-indexed data

##  API Documentation

### MCP Registration
```http
POST /register_mcp
Content-Type: multipart/form-data

Params:
- tx_hash: str (required) - Blockchain transaction hash
- logo: file (required) - Service logo image

Response:
{
  "status": "registered",
  "mcp_id": "0x..._123",
  "logo_url": "https://res.cloudinary.com/...",
  "metadata": { ... }
}
```

### MCP Discovery
```http
GET /available_mcps?[filters]
Filters:
- service_name: str - Partial name match
- wallet: str - Exact wallet match
- price_lte: float - Maximum price

Response:
[
  {
    "mcp_id": "0x..._123",
    "service_name": "AI Oracle",
    "price": 29.99,
    "logo_url": "..."
  }
]
```

### AI Query Endpoint
```http
POST /agent_query
Content-Type: application/json

Body:
{
  "mcp_id": "0x..._123",
  "user_prompt": "Analyze my portfolio risk",
  "openai_api_key": "sk-...",
  "env_vars": { ... }
}

Response:
{
  "response": "Analysis shows...",
  "sources": [...]
}
```

## 🚀 Deployment Guide

### Docker Setup
```bash
# Build and launch all services
docker-compose up --build -d

# View logs
docker-compose logs -f
```



### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `CLOUDINARY_CLOUD_NAME` | Yes | Cloudinary account name |
| `CLOUDINARY_API_KEY` | Yes | Cloudinary API key |
| `BLOCKCHAIN_RPC_URL` | Yes | Ethereum node RPC endpoint |
| `OPENAI_DEFAULT_MODEL` | No | Default AI model (default: gpt-4) |



## 🔐 Security

**Implemented Protections**
- CORS origin restrictions
- Request rate limiting
- Input validation
- API key rotation

**Best Practices**
1. Always use HTTPS
2. Rotate Cloudinary API keys quarterly
3. Restrict blockchain RPC access
4. Monitor for anomalous queries




## 📜 License

MIT License - Full text available in [LICENSE](LICENSE).

## 📧 Contact

**Technical Support**  
Email: trigslink@gmail.com
Youtube: [@trigslink](https://www.youtube.com/@trigslink)

**Business Inquiries**  
Email: partnerships@trigslink.com  


---

*© 2025 Trigslink. All rights reserved.*


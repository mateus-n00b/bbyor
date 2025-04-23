# BBYOR
Ongoing project


**Project Structure**

```
bbyor/                     # Root package
├── __init__.py            # Package initialization
├── main.py                # FastAPI app entrypoint (minimal, just app setup)
│
├── config/                # Configuration management
│   ├── __init__.py
│   ├── settings.py        # Pydantic settings (env vars, defaults)
│   └── provision.py       # Provisioning logic (moved from Config class)
│
├── api/                   # FastAPI route handlers
│   ├── __init__.py
│   ├── routers/           # Modular routers
│   │   ├── basicmessages.py
│   │   ├── connections.py
│   │   └── challenge.py   # Future implementation
│   └── dependencies.py    # Shared dependencies (e.g., auth, DB)
│
├── contracts/             # Smart contract interactions
│   ├── __init__.py
│   ├── client.py          # Web3.py client setup
│   └── random.py          # `getRandom()` and related logic
│
├── services/              # Business logic
│   ├── __init__.py
│   ├── connections.py     # Connection management (e.g., `missing_conn`)
│   └── fhe.py             # FHE key flow (future)
│
├── utils/                 # Shared utilities
│   ├── __init__.py
│   ├── http.py            # HTTP client wrappers
│   └── logging.py         # Custom logging setup
│
├── models/                # Pydantic models/DTOs
│   ├── __init__.py
│   ├── schemas.py         # Request/response schemas
│   └── events.py          # Webhook event models
│
├── tests/                 # Tests
│   ├── __init__.py
│   ├── test_api/
│   ├── test_services/
│   └── conftest.py        # Fixtures
│
└── scripts/               # Helper scripts (e.g., provisioning)
    └── bootstrap.py       # First-time setup
```
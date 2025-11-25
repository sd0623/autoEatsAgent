# AutoEats Agent MCP Server
A FastAPI-based Model Context Protocol (MCP) server that simulates online food ordering flows using CSV-backed dummy data and in-memory order/delivery storage (POC).
- The server exposes HTTP endpoints for dishes, restaurants, orders, and deliveries.
- A WebSocket endpoint at `/mcp` supports JSON-RPC 2.0 for agent integrations (with a backward-compatible legacy `{action,params}` format).
- The MCP manifest is available at `/mcp/manifest` and documents tools and message schemas.

## Project layout
```
autoeatsAgentMCP/
├── app/
│   ├── main.py          # FastAPI application, HTTP endpoints and WebSocket (JSON-RPC)
│   ├── models.py        # Pydantic models (Dish, Restaurant, Order, DeliveryInfo, etc.)
│   └── data_helper.py   # CSV loaders and in-memory data functions
├── data/                # CSV data: dishes.csv, restaurants.csv
├── scripts/             # example clients (ws_jsonrpc_client.py)
├── requirements.txt
└── README.md
```

## Deployed to Cloud Run Access
https://autoeatsagent-941463076318.us-central1.run.app/docs#/

## Quick setup (using a venv)
```zsh
# create venv in project root
python3 -m venv .venv
source .venv/bin/activate

# upgrade pip and install deps
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

# install example client dependency if not included
python -m pip install websockets
```

## Run the server (development)
```zsh
# preferred: use the module invocation (works even if uvicorn binary isn't on PATH)
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# or explicit venv uvicorn binary:
./.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open the interactive docs at: http://localhost:8000/docs

## HTTP API (current)
- GET `/` — basic server info
- GET `/dishes` — list all dishes
- GET `/dishes/{dish_id}` — fetch dish details
- POST `/dishes/search` — search dishes by body params (dish_name, restaurant_id, tags, max_price, min_popularity_score)
- GET `/restaurants` — list restaurants summary
- GET `/restaurants/{restaurant_id}` — get restaurant details
- POST `/orders` — create an order
  - Body: `{ "items": [{"dish_id":"d1","quantity":1}, ...], "user_id": "optional", "delivery_zip": "optional" }`
- GET `/orders/{order_id}` — get order
- PATCH `/orders/{order_id}/status` — update order status (body: enum string)
- GET `/deliveries/{order_id}` — get delivery info for an order

## WebSocket (agent integration)
- Path: `ws://<host>:<port>/mcp`
- Protocol: JSON-RPC 2.0 is supported and recommended. The server also accepts legacy messages of the shape `{ "action": "...", "params": { ... } }`.

JSON-RPC example request (search):
```json
{"jsonrpc":"2.0","id":"req-1","method":"search_dishes","params":{"dish_name":"chicken","max_price":15}}
```

JSON-RPC example response:
```json
{"jsonrpc":"2.0","id":"req-1","result":[ /* array of dish objects */ ]}
```

Supported JSON-RPC methods (same names appear in `/mcp/manifest`):
- `list_dishes`, `get_dish`, `search_dishes`, `list_restaurants`, `create_order`, `get_order`, `get_delivery`, `update_order_status`, `manifest`

Notifications: server or client can send JSON-RPC notifications (no `id`) for events like delivery updates. Notifications do not produce responses.

## MCP Manifest
- GET `/mcp/manifest` — returns a JSON manifest that documents HTTP tools and the WebSocket (includes `ws_protocol: json-rpc-2.0`).

## Example WebSocket client
- See `scripts/ws_jsonrpc_client.py` for an async example using the `websockets` package. Update `example_items` in the script to use a valid `dish_id` from `data/dishes.csv`.

## Data models (summary — see `app/models.py` for full definitions)
- Dish: `dish_id`, `restaurant_id`, `dish_name`, `price`, `prep_time_min`, `tags`, `popularity_score`
- Restaurant: `restaurant_id`, `name`, `cuisine_type`, `city`, `zip_code`, `avg_rating`, `delivery_eta`, `price_min`, `price_max`
- OrderItem: `dish_id`, `dish_name`, `quantity`, `price`, `restaurant_id`, `restaurant_name`
- Order: `order_id`, `user_id`, `items` (list of OrderItem), `total_price`, `restaurant_id`, `restaurant_name`, `status` (enum), `created_at`, `estimated_delivery_time`, `delivery_zip`
- DeliveryInfo: `delivery_id`, `order_id`, `status` (enum), `estimated_arrival`

## Order status flow
1. `pending` -> 2. `confirmed` -> 3. `preparing` -> 4. `ready` -> 5. `out_for_delivery` -> 6. `delivered`
`cancelled` is also available.

## Notes
- Data is loaded from `data/dishes.csv` and `data/restaurants.csv` at server start and kept in-memory. Orders and deliveries are stored in-memory and will be lost on restart.
- Authentication is not implemented (development POC). For production, require tokens and TLS.

## Development helpers
- Quick syntax check:
```zsh
python3 -m py_compile app/main.py
```
- To run the example client:
```zsh
python scripts/ws_jsonrpc_client.py
```

## License
This repository is a demo/PoC for educational use.


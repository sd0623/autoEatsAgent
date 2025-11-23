# AutoEats Agent MCP Server
A FastAPI-based Model Context Protocol (MCP) server for online food ordering automation with simulated API calls and dummy data.

## Features
- FastAPI-based MCP (Model Context Protocol) server that simulates online food ordering flows
- Exposes an MCP manifest, tools (callable actions) and resources (readable data URIs)
- Dish search, restaurant menus, order placement, order status, and delivery tracking (simulated)
- Uses simple CSV-backed dummy data and in-memory order/delivery storage for POC/testing

## Project Structure
```
autoeatsAgentMCP/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and MCP endpoints
│   ├── models.py        # Pydantic models and schemas
│   └── dummy_data.py   # Dummy dishes, menus, and data functions
├── requirements.txt
└── README.md
```

## Server available
The server will be available at:
- API: https://autoeatsagent-941463076318.us-central1.run.app/api
- API Documentation (Swagger UI): https://autoeatsagent-941463076318.us-central1.run.app/docs

## Installation
1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the LOCAL Server
Start the FastAPI server with Uvicorn:

```bash
# Option 1: Using python -m (recommended if uvicorn command not found)
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Direct command (if uvicorn is in PATH)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### MCP Endpoints
#### Get Manifest
```
GET /mcp/manifest
```
Returns the MCP server manifest - describes server capabilities, version, and metadata.

#### List Tools
```
GET /mcp/tools
```
Returns all available MCP tools for the AutoEats agent.

#### Call Tool
```
POST /mcp/tools/call?tool_name={tool_name}
Body: { "arguments": {...} }
```
Execute an MCP tool with arguments.

Available tools:
- `search_dishes` — Search dishes by name, restaurant, tags, price or popularity
- `get_dish` — Retrieve detailed dish information by `dish_id`
- `get_restaurant_menu` — Get a restaurant's menu by `restaurant_id`
- `list_restaurants` — Return a list of restaurants (summary info)
- `place_order` — Place an order (items, optional user_id, delivery_address)
- `get_order_status` — Retrieve order status by `order_id`
- `get_delivery_info` — Get delivery tracking information for an order
- `list_all_dishes` — Return all dishes across restaurants

#### List Resources
```
GET /mcp/resources
```
Returns all available MCP resources.

#### Read Resource
```
GET /mcp/resources/read?uri={uri}
```
Read a specific MCP resource.

Available resources:
- `dishes://all` — Complete list of dishes (JSON)
- `restaurants://all` — List of restaurants (JSON)
- `restaurants://{restaurant_id}/menu` — Menu for a specific restaurant (JSON)
- `dishes://by-tag/{tag}` — Dishes filtered by tag (e.g., `vegan`, `spicy`)

### Regular API Endpoints

#### Get All Dishes
```
GET /api/dishes
```

#### Get Dish by ID
```
GET /api/dishes/{dish_id}
```

#### Search Dishes
```
POST /api/dishes/search
Body: {
    "dish_name": "optional search text",
    "restaurant_id": "r1",
    "tags": ["vegan", "spicy"],
    "max_price": 15.00,
    "min_popularity_score": 0.5
}
```

#### Get All Restaurants
```
GET /api/restaurants
```

#### Get Restaurant Menu
```
GET /api/restaurants/{restaurant_id}/menu
```

#### Place Order
```
POST /api/orders
Body: {
  "items": [
    {"dish_id": "d1", "quantity": 2},
    {"dish_id": "d3", "quantity": 1}
  ],
  "user_id": "user123",
  "delivery_address": "123 Main St, City, State"
}
```

#### Get Order Status
```
GET /api/orders/{order_id}
```

#### Get Delivery Info
```
GET /api/orders/{order_id}/delivery
```

#### Update Order Status (for testing)
```
PATCH /api/orders/{order_id}/status
Body: "confirmed" | "preparing" | "ready" | "out_for_delivery" | "delivered"
```

#### Health Check
```
GET /api/health
```

## Example Usage

### Using MCP Tools
```python
import requests

# Search for vegan dishes
response = requests.post(
    "http://localhost:8000/mcp/tools/call?tool_name=search_dishes",
    json={
        "arguments": {
                "tags": ["vegan"],
                "max_price": 15.0
            }
    }
)
print(response.json())

# Place an order
response = requests.post(
    "http://localhost:8000/mcp/tools/call?tool_name=place_order",
    json={
        "arguments": {
            "items": [
                {"dish_id": "d1", "quantity": 2}
            ],
            "user_id": "user123",
            "delivery_address": "123 Main St"
        }
    }
)
print(response.json())

# Get delivery info
response = requests.post(
    "http://localhost:8000/mcp/tools/call?tool_name=get_delivery_info",
    json={
        "arguments": {
            "order_id": "ord_ABC12345"
        }
    }
)
print(response.json())
```

### Using Regular API

```python
import requests

# Get all dishes
dishes = requests.get("http://localhost:8000/api/dishes").json()

# Search for dishes
results = requests.post(
    "http://localhost:8000/api/dishes/search",
    json={
        "query": "pad thai",
        "tags": ["vegan"]
    }
).json()

# Get restaurant menu
menu = requests.get("http://localhost:8000/api/restaurants/r1/menu").json()

# Place an order
order = requests.post(
    "http://localhost:8000/api/orders",
    json={
        "items": [
            {"dish_id": "d1", "quantity": 2},
            {"dish_id": "d2", "quantity": 1}
        ],
        "user_id": "user123",
        "delivery_address": "123 Main St, City, State"
    }
).json()

# Get order status
order_status = requests.get(f"http://localhost:8000/api/orders/{order['order']['order_id']}").json()

# Get delivery info
delivery = requests.get(f"http://localhost:8000/api/orders/{order['order']['order_id']}/delivery").json()
```

## Data Models (summary)
These are simplified descriptions of the main data shapes used by the server. See `app/models.py` for full definitions.

- Dish: `dish_id`, `dish_name`, `restaurant_id`, `price`, `prep_time_min`, `tags`, `popularity_score`
- MenuItem: `item_id` (same as `dish_id`), `name`, `price`, `available`
- Order: `order_id`, `user_id`, `items` (list of order items), `total_price`, `restaurant_id`, `restaurant_name`, `status`, `created_at`, `estimated_delivery_time`, `delivery_address`
- DeliveryInfo: `delivery_id`, `order_id`, `status`, `driver_name` (optional), `driver_phone` (optional), `estimated_arrival`, `current_location`, `tracking_url`

## Order Status Flow
1. `pending` - Order placed, awaiting confirmation
2. `confirmed` - Order confirmed by restaurant
3. `preparing` - Order being prepared
4. `ready` - Order ready for pickup
5. `out_for_delivery` - Order out for delivery
6. `delivered` - Order delivered
7. `cancelled` - Order cancelled

## Dummy Data
The server comes pre-loaded with: `data/dishes.csv` and `data/restaurants.csv`

## Development
This project is a small POC used for testing MCP interactions and agent development. Notes:

- Uses FastAPI for the HTTP/MCP server and Pydantic models (`app/models.py`).
- Dummy data is loaded from CSVs in the `data/` directory and held in-memory (`app/dummy_data.py`).
- Orders and deliveries are stored in-memory (no external DB). Restarting the server clears orders.

To recreate a clean virtual environment (recommended after renaming the project directory):

```bash
# from project root
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## License
This repository is a demo/PoC for educational use.


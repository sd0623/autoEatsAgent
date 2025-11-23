# AutoEats Agent MCP Server

A FastAPI-based Model Context Protocol (MCP) server for online food ordering automation with simulated API calls and dummy data.

## Features

- **MCP Server Implementation**: Full MCP protocol support with tools and resources for food ordering agents
- **Dish Search & Browsing**: Search dishes by name, restaurant, tags, price, and rating
- **Restaurant Menus**: Access restaurant menus and available items
- **Order Management**: Place orders, track order status, and get delivery information
- **Delivery Tracking**: Real-time delivery status and tracking information
- **Dummy Data**: Pre-populated with sample dishes and restaurant menus
- **Simulated API Calls**: All endpoints simulate real API behavior

## Project Structure

```
automealAgentMCP/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and MCP endpoints
│   ├── models.py        # Pydantic models and schemas
│   └── dummy_data.py   # Dummy dishes, menus, and data functions
├── requirements.txt
└── README.md
```

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

## Running the Server

Start the FastAPI server with Uvicorn:

```bash
# Option 1: Using python -m (recommended if uvicorn command not found)
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Direct command (if uvicorn is in PATH)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## API Endpoints

### MCP Endpoints

#### Get Manifest
```
GET /mcp/manifest
```
Returns the MCP server manifest - describes server capabilities, version, and metadata.

**MCP Manifest vs Tools vs Resources:**
- **Manifest**: Server metadata and capabilities (what the server can do, protocol version, server info)
- **Tools**: Executable functions the agent can call (e.g., `search_dishes`, `place_order`)
- **Resources**: Data sources the agent can read (e.g., `dishes://all`, `restaurants://all`)

#### List Tools
```
GET /mcp/tools
```
Returns all available MCP tools for the AutoMeal agent.

#### Call Tool
```
POST /mcp/tools/call?tool_name={tool_name}
Body: { "arguments": {...} }
```
Execute an MCP tool with arguments.

Available tools:
- `search_dishes`: Search dishes by various criteria
- `get_dish`: Get a specific dish by ID
- `get_restaurant_menu`: Get menu for a restaurant
- `list_restaurants`: List all available restaurants
- `place_order`: Place a food order
- `get_order_status`: Get order status
- `get_delivery_info`: Get delivery tracking information
- `list_all_dishes`: List all available dishes

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
- `dishes://all`: All dishes
- `restaurants://all`: All restaurants
- `restaurants://{restaurant_id}/menu`: Restaurant menu
- `dishes://by-tag/{tag}`: Dishes by tag

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
  "query": "optional search text",
  "restaurant_id": "r1",
  "tags": ["vegan", "spicy"],
  "max_price_cents": 1500,
  "min_rating": 4.5
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
            "max_price_cents": 1500
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

## Data Models

### Dish
- `dish_id`: Unique identifier
- `dish_name`: Name of the dish
- `restaurant_id`: Restaurant ID
- `restaurant_name`: Restaurant name
- `price_cents`: Price in cents
- `eta_min`: Estimated time in minutes
- `rating`: Rating (0-5)
- `tags`: List of tags (e.g., vegan, spicy, vegetarian)

### MenuItem
- `item_id`: Item ID (same as dish_id)
- `name`: Item name
- `price_cents`: Price in cents
- `available`: Availability status

### Order
- `order_id`: Unique order identifier
- `user_id`: Optional user ID
- `items`: List of order items with quantities
- `total_price_cents`: Total order price
- `restaurant_id`: Restaurant ID
- `restaurant_name`: Restaurant name
- `status`: Order status (pending, confirmed, preparing, ready, out_for_delivery, delivered, cancelled)
- `created_at`: Order creation timestamp
- `estimated_delivery_time`: Estimated delivery time
- `delivery_address`: Delivery address

### DeliveryInfo
- `delivery_id`: Unique delivery identifier
- `order_id`: Associated order ID
- `status`: Delivery status (pending, assigned, picked_up, in_transit, delivered)
- `driver_name`: Driver name (when assigned)
- `driver_phone`: Driver phone number (when assigned)
- `estimated_arrival`: Estimated arrival time
- `current_location`: Current delivery location
- `tracking_url`: Tracking URL

## Order Status Flow

1. `pending` - Order placed, awaiting confirmation
2. `confirmed` - Order confirmed by restaurant
3. `preparing` - Order being prepared
4. `ready` - Order ready for pickup
5. `out_for_delivery` - Order out for delivery
6. `delivered` - Order delivered
7. `cancelled` - Order cancelled

## Dummy Data

The server comes pre-loaded with:

**Restaurants:**
- Green Thai (r1)
- Thai Quick (r2)
- Ramen House (r3)
- Curry Express (r4)
- Pizza Palace (r5)
- Sakura Sushi (r6)
- Burger Barn (r7)

**Sample Dishes:**
- Vegan Pad Thai (multiple restaurants)
- Spicy Ramen
- Chicken Tikka Masala
- Margherita Pizza
- Caesar Salad
- Sushi Platter
- Burger Deluxe

## Development

The server uses:
- **FastAPI**: Modern web framework
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server

All API calls are simulated - no actual database or external API calls are made. Orders and deliveries are stored in-memory for the POC.

## License

This is a demo project for educational purposes.


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
from datetime import datetime

from app.models import (
    Dish, MenuItem, Order, OrderRequest, OrderStatus,
    DeliveryInfo, DishSearchRequest, MCPTool, MCPResource, MCPManifest
)
from app.dummy_data import (
    get_all_dishes, get_dish_by_id, search_dishes,
    get_restaurant_menu, get_all_restaurants,
    create_order, get_order, get_delivery_info, update_order_status
)

app = FastAPI(
    title="AutoMeal Agent MCP Server",
    description="MCP server for online food ordering automation with simulated API calls",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "AutoMeal Agent MCP Server",
        "version": "1.0.0",
        "description": "MCP server for online food ordering automation"
    }


# ==================== MCP Server Endpoints ====================

@app.get("/mcp/manifest", response_model=MCPManifest)
async def get_manifest():
    """
    Get the MCP server manifest - describes server capabilities and metadata.
    
    The manifest is the server's "business card" - it tells clients what the server
    can do, what protocol version it uses, and provides general information.
    """
    return MCPManifest(
        name="AutoMeal Agent MCP Server",
        version="1.0.0",
        description="MCP server for online food ordering automation with simulated API calls",
        protocol_version="2024-11-05",
        capabilities={
            "tools": {
                "listChanged": False  # Tools list doesn't change dynamically
            },
            "resources": {
                "subscribe": False,
                "listChanged": False
            }
        },
        server_info={
            "vendor": "AutoMeal Agent",
            "product": "Food Ordering MCP Server",
            "features": [
                "dish_search",
                "restaurant_menus",
                "order_placement",
                "delivery_tracking"
            ]
        }
    )


@app.get("/mcp/tools", response_model=List[MCPTool])
async def list_tools():
    """List all available MCP tools for the AutoMeal agent"""
    return [
        MCPTool(
            name="search_dishes",
            description="Search for dishes by name, restaurant, tags, price, or popularity score",
            inputSchema={
                "type": "object",
                "properties": {
                    "dish_name": {"type": "string", "description": "Search dish_name for dish name"},
                    "restaurant_id": {"type": "string", "description": "Filter by restaurant ID"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags (e.g., vegan, spicy, vegetarian)"
                    },
                    "max_price": {"type": "number", "description": "Maximum price in dollars (e.g., 15.99)"},
                    "min_popularity_score": {"type": "number", "description": "Minimum popularity score (0-1)"}
                }
            }
        ),
        MCPTool(
            name="get_dish",
            description="Get detailed information about a specific dish by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "dish_id": {"type": "string", "description": "The ID of the dish to retrieve"}
                },
                "required": ["dish_id"]
            }
        ),
        MCPTool(
            name="get_restaurant_menu",
            description="Get the menu for a specific restaurant",
            inputSchema={
                "type": "object",
                "properties": {
                    "restaurant_id": {"type": "string", "description": "The restaurant ID"}
                },
                "required": ["restaurant_id"]
            }
        ),
        MCPTool(
            name="list_restaurants",
            description="List all available restaurants",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        MCPTool(
            name="place_order",
            description="Place a food order with specified dishes and quantities",
            inputSchema={
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "dish_id": {"type": "string"},
                                "quantity": {"type": "integer", "default": 1}
                            },
                            "required": ["dish_id"]
                        },
                        "description": "List of items to order"
                    },
                    "user_id": {"type": "string", "description": "Optional user ID"},
                    "delivery_address": {"type": "string", "description": "Delivery address"}
                },
                "required": ["items"]
            }
        ),
        MCPTool(
            name="get_order_status",
            description="Get the current status of an order",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID"}
                },
                "required": ["order_id"]
            }
        ),
        MCPTool(
            name="get_delivery_info",
            description="Get delivery tracking information for an order",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID"}
                },
                "required": ["order_id"]
            }
        ),
        MCPTool(
            name="list_all_dishes",
            description="List all available dishes from all restaurants",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.post("/mcp/tools/call")
async def call_tool(tool_name: str, arguments: dict):
    """Execute an MCP tool with the provided arguments"""
    try:
        if tool_name == "search_dishes":
            dish_name = arguments.get("dish_name")
            restaurant_id = arguments.get("restaurant_id")
            tags = arguments.get("tags")
            max_price = arguments.get("max_price")
            min_popularity_score = arguments.get("min_popularity_score")
            
            results = search_dishes(
                dish_name=dish_name,
                restaurant_id=restaurant_id,
                tags=tags,
                max_price=max_price,
                min_popularity_score=min_popularity_score
            )
            return {
                "content": [
                    {"type": "text", "text": json.dumps([r.model_dump() for r in results], indent=2)}
                ]
            }
        
        elif tool_name == "get_dish":
            dish_id = arguments.get("dish_id")
            if not dish_id:
                raise HTTPException(status_code=400, detail="dish_id is required")
            
            dish = get_dish_by_id(dish_id)
            if not dish:
                raise HTTPException(status_code=404, detail=f"Dish {dish_id} not found")
            
            return {
                "content": [
                    {"type": "text", "text": json.dumps(dish.model_dump(), indent=2)}
                ]
            }
        
        elif tool_name == "get_restaurant_menu":
            restaurant_id = arguments.get("restaurant_id")
            if not restaurant_id:
                raise HTTPException(status_code=400, detail="restaurant_id is required")
            
            menu = get_restaurant_menu(restaurant_id)
            if menu is None:
                raise HTTPException(status_code=404, detail=f"Restaurant {restaurant_id} not found")
            
            return {
                "content": [
                    {"type": "text", "text": json.dumps([item.model_dump() for item in menu], indent=2)}
                ]
            }
        
        elif tool_name == "list_restaurants":
            restaurants = get_all_restaurants()
            return {
                "content": [
                    {"type": "text", "text": json.dumps(restaurants, indent=2)}
                ]
            }
        
        elif tool_name == "place_order":
            items = arguments.get("items")
            user_id = arguments.get("user_id")
            delivery_address = arguments.get("delivery_address")
            
            if not items:
                raise HTTPException(status_code=400, detail="items are required")
            
            order, delivery = create_order(
                items=items,
                user_id=user_id,
                delivery_address=delivery_address
            )
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "order": order.model_dump(),
                            "delivery": delivery.model_dump()
                        }, indent=2)
                    }
                ]
            }
        
        elif tool_name == "get_order_status":
            order_id = arguments.get("order_id")
            if not order_id:
                raise HTTPException(status_code=400, detail="order_id is required")
            
            order = get_order(order_id)
            if not order:
                raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
            
            return {
                "content": [
                    {"type": "text", "text": json.dumps(order.model_dump(), indent=2)}
                ]
            }
        
        elif tool_name == "get_delivery_info":
            order_id = arguments.get("order_id")
            if not order_id:
                raise HTTPException(status_code=400, detail="order_id is required")
            
            delivery = get_delivery_info(order_id)
            if not delivery:
                raise HTTPException(status_code=404, detail=f"Delivery info for order {order_id} not found")
            
            return {
                "content": [
                    {"type": "text", "text": json.dumps(delivery.model_dump(), indent=2)}
                ]
            }
        
        elif tool_name == "list_all_dishes":
            dishes = get_all_dishes()
            return {
                "content": [
                    {"type": "text", "text": json.dumps([d.model_dump() for d in dishes], indent=2)}
                ]
            }
        
        else:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/resources", response_model=List[MCPResource])
async def list_resources():
    """List all available MCP resources"""
    return [
        MCPResource(
            uri="dishes://all",
            name="All Dishes",
            description="Complete list of all available dishes from all restaurants",
            mimeType="application/json"
        ),
        MCPResource(
            uri="restaurants://all",
            name="All Restaurants",
            description="List of all available restaurants",
            mimeType="application/json"
        ),
        MCPResource(
            uri="restaurants://{restaurant_id}/menu",
            name="Restaurant Menu",
            description="Menu for a specific restaurant",
            mimeType="application/json"
        ),
        MCPResource(
            uri="dishes://by-tag/{tag}",
            name="Dishes by Tag",
            description="Dishes filtered by tag (vegan, spicy, vegetarian, etc.)",
            mimeType="application/json"
        )
    ]


@app.get("/mcp/resources/read")
async def read_resource(uri: str):
    """Read a specific MCP resource"""
    try:
        if uri == "dishes://all":
            dishes = get_all_dishes()
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps([d.model_dump() for d in dishes], indent=2)
                    }
                ]
            }
        elif uri == "restaurants://all":
            restaurants = get_all_restaurants()
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(restaurants, indent=2)
                    }
                ]
            }
        elif uri.startswith("restaurants://") and uri.endswith("/menu"):
            restaurant_id = uri.split("/")[-2]
            menu = get_restaurant_menu(restaurant_id)
            if menu is None:
                raise HTTPException(status_code=404, detail=f"Restaurant {restaurant_id} not found")
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps([item.model_dump() for item in menu], indent=2)
                    }
                ]
            }
        elif uri.startswith("dishes://by-tag/"):
            tag = uri.split("/")[-1]
            dishes = search_dishes(tags=[tag])
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps([d.model_dump() for d in dishes], indent=2)
                    }
                ]
            }
        else:
            raise HTTPException(status_code=404, detail=f"Resource {uri} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Regular API Endpoints ====================

@app.get("/api/dishes", response_model=List[Dish])
async def get_dishes():
    """Get all available dishes"""
    return get_all_dishes()


@app.get("/api/dishes/{dish_id}", response_model=Dish)
async def get_dish(dish_id: str):
    """Get a specific dish by ID"""
    dish = get_dish_by_id(dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail=f"Dish {dish_id} not found")
    return dish


@app.post("/api/dishes/search", response_model=List[Dish])
async def search_dishes_endpoint(request: DishSearchRequest):
    """Search dishes based on criteria"""
    return search_dishes(
        dish_name=request.dish_name,
        restaurant_id=request.restaurant_id,
        tags=request.tags,
        max_price=request.max_price,
        min_popularity_score=request.min_popularity_score
    )


@app.get("/api/restaurants", response_model=List[dict])
async def get_restaurants():
    """Get all restaurants"""
    return get_all_restaurants()


@app.get("/api/restaurants/{restaurant_id}/menu", response_model=List[MenuItem])
async def get_menu(restaurant_id: str):
    """Get menu for a specific restaurant"""
    menu = get_restaurant_menu(restaurant_id)
    if menu is None:
        raise HTTPException(status_code=404, detail=f"Restaurant {restaurant_id} not found")
    return menu


@app.post("/api/orders", response_model=dict)
async def create_order_endpoint(request: OrderRequest):
    """Create a new order"""
    try:
        order, delivery = create_order(
            items=request.items,
            user_id=request.user_id,
            delivery_address=request.delivery_address
        )
        return {
            "order": order.model_dump(),
            "delivery": delivery.model_dump()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/orders/{order_id}", response_model=Order)
async def get_order_endpoint(order_id: str):
    """Get order by ID"""
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return order


@app.get("/api/orders/{order_id}/delivery", response_model=DeliveryInfo)
async def get_delivery_endpoint(order_id: str):
    """Get delivery information for an order"""
    delivery = get_delivery_info(order_id)
    if not delivery:
        raise HTTPException(status_code=404, detail=f"Delivery info for order {order_id} not found")
    return delivery


@app.patch("/api/orders/{order_id}/status")
async def update_order_status_endpoint(order_id: str, status: OrderStatus):
    """Update order status (for simulation/testing)"""
    try:
        order = update_order_status(order_id, status)
        return order.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AutoMeal Agent MCP Server",
        "dishes_count": len(get_all_dishes()),
        "restaurants_count": len(get_all_restaurants())
    }


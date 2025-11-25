from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Any, Dict
import json
from datetime import datetime

from app.models import (
    Dish, Order, OrderRequest, OrderStatus,
    DeliveryInfo, DishSearchRequest, MCPManifest
)
from app.data_helper import (
    get_all_dishes, get_dish_by_id, search_dishes,
    get_restaurant_by_id, get_all_restaurants,
    create_order, get_order, get_delivery_info, update_order_status
)

app = FastAPI(
    title="AutoEats Agent MCP Server",
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


# --- Root endpoint ---
@app.get("/")
async def root():
    return {
        "name": "AutoEats Agent MCP Server",
        "version": "1.0.0",
        "description": "MCP server for online food ordering automation"
    }


# --- Dish endpoints ---
@app.get("/dishes")
async def list_dishes():
    dishes = get_all_dishes()
    return [d.model_dump() for d in dishes]


@app.get("/dishes/{dish_id}")
async def get_dish(dish_id: str):
    dish = get_dish_by_id(dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    return dish.model_dump()


@app.post("/dishes/search")
async def post_search_dishes(req: DishSearchRequest):
    results = search_dishes(
        dish_name=req.dish_name,
        restaurant_id=req.restaurant_id,
        tags=req.tags,
        max_price=req.max_price,
        min_popularity_score=req.min_popularity_score
    )
    return [d.model_dump() for d in results]


# --- Restaurant endpoints ---
@app.get("/restaurants")
async def list_restaurants():
    return get_all_restaurants()


@app.get("/restaurants/{restaurant_id}")
async def get_restaurant(restaurant_id: str):
    r = get_restaurant_by_id(restaurant_id)
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return r.model_dump()


# --- Orders & Delivery endpoints ---
@app.post("/orders")
async def post_create_order(req: OrderRequest):
    try:
        order, delivery = create_order(req.items, user_id=req.user_id, delivery_zip=req.delivery_zip)
        return {"order": order.model_dump(), "delivery": delivery.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/orders/{order_id}")
async def get_order_endpoint(order_id: str):
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order.model_dump()


@app.get("/deliveries/{order_id}")
async def get_delivery(order_id: str):
    d = get_delivery_info(order_id)
    if not d:
        raise HTTPException(status_code=404, detail="Delivery info not found")
    return d.model_dump()


@app.patch("/orders/{order_id}/status")
async def patch_order_status(order_id: str, status: OrderStatus):
    try:
        order = update_order_status(order_id, status)
        return order.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- WebSocket for LLM / Agent interactions ---
@app.websocket("/mcp")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket that supports JSON-RPC 2.0 format.

    JSON-RPC requests (with an "id") will receive JSON-RPC responses.
    """
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            try:
                payload = json.loads(data)
            except Exception:
                # If incoming payload isn't valid JSON, return a small error and continue
                await ws.send_text(json.dumps({"status": "error", "error": "invalid_json", "message": "Could not parse JSON"}))
                continue

            # JSON-RPC 2.0 handling
            if isinstance(payload, dict) and payload.get("jsonrpc") == "2.0":
                req_id = payload.get("id")
                method = payload.get("method")
                params = payload.get("params", {}) or {}

                async def send_jsonrpc_result(result: Any):
                    if req_id is not None:
                        resp = {"jsonrpc": "2.0", "id": req_id, "result": result}
                        await ws.send_text(json.dumps(resp))

                async def send_jsonrpc_error(code: int, message: str, data: Any = None):
                    if req_id is not None:
                        err = {"code": code, "message": message}
                        if data is not None:
                            err["data"] = data
                        resp = {"jsonrpc": "2.0", "id": req_id, "error": err}
                        await ws.send_text(json.dumps(resp))

                try:
                    # Map JSON-RPC method names to implementation
                    if method == "list_dishes":
                        res = [d.model_dump() for d in get_all_dishes()]
                        await send_jsonrpc_result(res)

                    elif method == "get_dish":
                        dish_id = params.get("dish_id")
                        if not dish_id:
                            await send_jsonrpc_error(-32602, "Invalid params", "dish_id required")
                        else:
                            dish = get_dish_by_id(dish_id)
                            if not dish:
                                await send_jsonrpc_error(-32004, "Dish not found")
                            else:
                                await send_jsonrpc_result(dish.model_dump())

                    elif method == "search_dishes":
                        res = search_dishes(
                            dish_name=params.get("dish_name"),
                            restaurant_id=params.get("restaurant_id"),
                            tags=params.get("tags"),
                            max_price=params.get("max_price"),
                            min_popularity_score=params.get("min_popularity_score")
                        )
                        await send_jsonrpc_result([d.model_dump() for d in res])

                    elif method == "list_restaurants":
                        await send_jsonrpc_result(get_all_restaurants())

                    elif method == "create_order":
                        items = params.get("items")
                        if not items:
                            await send_jsonrpc_error(-32602, "Invalid params", "items required")
                        else:
                            try:
                                order, delivery = create_order(items, user_id=params.get("user_id"), delivery_zip=params.get("delivery_zip"))
                                await send_jsonrpc_result({"order": order.model_dump(), "delivery": delivery.model_dump()})
                            except ValueError as e:
                                await send_jsonrpc_error(-32002, "Bad request", str(e))

                    elif method == "get_order":
                        order_id = params.get("order_id")
                        if not order_id:
                            await send_jsonrpc_error(-32602, "Invalid params", "order_id required")
                        else:
                            order = get_order(order_id)
                            if not order:
                                await send_jsonrpc_error(-32004, "Order not found")
                            else:
                                await send_jsonrpc_result(order.model_dump())

                    elif method == "get_delivery":
                        order_id = params.get("order_id")
                        if not order_id:
                            await send_jsonrpc_error(-32602, "Invalid params", "order_id required")
                        else:
                            d = get_delivery_info(order_id)
                            if not d:
                                await send_jsonrpc_error(-32004, "Delivery not found")
                            else:
                                await send_jsonrpc_result(d.model_dump())

                    elif method == "update_order_status":
                        order_id = params.get("order_id")
                        status_str = params.get("status")
                        if not order_id or not status_str:
                            await send_jsonrpc_error(-32602, "Invalid params", "order_id and status required")
                        else:
                            try:
                                new_status = OrderStatus(status_str)
                                order = update_order_status(order_id, new_status)
                                await send_jsonrpc_result(order.model_dump())
                            except ValueError as e:
                                await send_jsonrpc_error(-32004, "Not found", str(e))

                    elif method == "manifest":
                        # Return manifest as a convenience
                        manifest = {
                            "name": "AutoEats Agent MCP",
                            "description": "MCP for automated food ordering",
                            "endpoints": {
                                "list_dishes": "/dishes",
                                "search_dishes": "/dishes/search",
                                "create_order": "/orders",
                                "get_order": "/orders/{order_id}",
                                "get_delivery": "/deliveries/{order_id}",
                                "websocket": "/mcp",
                                "ws_protocol": "json-rpc-2.0"
                            }
                        }
                        await send_jsonrpc_result(manifest)

                    else:
                        await send_jsonrpc_error(-32601, "Method not found")

                except WebSocketDisconnect:
                    raise
                except Exception as e:
                    # Internal error
                    await send_jsonrpc_error(-32000, "Internal error", str(e))


    except WebSocketDisconnect:
        # Client disconnected
        return


# --- MCP manifest HTTP endpoint ---
@app.get("/mcp/manifest")
async def get_mcp_manifest():
    base = {
        "name": "AutoEats Agent MCP Server",
        "description": "MCP server for automated food ordering (POC)",
        "tools": {
            "list_dishes": {
                "method": "GET",
                "path": "/dishes",
                "description": "List all dishes",
                "params": {
                    "query": {
                        "limit": {"type": "integer", "required": False, "description": "Optional max number of results"}
                    }
                }
            },
            "get_dish": {
                "method": "GET",
                "path": "/dishes/{dish_id}",
                "description": "Get dish details",
                "params": {
                    "path": {
                        "dish_id": {"type": "string", "required": True, "description": "ID of the dish"}
                    }
                }
            },
            "search_dishes": {
                "method": "POST",
                "path": "/dishes/search",
                "description": "Search dishes by criteria",
                "params": {
                    "body": {
                        "dish_name": {"type": "string", "required": False},
                        "restaurant_id": {"type": "string", "required": False},
                        "tags": {"type": "array[string]", "required": False},
                        "max_price": {"type": "number", "required": False},
                        "min_popularity_score": {"type": "number", "required": False}
                    }
                }
            },
            "list_restaurants": {
                "method": "GET",
                "path": "/restaurants",
                "description": "List restaurants",
                "params": {"query": {} }
            },
            "create_order": {
                "method": "POST",
                "path": "/orders",
                "description": "Create a new order",
                "params": {
                    "body": {
                        "items": {"type": "array[object]", "required": True, "description": "List of items [{dish_id, quantity}]"},
                        "user_id": {"type": "string", "required": False},
                        "delivery_zip": {"type": "string", "required": False}
                    }
                }
            },
            "get_order": {
                "method": "GET",
                "path": "/orders/{order_id}",
                "description": "Fetch order by id",
                "params": {
                    "path": {
                        "order_id": {"type": "string", "required": True}
                    }
                }
            },
            "get_delivery": {
                "method": "GET",
                "path": "/deliveries/{order_id}",
                "description": "Fetch delivery info",
                "params": {
                    "path": {
                        "order_id": {"type": "string", "required": True}
                    }
                }
            },
            "websocket": {
                "method": "WS",
                "path": "/mcp",
                "description": "WebSocket control channel for agents",
                "params": {
                    "message": {
                        "action": {"type": "string", "required": True, "description": "Action name (e.g., search_dishes, create_order)"},
                        "params": {"type": "object", "required": False, "description": "Action-specific parameters"}
                    }
                }
            }
        }
    }
    return MCPManifest(**base)




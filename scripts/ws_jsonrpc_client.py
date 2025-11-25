"""Example JSON-RPC WebSocket client for the AutoEats MCP server.

Requires: pip install websockets

This script demonstrates two JSON-RPC calls:
 - search_dishes
 - create_order

Run while the server is running (uvicorn app.main:app --reload)
"""
import asyncio
import json
import uuid

import websockets

WS_URI = "ws://localhost:8000/mcp"

async def send_jsonrpc(ws, method, params=None):
    req_id = str(uuid.uuid4())
    payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(payload))
    # Wait for response
    resp_txt = await ws.recv()
    resp = json.loads(resp_txt)
    return resp

async def main():
    async with websockets.connect(WS_URI) as ws:
        print("Connected to", WS_URI)

        # Example: search_dishes
        print("-> search_dishes\n")
        resp = await send_jsonrpc(ws, "search_dishes", {"dish_name": "chicken", "max_price": 20})
        print(json.dumps(resp, indent=2))

        # Example: create_order (adjust dish_id to one that exists in your data/dishes.csv)
        example_items = [{"dish_id": "R59D4", "quantity": 1}]
        print("-> create_order\n")
        resp = await send_jsonrpc(ws, "create_order", {"items": example_items, "user_id": "test_user"})
        print(json.dumps(resp, indent=2))

if __name__ == "__main__":
    asyncio.run(main())

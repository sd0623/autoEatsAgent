from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


class Dish(BaseModel):
    dish_id: str
    restaurant_id: str
    dish_name: str
    price: float
    prep_time_min: int
    tags: List[str]
    popularity_score: float


class Restaurant(BaseModel):
    restaurant_id: str
    name: str
    cuisine_type: str
    city: str
    zip_code: str
    avg_rating: float
    delivery_eta: int
    price_min: float
    price_max: float


class OrderItem(BaseModel):
    dish_id: str
    dish_name: str
    quantity: int
    price: float
    restaurant_id: str
    restaurant_name: str


class Order(BaseModel):
    order_id: str
    user_id: Optional[str] = None
    items: List[OrderItem]
    total_price: float
    restaurant_id: str
    restaurant_name: str
    status: OrderStatus
    created_at: str
    estimated_delivery_time: str
    delivery_zip: Optional[str] = None


class DeliveryInfo(BaseModel):
    delivery_id: str
    order_id: str
    status: DeliveryStatus
    estimated_arrival: str

class OrderRequest(BaseModel):
    items: List[dict]  # [{"dish_id": "d1", "quantity": 2}]
    user_id: Optional[str] = None
    delivery_zip: Optional[str] = None

class DishSearchRequest(BaseModel):
    dish_name: Optional[str] = None
    restaurant_id: Optional[str] = None
    tags: Optional[List[str]] = None
    max_price: Optional[float] = None
    min_popularity_score: Optional[float] = None

class MCPManifest(BaseModel):
    """MCP Server Manifest - describes the server's capabilities and metadata"""
    name: str
    description: str
    tools: dict

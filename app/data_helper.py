from app.models import Dish, Restaurant, Order, OrderItem, OrderStatus, DeliveryInfo, DeliveryStatus
from datetime import datetime, timedelta
from typing import List, Dict
import random
import string
import csv
from pathlib import Path

# ---- In-memory storage (POC) ----

# Get the data directory path
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DISHES_CSV = DATA_DIR / "dishes.csv"
RESTAURANTS_CSV = DATA_DIR / "restaurants.csv"

# Load restaurants from CSV
def load_restaurants() -> Dict[str, Restaurant]:
    """Load restaurants from restaurants.csv"""
    restaurants = {}
    if not RESTAURANTS_CSV.exists():
        raise FileNotFoundError(f"Restaurants CSV file not found: {RESTAURANTS_CSV}")
    
    with open(RESTAURANTS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            restaurant = Restaurant(
                restaurant_id=row['restaurant_id'],
                name=row['name'],
                cuisine_type=row['cuisine_type'],
                city=row['city'],
                zip_code=row['zip_code'],
                avg_rating=float(row['avg_rating']),
                delivery_eta=int(row['delivery_eta']),
                price_min=float(row['price_min']),
                price_max=float(row['price_max'])
            )
            restaurants[row['restaurant_id']] = restaurant
    
    return restaurants

# Load dishes from CSV
def load_dishes_from_csv() -> List[Dish]:
    """Load dishes from dishes.csv file - using CSV fields directly"""
    dishes = []
    
    if not DISHES_CSV.exists():
        raise FileNotFoundError(f"Dishes CSV file not found: {DISHES_CSV}")
    
    with open(DISHES_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse tags (comma-separated string, may have quotes)
            tags_str = row['tags'].strip('"').strip("'")
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            
            dish = Dish(
                dish_id=row['dish_id'],
                restaurant_id=row['restaurant_id'],
                dish_name=row['dish_name'],
                price=float(row['price']),
                prep_time_min=int(row['prep_time_min']),
                tags=tags,
                popularity_score=float(row['popularity_score'])
            )
            dishes.append(dish)
    
    return dishes



# Load data from CSV files
RESTAURANTS = load_restaurants()
DISHES = load_dishes_from_csv()

# In-memory order storage
ORDERS: dict = {}

# In-memory delivery storage
DELIVERIES: dict = {}


# ---- Data access and helper functions ----

# --- Dish related functions ----
def get_all_dishes():
    """Get all available dishes"""
    return DISHES.copy()


def get_dish_by_id(dish_id: str):
    """Get a specific dish by ID"""
    for dish in DISHES:
        if dish.dish_id == dish_id:
            return dish
    return None


def search_dishes(
    dish_name: str = None,
    restaurant_id: str = None,
    tags: List[str] = None,
    max_price: float = None,
    min_popularity_score: float = None
):
    """Search dishes based on criteria"""
    results = DISHES.copy()
    
    if dish_name:
        name_lower = dish_name.lower()
        results = [d for d in results if name_lower in d.dish_name.lower()]
    
    if restaurant_id:
        results = [d for d in results if d.restaurant_id == restaurant_id]
    
    if tags:
        results = [d for d in results if any(tag.lower() in [t.lower() for t in d.tags] for tag in tags)]
    
    if max_price is not None:
        results = [d for d in results if d.price <= max_price]
    
    if min_popularity_score is not None:
        results = [d for d in results if d.popularity_score >= min_popularity_score]
    
    return results

# --- Restaurant related functions ----
def get_restaurant_by_id(restaurant_id: str):
    """Get restaurant details by ID"""
    return RESTAURANTS.get(restaurant_id)

def get_all_restaurants():
    """Get all unique restaurants from restaurants.csv"""
    restaurants = []
    
    for rid, restaurant in RESTAURANTS.items():
        # Count dishes directly from DISHES
        dish_count = sum(1 for d in DISHES if d.restaurant_id == rid)
        restaurants.append({
            "restaurant_id": rid,
            "restaurant_name": restaurant.name,
            "cuisine_type": restaurant.cuisine_type,
            "city": restaurant.city,
            "avg_rating": restaurant.avg_rating,
            "dish_count": dish_count
        })
    
    return restaurants

# --- Order and Delivery related functions ----
def create_order(items: List[dict], user_id: str = None, delivery_zip: str = None):
    """Create a new order"""
    if not items:
        raise ValueError("Order must contain at least one item")
    
    # Validate items and get dish info
    order_items = []
    restaurant_id = None
    restaurant_name = None
    total_price = 0
    
    for item in items:
        dish_id = item.get("dish_id")
        quantity = item.get("quantity", 1)
        
        if not dish_id:
            raise ValueError("Each item must have a dish_id")
        
        dish = get_dish_by_id(dish_id)
        if not dish:
            raise ValueError(f"Dish {dish_id} not found")

        # Get restaurant info
        restaurant = get_restaurant_by_id(dish.restaurant_id)
        if not restaurant:
            raise ValueError(f"Restaurant {dish.restaurant_id} not found")
        
        # Set restaurant (all items must be from same restaurant)
        if restaurant_id is None:
            restaurant_id = dish.restaurant_id
            restaurant_name = restaurant.name
        elif restaurant_id != dish.restaurant_id:
            raise ValueError("All items in an order must be from the same restaurant")
        
        order_item = OrderItem(
            dish_id=dish.dish_id,
            dish_name=dish.dish_name,
            quantity=quantity,
            price=dish.price * quantity,
            restaurant_id=dish.restaurant_id,
            restaurant_name=restaurant.name
        )
        order_items.append(order_item)
        total_price += order_item.price
    
    # Generate order ID
    order_id = f"ord_{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
    
    # Calculate estimated delivery time (use max prep_time_min from dishes)
    max_prep_time = max(d.prep_time_min for d in [get_dish_by_id(item["dish_id"]) for item in items])
    estimated_delivery = datetime.now() + timedelta(minutes=max_prep_time)
    
    # Create order
    order = Order(
        order_id=order_id,
        user_id=user_id,
        items=order_items,
        total_price=total_price,
        restaurant_id=restaurant_id,
        restaurant_name=restaurant_name,
        status=OrderStatus.PENDING,
        created_at=datetime.now().isoformat(),
        estimated_delivery_time=estimated_delivery.isoformat(),
        delivery_zip=delivery_zip
    )
    
    ORDERS[order_id] = order
    
    # Create delivery info
    delivery = DeliveryInfo(
        delivery_id=f"del_{order_id}",
        order_id=order_id,
        status=DeliveryStatus.PENDING,
        estimated_arrival=estimated_delivery.isoformat()
    )
    DELIVERIES[order_id] = delivery
    
    return order, delivery


def get_order(order_id: str):
    """Get order by ID"""
    return ORDERS.get(order_id)


def get_delivery_info(order_id: str):
    """Get delivery information for an order"""
    return DELIVERIES.get(order_id)


def update_order_status(order_id: str, status: OrderStatus):
    """Update order status"""
    if order_id not in ORDERS:
        raise ValueError(f"Order {order_id} not found")
    
    order = ORDERS[order_id]
    order.status = status
    
    # Update delivery status based on order status
    if order_id in DELIVERIES:
        delivery = DELIVERIES[order_id]
        if status == OrderStatus.CONFIRMED or status == OrderStatus.PREPARING:
            delivery.status = DeliveryStatus.ASSIGNED
        elif status == OrderStatus.READY:
            delivery.status = DeliveryStatus.PICKED_UP
        elif status == OrderStatus.OUT_FOR_DELIVERY:
            delivery.status = DeliveryStatus.IN_TRANSIT
        elif status == OrderStatus.DELIVERED:
            delivery.status = DeliveryStatus.DELIVERED
    
    return order


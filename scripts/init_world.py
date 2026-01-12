import sys
import os


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


init_file = os.path.join(ROOT_DIR, 'core', '__init__.py')
if not os.path.exists(init_file):
    with open(init_file, 'w') as f:
        pass


try:
    from core.database import world_lore
    print("✅ Import successful!")
except ImportError as e:
    print(f"Still failing. Looking in: {ROOT_DIR}")
    print(f"Error: {e}")
    sys.exit(1)


locations = [{
    "location_id": "stout_city",
    "name": "The city of Stout",
    "description": "A wind-scoured trade hub clinging to a cliffside.",
    "details": "Controlled by Merchant Princes.",
    "points_of_interest": ["The Rusty Gear Tavern"]
}]

world_lore.delete_many({})
world_lore.insert_many(locations)
print("Database updated.")
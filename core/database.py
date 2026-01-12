import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = MongoClient(os.getenv("MONGO_URI"))
db = client["Kenshi_RPG"]

players = db["players"]
logs = db["game_logs"]
world_lore = db["world_lore"]
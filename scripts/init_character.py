import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT_DIR)

from core.database import players

kerman_data = {
    "name": "Kerman",
    "identity": {
        "gender": "Male",
        "age": 19,
        "appearance": "Rusted cybernetic plating, dusty cloak",
        "personality": "Stoic, analytical, dark humor.",
        "background": "Unknown, for memories are lost",
        "description": "A nobody carrying the weight of the Old World in his chest."
    },
    "stats": {
        "combat": {
            "strength": 5.0, "agility": 25.0, "athletics": 25.0,
            "melee_attack": 5.0, "melee_defence": 5.0, "toughness": 10.0, "ranged": 2.0
        },
        "utility": {
            "engineer": 20.0, "field_medic": 15.0, "stealth": 25.0
        }
    },
    "status": {
        "location": "The city of Stout",
        "integrity": 100.0,
        "core_stability": 100.0
    },
    "possession": {
        "inventory": [
            {"item": "Rusted Katana", "type": "Weapon", "weight": 2.0},
            {"item": "Emergency Medkit", "type": "Consumable", "weight": 1.0}
        ]
    }
}

players.delete_one({"name": "Kerman"})
players.insert_one(kerman_data)
print("Kerman initialized with Source of Truth schema.")
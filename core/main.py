import os
import json
import re
import google.generativeai as genai
from datetime import datetime
from validator import validate_ai_text

from database import players, logs, world_lore

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(BASE_DIR, '..', 'game_rules.json')

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('models/gemini-flash-latest')

def apply_updates(raw_text):
    """Finds JSON between tags, validates it, and updates MongoDB."""
    match = re.search(r'UPDATE_START (\{.*?\}) UPDATE_END', raw_text)
    if not match:
        return raw_text

    try:
        update_json = json.loads(match.group(1))
        
        valid_increments = {k: v for k, v in update_json.items() if isinstance(v, (int, float))}
        valid_sets = {k: v for k, v in update_json.items() if not isinstance(v, (int, float))}

        if valid_increments:
            players.update_one({"name": "Kerman"}, {"$inc": valid_increments})
        if valid_sets:
            players.update_one({"name": "Kerman"}, {"$set": valid_sets})
        
        print(f"⚙️  System Sync: {update_json}")
        return re.sub(r'UPDATE_START .* UPDATE_END', '', raw_text).strip()
    except Exception as e:
        print(f"⚠️  Sync Error: {e}")
        return raw_text

def start_game():
    kerman = players.find_one({"name": "Kerman"})
    
    if kerman and "_id" in kerman:
        kerman["_id"] = str(kerman["_id"])

    if not os.path.exists(RULES_PATH):
        print(f"Error: Cannot find {RULES_PATH}")
        return

    with open(RULES_PATH, 'r') as f:
        rules = json.load(f)

    loc_query = kerman['status']['location']
    loc_data = world_lore.find_one({"name": {"$regex": loc_query, "$options": "i"}})
    lore_text = loc_data['description'] if loc_data else "A dusty, unknown corner of the world."

    chat = model.start_chat(history=[])

    system_prompt = f"""
    SYSTEM: {rules['system_identity']['role']}
    SETTING: {rules['system_identity']['setting']}
    LORE: {lore_text}
    CHARACTER: {json.dumps(kerman, indent=2)}
    
    MECHANICS: {", ".join(rules['mechanics'])}
    RULE: Use UPDATE_START {{"key": value}} UPDATE_END for all changes.
    """

    print("\n" + "="*40 + "\n   THE SILENT ORBIT: ONLINE\n" + "="*40)
    
    response = chat.send_message(f"{system_prompt}\n\nBegin the story in Stout.")
    clean_msg = apply_updates(response.text)
    print(f"\nGM: {clean_msg}\n")

    while True:
        user_move = input("KERMAN: ")
        if user_move.lower() in ['exit', 'quit']: break
        
        response = chat.send_message(user_move)
        clean_msg = apply_updates(response.text)
        print(f"\nGM: {clean_msg}\n")

def apply_updates(raw_text):
    kerman = players.find_one({"name": "Kerman"})
    result = validate_ai_text(raw_text, current_state=kerman)

    if result.ok:
        update_doc = {}
        if result.inc_ops:
            update_doc["$inc"] = result.inc_ops
        if result.set_ops:
            update_doc["$set"] = result.set_ops

        if update_doc:
            players.update_one({"name": "Kerman"}, update_doc)

        if result.warnings:
            print("⚠️ Validator warnings:", result.warnings)
    else:
        print("❌ Validator blocked update:", result.errors)

    return result.cleaned_text


if __name__ == "__main__":
    start_game()
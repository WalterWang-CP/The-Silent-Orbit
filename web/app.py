import sys
import os
import json
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from core.validator import validate_ai_text


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv(os.path.join(ROOT_DIR, '.env'))

try:
    from core.database import players, world_lore
except ImportError as e:
    print(f"CRITICAL: Cannot find 'core' folder. Ensure __init__.py exists in core/.")
    raise e

import google.generativeai as genai

app = Flask(__name__)


genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('models/gemini-flash-latest')
chat_session = model.start_chat(history=[])

def sync_database(raw_text):
    """Finds JSON updates in AI text and updates MongoDB."""
    match = re.search(r'UPDATE_START (\{.*?\}) UPDATE_END', raw_text)
    if not match:
        return raw_text
    try:
        update_json = json.loads(match.group(1))
        incs = {k: v for k, v in update_json.items() if isinstance(v, (int, float))}
        sets = {k: v for k, v in update_json.items() if not isinstance(v, (int, float))}
        
        if incs: players.update_one({"name": "Kerman"}, {"$inc": incs})
        if sets: players.update_one({"name": "Kerman"}, {"$set": sets})
        
        return re.sub(r'UPDATE_START .* UPDATE_END', '', raw_text).strip()
    except:
        return raw_text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_initial_data', methods=['GET'])
def get_initial_data():
    """Fetches character data immediately on page load."""
    kerman = players.find_one({"name": "Kerman"})
    if kerman:
        kerman["_id"] = str(kerman["_id"])
        return jsonify({
            "stats": kerman.get('stats', {}),
            "location": kerman.get('status', {}).get('location', 'Unknown Sector'),
            "identity": kerman.get('identity', {})
        })
    return jsonify({"error": "Character not found"}), 404

@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.json.get('message')
    kerman = players.find_one({"name": "Kerman"})
    
    with open(os.path.join(ROOT_DIR, 'game_rules.json'), 'r') as f:
        rules = json.load(f)
    
    loc_name = kerman.get('status', {}).get('location', 'Stout')
    loc_data = world_lore.find_one({"name": {"$regex": loc_name, "$options": "i"}})
    lore_text = loc_data['description'] if loc_data else "A desolate sector."

    global chat_session
    try:
        if len(chat_session.history) == 0:
            prompt = (f"SYSTEM_INIT: {rules['system_identity']['role']}. "
                     f"Setting: {lore_text}. Stats: {json.dumps(kerman['stats'])}. "
                     f"User: {user_input}")
            response = chat_session.send_message(prompt)
        else:
            response = chat_session.send_message(user_input)

        clean_reply = sync_database(response.text)
        updated_kerman = players.find_one({"name": "Kerman"})
        
        return jsonify({
            "reply": clean_reply,
            "stats": updated_kerman['stats'],
            "location": updated_kerman['status']['location']
        })
    except Exception as e:
        return jsonify({"reply": f"CONNECTION_ERROR: {str(e)}", "stats": kerman['stats']})

def sync_database(raw_text):
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
    else:
        # Optional
        pass

    return result.cleaned_text

if __name__ == '__main__':
    app.run(debug=True)
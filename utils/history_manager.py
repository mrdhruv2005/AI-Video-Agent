import os
import json
import datetime
import re

HISTORY_DIR = 'history'
os.makedirs(HISTORY_DIR, exist_ok=True)

def slugify(text: str) -> str:
    """Convert text to a clean URL-friendly filename segment."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '_', text)
    return text.strip('_')[:50]

def save_meeting(data: dict) -> str:
    """
    Saves meeting analysis data to a JSON file in the history directory.
    Returns the file name of the saved meeting.
    """
    title = data.get("title", "Untitled Meeting")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    meeting_id = f"{timestamp}_{slugify(title)}"
    
    # Exclude non-serializable objects (like rag_chain vector store)
    serializable_data = {
        "meeting_id": meeting_id,
        "title": title,
        "timestamp": datetime.datetime.now().isoformat(),
        "source": data.get("source", "Unknown Source"),
        "transcript": data.get("transcript", ""),
        "summary": data.get("summary", ""),
        "action_items": data.get("action_items", ""),
        "key_decisions": data.get("key_decisions", ""),
        "open_questions": data.get("open_questions", ""),
    }
    
    file_path = os.path.join(HISTORY_DIR, f"{meeting_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(serializable_data, f, indent=4, ensure_ascii=False)
        
    return meeting_id

def list_meetings() -> list:
    """
    Lists all saved meetings in the history directory, sorted by timestamp descending.
    Returns a list of dicts with basic metadata (meeting_id, title, timestamp, source).
    """
    meetings = []
    if not os.path.exists(HISTORY_DIR):
        return []
        
    for filename in os.listdir(HISTORY_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(HISTORY_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    meetings.append({
                        "meeting_id": data.get("meeting_id", filename[:-5]),
                        "title": data.get("title", "Untitled Meeting"),
                        "timestamp": data.get("timestamp", ""),
                        "source": data.get("source", "Unknown"),
                    })
            except Exception as e:
                print(f"Error loading meeting header from {filename}: {e}")
                
    # Sort by timestamp descending (newest first)
    meetings.sort(key=lambda x: x["timestamp"], reverse=True)
    return meetings

def load_meeting(meeting_id: str) -> dict:
    """
    Loads complete meeting data from a JSON file in the history directory.
    """
    file_path = os.path.join(HISTORY_DIR, f"{meeting_id}.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Meeting history file {meeting_id}.json not found.")
        
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def delete_meeting(meeting_id: str):
    """
    Deletes a meeting from the history directory.
    """
    file_path = os.path.join(HISTORY_DIR, f"{meeting_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)

# adminpanel/models.py
from pymongo import MongoClient
from datetime import datetime
from ai_module.matcher import score_pair

# Mongo connection
client = MongoClient("mongodb://localhost:27017/")
db = client["lostfound_db"]
lost_col = db["lost_items"]
found_col = db["found_items"]
matches_col = db["matches"]

class LostFoundMatcher:
    """Handles lost and found item matching"""

    def __init__(self, min_score=0.25):
        self.min_score = min_score

    def generate_matches(self):
        lost_items = list(lost_col.find({"status": {"$in": [None, "pending", "open"]}}))
        found_items = list(found_col.find({"status": {"$in": [None, "pending", "open"]}}))

        new_suggestions = []
        for lost in lost_items:
            for found in found_items:
                if lost.get("lost_id") is None or found.get("found_id") is None:
                    continue
                existing = matches_col.find_one({"lost_id": lost["lost_id"], "found_id": found["found_id"]})
                if existing and existing.get("status") != "wrong":
                    continue
                score = score_pair(lost, found)
                if score >= self.min_score:
                    new_suggestions.append({
                        "lost_id": lost["lost_id"],
                        "found_id": found["found_id"],
                        "lost_name": lost.get("name"),
                        "found_name": found.get("name"),
                        "lost_user": lost.get("reported_by"),
                        "found_user": found.get("reported_by"),
                        "score": round(score, 3),
                        "status": "suggested",
                        "timestamp": datetime.utcnow()
                    })

        inserted = 0
        for s in new_suggestions:
            existing = matches_col.find_one({"lost_id": s["lost_id"], "found_id": s["found_id"]})
            if not existing:
                matches_col.insert_one(s)
                inserted += 1

        return inserted

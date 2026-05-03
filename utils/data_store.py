"""
utils/data_store.py
Simple JSON-based storage. Works out of the box — no DB setup required.
Replace with MongoDB calls if you have MONGODB_URI set.
"""
import json, os, uuid
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

def _path(collection: str) -> str:
    return os.path.join(DATA_DIR, f"{collection}.json")

def _load(collection: str) -> list:
    p = _path(collection)
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return json.load(f)

def _save(collection: str, data: list):
    with open(_path(collection), "w") as f:
        json.dump(data, f, indent=2, default=str)

def insert(collection: str, doc: dict) -> str:
    docs = _load(collection)
    doc["_id"] = str(uuid.uuid4())[:8]
    doc["created_at"] = datetime.now().isoformat()
    docs.append(doc)
    _save(collection, docs)
    return doc["_id"]

def find_all(collection: str) -> list:
    return _load(collection)

def find_by(collection: str, key: str, value) -> list:
    return [d for d in _load(collection) if d.get(key) == value]

def update_by_id(collection: str, doc_id: str, updates: dict):
    docs = _load(collection)
    for doc in docs:
        if doc.get("_id") == doc_id:
            doc.update(updates)
            doc["updated_at"] = datetime.now().isoformat()
    _save(collection, docs)

def seed_demo_data():
    """Seed with sample applications for demo purposes."""
    if find_all("applications"):
        return  # already seeded

    schools = ["SBOA Annanagar", "SBOA Mogappair", "SBOA Adyar",
               "SBOA Tambaram", "SBOA Porur"]
    classes = ["LKG", "Class 1", "Class 6", "Class 9", "Class 11"]
    statuses = ["Pending", "Under Review", "Approved", "Rejected"]

    import random
    random.seed(42)
    for i in range(40):
        insert("applications", {
            "student_name": f"Student {i+1}",
            "father_name": f"Father {i+1}",
            "mother_name": f"Mother {i+1}",
            "class_applying": random.choice(classes),
            "school": random.choice(schools),
            "phone": f"98{random.randint(10000000, 99999999)}",
            "email": f"parent{i+1}@email.com",
            "distance_km": round(random.uniform(0.5, 10), 1),
            "has_sibling": random.choice([True, False]),
            "percentage": round(random.uniform(55, 98), 1),
            "is_ews": random.choice([True, False, False, False]),
            "status": random.choice(statuses),
            "score": random.randint(30, 95),
        })

import pandas as pd
from pymongo import MongoClient, GEOSPHERE, ASCENDING

CSV = "data/collisions_clean.csv"
client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
client.admin.command("ping")          # fails fast if MongoDB isn't running
col = client["traffic_db"]["collisions"]

col.drop()                            # makes the script safe to re-run
total = 0

for chunk in pd.read_csv(CSV, chunksize=5000, parse_dates=["crash_datetime"]):
    docs = []
    for r in chunk.to_dict("records"):
        doc = {
            "collision_id": int(r["collision_id"]),
            "crash_datetime": r["crash_datetime"].to_pydatetime(),
            "hour": int(r["hour"]),
            "weekday": int(r["weekday"]),
            "month": int(r["month"]),
            "is_weekend": bool(r["is_weekend"]),
            "borough": r["borough"],
            "injured": int(r["number_of_persons_injured"]),
            "killed": int(r["number_of_persons_killed"]),
            "has_injury": bool(r["has_injury"]),
            "factor": r["factor"],
            "location": {                       # GeoJSON: [longitude, latitude]
                "type": "Point",
                "coordinates": [float(r["longitude"]), float(r["latitude"])],
            },
        }
        if pd.notna(r["zip_code"]):
            doc["zip_code"] = str(int(r["zip_code"]))
        if pd.notna(r["on_street_name"]):
            doc["street"] = str(r["on_street_name"]).strip()
        docs.append(doc)
    col.insert_many(docs)
    total += len(docs)
    print("Inserted", total)

# Indexes
col.create_index([("location", GEOSPHERE)])
col.create_index([("crash_datetime", ASCENDING)])
col.create_index([("borough", ASCENDING), ("hour", ASCENDING)])
col.create_index([("collision_id", ASCENDING)], unique=True)

print("Done. Documents:", col.count_documents({}))
print("Indexes:", [i["name"] for i in col.list_indexes()])
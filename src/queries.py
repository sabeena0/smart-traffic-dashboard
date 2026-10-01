from datetime import datetime
from pymongo import MongoClient

col = MongoClient("mongodb://localhost:27017")["traffic_db"]["collisions"]

def show(title, cursor):
    print("\n==", title)
    for d in cursor:
        print(d)

# ---------- CRUD ----------
test = {"collision_id": 0, "crash_datetime": datetime(2026, 1, 1, 12, 0),
        "hour": 12, "weekday": 3, "month": 1, "is_weekend": False,
        "borough": "Manhattan", "injured": 0, "killed": 0,
        "has_injury": False, "factor": "Test",
        "location": {"type": "Point", "coordinates": [-73.9855, 40.7580]}}
col.delete_many({"collision_id": 0})
col.insert_one(test)                                              # Create
print("\nRead:", col.find_one({"collision_id": 0}, {"_id": 0, "factor": 1}))
col.update_one({"collision_id": 0}, {"$set": {"injured": 2, "has_injury": True}})  # Update
print("Updated:", col.find_one({"collision_id": 0}, {"_id": 0, "injured": 1}))
col.delete_one({"collision_id": 0})                               # Delete
print("Deleted. Left:", col.count_documents({"collision_id": 0}))

# ---------- Aggregations ----------
show("Crashes by hour", col.aggregate([
    {"$group": {"_id": "$hour", "crashes": {"$sum": 1}}},
    {"$sort": {"_id": 1}}]))

show("Crashes and injuries by borough", col.aggregate([
    {"$group": {"_id": "$borough", "crashes": {"$sum": 1},
                "injured": {"$sum": "$injured"}, "killed": {"$sum": "$killed"}}},
    {"$sort": {"crashes": -1}}]))

show("Top 5 contributing factors", col.aggregate([
    {"$match": {"factor": {"$ne": "Unspecified"}}},
    {"$group": {"_id": "$factor", "crashes": {"$sum": 1}}},
    {"$sort": {"crashes": -1}}, {"$limit": 5}]))

show("Injury rate by hour (%)", col.aggregate([
    {"$group": {"_id": "$hour", "total": {"$sum": 1},
                "with_injury": {"$sum": {"$cond": ["$has_injury", 1, 0]}}}},
    {"$project": {"rate": {"$round": [{"$multiply": [{"$divide": ["$with_injury", "$total"]}, 100]}, 1]}}},
    {"$sort": {"_id": 1}}]))

# ---------- Geospatial ----------
times_sq = {"type": "Point", "coordinates": [-73.9855, 40.7580]}

print("\n== Crashes within 500 m of Times Square ($geoWithin):",
      col.count_documents({"location": {"$geoWithin": {"$centerSphere": [[-73.9855, 40.7580], 0.5 / 6378.1]}}}))

nearby = list(col.find({"location": {"$near": {"$geometry": times_sq, "$maxDistance": 500}}}, {"_id": 0, "borough": 1}))
print("== Same area using $near (find, sorted by distance):", len(nearby))

show("5 nearest crashes to Times Square", col.find(
    {"location": {"$near": {"$geometry": times_sq}}},
    {"_id": 0, "crash_datetime": 1, "borough": 1, "factor": 1}).limit(5))

print("\n== Crashes inside 1 km circle ($geoWithin):", col.count_documents(
    {"location": {"$geoWithin": {"$centerSphere": [[-73.9855, 40.7580], 1 / 6378.1]}}}))

show("Top 5 hotspot grid cells (about 100 m)", col.aggregate([
    {"$group": {"_id": {"lat": {"$round": [{"$arrayElemAt": ["$location.coordinates", 1]}, 3]},
                        "lon": {"$round": [{"$arrayElemAt": ["$location.coordinates", 0]}, 3]}},
                "crashes": {"$sum": 1}}},
    {"$sort": {"crashes": -1}}, {"$limit": 5}]))

# ---------- Index proof ----------
plan = col.find({"borough": "Brooklyn", "hour": 8}).explain()["queryPlanner"]["winningPlan"]
print("\nUses index (IXSCAN)?", "IXSCAN" in str(plan))
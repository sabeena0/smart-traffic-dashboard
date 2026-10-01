import pandas as pd
from pathlib import Path

URL = (
    "https://data.cityofnewyork.us/resource/h9gi-nx95.csv"
    "?$limit=50000"
    "&$where=latitude%20IS%20NOT%20NULL%20AND%20crash_date%3E%272025-01-01%27"
    "&$order=crash_date%20DESC"
)

Path("data").mkdir(exist_ok=True)
df = pd.read_csv(URL)
df.to_csv("data/nyc_collisions.csv", index=False)
print("Downloaded:", df.shape)
import pandas as pd
from pathlib import Path

RAW = Path("data/nyc_collisions.csv")
OUT = Path("data/collisions_clean.csv")

df = pd.read_csv(RAW)
print("Raw shape:", df.shape)

# 1. Drop the junk column and duplicate crashes
df = df.drop(columns=["location"], errors="ignore")
df = df.drop_duplicates(subset="collision_id")

# 2. Keep only rows with valid NYC coordinates
df = df.dropna(subset=["latitude", "longitude"])
df = df[df["latitude"].between(40.4, 41.0) & df["longitude"].between(-74.3, -73.6)]

# 3. Build one proper datetime and derived time fields
df["crash_datetime"] = pd.to_datetime(
    df["crash_date"].str[:10] + " " + df["crash_time"], errors="coerce"
)
df = df.dropna(subset=["crash_datetime"])
df["hour"] = df["crash_datetime"].dt.hour
df["weekday"] = df["crash_datetime"].dt.dayofweek   # 0 = Monday
df["month"] = df["crash_datetime"].dt.month
df["is_weekend"] = df["weekday"] >= 5

# 4. Clean text and number fields
df["borough"] = df["borough"].fillna("UNKNOWN").str.title()
for col in ["number_of_persons_injured", "number_of_persons_killed"]:
    df[col] = df[col].fillna(0).astype(int)
df["has_injury"] = (
    (df["number_of_persons_injured"] + df["number_of_persons_killed"]) > 0
)
df["factor"] = df["contributing_factor_vehicle_1"].fillna("Unspecified")

# 5. Keep only the columns we need
keep = ["collision_id", "crash_datetime", "hour", "weekday", "month", "is_weekend",
        "borough", "zip_code", "latitude", "longitude", "on_street_name",
        "number_of_persons_injured", "number_of_persons_killed",
        "has_injury", "factor"]
df = df[keep]

df.to_csv(OUT, index=False)
print("Clean shape:", df.shape)
print(df.head())
print(df.isna().sum())
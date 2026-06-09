import sys
import numpy as np
import pandas as pd
import requests

KMA_AUTH_KEY = "NS_K7kYZQOmvyu5GGXDp2A"
TARGET_STN_ID = "170"  # 완도
url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfcdd3.php"

p = {
    "tm1": "20250101",
    "tm2": "20251231",
    "stn": TARGET_STN_ID,
    "help": "0",
    "authKey": KMA_AUTH_KEY,
}
res = requests.get(url, params=p, timeout=30)
print("Status:", res.status_code)
lines = res.text.split("\n")
daily_records = []
for line in lines:
    if not line.strip() or line.startswith("#") or line.startswith("/*"):
        continue
    f = line.split()
    if len(f) < 40:
        continue
    daily_records.append({
        "date": f[0],
        "avg_temp": float(f[10]) if f[10] not in ["-9.0", "-9", ""] else None,
        "min_temp": float(f[13]) if f[13] not in ["-9.0", "-9", ""] else None,
        "rainfall": float(f[38]) if f[38] not in ["-9.0", "-9", ""] else 0.0,
        "sunshine": float(f[32]) if f[32] not in ["-9.0", "-9", ""] else 0.0,
    })

print("Parsed records:", len(daily_records))
if daily_records:
    df_daily = pd.DataFrame(daily_records)
    print(df_daily.head())
    print(df_daily.tail())
    cold_days = len(df_daily[df_daily["min_temp"] <= -9.0])
    df_daily["gdd"] = np.maximum(df_daily["avg_temp"] - 10.0, 0)
    gdd_sum = df_daily["gdd"].sum()
    rain_idx = df_daily["rainfall"].sum() / 3.5
    sun_idx = df_daily["sunshine"].sum() * 0.7
    print(f"cold_days: {cold_days}")
    print(f"gdd_sum: {gdd_sum}")
    print(f"rain_idx: {rain_idx}")
    print(f"sun_idx: {sun_idx}")

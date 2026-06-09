import sys
import numpy as np
import pandas as pd
import requests

KMA_AUTH_KEY = "NS_K7kYZQOmvyu5GGXDp2A"
TARGET_STN_ID = "170"  # 완도
STN_MAP = {"108": "서울", "119": "수원", "170": "완도", "192": "진주"}
REG_NAME = STN_MAP.get(TARGET_STN_ID, f"지점({TARGET_STN_ID})")

print(f"=== [1] 기상청 시간자료 API 연동 (대상: {REG_NAME}) ===")
url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"
hourly_records = []

# 1년치 시간자료를 부하 없이 수집 (2025년 1~12월)
for m in range(1, 13):
    end_day = 31 if m in [1, 3, 5, 7, 8, 10, 12] else (28 if m == 2 else 30)
    p = {
        "tm1": f"2025{m:02d}010100",
        "tm2": f"2025{m:02d}{end_day}2300",
        "stn": TARGET_STN_ID,
        "help": "0",
        "authKey": KMA_AUTH_KEY,
    }
    try:
        res = requests.get(url, params=p, timeout=30)
        print(f"Month {m}: status={res.status_code}, len={len(res.text)}")
        if res.status_code == 200 and "AUTH_ERROR" not in res.text:
            lines = res.text.split("\n")
            print(f"First 3 lines of month {m}:")
            for line in lines[:5]:
                print(line)
            count = 0
            for line in lines:
                if not line.strip() or line.startswith("#"):
                    continue
                f = line.split()
                if len(f) < 32:
                    continue
                hourly_records.append(
                    {
                        "date": f[0][:8],
                        "temp": float(f[11]) if f[11] != "-9.0" else None,
                        "rain": float(f[21])
                        if f[21] not in ["-9.0", ""]
                        else 0.0,
                        "sun": float(f[31])
                        if f[31] not in ["-9.0", ""]
                        else 0.0,
                    }
                )
                count += 1
            print(f"Parsed {count} records")
    except Exception as e:
        print(f"Error: {e}")
        continue

print(f"Total hourly records: {len(hourly_records)}")
if hourly_records:
    df = pd.DataFrame(hourly_records)
    df_daily = (
        df.groupby("date")
        .agg(
            avg_temp=("temp", "mean"),
            min_temp=("temp", "min"),
            rainfall=("rain", "sum"),
            sunshine=("sun", "sum"),
        )
        .reset_index()
    )
    print(df_daily.head())
    print(df_daily.tail())
    # 알고리즘 4대 핵심 독립변수 추출
    cold_days = len(df_daily[df_daily["min_temp"] <= -9.0])
    df_daily["gdd"] = np.maximum(df_daily["avg_temp"] - 10.0, 0)
    gdd_sum = df_daily["gdd"].sum()
    rain_idx = df_daily["rainfall"].sum() / 3.5
    sun_idx = df_daily["sunshine"].sum() * 0.7
    X_target = pd.DataFrame(
        [[cold_days, gdd_sum, rain_idx, sun_idx]],
        columns=[
            "extreme_cold_days",
            "gdd_accumulated",
            "rain_drainage_index",
            "solar_typhoon_risk",
        ],
    )
    print("X_target:")
    print(X_target)

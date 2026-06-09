import sys
import numpy as np
import pandas as pd
import requests

KMA_AUTH_KEY = "NS_K7kYZQOmvyu5GGXDp2A"
TARGET_STN_ID = "170"  # 완도
STN_MAP = {"108": "서울", "119": "수원", "170": "완도", "192": "진주"}
REG_NAME = STN_MAP.get(TARGET_STN_ID, f"지점({TARGET_STN_ID})")

print(f"=== [1] 기상청 시간자료 API 연동 (대상: {REG_NAME}) ===")
# Use kma_sfctm3.php for range queries
url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm3.php"
hourly_records = []

# Let's test just one month first
m = 1
end_day = 31
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
        print(f"Number of lines: {len(lines)}")
        count = 0
        for line in lines:
            if not line.strip() or line.startswith("#") or line.startswith("/*"):
                continue
            f = line.split()
            if len(f) < 32:
                continue
            # print some parsed lines
            if count < 5:
                print("Line fields:", f[0], f[1], f[11], f[21], f[31])
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

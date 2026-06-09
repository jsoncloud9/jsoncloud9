import requests

KMA_AUTH_KEY = "NS_K7kYZQOmvyu5GGXDp2A"
TARGET_STN_ID = "170"  # 완도
url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"

# Let's check a sunny day in 2025 (e.g. May 10, 2025)
for hour in ["0800", "1200", "1600", "2000", "2300"]:
    p = {
        "tm": f"20250510{hour}",
        "stn": TARGET_STN_ID,
        "help": "0",
        "authKey": KMA_AUTH_KEY,
    }
    res = requests.get(url, params=p, timeout=5)
    for line in res.text.split("\n"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.split()
        if len(f) < 34:
            continue
        print(f"Time: {f[0]}, TA: {f[11]}, RN_DAY: {f[16]}, SS: {f[33]}")

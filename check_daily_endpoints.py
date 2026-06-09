import requests

KMA_AUTH_KEY = "NS_K7kYZQOmvyu5GGXDp2A"
TARGET_STN_ID = "170"  # 완도
for i in range(1, 10):
    url = f"https://apihub.kma.go.kr/api/typ01/url/kma_sfcdd{i}.php"
    p = {
        "tm1": "20250101",
        "tm2": "20250131",
        "stn": TARGET_STN_ID,
        "help": "0",
        "authKey": KMA_AUTH_KEY,
    }
    try:
        res = requests.get(url, params=p, timeout=5)
        print(f"kma_sfcdd{i}.php: status={res.status_code}, len={len(res.text)}, start={res.text[:100]}")
    except Exception as e:
        print(f"kma_sfcdd{i}.php error: {e}")

import concurrent.futures
import requests
import time

KMA_AUTH_KEY = "NS_K7kYZQOmvyu5GGXDp2A"
TARGET_STN_ID = "170"  # 완도
url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"

# Let's try querying 20 dates concurrently
dates = [f"202505{d:02d}1200" for d in range(1, 21)]

def fetch(date):
    p = {
        "tm": date,
        "stn": TARGET_STN_ID,
        "help": "0",
        "authKey": KMA_AUTH_KEY,
    }
    try:
        res = requests.get(url, params=p, timeout=5)
        if res.status_code == 200 and "AUTH_ERROR" not in res.text:
            return date, res.text
    except Exception as e:
        return date, str(e)
    return date, None

t0 = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(fetch, dates))
t1 = time.time()

print(f"Fetched {len(results)} requests in {t1-t0:.2f}s")
for d, res in results[:3]:
    print(d, "len=", len(res) if res else "None")

import requests
import time

KMA_KEY = "NS_K7kYZQOmvyu5GGXDp2A"
url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfcdd3.php"

p = {
    "tm1": "20250101",
    "tm2": "20251231",
    "stn": "0",
    "help": "0",
    "authKey": KMA_KEY,
}
t0 = time.time()
res = requests.get(url, params=p, timeout=60)
t1 = time.time()
print("Status:", res.status_code)
print("Time taken:", t1-t0)
print("Length of text:", len(res.text))
lines = res.text.split("\n")
valid_lines = [l for l in lines if l.strip() and not l.startswith("#") and not l.startswith("/*")]
print("Total parsed lines:", len(valid_lines))
if valid_lines:
    print("Example lines:")
    for l in valid_lines[:5]:
        print(l)

import requests

KMA_AUTH_KEY = "NS_K7kYZQOmvyu5GGXDp2A"
TARGET_STN_ID = "170"  # 완도
url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"

p = {
    "tm": "202505151200",
    "stn": TARGET_STN_ID,
    "help": "0",
    "authKey": KMA_AUTH_KEY,
}
res = requests.get(url, params=p, timeout=30)
print(f"Status: {res.status_code}")
print(f"Length: {len(res.text)}")
lines = res.text.split("\n")
for line in lines:
    if not line.strip() or line.startswith("#"):
        continue
    print(line)

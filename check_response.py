import requests

KMA_AUTH_KEY = "NS_K7kYZQOmvyu5GGXDp2A"
TARGET_STN_ID = "170"  # 완도
url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm3.php"

p = {
    "tm1": "202501010100",
    "tm2": "202501012300",
    "stn": TARGET_STN_ID,
    "help": "0",
    "authKey": KMA_AUTH_KEY,
}
res = requests.get(url, params=p, timeout=30)
print(f"Status: {res.status_code}")
print(f"Content: {res.text}")

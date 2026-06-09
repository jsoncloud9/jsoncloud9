import requests

KMA_AUTH_KEY = "NS_K7kYZQOmvyu5GGXDp2A"
TARGET_STN_ID = "170"  # 완도
url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"

p = {
    "tm": "202505151200",
    "stn": TARGET_STN_ID,
    "help": "1",
    "authKey": KMA_AUTH_KEY,
}
res = requests.get(url, params=p, timeout=5)
print("help=1 response:")
print(res.text[:3000])

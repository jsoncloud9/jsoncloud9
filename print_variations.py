import requests

KMA_AUTH_KEY = "NS_K7kYZQOmvyu5GGXDp2A"
TARGET_STN_ID = "170"  # 완도
url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"

p = {
    "tm": "202505151200,202505151300",
    "stn": TARGET_STN_ID,
    "help": "0",
    "authKey": KMA_AUTH_KEY,
}
res = requests.get(url, params=p, timeout=5)
print("Comma-separated response:")
print(res.text)

p = {
    "tm": "20250515*",
    "stn": TARGET_STN_ID,
    "help": "0",
    "authKey": KMA_AUTH_KEY,
}
res = requests.get(url, params=p, timeout=5)
print("Wildcard response:")
print(res.text)

import requests

url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfcdd3.php"
p = {
    "tm1": "20250101",
    "tm2": "20251231",
    "stn": "170",
    "help": "0",
    "authKey": "NS_K7kYZQOmvyu5GGXDp2A"
}
res = requests.get(url, params=p, timeout=10)
print("Status:", res.status_code)
print("Length:", len(res.text))
print("Start of response:")
print(res.text[:1000])

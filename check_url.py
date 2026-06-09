import requests

url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm3.php"
p = {
    "tm1": "201512110100",
    "tm2": "201512140000",
    "stn": "108",
    "help": "1",
    "authKey": "NS_K7kYZQOmvyu5GGXDp2A"
}
res = requests.get(url, params=p, timeout=10)
print("Status:", res.status_code)
print("Length:", len(res.text))
print("Start of response:")
print(res.text[:1000])

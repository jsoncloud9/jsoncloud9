import requests

url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfcdd3.php"
p = {
    "tm1": "20151211",
    "tm2": "20151211",
    "stn": "108",
    "help": "1",
    "authKey": "NS_K7kYZQOmvyu5GGXDp2A"
}
res = requests.get(url, params=p, timeout=10)
lines = res.text.split("\n")
print("Help description:")
for line in lines:
    if line.startswith("#") and ":" in line:
        print(line)
print("\nData row format example:")
data_found = False
for line in lines:
    if not line.startswith("#") and line.strip():
        print(line)
        fields = line.split()
        print("Fields split count:", len(fields))
        for i, f in enumerate(fields):
            print(f"{i:2d}: {f}")
        break

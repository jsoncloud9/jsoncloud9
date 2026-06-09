import requests

key = "d6864cc17118d0b988ce8362f956b8501e5339926e672b8b3641aed37ee8fac3"

# Test 1: KMA API Hub
print("[1] 기상청 API 허브 테스트 중...")
url_kma = "https://apihub.kma.go.kr/api/typ01/url/kma_sfcdd3.php"
p_kma = {
    "tm1": "20250101",
    "tm2": "20250101",
    "stn": "108",
    "help": "0",
    "authKey": key
}
try:
    res_kma = requests.get(url_kma, params=p_kma, timeout=10)
    print(f"    - Status Code: {res_kma.status_code}")
    if "AUTH_ERROR" in res_kma.text or "인증오류" in res_kma.text:
        print("    - 결과: 기상청 인증 실패 (AUTH_ERROR)")
    else:
        print("    - 결과: 기상청 인증 성공!")
        print(res_kma.text[:200])
except Exception as e:
    print(f"    - 에러: {e}")

# Test 2: 공공데이터포털 감귤 API
print("\n[2] 공공데이터포털 감귤 API 테스트 중...")
url_citrus = f"http://apis.data.go.kr/1390804/Nihhs_Fruit_Citrus_GrwhInfo/citrusGrwnData?serviceKey={key}"
p_citrus = {
    "pageNo": "1",
    "numOfRows": "1"
}
try:
    res_citrus = requests.get(url_citrus, params=p_citrus, timeout=10)
    print(f"    - Status Code: {res_citrus.status_code}")
    print(f"    - 응답 일부: {res_citrus.text[:200]}")
except Exception as e:
    print(f"    - 에러: {e}")

import sys
import pandas as pd
import requests

# Windows 한글 출력 깨짐 방지
import io
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 기상청 인증키
KMA_KEY = "NS_K7kYZQOmvyu5GGXDp2A"

# 강원도 7개 시(市) 및 ASOS 관측소 ID 매핑
GANGWON_CITIES = {
    "춘천시": "101",
    "원주시": "114",
    "강릉시": "105",
    "동해시": "106",
    "태백시": "216",
    "속초시": "90",
    "삼척시": "106" # 삼척시는 가장 인접한 동해 관측소(106) 사용
}

# 조회할 날짜 범위 설정 (2025년 전체)
START_DATE = "20250101"
END_DATE = "20251231"

print(f"=== 강원도 7개 시의 기온 데이터 수집 시작 ({START_DATE} ~ {END_DATE}) ===")

# API 호출 공통 파라미터
url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfcdd3.php"

# 수집된 데이터를 저장할 리스트
weather_data = []

# 각 도시별로 순차 수집
for city_name, stn_id in GANGWON_CITIES.items():
    print(f"[+] {city_name} (지점코드: {stn_id}) 데이터 수집 중...")
    
    p = {
        "tm1": START_DATE,
        "tm2": END_DATE,
        "stn": stn_id,
        "help": "0",
        "authKey": KMA_KEY
    }
    
    try:
        res = requests.get(url, params=p, timeout=10)
        if res.status_code != 200 or "AUTH_ERROR" in res.text:
            print(f"    [!] {city_name} 데이터 수집 실패")
            continue
            
        lines = res.text.split("\n")
        count = 0
        for line in lines:
            if not line.strip() or line.startswith("#") or line.startswith("/*"):
                continue
            f = line.split()
            if len(f) < 40:
                continue
            
            # f[0]: 날짜 (TM), f[10]: 평균기온 (TA_AVG), f[13]: 최저기온 (TA_MIN)
            date_str = f[0]
            avg_temp = float(f[10]) if f[10] not in ["-9.0", "-9", ""] else None
            min_temp = float(f[13]) if f[13] not in ["-9.0", "-9", ""] else None
            
            # 일최저기온이 -12도 이하인 경우 한파(1)로 기록
            is_cold_wave = 1 if min_temp is not None and min_temp <= -12.0 else 0
            
            weather_data.append({
                "날짜": date_str,
                "도시명": city_name,
                "지점코드": stn_id,
                "일평균기온(℃)": avg_temp,
                "일최저기온(℃)": min_temp,
                "한파여부": is_cold_wave
            })
            count += 1
        print(f"    => {count}개 레코드 로드 완료")
    except Exception as e:
        print(f"    [!] 에러 발생: {e}")

# 판다스 데이터프레임 변환
df = pd.DataFrame(weather_data)

if not df.empty:
    # 날짜 형식 변환 (예: 20250101 -> 2025-01-01)
    df["날짜"] = pd.to_datetime(df["날짜"], format="%Y%m%d").dt.strftime("%Y-%m-%d")
    
    # CSV 파일 저장 (인코딩 utf-8-sig로 설정하여 엑셀 한글 안깨지게 함)
    csv_file = "gangwon_cities_temperature.csv"
    df.to_csv(csv_file, index=False, encoding="utf-8-sig")
    print(f"\n[+] 데이터 수집 완료! 저장 경로: '{csv_file}'")
    
    # 각 도시별 한파일수 요약 정보 산출
    summary_data = []
    print("\n=== [도시별 기온 및 연간 한파일수 요약 리포트 (2025년)] ===")
    for city_name in GANGWON_CITIES.keys():
        df_city = df[df["도시명"] == city_name]
        if not df_city.empty:
            cold_days = df_city["한파여부"].sum()
            avg_t = df_city["일평균기온(℃)"].mean()
            avg_min_t = df_city["일최저기온(℃)"].mean()
            print(f" * {city_name}: 연평균 기온 {avg_t:.1f} ℃ | 평균 최저기온 {avg_min_t:.1f} ℃ | 한파일수: {cold_days} 일")
            
    # 데이터 상위 일부 출력
    print("\n=== 수집된 상세 데이터 샘플 (상위 10개 행) ===")
    print(df.head(10).to_string(index=False))
else:
    print("\n[!] 수집된 데이터가 없습니다.")

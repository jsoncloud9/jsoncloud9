import sys
import numpy as np
import pandas as pd
import requests
from xgboost import XGBClassifier
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import GradientBoostingRegressor

# [1] 기본 설정 및 관측소 매핑 정보
KMA_KEY = "NS_K7kYZQOmvyu5GGXDp2A"
STN_MAP = {"108": "서울", "119": "수원", "170": "완도", "192": "진주"}

# 사용자 지점 선택 메뉴 출력
print("=== [지역 선택 메뉴] ===")
for i, (code, name) in enumerate(STN_MAP.items(), 1):
    print(f"{i}. {name} ({code})")
print("9. 기타 지점 직접 입력")

try:
    choice = input("\n지역을 선택하세요 (기본값 완도: 3): ").strip()
except Exception:
    choice = "3"

if choice == "1":
    STN_ID = "108"
elif choice == "2":
    STN_ID = "119"
elif choice == "3" or choice == "":
    STN_ID = "170"
elif choice == "4":
    STN_ID = "192"
elif choice == "9":
    STN_ID = input("기상청 지점 코드 입력 (예: 제주 184): ").strip()
else:
    if choice in STN_MAP:
        STN_ID = choice
    else:
        print("[!] 알 수 없는 선택으로 기본값 완도(170)로 지정합니다.")
        STN_ID = "170"

REG_NAME = STN_MAP.get(STN_ID, f"지점({STN_ID})")

print(f"\n=== [1] 기상청 일자료 API 연동 (대상: {REG_NAME}) ===")

# [2] 기상청 일자료 분할 수집 함수 (kma_sfcdd3.php 적용으로 1회 호출 수집)
def collect_weather_by_year(year_str):
    url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfcdd3.php"
    p = {
        "tm1": f"{year_str}0101",
        "tm2": f"{year_str}1231",
        "stn": STN_ID, 
        "help": "0", 
        "authKey": KMA_KEY
    }
    try:
        res = requests.get(url, params=p, timeout=30)
        if res.status_code != 200 or "AUTH_ERROR" in res.text:
            return []
        records = []
        for line in res.text.split("\n"):
            if not line.strip() or line.startswith("#") or line.startswith("/*"): 
                continue
            f = line.split()
            if len(f) < 40:
                continue
            # 공식 kma_sfcdd3.php 컬럼 규격 적용
            records.append({
                "date": f[0],
                "temp": float(f[10]) if f[10] not in ["-9.0", "-9", ""] else None,
                "min_t": float(f[13]) if f[13] not in ["-9.0", "-9", ""] else None,
                "rain": float(f[38]) if f[38] not in ["-9.0", "-9", ""] else 0.0,
                "sun": float(f[32]) if f[32] not in ["-9.0", "-9", ""] else 0.0
            })
        return records
    except:
        return []

# [3] 최신 연도 우선 쿼리 후 공백 발생 시 이전 연도 시퀀스 자동 매핑
hourly_records = collect_weather_by_year("2026")
if not hourly_records:
    print("[!] 2026년 공백 확인. 2025년 데이터로 전량 갱신 요청합니다...")
    hourly_records = collect_weather_by_year("2025")

if not hourly_records:
    print("[ERROR] 기상청 API 연동 실패로 분석을 강제 종료합니다.")
    sys.exit()

# [4] 데이터 요약 처리 (시간별 자료 -> 일별 자료 축약 연산)
df = pd.DataFrame(hourly_records)
df_d = df.groupby("date").agg(
    avg_t=("temp", "mean"), 
    min_t=("min_t", "min"),
    rain=("rain", "sum"), 
    sun=("sun", "sum")
).reset_index()

# 인코딩 에러 방지를 위해 이모지 대신 [+] 사용
print(f"[+] 데이터 로드 성공: {df_d['date'].iloc[0]} ~ {df_d['date'].iloc[-1]} ({len(df_d)}일 완료)")

# [5] 물리 피처 가공 알고리즘 반영
cold_days_df = df_d[df_d["min_t"] <= -12.0].copy() # 일최저기온 -12도 이하 (한파 기준)
cold_days = len(cold_days_df)

df_d["gdd"] = np.maximum(df_d["avg_t"] - 10.0, 0)
gdd_sum = df_d["gdd"].sum()
annual_rain = df_d["rain"].sum()
annual_sun = df_d["sun"].sum()

X_target = pd.DataFrame(
    [[cold_days, gdd_sum, annual_rain, annual_sun]],
    columns=["cold_wave_days", "gdd_accumulated", "annual_precipitation", "annual_sunshine"]
)

# [6] AI 예측 가설 적합 모델 빌드 및 학습
X_tr = pd.DataFrame({
    "cold_wave_days": [0, 2, 11, 1, 0, 14, 2, 4, 7, 0],
    "gdd_accumulated": [3300, 2800, 1900, 2700, 3400, 1600, 3050, 2350, 2150, 3250],
    "annual_precipitation": [1190, 1435, 2065, 1120, 980, 2380, 1190, 1610, 1785, 1085], # mm 단위
    "annual_sunshine": [2357, 1971, 1500, 2114, 2400, 1357, 2171, 1886, 1743, 2314]        # 시간 단위
})
y_clf = np.array([2, 2, 0, 2, 2, 0, 2, 1, 1, 2])
clf = XGBClassifier(n_estimators=30, random_state=42).fit(X_tr, y_clf)

# 가로축 잘림 버그 방지를 위해 타겟 행렬을 안전한 형태로 분할 선언
X_reg = X_tr[y_clf > 0]
y_reg_list = [
    [2250, 8.6, 1.5, 1.1, 3.4],
    [1980, 8.2, 4.5, 1.9, 4.0],
    [2380, 8.9, 1.2, 0.6, 4.9],
    [1650, 7.6, 13.5, 4.8, 2.3],
    [2100, 8.4, 2.5, 1.3, 3.6],
    [1750, 7.9, 10.0, 4.2, 2.9],
    [1580, 7.4, 14.0, 5.2, 2.0],
    [2200, 8.5, 2.1, 1.2, 3.5]
]
y_reg = pd.DataFrame(y_reg_list)

reg = MultiOutputRegressor(GradientBoostingRegressor(random_state=42)).fit(X_reg, y_reg)

# [7] 모델 가동 및 분석 통계 출력
print(f"\n=== [2] AI 모델 예측 결과 리포트 (대상: {REG_NAME}) ===")
pred_suit = clf.predict(X_target)[0]
# 인코딩 에러를 막기 위해 유니코드 이모지 대신 일반 기호 적용
suit_map = {0: "[X] 재배 불가 지역", 1: "[!] 시험재배 가능 지역", 2: "[O] 상업재배 가능 최적 지역"}
print(f"▶ [1단계 적합성 결과] {REG_NAME}: {suit_map[pred_suit]}")

# 동해 임계 조건 비교 상세 정보 출력
print("\n▶ [동해(한파) 위험 분석 및 임계 조건 비교]")
print(f"   - 분석 기준 최저 온도 (한파 기준)   : -12.0 ℃ 이하")
print(f"   - 해당 지역 연간 한파일수 (산출값) : {cold_days} 일")
print(f"   - [판정 기준 (임계치)]")
print(f"     * 최적 지역 (상업재배 가능) : 2일 이하")
print(f"     * 한계 지역 (시험재배 가능) : 3일 ~ 9일")
print(f"     * 불가 지역 (동해 피해 위험) : 10일 이상 (임계 초과)")

if cold_days >= 10:
    print(f"   => 판정 결과: [동해 조건 초과] 연간 한파일수가 임계치(10일)를 초과하여 재배가 불가능합니다. (초과일수: {cold_days - 9}일)")
elif cold_days >= 3:
    print(f"   => 판정 결과: [조건 한계 경계] 일부 동해 피해 위험이 있어 시험재배만 권장합니다.")
else:
    print(f"   => 판정 결과: [조건 충족 안전] 한파 발생 빈도가 매우 낮아 안전한 상업재배가 가능합니다.")

if cold_days > 0:
    print(f"\n▶ [한파 일수 상세 기록]")
    for idx, row in enumerate(cold_days_df.itertuples(), 1):
        dt_str = f"{row.date[:4]}년 {row.date[4:6]}월 {row.date[6:8]}일"
        print(f"     {idx}) {dt_str}: {row.min_t:.1f} ℃")

print()
if pred_suit > 0:
    out = reg.predict(X_target)[0]
    print(f"▶ [2단계 상세 예측 지표]")
    print(f"   - 실제 기후 연동 예상 수량    : {out[0]:.1f} kg/10a")
    print(f"   - 예측 과실 품질(당·산도) 점수: {out[1]:.2f} / 10.0")
    print(f"   - 기습 한파 동해 피해 확률    : {out[2]:.1f} %")
    print(f"   - 가을철 야간 온도 착색불량도 : {out[3]:.1f} 점")
    print(f"   - 기온 상승 연동 병해충 위험도 : {out[4]:.1f} 점")
else:
    print("▶ 동해 발생 조건 초과(한파 임계 돌파)로 인해 2단계 상세 지표 추론을 차단합니다.")

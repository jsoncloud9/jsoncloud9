import sys
import numpy as np
import pandas as pd
import requests
from flask import Flask, request, jsonify
from xgboost import XGBClassifier
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import GradientBoostingRegressor

app = Flask(__name__)

# [1] 기상청 인증키
KMA_KEY = "NS_K7kYZQOmvyu5GGXDp2A"

# 226개 기초자치단체 목록 및 ASOS 관측소 ID 매핑
MUNI_STN_MAP = {
    # 서울
    "서울 종로구": "108", "서울 중구": "108", "서울 용산구": "108", "서울 성동구": "108", "서울 광진구": "108",
    "서울 동대문구": "108", "서울 중랑구": "108", "서울 성북구": "108", "서울 강북구": "108", "서울 도봉구": "108",
    "서울 노원구": "108", "서울 은평구": "108", "서울 서대문구": "108", "서울 마포구": "108", "서울 양천구": "108",
    "서울 강서구": "108", "서울 구로구": "108", "서울 금천구": "108", "서울 영등포구": "108", "서울 동작구": "108",
    "서울 관악구": "108", "서울 서초구": "108", "서울 강남구": "108", "서울 송파구": "108", "서울 강동구": "108",
    # 부산
    "부산 중구": "159", "부산 서구": "159", "부산 동구": "159", "부산 영도구": "159", "부산 부산진구": "159",
    "부산 동래구": "159", "부산 남구": "159", "부산 북구": "159", "부산 해운대구": "159", "부산 사하구": "159",
    "부산 금정구": "159", "부산 강서구": "159", "부산 연제구": "159", "부산 수영구": "159", "부산 사상구": "159",
    "부산 기장군": "159",
    # 대구
    "대구 중구": "143", "대구 동구": "143", "대구 서구": "143", "대구 남구": "143", "대구 북구": "143",
    "대구 수성구": "143", "대구 달서구": "143", "대구 달성군": "143", "대구 군위군": "136",
    # 인천
    "인천 중구": "112", "인천 동구": "112", "인천 미추홀구": "112", "인천 연수구": "112", "인천 남동구": "112",
    "인천 부평구": "112", "인천 계양구": "112", "인천 서구": "112", "인천 강화군": "201", "인천 옹진군": "112",
    # 광주
    "광주 동구": "156", "광주 서구": "156", "광주 남구": "156", "광주 북구": "156", "광주 광산구": "156",
    # 대전
    "대전 동구": "133", "대전 중구": "133", "대전 서구": "133", "대전 유성구": "133", "대전 대덕구": "133",
    # 울산
    "울산 중구": "152", "울산 남구": "152", "울산 동구": "152", "울산 북구": "152", "울산 울주군": "152",
    # 세종
    "세종특별자치시": "133",
    # 경기
    "경기 수원시": "119", "경기 성남시": "119", "경기 의정부시": "98", "경기 안양시": "119",
    "경기 부천시": "112", "경기 광명시": "108", "경기 평택시": "119", "경기 동두천시": "98", "경기 안산시": "119",
    "경기 고양시": "99", "경기 과천시": "108", "경기 구리시": "108", "경기 남양주시": "108", "경기 오산시": "119",
    "경기 시흥시": "112", "경기 군포시": "119", "경기 의왕시": "119", "경기 하남시": "108", "경기 용인시": "119",
    "경기 파주시": "99", "경기 이천시": "203", "경기 안성시": "203", "경기 김포시": "112", "경기 화성시": "119",
    "경기 광주시": "202", "경기 양주시": "98", "경기 포천시": "98", "경기 여주시": "203", "경기 연천군": "99",
    "경기 가평군": "202", "경기 양평군": "202",
    # 강원
    "강원 춘천시": "101", "강원 원주시": "114", "강원 강릉시": "105", "강원 동해시": "106", "강원 태백시": "216",
    "강원 속초시": "90", "강원 삼척시": "106", "강원 홍천군": "101", "강원 횡성군": "114", "강원 영월군": "114",
    "강원 평창군": "114", "강원 정선군": "114", "강원 철원군": "101", "강원 화천군": "101", "강원 양구군": "101",
    "강원 인제군": "101", "강원 고성군": "90", "강원 양양군": "90",
    # 충북
    "충북 청주시": "131", "충북 충주시": "127", "충북 제천시": "221", "충북 보은군": "131", "충북 옥천군": "131",
    "충북 영동군": "131", "충북 증평군": "131", "충북 진천군": "131", "충북 괴산군": "127", "충북 음성군": "127",
    "충북 단양군": "221",
    # 충남
    "충남 천안시": "232", "충남 공주시": "232", "충남 보령시": "235", "충남 아산시": "232", "충남 서산시": "129",
    "충남 논산시": "236", "충남 계룡시": "236", "충남 당진시": "129", "충남 금산군": "238", "충남 부여군": "236",
    "충남 서천군": "235", "충남 청양군": "236", "충남 홍성군": "129", "충남 예산군": "129", "충남 태안군": "129",
    # 전북
    "전북 전주시": "146", "전북 군산시": "140", "전북 익산시": "140", "전북 정읍시": "245", "전북 남원시": "247",
    "전북 김제시": "146", "전북 완주군": "146", "전북 진안군": "244", "전북 무주군": "247", "전북 장수군": "244",
    "전북 임실군": "244", "전북 순창군": "245", "전북 고창군": "243", "전북 부안군": "243",
    # 전남
    "전남 목포시": "165", "전남 여수시": "168", "전남 순천시": "174", "전남 광양시": "174", "전남 담양군": "156",
    "전남 곡성군": "174", "전남 구례군": "174", "전남 고흥군": "262", "전남 보성군": "262", "전남 화순군": "156",
    "전남 장흥군": "260", "전남 강진군": "260", "전남 해남군": "261", "전남 영암군": "261", "전남 무안군": "165",
    "전남 함평군": "165", "전남 영광군": "165", "전남 장성군": "156", "전남 완도군": "170", "전남 진도군": "268",
    "전남 신안군": "165",
    # 경북
    "경북 포항시": "138", "경북 경주시": "138", "경북 김천시": "137", "경북 안동시": "136", "경북 구미시": "279",
    "경북 영주시": "272", "경북 영천시": "138", "경북 상주시": "137", "경북 문경시": "137", "경북 경산시": "143",
    "경북 의성군": "136", "경북 청송군": "136", "경북 영양군": "136", "경북 영덕군": "130", "경북 청도군": "143",
    "경북 고령군": "143", "경북 성주군": "279", "경북 칠곡군": "279", "경북 예천군": "136", "경북 봉화군": "272",
    "경북 울진군": "130", "경북 울릉군": "115",
    # 경남
    "경남 창원시": "155", "경남 진주시": "192", "경남 통영시": "162", "경남 사천시": "192", "경남 김해시": "159",
    "경남 밀양시": "288", "경남 거제시": "294", "경남 양산시": "159", "경남 의령군": "192", "경남 함안군": "192",
    "경남 창녕군": "288", "경남 고성군": "162", "경남 남해군": "295", "경남 하동군": "192", "경남 산청군": "289",
    "경남 함양군": "284", "경남 거창군": "284", "경남 합천군": "192",
    # 제주
    "제주 제주시": "184", "제주 서귀포시": "189"
}

# 영문 및 중복 제거 목록 정형화
cleaned_muni_map = {}
for k, v in MUNI_STN_MAP.items():
    if any(c.isalpha() and ord(c) < 128 for c in k) or k.endswith("2"):
        continue
    cleaned_muni_map[k] = v

# [2] AI 모델 사전 학습 (스케일 보정 없이 실제 물리 단위를 직접 학습 데이터로 사용)
X_tr = pd.DataFrame({
    "cold_wave_days": [0, 2, 11, 1, 0, 14, 2, 4, 7, 0],
    "gdd_accumulated": [3300, 2800, 1900, 2700, 3400, 1600, 3050, 2350, 2150, 3250],
    "annual_precipitation": [1190, 1435, 2065, 1120, 980, 2380, 1190, 1610, 1785, 1085], # mm
    "annual_sunshine": [2357, 1971, 1500, 2114, 2400, 1357, 2171, 1886, 1743, 2314]        # 시간
})
y_clf = np.array([2, 2, 0, 2, 2, 0, 2, 1, 1, 2])
clf = XGBClassifier(n_estimators=30, random_state=42).fit(X_tr, y_clf)

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

# 평가지표 판정 기준 매핑용 헬퍼 함수
def get_cold_status(val):
    if val <= 2: return "최적", f"{val:d}일 (기준: <=2일 최적)"
    elif val <= 9: return "한계", f"{val:d}일 (기준: 3~9일 한계)"
    else: return "불가", f"{val:d}일 (기준: >=10일 불가)"

def get_heat_status(val):
    if val == 0: return "최적", f"{val:d}일 (기준: 0일 최적)"
    elif val <= 5: return "한계", f"{val:d}일 (기준: 1~5일 한계)"
    else: return "불가", f"{val:d}일 (기준: >=6일 불가)"

def get_gdd_status(val):
    if val >= 2500: return "최적", f"{val:.1f} (기준: >=2500 최적)"
    elif val >= 2000: return "한계", f"{val:.1f} (기준: 2000~2499 한계)"
    else: return "불가", f"{val:.1f} (기준: <2000 불가)"

def get_rain_status(val):
    if val <= 1575: return "최적", f"{val:.1f}mm (기준: <=1575mm 최적)"
    elif val <= 1925: return "한계", f"{val:.1f}mm (기준: 1576~1925mm 한계)"
    else: return "불가", f"{val:.1f}mm (기준: >1925mm 불가)"

def get_sun_status(val):
    if val >= 1928: return "최적", f"{val:.1f}시간 (기준: >=1928시간 최적)"
    elif val >= 1571: return "한계", f"{val:.1f}시간 (기준: 1571~1927시간 한계)"
    else: return "불가", f"{val:.1f}시간 (기준: <1571시간 불가)"

@app.route('/predict', methods=['GET'])
def predict_suitability():
    # 파라미터 수집 (muni: 기초자치단체명, year: 조회연도)
    muni_name = request.args.get('muni', '').strip()
    year = request.args.get('year', '2025').strip()
    
    if not muni_name:
        return jsonify({"error": "muni 파라미터가 누락되었습니다. (예: ?muni=경기 수원시)"}), 400
        
    if muni_name not in cleaned_muni_map:
        return jsonify({"error": f"지원하지 않거나 올바르지 않은 자치단체명입니다. 입력값: '{muni_name}'"}), 400
        
    stn_id = cleaned_muni_map[muni_name]
    
    # 기상청 일자료 조회
    url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfcdd3.php"
    p = {
        "tm1": f"{year}0101",
        "tm2": f"{year}1231",
        "stn": stn_id,
        "help": "0",
        "authKey": KMA_KEY
    }
    
    try:
        res = requests.get(url, params=p, timeout=20)
        if res.status_code != 200 or "AUTH_ERROR" in res.text:
            return jsonify({"error": "기상청 API 연동 오류 발생"}), 500
    except Exception as e:
        return jsonify({"error": f"API 호출 에러: {str(e)}"}), 500
        
    lines = res.text.split("\n")
    records = []
    for line in lines:
        if not line.strip() or line.startswith("#") or line.startswith("/*"):
            continue
        f = line.split()
        if len(f) < 40:
            continue
        records.append({
            "temp": float(f[10]) if f[10] not in ["-9.0", "-9", ""] else 0.0,
            "min_t": float(f[13]) if f[13] not in ["-9.0", "-9", ""] else 0.0,
            "rain": float(f[38]) if f[38] not in ["-9.0", "-9", ""] else 0.0,
            "sun": float(f[32]) if f[32] not in ["-9.0", "-9", ""] else 0.0
        })
        
    if not records:
        return jsonify({"error": f"{year}년도 관측 데이터가 존재하지 않습니다."}), 404
        
    df_stn = pd.DataFrame(records)
    
    # 5대 피처 계산
    cold_days = len(df_stn[df_stn["min_t"] <= -12.0])
    heat_days = len(df_stn[df_stn["temp"] >= 30.0])
    df_stn["gdd"] = np.maximum(df_stn["temp"] - 10.0, 0)
    gdd_sum = df_stn["gdd"].sum()
    annual_rain = df_stn["rain"].sum()
    annual_sun = df_stn["sun"].sum()
    
    # 1단계 적합성 예측
    X_target = pd.DataFrame(
        [[cold_days, gdd_sum, annual_rain, annual_sun]],
        columns=["cold_wave_days", "gdd_accumulated", "annual_precipitation", "annual_sunshine"]
    )
    pred_suit = int(clf.predict(X_target)[0])
    suit_labels = {0: "재배 불가", 1: "시험 재배", 2: "상업 최적"}
    
    # 지표별 상세 판정
    c_status, c_msg = get_cold_status(cold_days)
    h_status, h_msg = get_heat_status(heat_days)
    g_status, g_msg = get_gdd_status(gdd_sum)
    r_status, r_msg = get_rain_status(annual_rain)
    s_status, s_msg = get_sun_status(annual_sun)
    
    # 2단계 예측 지표 (상업/시험재배 적합지일 경우)
    detailed_metrics = {}
    if pred_suit > 0:
        out = reg.predict(X_target)[0]
        detailed_metrics = {
            "expected_yield_kg_10a": round(float(out[0]), 1),
            "quality_score_10": round(float(out[1]), 2),
            "freeze_risk_pct": round(float(out[2]), 1),
            "coloring_fault_score": round(float(out[3]), 1),
            "disease_pest_score": round(float(out[4]), 1)
        }
        
    return jsonify({
        "municipality": muni_name,
        "station_id": stn_id,
        "analysis_year": year,
        "suitability_code": pred_suit,
        "suitability_result": suit_labels[pred_suit],
        "physical_indicators": {
            "cold_wave_days": {"value": cold_days, "status": c_status, "detail": c_msg},
            "heat_stress_days": {"value": heat_days, "status": h_status, "detail": h_msg},
            "gdd_accumulated": {"value": round(gdd_sum, 1), "status": g_status, "detail": g_msg},
            "annual_precipitation_mm": {"value": round(annual_rain, 1), "status": r_status, "detail": r_msg},
            "annual_sunshine_hours": {"value": round(annual_sun, 1), "status": s_status, "detail": s_msg}
        },
        "secondary_predictions": detailed_metrics
    })

@app.route('/municipalities', methods=['GET'])
def list_municipalities():
    return jsonify({"municipalities": sorted(list(cleaned_muni_map.keys()))})

if __name__ == '__main__':
    # Flask 앱 실행 (포트 5000)
    print("[+] 기후 적합성 분석 웹 API 서버 시작 중...")
    app.run(host='0.0.0.0', port=5000, debug=True)

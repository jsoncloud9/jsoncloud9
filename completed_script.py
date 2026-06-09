import sys
import numpy as np
import pandas as pd
import requests
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from xgboost import XGBClassifier

# [기상청 인증키 및 설정]
KMA_AUTH_KEY = "NS_K7kYZQOmvyu5GGXDp2A"
TARGET_STN_ID = "170"  # 완도: 170, 진주: 192, 수원: 119
STN_MAP = {"108": "서울", "119": "수원", "170": "완도", "192": "진주"}
REG_NAME = STN_MAP.get(TARGET_STN_ID, f"지점({TARGET_STN_ID})")

print(f"=== [1] KMA Hourly Data API (Target: {REG_NAME}) ===")
url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfctm2.php"
hourly_records = []

# 1년치 시간자료를 부하 없이 수집
for m in range(1, 13):
    end_day = 31 if m in [1, 3, 5, 7, 8, 10, 12] else (28 if m == 2 else 30)
    p = {
        "tm1": f"2025{m:02d}010100",
        "tm2": f"2025{m:02d}{end_day}2300",
        "stn": TARGET_STN_ID,
        "help": "0",
        "authKey": KMA_AUTH_KEY,
    }
    try:
        res = requests.get(url, params=p, timeout=30)
        if res.status_code == 200 and "AUTH_ERROR" not in res.text:
            for line in res.text.split("\n"):
                if not line.strip() or line.startswith("#"):
                    continue
                f = line.split()
                if len(f) < 34:
                    continue
                hourly_records.append(
                    {
                        "date": f[0][:8],
                        "temp": float(f[11]) if f[11] != "-9.0" else None,
                        "rain": float(f[21])
                        if f[21] not in ["-9.0", ""]
                        else 0.0,
                        "sun": float(f[31])
                        if f[31] not in ["-9.0", ""]
                        else 0.0,
                    }
                )
    except Exception:
        continue

if not hourly_records:
    print("[-] Data collection failed"); sys.exit()

# 시간별 데이터를 일별 데이터로 가공 (다운샘플링)
df = pd.DataFrame(hourly_records)
df_daily = (
    df.groupby("date")
    .agg(
        avg_temp=("temp", "mean"),
        min_temp=("temp", "min"),
        rainfall=("rain", "sum"),
        sunshine=("sun", "sum"),
    )
    .reset_index()
)
print(
    f"[+] Collection Complete: {df_daily['date'].iloc[0]}~{df_daily['date'].iloc[-1]} ({len(df_daily)} days)"
)

# 알고리즘 4대 핵심 독립변수 추출
cold_days = len(df_daily[df_daily["min_temp"] <= -9.0])
df_daily["gdd"] = np.maximum(df_daily["avg_temp"] - 10.0, 0)
gdd_sum = df_daily["gdd"].sum()
rain_idx = df_daily["rainfall"].sum() / 3.5
sun_idx = df_daily["sunshine"].sum() * 0.7
X_target = pd.DataFrame(
    [[cold_days, gdd_sum, rain_idx, sun_idx]],
    columns=[
        "extreme_cold_days",
        "gdd_accumulated",
        "rain_drainage_index",
        "solar_typhoon_risk",
    ],
)

# ---- [AI 모델 빌드 및 학습] ----
X_tr = pd.DataFrame(
    {
        "extreme_cold_days": [0, 2, 11, 1, 0, 14, 2, 4, 7, 0],
        "gdd_accumulated": [
            3300,
            2800,
            1900,
            2700,
            3400,
            1600,
            3050,
            2350,
            2150,
            3250,
        ],
        "rain_drainage_index": [415, 340, 210, 310, 480, 180, 360, 280, 240, 430],
        "solar_typhoon_risk": [1450, 1380, 1150, 1300, 1550, 1020, 1410, 1280, 1220, 1510],
    }
)

# 회귀용 다중 출력 타겟 데이터 (재배 적합도 점수, 예상 수확량)
y_tr_reg = pd.DataFrame(
    {
        "suitability_score": [95, 80, 25, 75, 98, 15, 88, 60, 50, 92],
        "expected_yield": [45.2, 38.0, 12.5, 35.8, 48.0, 8.2, 41.5, 28.0, 23.5, 43.8]
    }
)

# 분류용 타겟 데이터 (재배 등급: 0=부적합, 1=한계, 2=적합)
y_tr_clf = pd.Series([2, 1, 0, 1, 2, 0, 2, 1, 0, 2])

# 1. 다중 출력 회귀 모델 학습 (GradientBoostingRegressor 기반)
reg_model = MultiOutputRegressor(GradientBoostingRegressor(random_state=42))
reg_model.fit(X_tr, y_tr_reg)

# 2. 분류 모델 학습 (XGBClassifier 기반)
clf_model = XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42)
clf_model.fit(X_tr, y_tr_clf)

# ---- [대상 지점 예측 실행 및 결과 출력] ----
pred_reg = reg_model.predict(X_target)[0]
pred_clf = clf_model.predict(X_target)[0]

class_labels = {0: "Unsuitable", 1: "Marginal", 2: "Suitable"}
predicted_class_name = class_labels.get(pred_clf, "Unknown")

print("\n=== [2] Climate Analysis Results ===")
print(f"Target Region: {REG_NAME} (Station ID: {TARGET_STN_ID})")
print(f"- Extreme Cold Days: {cold_days} days")
print(f"- GDD Accumulated: {gdd_sum:.2f} GDD")
print(f"- Rain Drainage Index: {rain_idx:.2f}")
print(f"- Solar Typhoon Risk: {sun_idx:.2f}")

print("\n=== [3] AI Predictions ===")
print(f"- Predicted Cultivation Suitability Score: {pred_reg[0]:.2f} / 100")
print(f"- Predicted Expected Yield (tons/ha): {pred_reg[1]:.2f}")
print(f"- Predicted Suitability Class: {predicted_class_name} (Class {pred_clf})")

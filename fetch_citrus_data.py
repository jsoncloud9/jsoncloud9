import requests
import xml.etree.ElementTree as ET

def fetch_citrus_growth_data(service_key, page_no=1, num_rows=10):
    """
    농촌진흥청 국립원예특작과학원 감귤연구소 API를 호출하여
    감귤 생육 및 품질 조사 데이터를 가져옵니다.
    (공공데이터포털 공식 요청 주소 반영)
    """
    # [수정] 공식 상세 페이지에 기재된 정확한 요청 주소(Endpoint)로 변경
    base_url = "http://apis.data.go.kr/1390804/Nihhs_Fruit_Citrus_GrwhInfo/citrusGrwnData"
    
    # 이중 인코딩 방지를 위해 서비스키 결합
    request_url = f"{base_url}?serviceKey={service_key}"
    
    params = {
        'pageNo': str(page_no),
        'numOfRows': str(num_rows)
    }
    
    try:
        response = requests.get(request_url, params=params, timeout=10)
        
        # 응답 상태 확인
        if response.status_code != 200:
            print(f"[-] API 요청 실패 (Status Code: {response.status_code})")
            return None
            
        print("[+] API 응답 수신 완료 (Status 200). 응답 데이터 분석 중...")
        
        # XML 데이터 파싱
        root = ET.fromstring(response.text)
        
        # 에러 메시지 체크 (인증키 오류 등)
        header_code = root.find('.//resultCode')
        if header_code is not None and header_code.text != "00":
            header_msg = root.find('.//resultMsg')
            msg_text = header_msg.text if header_msg is not None else "Unknown Error"
            print(f"[-] 공공데이터포털 에러 발생 ({header_code.text}): {msg_text}")
            return None
            
        items = root.findall('.//item')
        if not items:
            print("[!] 조회된 감귤 생육 데이터가 없습니다.")
            print(f"응답 본문 일부: {response.text[:500]}")
            return []
            
        citrus_dataset = []
        for item in items:
            data = {
                "year": item.findtext("examYear"),
                "area_name": item.findtext("areaName"),
                "spcs_name": item.findtext("spcsName"),
                "bud_date": item.findtext("budDate"),
                "flower_date": item.findtext("flwrDate"),
                "sugar_degree": item.findtext("brix"),
                "acid_degree": item.findtext("acid")
            }
            citrus_dataset.append(data)
            
        return citrus_dataset
        
    except requests.exceptions.Timeout:
        print("[-] API 호출 시간 초과 (Timeout)")
        return None
    except ET.ParseError:
        print("[-] XML 파싱 실패 (응답 데이터 형식을 확인하세요)")
        print(f"원문 데이터 일부: {response.text[:200]}")
        return None
    except Exception as e:
        print(f"[-] 예기치 못한 오류 발생: {e}")
        return None

if __name__ == "__main__":
    MY_SERVICE_KEY = "d6864cc17118d0b988ce8362f956b8501e5339926e672b8b3641aed37ee8fac3"
    
    print("[1] 감귤연구소 공공 데이터 조회를 시작합니다...")
    data_list = fetch_citrus_growth_data(MY_SERVICE_KEY, page_no=1, num_rows=5)
    
    if data_list:
        print(f"\n[✔] 총 {len(data_list)}개의 감귤 생육/품질 데이터를 성공적으로 가져왔습니다.")
        print("-" * 60)
        for idx, item in enumerate(data_list, start=1):
            print(f"[{idx}] {item['year']}년 | 지역: {item['area_name']} | 품종: {item['spcs_name']}")
            print(f"    - 생육 단계: 발아기({item['bud_date']}), 만개기({item['flower_date']})")
            print(f"    - 과실 품질: 당도({item['sugar_degree']} Brix), 산도({item['acid_degree'] or '미측정'} %)")
            print("-" * 60)

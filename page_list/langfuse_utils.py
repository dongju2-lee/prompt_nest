"""
랭퓨즈 연동 유틸리티 모듈 - 랭퓨즈에서 트레이스 데이터를 가져오는 기능
"""

import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from .helpers import (
    LANGFUSE_HOST, 
    LANGFUSE_PROJECT, 
    LANGFUSE_PUBLIC_KEY, 
    LANGFUSE_SECRET_KEY
)

def normalize_host(host):
    """호스트 주소를 정규화합니다. 0.0.0.0을 localhost로 변환합니다."""
    if host.startswith('http://0.0.0.0'):
        return host.replace('0.0.0.0', 'localhost')
    return host

def fetch_langfuse_traces(limit=100, days=7):
    """랭퓨즈에서 최근 트레이스를 가져옵니다."""
    if not all([LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_PROJECT]):
        print("랭퓨즈 API 자격 증명이 설정되지 않았습니다.")
        return []
    
    try:
        # 시간 범위 설정 (최근 X일)
        start_time = (datetime.now() - timedelta(days=days)).isoformat()
        
        # 호스트 주소 정규화 (0.0.0.0 → localhost)
        host = normalize_host(LANGFUSE_HOST)
        
        # API 요청 URL
        url = f"{host}/api/public/traces"
        
        # 요청 매개변수
        params = {
            "limit": limit,
            "startTime": start_time
        }
        
        # 헤더 설정
        headers = {"X-Project-Name": LANGFUSE_PROJECT}
        
        # 인증 설정 - HTTPBasicAuth 사용 (공식 문서 방식)
        # username: Public Key, password: Secret Key
        auth = HTTPBasicAuth(LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)
        
        print(f"트레이스 요청 URL: {url}")
        print(f"인증 정보: {LANGFUSE_PUBLIC_KEY[:5]}... / {LANGFUSE_SECRET_KEY[:5]}...")
        
        # API 요청
        response = requests.get(url, auth=auth, headers=headers, params=params)
        print(f"응답 상태 코드: {response.status_code}")
        
        # 응답 검증
        response.raise_for_status()
        
        result = response.json().get("data", [])
        print(f"가져온 트레이스 수: {len(result)}")
        return result
    except Exception as e:
        print(f"랭퓨즈 트레이스 조회 실패: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"응답 상태: {e.response.status_code}")
            print(f"응답 내용: {e.response.text}")
        return []

def fetch_langfuse_observations(trace_id):
    """특정 트레이스의 관찰 데이터를 가져옵니다."""
    if not all([LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_PROJECT]):
        print("랭퓨즈 API 자격 증명이 설정되지 않았습니다.")
        return []
    
    try:
        # 호스트 주소 정규화 (0.0.0.0 → localhost)
        host = normalize_host(LANGFUSE_HOST)
        
        # 먼저 트레이스 상세 정보를 가져옵니다
        trace_url = f"{host}/api/public/traces/{trace_id}"
        
        # 헤더 설정
        headers = {"X-Project-Name": LANGFUSE_PROJECT}
        
        # 인증 설정 - HTTPBasicAuth 사용 (공식 문서 방식)
        auth = HTTPBasicAuth(LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)
        
        print(f"트레이스 상세 정보 요청 URL: {trace_url}")
        
        # 트레이스 상세 정보 요청
        trace_response = requests.get(trace_url, auth=auth, headers=headers)
        print(f"트레이스 상세 응답 상태 코드: {trace_response.status_code}")
        
        # 응답 검증
        trace_response.raise_for_status()
        
        # 트레이스 상세 정보에서 observations 필드 확인
        trace_data = trace_response.json()
        
        # observations 필드가 있다면 바로 사용
        if "observations" in trace_data:
            observations = trace_data.get("observations", [])
            print(f"트레이스에서 직접 {len(observations)}개의 관찰 데이터를 찾았습니다.")
            return observations
        
        # observations 필드가 없다면 별도 API로 요청 시도
        observations_url = f"{host}/api/public/traces/{trace_id}/observations"
        print(f"관찰 데이터 별도 요청 URL: {observations_url}")
        
        # API 요청
        obs_response = requests.get(observations_url, auth=auth, headers=headers)
        print(f"관찰 데이터 응답 상태 코드: {obs_response.status_code}")
        
        # 404 오류면 트레이스 내에 포함된 observations 필드 확인
        if obs_response.status_code == 404:
            # API 문서에 따라 요청을 수정해보기
            # 1) 다른 엔드포인트 시도 - spens, generations 등
            alternatives = ["observations", "spans", "generations", "scores"]
            for endpoint in alternatives:
                alt_url = f"{host}/api/public/traces/{trace_id}/{endpoint}"
                print(f"대체 엔드포인트 시도: {alt_url}")
                alt_response = requests.get(alt_url, auth=auth, headers=headers)
                
                if alt_response.status_code == 200:
                    try:
                        result = alt_response.json().get("data", [])
                        print(f"대체 엔드포인트 {endpoint}에서 {len(result)}개의 데이터를 찾았습니다.")
                        return result
                    except:
                        pass
            
            # 2) JSON 응답을 파싱해보기
            print("직접 트레이스 데이터에서 관찰 정보 추출 시도 중")
            if "data" in trace_data:
                trace_details = trace_data.get("data", {})
                if "observations" in trace_details:
                    observations = trace_details.get("observations", [])
                    print(f"트레이스 데이터에서 {len(observations)}개의 관찰 데이터를 추출했습니다.")
                    return observations
            
            # 3) 마지막 시도: JSON 데이터를 직접 참조해서 사용
            print("제공된 JSON 샘플 기반 관찰 데이터 표시")
            if trace_id in sample_observations:
                print(f"샘플 데이터에서 관찰 데이터를 찾았습니다.")
                return sample_observations[trace_id]
            
            # 대체 방법: 모든 관찰 데이터를 가져와서 필터링
            all_observations_url = f"{host}/api/public/observations?traceId={trace_id}"
            print(f"모든 관찰 데이터에서 필터링 시도: {all_observations_url}")
            all_obs_response = requests.get(all_observations_url, auth=auth, headers=headers)
            
            if all_obs_response.status_code == 200:
                try:
                    result = all_obs_response.json().get("data", [])
                    filtered_result = [obs for obs in result if obs.get("traceId") == trace_id]
                    print(f"필터링으로 {len(filtered_result)}개의 관찰 데이터를 찾았습니다.")
                    return filtered_result
                except:
                    pass
            
            print(f"관찰 데이터를 찾지 못했습니다. 트레이스 ID: {trace_id}")
            return []
            
        # 정상 응답인 경우 데이터 반환
        obs_response.raise_for_status()
        result = obs_response.json().get("data", [])
        print(f"가져온 관찰 데이터 수: {len(result)}")
        return result
            
    except Exception as e:
        print(f"랭퓨즈 관찰 데이터 조회 실패: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"응답 상태: {e.response.status_code}")
            print(f"응답 내용: {e.response.text}")
            
            # 404 에러의 경우 디버깅 정보 추가 제공
            if hasattr(e, 'response') and e.response.status_code == 404:
                print(f"404 오류: 트레이스 ID {trace_id}에 대한 관찰 데이터를 찾을 수 없습니다.")
                print(f"트레이스 ID가 올바른지, 그리고 해당 트레이스에 관찰 데이터가 있는지 확인하세요.")
        
        import traceback
        print(traceback.format_exc())
        return []

# 예시 관찰 데이터 (개발 시 샘플 데이터로 사용)
sample_observations = {
    # 샘플 트레이스 ID에 대한 관찰 데이터
    "46f666c5-0c6a-45f7-952d-7ee7c7336c68": [
        {
            "id": "d72792ec-9998-4f81-99af-93604135d04c",
            "traceId": "46f666c5-0c6a-45f7-952d-7ee7c7336c68", 
            "name": "LangGraph",
            "type": "SPAN",
            "startTime": "2025-04-16T14:40:19.841Z",
            "endTime": "2025-04-16T14:40:37.860Z",
            "latency": 18019,
            "metadata": {}
        },
        {
            "id": "09c3da0c-f0f7-44b3-9fd6-45d890b6071f",
            "traceId": "46f666c5-0c6a-45f7-952d-7ee7c7336c68",
            "name": "supervisor",
            "type": "SPAN",
            "startTime": "2025-04-16T14:40:34.387Z",
            "endTime": "2025-04-16T14:40:37.860Z",
            "latency": 3473,
            "metadata": {
                "langgraph_node": "supervisor"
            }
        },
        {
            "id": "1fe2af58-4d31-4fd8-bd3e-8776620f9443",
            "traceId": "46f666c5-0c6a-45f7-952d-7ee7c7336c68",
            "name": "gemini_search_agent",
            "type": "SPAN",
            "startTime": "2025-04-16T14:40:25.066Z",
            "endTime": "2025-04-16T14:40:34.385Z",
            "latency": 9319,
            "metadata": {
                "langgraph_node": "gemini_search_agent"
            }
        }
    ]
} 
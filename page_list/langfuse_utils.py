"""
랭퓨즈 연동 유틸리티 모듈 - 랭퓨즈에서 트레이스 데이터를 가져오는 기능
"""

import os
import requests
from datetime import datetime, timedelta
from .helpers import (
    LANGFUSE_HOST, 
    LANGFUSE_PROJECT, 
    LANGFUSE_PUBLIC_KEY, 
    LANGFUSE_SECRET_KEY
)

def get_langfuse_headers():
    """랭퓨즈 API 요청을 위한 헤더를 생성합니다."""
    return {
        "X-Project-Name": LANGFUSE_PROJECT,
        "Authorization": f"Bearer {LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}"
    }

def fetch_langfuse_traces(limit=100, days=7):
    """랭퓨즈에서 최근 트레이스를 가져옵니다."""
    if not all([LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_PROJECT]):
        return []
    
    try:
        # 시간 범위 설정 (최근 X일)
        start_time = (datetime.now() - timedelta(days=days)).isoformat()
        
        # API 요청 URL
        url = f"{LANGFUSE_HOST}/api/public/traces"
        
        # 요청 매개변수
        params = {
            "limit": limit,
            "startTime": start_time
        }
        
        # API 요청
        response = requests.get(url, headers=get_langfuse_headers(), params=params)
        response.raise_for_status()  # 에러 체크
        
        return response.json().get("data", [])
    except Exception as e:
        print(f"랭퓨즈 트레이스 조회 실패: {e}")
        return []

def fetch_langfuse_observations(trace_id):
    """특정 트레이스의 관찰 데이터를 가져옵니다."""
    if not all([LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_PROJECT]):
        return []
    
    try:
        # API 요청 URL
        url = f"{LANGFUSE_HOST}/api/public/traces/{trace_id}/observations"
        
        # API 요청
        response = requests.get(url, headers=get_langfuse_headers())
        response.raise_for_status()  # 에러 체크
        
        return response.json().get("data", [])
    except Exception as e:
        print(f"랭퓨즈 관찰 데이터 조회 실패: {e}")
        return [] 
import os
import json
from .helpers import DATA_DIR, PROMPTS_FILE

# 전체 파일 경로
FULL_PROMPTS_FILE = os.path.join(DATA_DIR, PROMPTS_FILE)

# 데이터 디렉토리 생성
os.makedirs(DATA_DIR, exist_ok=True)

# 프롬프트 불러오기
def load_prompts():
    if os.path.exists(FULL_PROMPTS_FILE):
        with open(FULL_PROMPTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# 프롬프트 저장하기
def save_prompts(prompts):
    with open(FULL_PROMPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=4) 
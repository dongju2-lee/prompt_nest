import os
import json
from .helpers import DATA_DIR, PROMPTS_FILE

# 전체 파일 경로
FULL_PROMPTS_FILE = os.path.join(DATA_DIR, PROMPTS_FILE)
LANGFUSE_FAVORITES_FILE = os.path.join(DATA_DIR, "langfuse_favorites.json")

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

# 랭퓨즈 즐겨찾기 불러오기
def load_langfuse_favorites():
    if os.path.exists(LANGFUSE_FAVORITES_FILE):
        try:
            with open(LANGFUSE_FAVORITES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"good": [], "bad": []}
    return {"good": [], "bad": []}

# 랭퓨즈 즐겨찾기 저장하기
def save_langfuse_favorites(favorites):
    with open(LANGFUSE_FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, ensure_ascii=False, indent=4)

# 랭퓨즈 트레이스를 즐겨찾기에 추가
def add_to_langfuse_favorites(trace_id, trace_name, type_key="good", note=""):
    favorites = load_langfuse_favorites()
    
    # 이미 등록된 즐겨찾기 확인
    existing_item = next((item for item in favorites[type_key] if item["id"] == trace_id), None)
    
    if existing_item:
        # 이미 존재하는 경우 노트를 업데이트
        existing_item["note"] = note
    else:
        # 새로운 즐겨찾기 항목을 추가
        favorites[type_key].append({
            "id": trace_id,
            "name": trace_name,
            "timestamp": os.path.getmtime(LANGFUSE_FAVORITES_FILE) if os.path.exists(LANGFUSE_FAVORITES_FILE) else None,
            "note": note
        })
    
    # 저장
    save_langfuse_favorites(favorites)
    return True

# 랭퓨즈 트레이스를 즐겨찾기에서 제거
def remove_from_langfuse_favorites(trace_id, type_key="good"):
    favorites = load_langfuse_favorites()
    
    # 해당 ID를 가진 항목 제거
    favorites[type_key] = [item for item in favorites[type_key] if item["id"] != trace_id]
    
    # 저장
    save_langfuse_favorites(favorites)
    return True 
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 페이지 상수 정의
HOME_PAGE = "🏠 프롬프트 등록"
PROMPT_LIST_PAGE = "📋 프롬프트 목록"
FAVORITE_PAGE = "⭐ 즐겨찾기"
LANGFUSE_PAGE = "🔍 랭퓨즈 데이터"

# 앱 설정 관련 상수
APP_TITLE = os.getenv("APP_TITLE", "프롬프트 네스트")
APP_ICON = os.getenv("APP_ICON", "🪺")
APP_LAYOUT = os.getenv("APP_LAYOUT", "wide")
SIDEBAR_WIDTH = int(os.getenv("SIDEBAR_WIDTH", "290"))

# 데이터 관련 상수
DATA_DIR = os.getenv("DATA_DIRECTORY", "data")
PROMPTS_FILE = os.getenv("PROMPTS_FILENAME", "prompts.json")

# 카테고리 및 모델 관련 상수
CATEGORIES = os.getenv("CATEGORIES", "일반,비즈니스,교육,창작,기술,마케팅,기타").split(",")
MODELS = os.getenv("MODELS", "모든 모델,GPT-3.5,GPT-4,Claude,Gemini,DALL-E,Midjourney,기타").split(",")

# 랭퓨즈 관련 설정
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
LANGFUSE_PROJECT = os.getenv("LANGFUSE_PROJECT", "")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "") 
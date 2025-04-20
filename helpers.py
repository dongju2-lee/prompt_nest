"""
공통 헬퍼 함수와 상수를 저장하는 파일입니다.
"""

# 페이지 정의
PROMPT_REGISTER_PAGE = "프롬프트 등록"
LANGFUSE_PAGE = "랭퓨즈 데이터"
FAVORITES_PAGE = "즐겨찾기"

# 시스템 설정
CONFIG_DIR = "config"
DATA_DIR = "data"
UI_CONFIG_FILE = f"{CONFIG_DIR}/ui_config.json"
PROMPTS_FILE = f"{DATA_DIR}/prompts.json"
LANGFUSE_FAVORITES_FILE = f"{DATA_DIR}/langfuse_favorites.json"

# LangFuse 환경 변수 키
LANGFUSE_HOST = "LANGFUSE_HOST"
LANGFUSE_PUBLIC_KEY = "LANGFUSE_PUBLIC_KEY"
LANGFUSE_SECRET_KEY = "LANGFUSE_SECRET_KEY"
LANGFUSE_PROJECT_NAME = "LANGFUSE_PROJECT_NAME"
LANGFUSE_DEFAULT_HOST = "https://cloud.langfuse.com" 
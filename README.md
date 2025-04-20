# 🪺 프롬프트 네스트 (Prompt Nest)

AI 프롬프트와 LangFuse 트레이스를 관리하는 Streamlit 기반 애플리케이션입니다.

## 소개

프롬프트 네스트는 다양한 AI 모델(GPT, Claude, Gemini 등)에 사용할 수 있는 프롬프트를 등록하고, 관리하고, 즐겨찾기할 수 있는 웹 애플리케이션입니다. 또한 LangFuse를 통해 수집된 트레이스를 검색하고 즐겨찾기로 등록하여 좋은/나쁜 예제로 관리할 수 있습니다. 통합된 사이드바 메뉴로 직관적으로 사용할 수 있습니다.

## 기능

- **트레이스 등록**: LangFuse에서 특정 트레이스 ID를 검색하고 좋은/나쁜 예제로 등록할 수 있습니다.
- **즐겨찾기**: 자주 사용하는 프롬프트나 중요한 트레이스를 즐겨찾기로 등록하여 빠르게 접근할 수 있습니다.
- **랭퓨즈 데이터**: LangFuse에서 최근 트레이스를 조회하고 세부 정보를 확인할 수 있습니다.

## 설치 방법

1. 레포지토리 클론:
```bash
git clone https://github.com/yourusername/prompt_nest.git
cd prompt_nest
```

2. 가상 환경 생성 (선택사항):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. 의존성 설치:
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정:
   - `.env.example` 파일을 `.env`로 복사하고 필요한 설정을 업데이트하세요.
   - LangFuse 연결을 위한 API 키와 프로젝트 정보를 설정하세요.

## 실행 방법

```bash
streamlit run app.py
```

웹 브라우저에서 자동으로 앱이 열립니다. 기본 주소는 `http://localhost:8501` 입니다.

## 프로젝트 구조

```
prompt_nest/
├── app.py                      # 메인 애플리케이션 파일 (MultiApp 클래스 구현)
├── page_list/                  # 페이지 모듈 패키지
│   ├── __init__.py             # 패키지 초기화 파일
│   ├── helpers.py              # 상수 및 도우미 함수
│   ├── data_utils.py           # 데이터 관리 유틸리티
│   ├── home_page.py            # 트레이스 등록 페이지
│   ├── favorite_page.py        # 즐겨찾기 페이지
│   ├── langfuse_page.py        # 랭퓨즈 데이터 페이지
│   └── langfuse_utils.py       # 랭퓨즈 API 연동 유틸리티
├── data/                       # 데이터 저장 디렉토리 (gitignore에 의해 무시됨)
│   ├── prompts.json            # 저장된 프롬프트 데이터
│   └── langfuse_favorites.json # 즐겨찾기한 랭퓨즈 트레이스 데이터
├── requirements.txt            # 의존성 패키지 목록
├── .env.example                # 환경 변수 예시 (이 파일을 복사하여 .env 생성)
├── .gitignore                  # Git 무시 파일 목록
└── README.md                   # 프로젝트 설명
```

## 사용 방법

1. **트레이스 등록 (🏠 트레이스 등록)**
   - LangFuse에서 트레이스 ID를 복사하여 입력창에 붙여넣고 검색합니다.
   - 검색된 트레이스의 사용자 질문, 최종 답변, 시스템 프롬프트를 확인합니다.
   - 좋은 예제 또는 나쁜 예제로 등록하여 즐겨찾기에 추가합니다.

2. **즐겨찾기 (⭐ 즐겨찾기)**
   - 즐겨찾기로 등록한 프롬프트나 트레이스를 확인할 수 있습니다.
   - 좋은 예제와 나쁜 예제로 분류되어 표시됩니다.
   - 각 트레이스의 세부 정보를 확인하고 메모를 추가할 수 있습니다.

3. **랭퓨즈 데이터 (🔍 랭퓨즈 데이터)**
   - LangFuse에서 최근 트레이스 목록을 조회합니다.
   - 조회 기간과 최대 트레이스 수를 설정할 수 있습니다.
   - 트레이스 목록에서 특정 트레이스를 선택하여 세부 정보를 확인합니다.
   - 사용자 질문, 최종 답변, 시스템 프롬프트 등의 정보를 확인할 수 있습니다.
   - 트레이스를 즐겨찾기에 추가할 수 있습니다.

## LangFuse 연동 설정

LangFuse와 연동하려면 다음 환경 변수를 `.env` 파일에 설정해야 합니다:

```
LANGFUSE_HOST=https://cloud.langfuse.com  # 또는 자체 호스팅 URL
LANGFUSE_PROJECT=your-project-name
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 
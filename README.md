# 🪺 프롬프트 네스트 (Prompt Nest)

AI 프롬프트를 관리하고 저장하는 Streamlit 기반 애플리케이션입니다.

## 소개

프롬프트 네스트는 다양한 AI 모델(GPT, Claude, Gemini 등)에 사용할 수 있는 프롬프트를 등록하고, 관리하고, 즐겨찾기할 수 있는 웹 애플리케이션입니다. 통합된 사이드바 메뉴로 직관적으로 사용할 수 있습니다.

## 기능

- **프롬프트 등록**: 다양한 AI 모델용 프롬프트를 카테고리, 태그, 설명과 함께 등록할 수 있습니다.
- **프롬프트 목록**: 등록된 모든 프롬프트를 검색하고 관리할 수 있습니다.
- **즐겨찾기**: 자주 사용하는 프롬프트를 즐겨찾기로 등록하여 빠르게 접근할 수 있습니다.

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
│   ├── home_page.py            # 프롬프트 등록 페이지
│   ├── prompt_list_page.py     # 프롬프트 목록 페이지
│   └── favorite_page.py        # 즐겨찾기 페이지
├── data/                       # 데이터 저장 디렉토리
│   └── prompts.json            # 저장된 프롬프트 데이터
├── requirements.txt            # 의존성 패키지 목록
└── README.md                   # 프로젝트 설명
```

## 사용 방법

1. **프롬프트 등록 (🏠 프롬프트 등록)**
   - 제목, 내용, 카테고리, 태그, 대상 모델, 설명을 입력하여 새로운 프롬프트를 등록합니다.
   - 최근 등록된 프롬프트 목록을 확인할 수 있습니다.

2. **프롬프트 목록 (📋 프롬프트 목록)**
   - 등록된 모든 프롬프트를 검색하고 관리할 수 있습니다.
   - 카테고리별 필터링과 다양한 정렬 옵션을 사용할 수 있습니다.
   - 클립보드에 복사, 즐겨찾기 추가/제거, 삭제 기능을 제공합니다.

3. **즐겨찾기 (⭐ 즐겨찾기)**
   - 즐겨찾기로 등록한 프롬프트만 모아서 볼 수 있습니다.
   - 카드 형태로 직관적으로 표시됩니다.
   - 편집 기능을 통해 내용을 수정할 수 있습니다.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 
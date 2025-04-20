import streamlit as st
from .data_utils import (
    load_prompts, save_prompts, 
    load_langfuse_favorites, remove_from_langfuse_favorites
)
from .langfuse_utils import fetch_langfuse_observations
from .helpers import CATEGORIES, MODELS

def favorite_page():
    """즐겨찾기 페이지"""
    
    # 타이틀 및 설명
    st.title("⭐ 즐겨찾기")
    st.subheader("자주 사용하는 프롬프트와 트레이스 모음")
    
    # 초기화
    if 'selected_favorite' not in st.session_state:
        st.session_state.selected_favorite = None
    
    if 'favorite_observations' not in st.session_state:
        st.session_state.favorite_observations = []
    
    # 탭 생성 - 프롬프트, 좋은 예제, 나쁜 예제
    tabs = st.tabs(["📋 프롬프트", "✅ 좋은 랭퓨즈 예제", "❌ 개선 필요 랭퓨즈 예제"])
    
    # 프롬프트 즐겨찾기 탭
    with tabs[0]:
        display_prompt_favorites()
    
    # 좋은 랭퓨즈 예제 탭
    with tabs[1]:
        # 랭퓨즈 즐겨찾기 불러오기
        favorites = load_langfuse_favorites()
        display_langfuse_favorites(favorites.get("good", []), "good")
    
    # 개선 필요 랭퓨즈 예제 탭
    with tabs[2]:
        # 랭퓨즈 즐겨찾기 불러오기
        favorites = load_langfuse_favorites()
        display_langfuse_favorites(favorites.get("bad", []), "bad")

def display_prompt_favorites():
    """프롬프트 즐겨찾기를 표시합니다"""
    
    # 프롬프트 불러오기
    all_prompts = load_prompts()
    
    # 즐겨찾기만 필터링
    favorite_prompts = [p for p in all_prompts if p.get("favorite", False)]
    
    # 정렬 옵션
    sort_option = st.selectbox(
        "정렬 기준",
        options=["최신순", "오래된순", "제목 오름차순", "제목 내림차순"],
        key="prompt_sort"
    )
    
    # 정렬 적용
    if sort_option == "최신순":
        favorite_prompts = sorted(favorite_prompts, key=lambda x: x["created_at"], reverse=True)
    elif sort_option == "오래된순":
        favorite_prompts = sorted(favorite_prompts, key=lambda x: x["created_at"])
    elif sort_option == "제목 오름차순":
        favorite_prompts = sorted(favorite_prompts, key=lambda x: x["title"])
    elif sort_option == "제목 내림차순":
        favorite_prompts = sorted(favorite_prompts, key=lambda x: x["title"], reverse=True)
    
    # 즐겨찾기 목록 표시
    st.markdown("---")
    
    if not favorite_prompts:
        st.info("즐겨찾기한 프롬프트가 없습니다. '프롬프트 목록' 페이지에서 프롬프트를 즐겨찾기로 등록해보세요.")
    else:
        st.markdown(f"### 즐겨찾기 목록: {len(favorite_prompts)}개의 프롬프트")
        
        # 프롬프트 카드 형태로 표시
        cols = st.columns(2)  # 2열 그리드
        
        for i, prompt in enumerate(favorite_prompts):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"""
                    <div style="
                        border: 1px solid #ddd;
                        border-radius: 10px;
                        padding: 15px;
                        margin-bottom: 15px;
                        background-color: #f9f9f9;
                    ">
                        <h3 style="margin-top: 0;">{prompt['title']}</h3>
                        <p><strong>카테고리:</strong> {prompt['category']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 프롬프트 내용
                    with st.expander("프롬프트 내용 보기"):
                        st.markdown(f"> {prompt['content']}")
                        
                        if prompt.get("description"):
                            st.markdown(f"**설명:** {prompt['description']}")
                        
                        if prompt.get("tags"):
                            st.markdown(f"**태그:** {', '.join(prompt['tags'])}")
                        
                        st.markdown(f"**모델:** {prompt['model']} | **등록일:** {prompt['created_at']}")
                    
                    # 버튼 행
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("클립보드에 복사", key=f"copy_{i}"):
                            st.code(prompt["content"], language="")
                            st.success("클립보드에 복사되었습니다!")
                    
                    with col2:
                        if st.button("즐겨찾기 해제", key=f"unfav_{i}"):
                            # 즐겨찾기 상태 변경
                            for p in all_prompts:
                                if p["id"] == prompt["id"]:
                                    p["favorite"] = False
                                    break
                            
                            # 저장
                            save_prompts(all_prompts)
                            st.success("즐겨찾기에서 해제되었습니다!")
                            st.experimental_rerun()
                    
                    with col3:
                        if st.button("편집", key=f"edit_{i}"):
                            st.session_state["edit_prompt_id"] = prompt["id"]
                            st.session_state["show_edit"] = True
    
    # 프롬프트 편집 기능
    if st.session_state.get("show_edit", False):
        st.markdown("---")
        st.subheader("프롬프트 편집")
        
        # 편집할 프롬프트 찾기
        edit_id = st.session_state["edit_prompt_id"]
        edit_prompt = next((p for p in all_prompts if p["id"] == edit_id), None)
        
        if edit_prompt:
            with st.form("edit_form"):
                prompt_title = st.text_input("프롬프트 제목 *", value=edit_prompt["title"])
                
                category = st.selectbox(
                    "카테고리",
                    options=CATEGORIES,
                    index=CATEGORIES.index(edit_prompt["category"]) if edit_prompt["category"] in CATEGORIES else 0
                )
                
                prompt_text = st.text_area("프롬프트 내용 *", value=edit_prompt["content"], height=200)
                
                tags = st.text_input("태그 (쉼표로 구분)", value=", ".join(edit_prompt.get("tags", [])))
                
                model = st.selectbox(
                    "대상 모델",
                    options=MODELS,
                    index=MODELS.index(edit_prompt["model"]) if edit_prompt["model"] in MODELS else 0
                )
                
                description = st.text_area("설명 (선택사항)", value=edit_prompt.get("description", ""), height=100)
                
                # 필수 항목 설명 추가
                st.markdown("<small>* 표시된 항목은 필수 입력 항목입니다</small>", unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    submit = st.form_submit_button("저장")
                
                with col2:
                    cancel = st.form_submit_button("취소")
                
                if submit:
                    if not prompt_title or not prompt_text:
                        st.error("제목과 프롬프트 내용은 필수 입력 항목입니다.")
                    else:
                        # 프롬프트 업데이트
                        for p in all_prompts:
                            if p["id"] == edit_id:
                                p["title"] = prompt_title
                                p["content"] = prompt_text
                                p["category"] = category
                                p["tags"] = [tag.strip() for tag in tags.split(",")] if tags else []
                                p["model"] = model
                                p["description"] = description
                                break
                        
                        # 저장
                        save_prompts(all_prompts)
                        st.success("프롬프트가 수정되었습니다!")
                        
                        # 편집 모드 종료
                        st.session_state["show_edit"] = False
                        st.experimental_rerun()
                
                if cancel:
                    # 편집 모드 종료
                    st.session_state["show_edit"] = False
                    st.experimental_rerun()

def display_langfuse_favorites(favorites, type_key):
    """랭퓨즈 즐겨찾기 목록을 표시하고 관리합니다"""
    
    if not favorites:
        st.info(f"저장된 {'좋은' if type_key == 'good' else '나쁜'} 랭퓨즈 예제가 없습니다. '랭퓨즈 데이터' 페이지에서 추가해보세요.")
        return
    
    # 정렬 옵션
    sort_option = st.selectbox(
        "정렬 기준",
        options=["최신순", "이름순"],
        key=f"sort_{type_key}"
    )
    
    # 정렬 적용
    if sort_option == "최신순":
        # timestamp가 None인 경우는 가장 오래된 것으로 처리
        sorted_favorites = sorted(favorites, 
                                 key=lambda x: x.get("timestamp") or 0, 
                                 reverse=True)
    else:  # 이름순
        sorted_favorites = sorted(favorites, 
                                 key=lambda x: x.get("name", ""))
    
    # 즐겨찾기 목록을 카드 형태로 표시
    st.markdown(f"### {'좋은' if type_key == 'good' else '나쁜'} 예제 목록: {len(sorted_favorites)}개")
    
    # 카드 표시를 위한 열 생성
    cols = st.columns(2)  # 2열 그리드
    
    for i, favorite in enumerate(sorted_favorites):
        with cols[i % 2]:
            with st.container():
                # 카드 디자인
                card_color = "#e5f9e0" if type_key == "good" else "#ffebee"
                st.markdown(f"""
                <div style="
                    border: 1px solid {'#a0d8b3' if type_key == 'good' else '#ffcdd2'};
                    border-radius: 10px;
                    padding: 15px;
                    margin-bottom: 15px;
                    background-color: {card_color};
                ">
                    <h3 style="margin-top: 0;">{favorite.get('name', '이름 없음')}</h3>
                    <p><strong>ID:</strong> {favorite.get('id', '')[:8]}...</p>
                    {f"<p><strong>노트:</strong> {favorite.get('note', '')}</p>" if favorite.get('note') else ""}
                </div>
                """, unsafe_allow_html=True)
                
                # 버튼 행
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("자세히 보기", key=f"view_{type_key}_{i}"):
                        st.session_state.selected_favorite = favorite
                        st.session_state.favorite_type = type_key
                        # 랭퓨즈에서 관찰 데이터를 가져오기 위한 플래그 설정
                        st.session_state.load_favorite_observations = True
                
                with col2:
                    if st.button("즐겨찾기 해제", key=f"unfav_{type_key}_{i}"):
                        if st.session_state.get(f"confirm_delete_{type_key}_{i}", False):
                            # 삭제 확인 상태인 경우 실제 삭제 수행
                            remove_from_langfuse_favorites(favorite["id"], type_key)
                            st.success("즐겨찾기에서 제거되었습니다!")
                            st.experimental_rerun()
                        else:
                            # 삭제 확인 상태로 변경
                            st.session_state[f"confirm_delete_{type_key}_{i}"] = True
                            st.warning("정말 제거하시겠습니까? 다시 한 번 '즐겨찾기 해제' 버튼을 클릭하면 영구적으로 제거됩니다.")
    
    # 선택된 트레이스 세부 정보 표시
    if st.session_state.selected_favorite and st.session_state.favorite_type == type_key:
        display_selected_favorite()

def display_selected_favorite():
    """선택된 즐겨찾기 항목의 세부 정보를 표시합니다"""
    
    st.markdown("---")
    favorite = st.session_state.selected_favorite
    
    st.markdown(f"## {favorite.get('name', '이름 없음')}")
    st.markdown(f"**ID:** {favorite.get('id', '')}")
    
    if favorite.get('note'):
        st.markdown(f"**노트:** {favorite.get('note', '')}")
    
    # 관찰 데이터 로드 필요 여부 확인
    should_load = False
    if 'load_favorite_observations' not in st.session_state:
        st.session_state.load_favorite_observations = True
        should_load = True
    elif st.session_state.load_favorite_observations:
        should_load = True
        st.session_state.load_favorite_observations = False
    
    # 관찰 데이터 가져오기
    if should_load:
        try:
            with st.spinner("랭퓨즈에서 트레이스 데이터를 가져오는 중..."):
                observations = fetch_langfuse_observations(favorite.get('id', ''))
                st.session_state.favorite_observations = observations
                
            if not observations:
                st.warning("이 트레이스에는 관찰 데이터가 없습니다. 삭제되었거나 접근할 수 없는 트레이스일 수 있습니다.")
        except Exception as e:
            st.error(f"트레이스 데이터를 가져오는 중 오류가 발생했습니다: {str(e)}")
    
    # 저장된 관찰 데이터 표시
    observations = st.session_state.favorite_observations
    if observations:
        st.success(f"{len(observations)}개의 관찰 데이터가 있습니다.")
        
        # 관찰 데이터를 유형별로 정렬
        sorted_observations = sorted(observations, key=lambda x: x.get("type", ""))
        
        # 관찰 데이터 표시 옵션
        with st.expander("관찰 데이터 보기", expanded=True):
            st.markdown("### 관찰 데이터")
            
            for idx, obs in enumerate(sorted_observations):
                with st.container():
                    # 구분선 추가
                    if idx > 0:
                        st.markdown("---")
                    
                    # 관찰 데이터 헤더 정보
                    st.markdown(f"**{idx+1}. {obs.get('name', '무제')}** ({obs.get('type', '알 수 없음')})")
                    
                    # 시간 정보 표시
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**시작:** {obs.get('startTime', '')}")
                    with col2:
                        st.markdown(f"**종료:** {obs.get('endTime', '')}")
                    
                    # 입력/출력 데이터를 탭으로 표시
                    tabs = st.tabs(["입력", "출력", "메타데이터"])
                    
                    with tabs[0]:  # 입력 탭
                        if obs.get("input"):
                            # 시스템 프롬프트 강조 표시
                            if isinstance(obs.get("input"), list):
                                for item in obs.get("input", []):
                                    if isinstance(item, dict) and (item.get("role") == "system" or item.get("type") == "system"):
                                        st.markdown("### ⚙️ 시스템 프롬프트")
                                        st.markdown(f"> {item.get('content', '')}")
                                        st.markdown("---")
                            
                            # 전체 입력 데이터 표시
                            st.json(obs.get("input", {}))
                        else:
                            st.info("입력 데이터가 없습니다.")
                    
                    with tabs[1]:  # 출력 탭
                        if obs.get("output"):
                            st.json(obs.get("output", {}))
                        else:
                            st.info("출력 데이터가 없습니다.")
                    
                    with tabs[2]:  # 메타데이터 탭
                        if obs.get("metadata"):
                            st.json(obs.get("metadata", {}))
                        else:
                            st.info("메타데이터가 없습니다.")
    else:
        st.info("관찰 데이터를 불러오는 중입니다...") 
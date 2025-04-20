import streamlit as st
from .data_utils import load_prompts, save_prompts
from .helpers import CATEGORIES, MODELS

def favorite_page():
    """즐겨찾기 페이지"""
    
    # 타이틀 및 설명
    st.title("⭐ 즐겨찾기")
    st.subheader("자주 사용하는 프롬프트 모음")
    
    # 프롬프트 불러오기
    all_prompts = load_prompts()
    
    # 즐겨찾기만 필터링
    favorite_prompts = [p for p in all_prompts if p.get("favorite", False)]
    
    # 정렬 옵션
    sort_option = st.selectbox(
        "정렬 기준",
        options=["최신순", "오래된순", "제목 오름차순", "제목 내림차순"]
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
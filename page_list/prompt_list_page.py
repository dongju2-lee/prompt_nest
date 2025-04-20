import streamlit as st
from .data_utils import load_prompts, save_prompts
from .helpers import CATEGORIES

def prompt_list_page():
    """프롬프트 목록 페이지"""
    
    # 타이틀 및 설명
    st.title("📋 프롬프트 목록")
    st.subheader("등록된 모든 프롬프트 확인 및 관리")
    
    # 프롬프트 불러오기
    prompts = load_prompts()
    
    # 검색 및 필터링 기능
    st.markdown("### 검색 및 필터링")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("검색어", placeholder="제목 또는 내용으로 검색")
    
    with col2:
        available_categories = ["전체"] + (list(set([p["category"] for p in prompts])) if prompts else CATEGORIES)
        category_filter = st.selectbox(
            "카테고리 필터", 
            options=available_categories
        )
    
    with col3:
        sort_option = st.selectbox(
            "정렬 기준",
            options=["최신순", "오래된순", "제목 오름차순", "제목 내림차순"]
        )
    
    # 필터링 적용
    filtered_prompts = prompts
    
    # 검색어 필터링
    if search_term:
        filtered_prompts = [
            p for p in filtered_prompts if 
            search_term.lower() in p["title"].lower() or 
            search_term.lower() in p["content"].lower() or
            any(search_term.lower() in tag.lower() for tag in p["tags"])
        ]
    
    # 카테고리 필터링
    if category_filter != "전체":
        filtered_prompts = [p for p in filtered_prompts if p["category"] == category_filter]
    
    # 정렬 적용
    if sort_option == "최신순":
        filtered_prompts = sorted(filtered_prompts, key=lambda x: x["created_at"], reverse=True)
    elif sort_option == "오래된순":
        filtered_prompts = sorted(filtered_prompts, key=lambda x: x["created_at"])
    elif sort_option == "제목 오름차순":
        filtered_prompts = sorted(filtered_prompts, key=lambda x: x["title"])
    elif sort_option == "제목 내림차순":
        filtered_prompts = sorted(filtered_prompts, key=lambda x: x["title"], reverse=True)
    
    # 프롬프트 목록 표시
    st.markdown("---")
    st.markdown(f"### 검색 결과: {len(filtered_prompts)}개의 프롬프트")
    
    if not filtered_prompts:
        st.info("검색 결과가 없습니다. 다른 검색어나 필터를 시도해보세요.")
    else:
        # 프롬프트 표시
        for i, prompt in enumerate(filtered_prompts):
            with st.expander(f"{prompt['title']} ({prompt['category']})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**내용:**\n> {prompt['content']}")
                    
                    if prompt.get("description"):
                        st.markdown(f"**설명:** {prompt['description']}")
                    
                    if prompt.get("tags"):
                        st.markdown(f"**태그:** {', '.join(prompt['tags'])}")
                    
                    st.markdown(f"**모델:** {prompt['model']} | **등록일:** {prompt['created_at']}")
                
                with col2:
                    # 복사 버튼
                    if st.button("클립보드에 복사", key=f"copy_{i}"):
                        st.code(prompt["content"], language="")
                        st.success("클립보드에 복사되었습니다!")
                    
                    # 즐겨찾기 토글 버튼
                    favorite_label = "즐겨찾기 해제" if prompt.get("favorite") else "즐겨찾기 추가"
                    if st.button(favorite_label, key=f"fav_{i}"):
                        # 즐겨찾기 상태 토글
                        prompt["favorite"] = not prompt.get("favorite", False)
                        
                        # 원래 프롬프트 목록 업데이트
                        for p in prompts:
                            if p["id"] == prompt["id"]:
                                p["favorite"] = prompt["favorite"]
                                break
                        
                        # 저장
                        save_prompts(prompts)
                        
                        # 성공 메시지
                        action = "추가되었습니다" if prompt["favorite"] else "해제되었습니다"
                        st.success(f"즐겨찾기에 {action}!")
                        st.experimental_rerun()
                    
                    # 삭제 버튼
                    if st.button("삭제", key=f"del_{i}"):
                        if st.session_state.get(f"confirm_delete_{i}", False):
                            # 삭제 확인 상태인 경우 실제 삭제 수행
                            prompts = [p for p in prompts if p["id"] != prompt["id"]]
                            save_prompts(prompts)
                            st.success("프롬프트가 삭제되었습니다!")
                            st.experimental_rerun()
                        else:
                            # 삭제 확인 상태로 변경
                            st.session_state[f"confirm_delete_{i}"] = True
                            st.warning("정말 삭제하시겠습니까? 다시 한 번 '삭제' 버튼을 클릭하면 영구적으로 삭제됩니다.") 
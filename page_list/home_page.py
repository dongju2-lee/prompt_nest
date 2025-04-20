import streamlit as st
from datetime import datetime
from .data_utils import load_prompts, save_prompts
from .helpers import CATEGORIES, MODELS

def home_page():
    """프롬프트 등록 페이지"""
    
    # 타이틀 및 설명
    st.title("🏠 프롬프트 등록")
    st.subheader("나만의 AI 프롬프트 등록하기")
    
    # 저장된 프롬프트 불러오기
    prompts = load_prompts()
    
    # 프롬프트 입력 폼
    with st.form("prompt_form", clear_on_submit=True):
        st.subheader("새 프롬프트 등록")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            prompt_title = st.text_input(
                "프롬프트 제목 *", 
                placeholder="제목을 입력하세요"
            )
        
        with col2:
            category = st.selectbox(
                "카테고리",
                options=CATEGORIES
            )
        
        prompt_text = st.text_area(
            "프롬프트 내용 *", 
            height=200,
            placeholder="여기에 프롬프트 내용을 입력하세요..."
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            tags = st.text_input(
                "태그 (쉼표로 구분)", 
                placeholder="예: GPT-4, 마케팅, 소셜미디어"
            )
        
        with col2:
            model = st.selectbox(
                "대상 모델",
                options=MODELS
            )
        
        description = st.text_area(
            "메모 (선택사항)", 
            height=100,
            placeholder="이 프롬프트의 목적과 사용법에 대한 간단한 메모를 작성하세요."
        )
        
        # 필수 항목 설명 추가
        st.markdown("<small>* 표시된 항목은 필수 입력 항목입니다</small>", unsafe_allow_html=True)
        
        submit = st.form_submit_button("등록하기")
        
        if submit:
            if not prompt_title or not prompt_text:
                st.error("제목과 프롬프트 내용은 필수 입력 항목입니다.")
            else:
                # 새 프롬프트 데이터 생성
                new_prompt = {
                    "id": len(prompts) + 1,
                    "title": prompt_title,
                    "content": prompt_text,
                    "category": category,
                    "tags": [tag.strip() for tag in tags.split(",")] if tags else [],
                    "model": model,
                    "description": description,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "favorite": False
                }
                
                # 프롬프트 목록에 추가
                prompts.append(new_prompt)
                
                # 파일에 저장
                save_prompts(prompts)
                
                st.success("프롬프트가 성공적으로 등록되었습니다!")
    
    # 최근 등록된 프롬프트 표시
    st.markdown("---")
    st.subheader("최근 등록된 프롬프트")
    
    if prompts:
        # 최신 5개만 표시
        recent_prompts = sorted(prompts, key=lambda x: x["created_at"], reverse=True)[:5]
        
        for prompt in recent_prompts:
            with st.expander(f"{prompt['title']} ({prompt['category']})"):
                st.markdown(f"**내용:** {prompt['content']}")
                st.markdown(f"**모델:** {prompt['model']} | **등록일:** {prompt['created_at']}")
                if prompt['tags']:
                    st.markdown(f"**태그:** {', '.join(prompt['tags'])}")
    else:
        st.info("등록된 프롬프트가 없습니다. 첫 번째 프롬프트를 등록해보세요!") 
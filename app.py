"""
프롬프트 네스트 - AI 프롬프트 관리 애플리케이션
"""

import streamlit as st
from typing import List, Dict, Any, Callable

# 페이지 임포트
from page_list.home_page import home_page
from page_list.favorite_page import favorite_page
from page_list.langfuse_page import langfuse_page
from page_list.helpers import (
    HOME_PAGE, FAVORITE_PAGE, LANGFUSE_PAGE,
    APP_TITLE, APP_ICON, APP_LAYOUT, SIDEBAR_WIDTH
)

class MultiApp:
    """여러 페이지를 관리하는 멀티앱 클래스"""
    
    def __init__(self):
        self.apps = []

    def add_app(self, title, func):
        """앱 페이지 추가"""
        self.apps.append({
            "title": title,
            "function": func
        })

    def run(self):
        """멀티앱 실행"""
        # 페이지 설정
        st.set_page_config(
            page_title=APP_TITLE,
            page_icon=APP_ICON,
            layout=APP_LAYOUT,
            initial_sidebar_state="expanded"
        )
        
        # 사이드바 너비 조정을 위한 CSS 추가
        st.markdown(f"""
        <style>
        [data-testid="stSidebar"] {{
            min-width: {SIDEBAR_WIDTH}px;
            max-width: {SIDEBAR_WIDTH}px;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        # 사이드바 설정
        with st.sidebar:
            st.title(f"{APP_TITLE} {APP_ICON}")
            st.markdown("## 메뉴")
            
            # 페이지 선택 라디오 버튼
            app_options = [app["title"] for app in self.apps]
            selected_app_title = st.radio("페이지 선택", app_options)
            
            # 선택된 앱 찾기
            selected_app = next(app for app in self.apps if app["title"] == selected_app_title)
            
            st.markdown("---")
        
        # 선택한 앱 실행
        selected_app["function"]()

# 메인 실행 코드
if __name__ == "__main__":
    app = MultiApp()
    
    # 앱 페이지 추가
    app.add_app(HOME_PAGE, home_page)
    app.add_app(FAVORITE_PAGE, favorite_page)
    app.add_app(LANGFUSE_PAGE, langfuse_page)
    
    # 앱 실행
    app.run() 
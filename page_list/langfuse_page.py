import streamlit as st
import pandas as pd
import traceback
import sys
from .langfuse_utils import fetch_langfuse_traces, fetch_langfuse_observations
from .helpers import LANGFUSE_HOST, LANGFUSE_PROJECT, LANGFUSE_PUBLIC_KEY

def langfuse_page():
    """랭퓨즈 데이터를 표시하는 페이지"""
    
    # 세션 상태 초기화
    if 'traces' not in st.session_state:
        st.session_state.traces = []
    
    if 'selected_trace_id' not in st.session_state:
        st.session_state.selected_trace_id = None
    
    if 'observations' not in st.session_state:
        st.session_state.observations = []
    
    if 'expanded_observation' not in st.session_state:
        st.session_state.expanded_observation = None
    
    # 타이틀 및 설명
    st.title("🔍 랭퓨즈 데이터")
    
    # 연결 정보 표시
    with st.expander("랭퓨즈 연결 정보"):
        st.markdown(f"**호스트:** {LANGFUSE_HOST}")
        st.markdown(f"**프로젝트:** {LANGFUSE_PROJECT}")
        st.markdown(f"**Public Key:** {LANGFUSE_PUBLIC_KEY[:5]}...")
        st.markdown("""
        연결에 문제가 있다면 .env 파일에서 다음 설정을 확인하세요:
        - LANGFUSE_HOST
        - LANGFUSE_PROJECT
        - LANGFUSE_PUBLIC_KEY
        - LANGFUSE_SECRET_KEY
        """)
    
    # 검색 컨트롤 영역
    st.markdown("### 🔍 랭퓨즈 데이터 조회")
    
    # 왼쪽과 오른쪽 열 생성
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 기간 선택
        days = st.slider("조회 기간 (일)", min_value=1, max_value=30, value=7)
        
    with col2:
        # 최대 트레이스 수
        limit = st.slider("조회할 최대 트레이스 수", min_value=10, max_value=500, value=100)
    
    # 디버그 모드 (개발용 토글)
    debug_mode = st.checkbox("디버그 모드 활성화", value=False, help="API 호출 및 오류 정보를 상세하게 표시합니다")
    
    # 트레이스 데이터 가져오기
    if st.button("트레이스 조회") or ('should_load_traces' in st.session_state and st.session_state.should_load_traces):
        # 다음 자동 조회 방지
        if 'should_load_traces' in st.session_state:
            st.session_state.should_load_traces = False
            
        try:
            with st.spinner("랭퓨즈에서 트레이스를 가져오는 중..."):
                traces = fetch_langfuse_traces(limit=limit, days=days)
                st.session_state.traces = traces  # 세션에 트레이스 저장
            
            if not traces:
                st.warning("랭퓨즈에서 가져온 트레이스가 없습니다. 설정을 확인하거나 시간 범위를 늘려보세요.")
            else:
                # 트레이스 수 표시
                st.success(f"총 {len(traces)}개의 트레이스를 가져왔습니다.")
                display_traces_and_details()
        except Exception as e:
            st.error(f"트레이스 조회 중 오류가 발생했습니다: {str(e)}")
            with st.expander("오류 세부 정보"):
                st.code(traceback.format_exc())
                
                # 디버그 모드에서 추가 오류 정보 표시
                if debug_mode and hasattr(e, 'response'):
                    st.markdown("**응답 상태 및 내용:**")
                    st.markdown(f"상태 코드: {e.response.status_code}")
                    st.code(e.response.text)
    
    # 트레이스가 이미 로드되어 있는 경우 (페이지 새로고침시에도 데이터 유지)
    elif st.session_state.traces:
        display_traces_and_details()

def display_traces_and_details():
    """트레이스 목록과 세부 정보를 표시합니다"""
    
    traces = st.session_state.traces
    
    # 트레이스 데이터 가공
    trace_data = []
    for trace in traces:
        trace_data.append({
            "이름": trace.get("name", ""),
            "상태": trace.get("status", ""),
            "생성일": trace.get("timestamp", ""),
            "ID": trace.get("id", "")
        })
    
    # 데이터프레임으로 변환
    trace_df = pd.DataFrame(trace_data)
    
    # 데이터프레임 표시
    st.markdown("### 트레이스 목록")
    st.dataframe(trace_df, use_container_width=True)
    
    # 트레이스 세부 정보
    st.markdown("### 트레이스 세부 정보")
    
    # 트레이스 선택 옵션 생성 - ID와 이름을 함께 표시
    trace_options = [t["ID"] for t in trace_data]
    trace_display = {t["ID"]: f"{t['이름']} - {t['ID']}" for t in trace_data}
    
    # 선택한 트레이스 ID 가져오기 (세션 상태에서 먼저 확인)
    current_selected_id = None
    
    # 트레이스 선택 selectbox
    selected_trace_id = st.selectbox(
        "세부 정보를 볼 트레이스 선택",
        options=trace_options,
        format_func=lambda x: trace_display.get(x, x),
        key="trace_selector"
    )
    
    # 선택이 변경되었는지 확인
    if selected_trace_id != st.session_state.selected_trace_id:
        st.session_state.selected_trace_id = selected_trace_id
        # 새로운 트레이스를 선택하면 관찰 데이터를 로드하기 위한 플래그 설정
        st.session_state.load_observations = True
    
    # 선택한 트레이스가 있으면 세부 정보 표시
    if selected_trace_id:
        # 선택한 트레이스 찾기
        selected_trace = next((t for t in traces if t.get("id") == selected_trace_id), None)
        
        if selected_trace:
            # 트레이스 정보 표시
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {selected_trace.get('name', '')}")
                st.markdown(f"**상태:** {selected_trace.get('status', '')}")
                st.markdown(f"**생성일:** {selected_trace.get('timestamp', '')}")
            
            with col2:
                # 수동 새로고침 버튼
                if st.button("관찰 데이터 새로고침", key="refresh_observations"):
                    st.session_state.load_observations = True
            
            # 메타데이터 표시
            if selected_trace.get("metadata"):
                with st.expander("메타데이터", expanded=True):
                    st.json(selected_trace.get("metadata", {}))
            
            # 관찰 데이터 표시 영역
            st.markdown("### 관찰 데이터")
            
            # 관찰 데이터 로드 필요 여부 확인
            should_load = False
            if 'load_observations' not in st.session_state:
                st.session_state.load_observations = True
                should_load = True
            elif st.session_state.load_observations:
                should_load = True
                st.session_state.load_observations = False
            
            # 관찰 데이터 가져오기
            if should_load:
                try:
                    with st.spinner("관찰 데이터를 가져오는 중..."):
                        observations = fetch_langfuse_observations(selected_trace_id)
                        st.session_state.observations = observations
                        
                    if not observations:
                        st.info("이 트레이스에는 관찰 데이터가 없습니다.")
                except Exception as e:
                    st.error(f"관찰 데이터를 가져오는 중 오류가 발생했습니다: {str(e)}")
                    with st.expander("오류 세부 정보"):
                        st.code(traceback.format_exc())
            
            # 저장된 관찰 데이터 표시
            observations = st.session_state.observations
            if observations:
                st.success(f"{len(observations)}개의 관찰 데이터가 있습니다.")
                
                # 관찰 데이터 종류별로 탭 생성
                tabs = {}
                for obs in observations:
                    obs_type = obs.get("type", "기타")
                    if obs_type not in tabs:
                        tabs[obs_type] = []
                    tabs[obs_type].append(obs)
                
                # 탭 UI 생성
                if tabs:
                    tab_names = list(tabs.keys())
                    selected_tabs = st.tabs(tab_names)
                    
                    for i, tab_name in enumerate(tab_names):
                        with selected_tabs[i]:
                            for obs_idx, obs in enumerate(tabs[tab_name]):
                                # 각 관찰 데이터를 위한 컨테이너
                                with st.container():
                                    # 제목 및 상세 정보 토글 버튼
                                    col1, col2 = st.columns([4, 1])
                                    
                                    with col1:
                                        st.markdown(f"**{obs.get('name', '무제')}** ({obs.get('id', '')})")
                                    
                                    with col2:
                                        # 관찰 데이터 ID를 키로 사용해 버튼 토글
                                        button_key = f"toggle_{obs.get('id', '')}_{obs_idx}"
                                        if st.button("상세 정보", key=button_key):
                                            if st.session_state.expanded_observation == obs.get('id', ''):
                                                # 이미 확장된 상태면 닫기
                                                st.session_state.expanded_observation = None
                                            else:
                                                # 확장하기
                                                st.session_state.expanded_observation = obs.get('id', '')
                                    
                                    # 해당 관찰 데이터가 확장 상태인 경우 상세 정보 표시
                                    if st.session_state.expanded_observation == obs.get('id', ''):
                                        # 시간 정보 및 지연시간 표시
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.markdown(f"**시작:** {obs.get('startTime', '')}")
                                            st.markdown(f"**종료:** {obs.get('endTime', '')}")
                                        
                                        with col2:
                                            st.markdown(f"**지연시간:** {obs.get('latency', '')} ms")
                                            st.markdown(f"**유형:** {obs.get('type', '')}")
                                        
                                        # 상세 데이터 표시
                                        data_tabs = st.tabs(["메타데이터", "입력", "출력"])
                                        
                                        with data_tabs[0]:  # 메타데이터 탭
                                            if obs.get("metadata"):
                                                st.json(obs.get("metadata", {}))
                                            else:
                                                st.info("메타데이터가 없습니다.")
                                        
                                        with data_tabs[1]:  # 입력 탭
                                            if obs.get("input"):
                                                st.json(obs.get("input", {}))
                                            else:
                                                st.info("입력 데이터가 없습니다.")
                                        
                                        with data_tabs[2]:  # 출력 탭
                                            if obs.get("output"):
                                                st.json(obs.get("output", {}))
                                            else:
                                                st.info("출력 데이터가 없습니다.")
                                    
                                    # 구분선 추가
                                    st.markdown("---")
            else:
                st.info("이 트레이스에는 관찰 데이터가 없습니다.")
        else:
            st.warning("선택한 트레이스를 찾을 수 없습니다. 다시 조회해보세요.") 
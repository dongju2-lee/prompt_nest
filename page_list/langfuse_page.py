import streamlit as st
import pandas as pd
from .langfuse_utils import fetch_langfuse_traces, fetch_langfuse_observations

def langfuse_page():
    """랭퓨즈 데이터를 표시하는 페이지"""
    
    # 타이틀 및 설명
    st.title("🔍 랭퓨즈 데이터")
    
    # 기간 선택
    days = st.slider("조회 기간 (일)", min_value=1, max_value=30, value=7)
    limit = st.slider("조회할 최대 트레이스 수", min_value=10, max_value=500, value=100)
    
    # 트레이스 데이터 가져오기
    if st.button("트레이스 조회"):
        with st.spinner("랭퓨즈에서 트레이스를 가져오는 중..."):
            traces = fetch_langfuse_traces(limit=limit, days=days)
        
        if not traces:
            st.info("랭퓨즈에서 가져온 트레이스가 없습니다.")
        else:
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
            st.dataframe(trace_df, use_container_width=True)
            
            # 트레이스 세부 정보
            st.subheader("트레이스 세부 정보")
            selected_trace_id = st.selectbox(
                "세부 정보를 볼 트레이스 선택",
                options=[t["ID"] for t in trace_data],
                format_func=lambda x: next((t["이름"] for t in trace_data if t["ID"] == x), x)
            )
            
            if selected_trace_id:
                # 선택한 트레이스 찾기
                selected_trace = next((t for t in traces if t.get("id") == selected_trace_id), None)
                
                if selected_trace:
                    st.markdown(f"### {selected_trace.get('name', '')}")
                    st.markdown(f"**상태:** {selected_trace.get('status', '')}")
                    st.markdown(f"**생성일:** {selected_trace.get('timestamp', '')}")
                    
                    # 메타데이터 표시
                    if selected_trace.get("metadata"):
                        st.markdown("**메타데이터:**")
                        st.json(selected_trace.get("metadata", {}))
                    
                    # 관찰 데이터 가져오기
                    with st.spinner("관찰 데이터를 가져오는 중..."):
                        observations = fetch_langfuse_observations(selected_trace_id)
                    
                    if observations:
                        st.markdown("**관찰:**")
                        for obs in observations:
                            st.markdown(f"- **{obs.get('name', '')}** ({obs.get('type', '')})")
                            if obs.get("input"):
                                with st.expander("입력 보기"):
                                    st.code(obs.get("input", ""), language="")
                            if obs.get("output"):
                                with st.expander("출력 보기"):
                                    st.code(obs.get("output", ""), language="") 
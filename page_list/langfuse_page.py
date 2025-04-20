import streamlit as st
import pandas as pd
import traceback
import sys
import datetime
from .langfuse_utils import fetch_langfuse_traces, fetch_langfuse_observations
from .helpers import LANGFUSE_HOST, LANGFUSE_PROJECT, LANGFUSE_PUBLIC_KEY
from .data_utils import load_langfuse_favorites, add_to_langfuse_favorites, remove_from_langfuse_favorites

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

def find_user_question(observations):
    """사용자의 처음 질문을 찾습니다"""
    for obs in observations:
        # LangGraph 형식의 messages 배열 확인 (스크린샷에서 확인한 형식)
        if isinstance(obs.get("output"), dict) and "messages" in obs.get("output", {}):
            messages = obs.get("output", {}).get("messages", [])
            for msg in messages:
                if isinstance(msg, dict) and msg.get("type") == "human":
                    return {
                        "id": obs.get("id", ""),
                        "name": obs.get("name", ""),
                        "input": {"content": msg.get("content", "")}
                    }
        
        # 입력 데이터에서 사용자 질문을 찾습니다
        if obs.get("input") and isinstance(obs.get("input"), dict):
            # human_input 키가 있는 경우
            if "human_input" in obs.get("input"):
                return obs
                
            # messages 배열이 있는 경우
            if "messages" in obs.get("input"):
                messages = obs.get("input").get("messages", [])
                for msg in messages:
                    if isinstance(msg, dict) and msg.get("type", "").lower() == "human":
                        return obs
        
        # 출력 데이터에서 메시지를 확인합니다
        if obs.get("output") and isinstance(obs.get("output"), dict):
            # messages 배열이 있는 경우
            if "messages" in obs.get("output"):
                messages = obs.get("output").get("messages", [])
                for msg in messages:
                    if isinstance(msg, dict) and msg.get("type", "").lower() == "human":
                        # 사용자 메시지를 발견하면 해당 관찰 데이터로 가상의 사용자 질문 객체 생성
                        return {
                            "id": obs.get("id", ""),
                            "name": "사용자 메시지",
                            "input": {"content": msg.get("content", "")}
                        }
        
        # 이름이 "user" 또는 "human"을 포함하는 관찰 데이터를 찾습니다
        if "user" in str(obs.get("name", "")).lower() or "human" in str(obs.get("name", "")).lower():
            return obs
        
        # 메타데이터에서 사용자 질문 힌트를 찾습니다
        if obs.get("metadata") and ("user_message" in str(obs.get("metadata")) or "human_message" in str(obs.get("metadata"))):
            return obs
            
        # 입력 또는 출력 데이터에서 content 키가 있고 type이 "human"인 경우
        for data_key in ["input", "output"]:
            data = obs.get(data_key, {})
            if isinstance(data, dict):
                if "content" in data and "type" in data and data.get("type", "").lower() == "human":
                    return obs
    
    return None

def find_final_answer(observations):
    """최종 답변을 찾습니다"""
    # 시간순으로 정렬 (가장 마지막 응답을 찾기 위해)
    # None값이 있는 경우 빈 문자열로 대체하여 정렬 오류 방지
    sorted_obs = sorted(observations, key=lambda x: x.get("endTime") or "", reverse=True)
    
    for obs in sorted_obs:
        # 출력 데이터에서 메시지 배열이 있는지 확인 (LangGraph 형식)
        if isinstance(obs.get("output"), dict) and "messages" in obs.get("output", {}):
            messages = obs.get("output", {}).get("messages", [])
            if messages:
                # 마지막 메시지를 찾아서 최종 답변으로 사용
                last_message = messages[-1]
                if isinstance(last_message, dict) and "content" in last_message:
                    # 가상의 최종 답변 객체 생성
                    return {
                        "id": obs.get("id", ""),
                        "name": obs.get("name", "") or "최종 답변",
                        "output": {"content": last_message.get("content", "")}
                    }
                    
        # 출력 데이터가 있는 관찰 중 응답 또는 답변으로 보이는 것을 찾습니다
        if obs.get("output") and isinstance(obs.get("output"), dict):
            return obs
            
        # 이름에 "response", "answer", "output" 등이 포함된 관찰을 찾습니다
        if any(key in str(obs.get("name", "")).lower() for key in ["response", "answer", "output", "assistant"]):
            return obs
    
    return None

def find_system_prompts(observations):
    """ChatVertexAI의 시스템 프롬프트를 찾습니다"""
    system_prompts = []
    unique_contents = set()  # 중복 제거를 위한 세트
    
    for obs in observations:
        # ChatVertexAI 생성 관찰 데이터 확인 (GENERATION 타입)
        if obs.get("type") == "GENERATION" and obs.get("name") == "ChatVertexAI":
            # 입력 메시지 배열에서 시스템 프롬프트 검색
            input_messages = obs.get("input", [])
            
            for msg in input_messages:
                if isinstance(msg, dict) and msg.get("role") == "system":
                    content = msg.get("content")
                    if content and str(content) not in unique_contents:
                        unique_contents.add(str(content))
                        system_prompts.append({
                            "id": obs.get("id", ""),
                            "name": f"{obs.get('name', '')} - {obs.get('metadata', {}).get('langgraph_node', '알 수 없음')}",
                            "content": content,
                            "original_obs": obs
                        })
        
        # 기존 검색 로직 유지 (메타데이터나 입력에서 시스템 프롬프트 검색)        
        metadata = obs.get("metadata", {})
        input_data = obs.get("input", {})
        
        is_system_prompt = False
        content = None
        
        # 이름에 "system", "prompt", "chatvertexai" 등이 포함된 경우
        if any(key in str(obs.get("name", "")).lower() for key in ["system", "prompt", "chatvertexai", "vertex"]):
            is_system_prompt = True
        
        # 메타데이터에 시스템 프롬프트 관련 키워드가 있는 경우
        if isinstance(metadata, dict) and any(key in str(metadata).lower() for key in ["system_prompt", "system_message", "instructions"]):
            is_system_prompt = True
            # 메타데이터에서 프롬프트 내용 추출
            for key in ["system_prompt", "system_message", "system_content", "instructions"]:
                if key in metadata:
                    content = metadata[key]
                    break
        
        # 입력이 리스트인 경우 (LangGraph 형식) - 메시지 배열 확인
        if isinstance(input_data, list):
            for item in input_data:
                if isinstance(item, dict):
                    # role이 system인 메시지 찾기
                    if item.get("role") == "system" or item.get("type") == "system":
                        content = item.get("content")
                        is_system_prompt = True
                        break
                    # content 필드와 type이 system인 메시지 찾기
                    elif "content" in item and item.get("type") == "system":
                        content = item.get("content")
                        is_system_prompt = True
                        break
            
        # 입력 데이터에 시스템 프롬프트 관련 키워드가 있는 경우
        if isinstance(input_data, dict) and any(key in str(input_data).lower() for key in ["system_prompt", "system_message", "instructions"]):
            is_system_prompt = True
            # 입력 데이터에서 프롬프트 내용 추출
            for key in ["system_prompt", "system_message", "system_content", "instructions"]:
                if key in input_data:
                    content = input_data[key]
                    break
                    
        if is_system_prompt:
            # 중복 검사 - 같은 내용의 프롬프트는 추가하지 않음
            if content and str(content) not in unique_contents:
                unique_contents.add(str(content))
                system_prompts.append({
                    "id": obs.get("id", ""),
                    "name": obs.get("name", ""),
                    "content": content,
                    "original_obs": obs
                })
    
    return system_prompts

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
            col1, col2, col3 = st.columns([5, 1, 1])
            
            with col1:
                st.markdown("### 🔍 주요 관찰 데이터")
            
            # 즐겨찾기 버튼 추가
            with col2:
                if st.button("✅ 좋은 예제", key="good_favorite", help="이 트레이스를 좋은 예제로 즐겨찾기에 추가합니다"):
                    # 노트 입력 받기
                    if "favorite_note" not in st.session_state:
                        st.session_state.favorite_note = ""
                        st.session_state.favorite_type = "good"
                        st.session_state.show_note_input = True
                    else:
                        st.session_state.favorite_type = "good"
                        st.session_state.show_note_input = True
            
            with col3:
                if st.button("❌ 나쁜 예제", key="bad_favorite", help="이 트레이스를 개선이 필요한 나쁜 예제로 즐겨찾기에 추가합니다"):
                    # 노트 입력 받기
                    if "favorite_note" not in st.session_state:
                        st.session_state.favorite_note = ""
                        st.session_state.favorite_type = "bad"
                        st.session_state.show_note_input = True
                    else:
                        st.session_state.favorite_type = "bad"
                        st.session_state.show_note_input = True
            
            # 노트 입력 폼 표시
            if st.session_state.get("show_note_input", False):
                with st.form("note_form"):
                    note = st.text_area("즐겨찾기 노트 (선택사항)", value=st.session_state.get("favorite_note", ""), 
                                       help="이 트레이스에 대한 메모를 입력하세요.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("저장"):
                            # 즐겨찾기에 추가
                            add_to_langfuse_favorites(
                                selected_trace_id, 
                                selected_trace.get('name', '익명 트레이스'),
                                st.session_state.favorite_type,
                                note
                            )
                            st.success(f"트레이스가 {'좋은' if st.session_state.favorite_type == 'good' else '나쁜'} 예제로 즐겨찾기에 추가되었습니다!")
                            # 입력 폼 숨기기
                            st.session_state.show_note_input = False
                    
                    with col2:
                        if st.form_submit_button("취소"):
                            # 입력 폼 숨기기
                            st.session_state.show_note_input = False
            
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
            
            # 저장된 관찰 데이터에서 주요 정보 추출
            observations = st.session_state.observations
            if observations:
                st.success(f"{len(observations)}개의 관찰 데이터가 있습니다.")
                
                # 사용자 질문, 최종 답변, 시스템 프롬프트 추출
                user_question = find_user_question(observations)
                final_answer = find_final_answer(observations)
                system_prompts = find_system_prompts(observations)
                
                # 주요 데이터 표시
                tabs = st.tabs(["사용자 질문", "최종 답변", "시스템 프롬프트"])
                
                with tabs[0]:  # 사용자 질문 탭
                    if user_question:
                        st.markdown(f"**이름:** {user_question.get('name', '무제')}")
                        st.markdown(f"**ID:** {user_question.get('id', '')}")
                        
                        # 입력 데이터에서 사용자 질문 찾기
                        input_data = user_question.get("input", {})
                        
                        # 깔끔하게 내용만 표시
                        st.markdown("---")
                        st.markdown("### 질문 내용")
                        
                        # 데이터 추출 및 표시
                        content = None
                        
                        # JSON 형식인 경우 사람이 읽기 쉽게 처리
                        if isinstance(input_data, dict):
                            if "content" in input_data:
                                content = input_data["content"]
                            elif "message" in input_data:
                                content = input_data["message"]
                            elif "human_input" in input_data:
                                content = input_data["human_input"]
                        else:
                            content = str(input_data)
                        
                        # 내용 표시
                        if content:
                            st.markdown(f"> {content}")
                        else:
                            st.markdown("*내용을 찾을 수 없습니다*")
                    else:
                        st.info("사용자 질문을 찾을 수 없습니다.")
                
                with tabs[1]:  # 최종 답변 탭
                    if final_answer:
                        st.markdown(f"**이름:** {final_answer.get('name', '무제')}")
                        st.markdown(f"**ID:** {final_answer.get('id', '')}")
                        
                        # 출력 데이터에서 최종 답변 찾기
                        output_data = final_answer.get("output", {})
                        
                        # 깔끔하게 내용만 표시
                        st.markdown("---")
                        st.markdown("### 답변 내용")
                        
                        # 데이터 추출 및 표시
                        content = None
                        
                        # JSON 형식인 경우 사람이 읽기 쉽게 처리
                        if isinstance(output_data, dict):
                            # 메시지 배열이 있는 경우 (LangGraph 형식)
                            if "messages" in output_data:
                                messages = output_data.get("messages", [])
                                if messages:  # 메시지가 하나 이상 있으면
                                    # 마지막 메시지를, 없으면 어시스턴트 타입의 메시지를 찾음
                                    last_message = messages[-1]
                                    if isinstance(last_message, dict) and "content" in last_message:
                                        content = last_message.get("content", "")
                                    else:
                                        # 타입이 assistant인 메시지 찾기 (백업 방법)
                                        for msg in messages:
                                            if isinstance(msg, dict) and msg.get("type") == "assistant":
                                                content = msg.get("content", "")
                                                break
                            # 일반적인 출력 형식
                            elif "content" in output_data:
                                content = output_data["content"]
                            elif "message" in output_data:
                                content = output_data["message"]
                            elif "response" in output_data:
                                content = output_data["response"]
                            elif "answer" in output_data:
                                content = output_data["answer"]
                        else:
                            content = str(output_data)
                        
                        # 내용 표시
                        if content:
                            st.markdown(f"> {content}")
                        else:
                            st.markdown("*내용을 찾을 수 없습니다*")
                            st.markdown("#### 전체 출력 데이터:")
                            st.json(output_data)
                    else:
                        st.info("최종 답변을 찾을 수 없습니다.")
                
                with tabs[2]:  # 시스템 프롬프트 탭
                    if system_prompts:
                        for idx, prompt in enumerate(system_prompts):
                            # 프롬프트 내용 표시
                            st.markdown(f"### 프롬프트 {idx+1}")
                            
                            # 이름과 ID 표시
                            st.markdown(f"**노드:** {prompt.get('name', '무제')}")
                            
                            # 프롬프트 내용
                            if prompt.get("content"):
                                st.markdown("---")
                                st.markdown("> " + prompt.get("content").replace("\n", "\n> "))
                            else:
                                st.markdown("*내용을 찾을 수 없습니다*")
                            
                            # 구분선 추가 (마지막 항목이 아닌 경우)
                            if idx < len(system_prompts) - 1:
                                st.markdown("---")
                    else:
                        st.info("ChatVertexAI 시스템 프롬프트를 찾을 수 없습니다.")
                
                # 모든 관찰 데이터 표시 옵션
                with st.expander("모든 관찰 데이터 보기", expanded=False):
                    st.markdown("### 전체 관찰 데이터")
                    
                    # 데이터 유형별로 정렬
                    sorted_observations = sorted(observations, key=lambda x: x.get("type", ""))
                    
                    for idx, obs in enumerate(sorted_observations):
                        with st.container():
                            # 구분선 추가 (첫 번째 항목 제외)
                            if idx > 0:
                                st.markdown("---")
                                
                            # 관찰 데이터 헤더 정보
                            st.markdown(f"**{idx+1}. {obs.get('name', '무제')}** ({obs.get('id', '')})")
                            st.markdown(f"**유형:** {obs.get('type', '알 수 없음')}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**시작:** {obs.get('startTime', '')}")
                            with col2:
                                st.markdown(f"**종료:** {obs.get('endTime', '')}")
                            
                            # 탭을 사용하여 상세 데이터 표시 (확장 패널 대신)
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
            else:
                st.info("이 트레이스에는 관찰 데이터가 없습니다.")
        else:
            st.warning("선택한 트레이스를 찾을 수 없습니다. 다시 조회해보세요.") 
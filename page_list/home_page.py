import streamlit as st
from datetime import datetime
from .langfuse_utils import fetch_langfuse_observations
from .data_utils import add_to_langfuse_favorites

def find_user_question(observations):
    """사용자의 처음 질문을 찾습니다"""
    for obs in observations:
        # LangGraph 형식의 messages 배열 확인
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

def display_trace_data(trace_id):
    """트레이스 데이터를 가져와서 표시합니다"""
    # 초기화
    if 'trace_observations' not in st.session_state:
        st.session_state.trace_observations = {}
    
    if 'favorite_success' not in st.session_state:
        st.session_state.favorite_success = None
    
    # 즐겨찾기 성공 메시지 표시
    if st.session_state.favorite_success:
        status_type = st.session_state.favorite_success.get("type", "")
        message = st.session_state.favorite_success.get("message", "")
        
        if status_type == "success":
            st.success(message)
        elif status_type == "error":
            st.error(message)
        
        # 메시지를 표시한 후 상태 초기화 (한 번만 표시)
        st.session_state.favorite_success = None
    
    # 관찰 데이터 가져오기
    try:
        with st.spinner("랭퓨즈에서 트레이스 데이터를 가져오는 중..."):
            if trace_id not in st.session_state.trace_observations:
                observations = fetch_langfuse_observations(trace_id)
                st.session_state.trace_observations[trace_id] = observations
            else:
                observations = st.session_state.trace_observations[trace_id]
            
        if not observations:
            st.warning("이 트레이스에는 관찰 데이터가 없습니다. 트레이스 ID를 확인해주세요.")
            return False
        
        # 사용자 질문, 최종 답변, 시스템 프롬프트 추출
        user_question = find_user_question(observations)
        final_answer = find_final_answer(observations)
        system_prompts = find_system_prompts(observations)
        
        # 데이터 표시
        st.success(f"트레이스 ID: {trace_id}")
        
        # 주요 데이터 표시
        tabs = st.tabs(["사용자 질문", "최종 답변", "시스템 프롬프트"])
        
        with tabs[0]:  # 사용자 질문 탭
            if user_question:
                # 입력 데이터에서 사용자 질문 찾기
                input_data = user_question.get("input", {})
                
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
                    st.markdown("### 질문 내용")
                    st.markdown(f"> {content}")
                else:
                    st.markdown("*질문 내용을 찾을 수 없습니다*")
            else:
                st.info("사용자 질문을 찾을 수 없습니다.")
        
        with tabs[1]:  # 최종 답변 탭
            if final_answer:
                # 출력 데이터에서 최종 답변 찾기
                output_data = final_answer.get("output", {})
                
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
                    st.markdown("### 답변 내용")
                    st.markdown(f"> {content}")
                else:
                    st.markdown("*답변 내용을 찾을 수 없습니다*")
            else:
                st.info("최종 답변을 찾을 수 없습니다.")
        
        with tabs[2]:  # 시스템 프롬프트 탭
            if system_prompts:
                for idx, prompt in enumerate(system_prompts):
                    # 프롬프트 내용이 있는 경우만 표시
                    if prompt.get("content"):
                        st.markdown(f"#### 프롬프트 {idx+1}: {prompt.get('name', '무제')}")
                        st.markdown("> " + prompt.get("content").replace("\n", "\n> "))
                        
                        # 구분선 추가 (마지막 항목이 아닌 경우)
                        if idx < len(system_prompts) - 1:
                            st.markdown("---")
                    
            else:
                st.info("시스템 프롬프트를 찾을 수 없습니다.")
        
        # 즐겨찾기 등록 버튼
        st.markdown("### 즐겨찾기 등록")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ 좋은 예제로 등록", key="good_favorite_btn"):
                st.session_state.add_favorite_type = "good"
                st.session_state.show_note_input = True
                # 버튼 클릭 후 페이지가 리로드되더라도 이전 트레이스 ID를 유지
                st.session_state.trace_id = trace_id
        
        with col2:
            if st.button("❌ 나쁜 예제로 등록", key="bad_favorite_btn"):
                st.session_state.add_favorite_type = "bad"
                st.session_state.show_note_input = True
                # 버튼 클릭 후 페이지가 리로드되더라도 이전 트레이스 ID를 유지
                st.session_state.trace_id = trace_id
        
        # 노트 입력 폼 표시
        if st.session_state.get("show_note_input", False):
            with st.form("add_to_favorites_form"):
                note = st.text_area("메모 (선택사항)", placeholder="이 예제에 대한 메모를 작성하세요.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("등록"):
                        # 트레이스 이름 추출
                        trace_name = "트레이스"
                        if user_question and isinstance(user_question.get("input"), dict) and "content" in user_question.get("input", {}):
                            content = user_question.get("input", {}).get("content", "")
                            trace_name = content[:30] + "..." if len(content) > 30 else content
                        
                        # 즐겨찾기에 추가
                        success = add_to_langfuse_favorites(
                            trace_id,
                            trace_name,
                            st.session_state.add_favorite_type,
                            note
                        )
                        
                        if success:
                            # 성공 메시지 상태 저장 (페이지 리로드 후에도 표시)
                            st.session_state.favorite_success = {
                                "type": "success",
                                "message": f"트레이스가 {'좋은' if st.session_state.add_favorite_type == 'good' else '나쁜'} 예제로 즐겨찾기에 등록되었습니다!"
                            }
                        else:
                            # 오류 메시지 상태 저장
                            st.session_state.favorite_success = {
                                "type": "error",
                                "message": "즐겨찾기 등록에 실패했습니다."
                            }
                        
                        # 상태 초기화 (폼은 닫히도록)
                        st.session_state.show_note_input = False
                        
                        # 트레이스 ID 유지 (페이지 리로드 후에도 같은 트레이스 표시)
                        st.session_state.trace_id = trace_id
                        
                        # 페이지 다시 로드 - 이 부분은 필요 없어짐
                        # st.rerun()
                
                with col2:
                    if st.form_submit_button("취소"):
                        # 상태 초기화
                        st.session_state.show_note_input = False
                        # 트레이스 ID 유지
                        st.session_state.trace_id = trace_id
        
        return True
    except Exception as e:
        st.error(f"트레이스 데이터를 가져오는 중 오류가 발생했습니다: {str(e)}")
        return False

def home_page():
    """트레이스 등록 페이지"""
    
    # 세션 상태 초기화
    if 'trace_id' not in st.session_state:
        st.session_state.trace_id = ""
    
    if 'trace_observations' not in st.session_state:
        st.session_state.trace_observations = {}
    
    if 'show_note_input' not in st.session_state:
        st.session_state.show_note_input = False
    
    if 'add_favorite_type' not in st.session_state:
        st.session_state.add_favorite_type = None
    
    if 'favorite_success' not in st.session_state:
        st.session_state.favorite_success = None
    
    # 타이틀 및 설명
    st.title("🏠 트레이스 등록")
    st.subheader("랭퓨즈 트레이스 검색 및 등록")
    
    # 트레이스 ID 입력 폼
    st.markdown("### 트레이스 ID 입력")
    
    # 입력 필드와 검색 버튼을 하나의 컨테이너에 가로로 배치
    input_container = st.container()
    with input_container:
        cols = st.columns([5, 1])
        with cols[0]:
            trace_id = st.text_input(
                "트레이스 ID", 
                value=st.session_state.trace_id,
                placeholder="트레이스 ID를 입력하세요",
                label_visibility="collapsed"
            )
        with cols[1]:
            search_button = st.button("검색", use_container_width=True)
    
    # 검색 버튼 클릭 또는 이미 trace_id가 세션에 저장되어 있는 경우
    if (search_button and trace_id) or (st.session_state.trace_id and not search_button):
        # 검색 버튼을 클릭한 경우에만 trace_id 업데이트
        if search_button and trace_id:
            st.session_state.trace_id = trace_id
        
        # 검색 결과 표시 영역
        st.markdown("---")
        st.markdown("### 검색 결과")
        
        # 저장된 트레이스 ID로 데이터 표시
        display_trace_data(st.session_state.trace_id)
    
    # 등록된 최근 즐겨찾기 표시 (나중에 필요하면 구현)
    st.markdown("---")
    st.markdown("### 🔍 트레이스 검색 및 등록 방법")
    st.info("""
    1. 랭퓨즈에서 트레이스 ID를 복사합니다.
    2. 위 입력창에 ID를 붙여넣고 검색 버튼을 클릭합니다.
    3. 검색된 트레이스 데이터를 확인하고 좋은 예제 또는 나쁜 예제로 등록합니다.
    4. 등록된 트레이스는 '즐겨찾기' 페이지에서 확인할 수 있습니다.
    """) 
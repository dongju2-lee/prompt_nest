import streamlit as st
import datetime
from .data_utils import (
    load_langfuse_favorites, remove_from_langfuse_favorites
)
from .langfuse_utils import fetch_langfuse_observations

def favorite_page():
    """즐겨찾기 페이지"""
    
    # 타이틀 및 설명
    st.title("⭐ 즐겨찾기")
    
    # 초기화
    if 'expanded_favorite' not in st.session_state:
        st.session_state.expanded_favorite = None
    
    if 'favorite_observations' not in st.session_state:
        st.session_state.favorite_observations = {}
    
    # 모든 즐겨찾기 데이터 불러오기
    all_favorites = load_all_favorites()
    
    if not all_favorites:
        st.info("즐겨찾기한 항목이 없습니다. 랭퓨즈 데이터 페이지에서 항목을 즐겨찾기로 등록해보세요.")
        return
    
    # 즐겨찾기 목록 표시
    st.markdown("---")
    st.markdown(f"### 즐겨찾기 목록: {len(all_favorites)}개 항목")
    
    # 데이터 표시 - 테이블 형태로
    for i, favorite in enumerate(all_favorites):
        # 현재 아이템의 확장 상태 확인
        current_id = favorite.get('id', '')
        is_expanded = st.session_state.expanded_favorite == current_id
        
        # 행 생성
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.caption(f"{current_id[:100]}")
        
        with col2:
            # 유형 표시 (좋은 예제, 나쁜 예제)
            type_text = ""
            type_color = ""
            
            if favorite.get('type') == 'good':
                type_text = "✅ 좋은 예제"
                type_color = "#a0d8b3"
            elif favorite.get('type') == 'bad':
                type_text = "❌ 나쁜 예제"
                type_color = "#ffcdd2"
            
            st.markdown(f"""
            <div style="
                background-color: {type_color};
                padding: 5px 10px;
                border-radius: 5px;
                text-align: center;
                margin-top: 10px;
            ">
                <p style="margin: 0;">{type_text}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # 상세보기/접기 버튼
            button_label = "접기" if is_expanded else "상세보기"
            
            if st.button(button_label, key=f"view_{i}_{is_expanded}"):
                # 상태 변경
                if is_expanded:
                    # 접기
                    st.session_state.expanded_favorite = None
                else:
                    # 펼치기
                    st.session_state.expanded_favorite = current_id
                    # 관찰 데이터 로딩
                    if current_id not in st.session_state.favorite_observations:
                        load_observations_for_favorite(favorite)
                
                # 상태가 변경되었으므로 페이지 리로드
                st.rerun()
        
        # 구분선 추가
        st.markdown("---")
        
        # 확장된 상세 정보 표시
        if is_expanded:
            display_langfuse_details(favorite)

def load_all_favorites():
    """모든 즐겨찾기 항목을 불러와 시간순으로 정렬합니다"""
    all_favorites = []
    
    # 랭퓨즈 즐겨찾기 불러오기
    langfuse_favorites = load_langfuse_favorites()
    
    # 좋은 예제 추가
    for favorite in langfuse_favorites.get('good', []):
        all_favorites.append({
            'id': favorite.get('id', ''),
            'name': favorite.get('name', '무제 트레이스'),
            'type': 'good',
            'data': favorite,
            'timestamp': favorite.get('timestamp') or 0
        })
    
    # 나쁜 예제 추가
    for favorite in langfuse_favorites.get('bad', []):
        all_favorites.append({
            'id': favorite.get('id', ''),
            'name': favorite.get('name', '무제 트레이스'),
            'type': 'bad',
            'data': favorite,
            'timestamp': favorite.get('timestamp') or 0
        })
    
    # 시간순으로 정렬 (최신순)
    sorted_favorites = sorted(all_favorites, key=lambda x: x.get('timestamp') or 0, reverse=True)
    
    return sorted_favorites

def load_observations_for_favorite(favorite):
    """즐겨찾기한 랭퓨즈 트레이스의 관찰 데이터를 로드합니다"""
    try:
        with st.spinner("랭퓨즈에서 트레이스 데이터를 가져오는 중..."):
            observations = fetch_langfuse_observations(favorite.get('id', ''))
            st.session_state.favorite_observations[favorite.get('id')] = observations
            
        if not observations:
            st.warning("이 트레이스에는 관찰 데이터가 없습니다. 삭제되었거나 접근할 수 없는 트레이스일 수 있습니다.")
    except Exception as e:
        st.error(f"트레이스 데이터를 가져오는 중 오류가 발생했습니다: {str(e)}")
        st.session_state.favorite_observations[favorite.get('id')] = []

def display_favorite_details(favorite):
    """즐겨찾기 항목의 상세 정보를 표시합니다"""
    display_langfuse_details(favorite)

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

def display_langfuse_details(favorite):
    """랭퓨즈 트레이스 상세 정보를 표시합니다"""
    st.markdown(f"### {favorite.get('name', '무제 트레이스')}")
    st.markdown(f"**ID:** {favorite.get('id', '')}")
    
    if favorite.get('data', {}).get('note'):
        st.markdown(f"**노트:** {favorite.get('data', {}).get('note', '')}")
    
    # 현재 관찰 데이터 가져오기
    observations = st.session_state.favorite_observations.get(favorite.get('id'), [])
    
    if not observations:
        with st.spinner("랭퓨즈에서 트레이스 데이터를 가져오는 중..."):
            observations = fetch_langfuse_observations(favorite.get('id', ''))
            st.session_state.favorite_observations[favorite.get('id')] = observations
    
    if observations:
        # 사용자 질문, 최종 답변, 시스템 프롬프트 추출
        user_question = find_user_question(observations)
        final_answer = find_final_answer(observations)
        system_prompts = find_system_prompts(observations)
        
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
                st.markdown("### 시스템 프롬프트")
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
    else:
        st.warning("이 트레이스에는 관찰 데이터가 없습니다. 삭제되었거나 접근할 수 없는 트레이스일 수 있습니다.")
    
    # 즐겨찾기 해제 버튼
    if st.button("즐겨찾기 해제", key=f"unfav_{favorite.get('id')}"):
        remove_from_langfuse_favorites(favorite.get('id'), favorite.get('type'))
        st.success("즐겨찾기에서 해제되었습니다!")
        st.rerun() 
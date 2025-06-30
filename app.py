"""
음악 이론 RAG 시스템 - Streamlit 웹 인터페이스
"""
import streamlit as st
import time
import datetime
from datetime import datetime, timedelta
import sys
import os

# 페이지 설정
st.set_page_config(
    page_title="🎼 음악 이론 Q&A",
    page_icon="🎵",
    layout="wide"
)

# 경로 설정
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.main import initialize_system
from utils.music_utils import extract_musical_terms 

# 질문 제한 설정
MAX_QUESTIONS = 15  
RECHARGE_MINUTES = 20 

# 세션 상태 초기화
if 'question_count' not in st.session_state:
    st.session_state.question_count = 0

if 'history' not in st.session_state:
    st.session_state.history = []

if 'last_recharge_time' not in st.session_state:
    st.session_state.last_recharge_time = datetime.now()

# 질문 충전 기능
def recharge_questions():
    now = datetime.now()
    elapsed_minutes = (now - st.session_state.last_recharge_time).total_seconds() / 60
    
    # 20분마다 질문 1개씩 충전
    recharges = int(elapsed_minutes / RECHARGE_MINUTES)
    
    if recharges > 0:
        # 충전할 질문 수 계산 (최대 MAX_QUESTIONS까지)
        old_count = st.session_state.question_count
        st.session_state.question_count = max(0, st.session_state.question_count - recharges)
        st.session_state.question_count = max(0, st.session_state.question_count)  # 음수 방지
        
        # 최대치 제한
        if st.session_state.question_count < 0:
            st.session_state.question_count = 0
            
        # 최대 MAX_QUESTIONS개까지만 가능
        recharged = old_count - st.session_state.question_count
        
        # 마지막 충전 시간 업데이트 (부분 충전 고려)
        st.session_state.last_recharge_time = st.session_state.last_recharge_time + timedelta(minutes=recharged * RECHARGE_MINUTES)
        
        return recharged
    return 0


def format_json_content(content):
    """JSON 형태의 참고자료를 읽기 좋게 변환"""
    import json
    import re
    
    if not content or content.strip() == "":
        return "내용이 없습니다."
    
    try:
        # JSON 문자열인지 확인
        if content.strip().startswith('{') and content.strip().endswith('}'):
            # JSON 파싱
            json_data = json.loads(content)
            
            # 읽기 좋은 형태로 변환
            formatted_parts = []
            for key, value in json_data.items():
                # 키를 읽기 좋게 변환
                if key == "definition":
                    formatted_parts.append(f"**📖 정의**\n{value}")
                elif key == "notation":
                    formatted_parts.append(f"**🎼 표기법**\n{value}")
                elif key == "temporary_tonicization":
                    formatted_parts.append(f"**🔄 일시적 토닉화**\n{value}")
                elif key == "function":
                    formatted_parts.append(f"**⚙️ 기능**\n{value}")
                elif key == "usage":
                    formatted_parts.append(f"**🎯 활용법**\n{value}")
                elif key == "example":
                    formatted_parts.append(f"**💡 예시**\n{value}")
                else:
                    # 기타 키들은 제목 형태로 변환
                    readable_key = key.replace('_', ' ').title()
                    formatted_parts.append(f"**{readable_key}**\n{value}")
            
            return "\n\n".join(formatted_parts)
        
        # JSON이 아닌 일반 텍스트
        return content
        
    except json.JSONDecodeError:
        # JSON 파싱 실패 시 원본 반환
        return content
    except Exception as e:
        # 기타 오류 시 원본 반환
        return content
    
    
# 시스템 초기화 (캐싱)
@st.cache_resource
def load_rag_system():
    """ RAG 시스템을 로드합니다 (캐시됨)"""
    return initialize_system()

def main():
    # 질문 충전 확인
    recharged = recharge_questions()
    if recharged > 0:
        st.success(f"⚡ {recharged}개의 질문이 충전되었습니다!")
    
    # 제목 및 설명 (파인튜닝 완료 표시)
    st.title("🎼 음악 이론 Q&A 시스템")
    st.markdown("### 🎯 자체 구축 데이터셋 기반 정확한 답변 제공")
    st.markdown("음악 이론에 대한 질문을 하시면 AI가 답변을 해드립니다!")
    
    # 남은 질문 수 표시
    remaining_questions = MAX_QUESTIONS - st.session_state.question_count
    
    # 다음 충전까지 남은 시간 계산
    now = datetime.now()
    elapsed_minutes = (now - st.session_state.last_recharge_time).total_seconds() / 60
    next_recharge_minutes = max(0, RECHARGE_MINUTES - (elapsed_minutes % RECHARGE_MINUTES))
    next_recharge_time = now + timedelta(minutes=next_recharge_minutes)
    
    # 정보 표시 (색상 개선)
    col1, col2 = st.columns(2)
    with col1:
        if remaining_questions > 5:
            st.success(f"📊 남은 질문 수: **{remaining_questions}개** / {MAX_QUESTIONS}개")
        elif remaining_questions > 0:
            st.warning(f"⚠️ 남은 질문 수: **{remaining_questions}개** / {MAX_QUESTIONS}개")
        else:
            st.error("❌ 질문 한도에 도달했습니다. 더 이상 질문할 수 없습니다.")
    
    with col2:
        st.info(f"⏱️ 다음 질문 충전: **{next_recharge_time.strftime('%H:%M:%S')}** (약 {int(next_recharge_minutes)}분 후)")
    
    # 시스템 로드
    with st.spinner("파인튜닝된 시스템 초기화 중..."):
        rag_model = load_rag_system()
    
    if rag_model is None:
        st.error("시스템 초기화에 실패했습니다.")
        return
    
    st.success("✅ RAG 시스템 로드 완료")
    
    # 사이드바에 시스템 정보 추가
    st.sidebar.markdown("## 🎯 시스템 특징")
    st.sidebar.info("""
    ✅ 자체 구축 데이터셋 기반 답변\n  
    ✅ 참고 자료 명시 의무화\n
    ✅ 음악 용어 자동 인식\n
    ✅ 지속적 품질 개선
    """)
    
    # 사이드바에 예시 질문들 (카테고리 추가)
    st.sidebar.markdown("## 💡 예시 질문들")
    
    # 카테고리별 예시 질문
    st.sidebar.markdown("### 🎹 코드 이론")
    chord_questions = [
        "dominant 7th 코드의 기능은?",
        "세컨더리 도미넌트란?",
        "suspended 코드는 왜 사용해?"
    ]
    
    st.sidebar.markdown("### 🎼 스케일과 모드")  
    scale_questions = [
        "도리안 모드의 특징은?",
        "하모닉 마이너 스케일 구조",
        "pentatonic scale 활용법"
    ]
    
    st.sidebar.markdown("### 🎵 화성 진행")
    progression_questions = [
        "ii-V-I 진행의 중요성",
        "트라이톤 서브스티튜션",
        "circle of fifths 활용법"
    ]
    
    # 예시 질문 버튼들
    all_questions = chord_questions + scale_questions + progression_questions
    
    for question in all_questions:
        if st.sidebar.button(
            question, 
            key=f"example_{question}",
            disabled=(remaining_questions <= 0),
            use_container_width=True
        ):
            st.session_state.query = question
    
    # 메인 질문 입력
    query = st.text_input(
        "🎵 **음악 이론 질문을 입력하세요**:",
        value=st.session_state.get('query', ''),
        placeholder="예: dominant 7th 코드는 왜 토닉으로 해결되려고 하나요?",
        disabled=(remaining_questions <= 0),
        help="구체적이고 명확한 질문일수록 더 정확한 답변을 받을 수 있습니다."
    )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        ask_button = st.button(
            "🔍 질문하기", 
            type="primary",
            disabled=(remaining_questions <= 0 or not query),
            use_container_width=True
        )
    
    with col2:
        if st.button("🗑️ 기록 지우기", use_container_width=True):
            # 질문 기록만 지우고 카운트는 유지
            st.session_state.history = []
            st.rerun()
    
    with col3:
        if st.button("🔄 세션 리셋", type="secondary", use_container_width=True):
            # 모든 세션 상태 초기화
            st.session_state.question_count = 0
            st.session_state.history = []
            st.session_state.query = ""
            st.session_state.last_recharge_time = datetime.now()
            st.rerun()
    
    # 질문 처리 (원래 로직 유지 + 약간의 개선)
    if ask_button and query and remaining_questions > 0:
        with st.spinner("🤖 모델이 답변을 생성하고 있습니다..."):
            try:
                # 질문 카운트 증가
                st.session_state.question_count += 1
                
                # 음악 용어 추출
                musical_terms = extract_musical_terms(query)
                if musical_terms:
                    st.info(f"🔍 **감지된 음악 용어**: {', '.join(musical_terms)}")
                
                # 답변 생성 (원래 로직 그대로)
                response = rag_model.get_conversation_response(query)
                
                # 품질 정보 표시 (추가)
                confidence = response.get('confidence', 'unknown')
                coverage = response.get('data_coverage', 'unknown')
                
                quality_color = {'high': '🟢', 'medium': '🟡', 'low': '🟠', 'none': '🔴'}
                quality_icon = quality_color.get(confidence, '⚪')
                
                # 답변 표시 (원래 로직 + 품질 표시)
                st.markdown(f"## 💡 답변 {quality_icon}")
                if confidence != 'unknown':
                    st.caption(f"품질: {confidence} | 데이터 커버리지: {coverage}")
                
                st.markdown(response['answer'])
                
                # 참고자료 표시
                st.markdown("## 📚 참고자료")
                sources = response.get('sources', [])
                
                if sources:
                    for i, source in enumerate(sources, 1):
                        score = source.get('score', 0)
                        score_color = "🟢" if score > 0.8 else "🟡" if score > 0.6 else "🟠"
                        title = source.get('title', f'참고자료 {i}')
                        
                        with st.expander(f"{score_color} 참고자료 {i}: {title} (관련도: {score:.3f})"):
                            # JSON 형태 처리
                            content = source.get('content', '')
                            formatted_content = format_json_content(content)
                            st.markdown(formatted_content)
                else:
                    st.warning("📚 현재 데이터셋에서 관련 참고자료를 찾을 수 없습니다.")
                
                # 질문 기록 추가 (약간 개선)
                st.session_state.history.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'query': query,
                    'answer': response['answer'],
                    'confidence': confidence,
                    'sources_count': len(sources)
                })
                
                # 업데이트된 남은 질문 수 표시
                remaining_questions = MAX_QUESTIONS - st.session_state.question_count
                if remaining_questions <= 0:
                    st.warning("⚠️ 질문 한도에 도달했습니다. 더 이상 질문할 수 없습니다.")
                elif remaining_questions <= 3:
                    st.warning(f"⚠️ 남은 질문 수: {remaining_questions}개")
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")
                # 오류 시 질문 카운트 복구
                st.session_state.question_count = max(0, st.session_state.question_count - 1)
    
    # 질문 기록 표시 (약간 개선)
    if st.session_state.history:
        st.markdown("## 📝 질문 기록")
        # 최근 5개만 표시
        recent_history = list(reversed(st.session_state.history))[:5]
        
        for i, item in enumerate(recent_history, 1):
            confidence = item.get('confidence', 'unknown')
            quality_icon = {'high': '🟢', 'medium': '🟡', 'low': '🟠', 'none': '🔴'}.get(confidence, '⚪')
            timestamp = item.get('timestamp', '')
            
            with st.expander(f"{quality_icon} 질문 {i}: {item['query'][:50]}... ({timestamp})"):
                st.markdown(f"**질문:** {item['query']}")
                st.markdown(f"**답변:** {item['answer']}")
                if 'sources_count' in item:
                    st.caption(f"참고자료: {item['sources_count']}개 | 품질: {confidence}")

    # 푸터 (업데이트)
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center'>
        <b>🎵 음악 이론 Q&A 시스템</b><br>
        <small>AI Portfolio Project | RAG 기반 모델</small><br>
        <small>Contact : cbg1704@gmail.com</small>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
"""
음악 이론 RAG 시스템 - Streamlit 웹 인터페이스
"""
import streamlit as st
import time
import datetime
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(
    page_title="🎼 음악 이론 Q&A",
    page_icon="🎵",
    layout="wide"
)

# 이제 다른 임포트 진행
import sys
import os

# 경로 설정
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 메인 모듈 임포트
from src.main import initialize_system
from src.utils.music_utils import extract_musical_terms

# 질문 제한 설정
MAX_QUESTIONS = 10
RECHARGE_MINUTES = 30  # 30분마다 질문 1개 충전

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
    
    # 30분마다 질문 1개씩 충전
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

# 시스템 초기화 (캐싱)
@st.cache_resource
def load_rag_system():
    """RAG 시스템을 로드합니다 (캐시됨)"""
    return initialize_system()

def main():
    # 질문 충전 확인
    recharged = recharge_questions()
    if recharged > 0:
        st.success(f"⚡ {recharged}개의 질문이 충전되었습니다!")
    
    # 제목 및 설명
    st.title("🎼 음악 이론 Q&A 시스템")
    st.markdown("음악 이론에 대한 질문을 하시면 AI가 답변해드립니다!")
    
    # 남은 질문 수 표시
    remaining_questions = MAX_QUESTIONS - st.session_state.question_count
    
    # 다음 충전까지 남은 시간 계산
    now = datetime.now()
    elapsed_minutes = (now - st.session_state.last_recharge_time).total_seconds() / 60
    next_recharge_minutes = max(0, RECHARGE_MINUTES - (elapsed_minutes % RECHARGE_MINUTES))
    next_recharge_time = now + timedelta(minutes=next_recharge_minutes)
    
    # 정보 표시
    col1, col2 = st.columns(2)
    with col1:
        if remaining_questions > 0:
            st.info(f"📊 남은 질문 수: {remaining_questions}개 / {MAX_QUESTIONS}개")
        else:
            st.warning("⚠️ 질문 한도에 도달했습니다. 더 이상 질문할 수 없습니다.")
    
    with col2:
        st.info(f"⏱️ 다음 질문 충전: {next_recharge_time.strftime('%H:%M:%S')} (약 {int(next_recharge_minutes)}분 후)")
    
    # 시스템 로드
    with st.spinner("시스템 초기화 중..."):
        rag_model = load_rag_system()
    
    if rag_model is None:
        st.error("시스템 초기화에 실패했습니다.")
        return
    
    # 사이드바에 예시 질문들
    st.sidebar.header("💡 예시 질문들")
    example_questions = [
        "세븐스 코드가 뭐야?",
        "메이저 스케일의 구조를 설명해줘",
        "ii-V-I 진행이 뭔가요?",
        "트라이톤 서브스티튜션에 대해 알려줘",
        "도리안 모드의 특징은?",
        "세컨더리 도미넌트는 언제 사용해?"
    ]
    
    # 예시 질문 버튼 (남은 질문 수가 있을 때만 활성화)
    for question in example_questions:
        if st.sidebar.button(
            question, 
            key=f"example_{question}",
            disabled=(remaining_questions <= 0)
        ):
            st.session_state.query = question
    
    # 메인 질문 입력
    query = st.text_input(
        "🎵 질문을 입력하세요:",
        value=st.session_state.get('query', ''),
        placeholder="예: 메이저 코드와 마이너 코드의 차이점은?",
        disabled=(remaining_questions <= 0)
    )
    
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        ask_button = st.button(
            "🔍 질문하기", 
            type="primary",
            disabled=(remaining_questions <= 0 or not query)
        )
    
    with col2:
        if st.button("🗑️ 질문 기록 지우기"):
            # 질문 기록만 지우고 카운트는 유지
            st.session_state.history = []
            st.rerun()
    
    with col3:
        if st.button("🔄 세션 초기화 (질문 카운트 리셋)", type="secondary"):
            # 모든 세션 상태 초기화
            st.session_state.question_count = 0
            st.session_state.history = []
            st.session_state.query = ""
            st.session_state.last_recharge_time = datetime.now()
            st.rerun()
    
    # 질문 처리
    if ask_button and query and remaining_questions > 0:
        with st.spinner("답변 생성 중..."):
            try:
                # 질문 카운트 증가
                st.session_state.question_count += 1
                
                # 음악 용어 추출
                musical_terms = extract_musical_terms(query)
                if musical_terms:
                    st.info(f"🔍 감지된 음악 용어: {', '.join(musical_terms)}")
                
                # 답변 생성
                response = rag_model.get_conversation_response(query)
                
                # 답변 표시
                st.markdown("## 💡 답변")
                st.markdown(response['answer'])
                
                # 참고자료 표시
                st.markdown("## 📚 참고자료")
                for i, source in enumerate(response['sources'], 1):
                    with st.expander(f"참고자료 {i}: {source['title']} (유사도: {source['score']:.3f})"):
                        st.text(source['content'])
                
                # 질문 기록 추가
                st.session_state.history.append({
                    'query': query,
                    'answer': response['answer']
                })
                
                # 업데이트된 남은 질문 수 표시
                remaining_questions = MAX_QUESTIONS - st.session_state.question_count
                if remaining_questions <= 0:
                    st.warning("⚠️ 질문 한도에 도달했습니다. 더 이상 질문할 수 없습니다.")
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")
    
    # 질문 기록 표시
    if st.session_state.history:
        st.markdown("## 📝 질문 기록")
        for i, item in enumerate(reversed(st.session_state.history), 1):
            with st.expander(f"질문 {i}: {item['query'][:50]}..."):
                st.markdown(f"**질문:** {item['query']}")
                st.markdown(f"**답변:** {item['answer']}")

    # 푸터
    st.markdown("---")
    st.markdown("**🎵 음악 이론 Q&A 시스템** | AI Portfolio Project")

if __name__ == "__main__":
    main()
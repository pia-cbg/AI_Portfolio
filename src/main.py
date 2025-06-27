"""
음악 이론 RAG 시스템 - Streamlit 웹 인터페이스
"""
import streamlit as st
import sys
import os
import anthropic
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# 경로 설정
sys.path.append(os.path.dirname(__file__))

# 모듈 임포트
from src.data_processing.json_loader import MusicTheoryDataLoader
from src.data_processing.embedding_generator import EmbeddingGenerator
from src.models.retriever import MusicKnowledgeRetriever
from src.models.rag_model import MusicRAGModel
from src.utils.music_utils import extract_musical_terms

# 환경 변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="🎼 음악 이론 Q&A",
    page_icon="🎵",
    layout="wide"
)

# 시스템 초기화 (캐싱)
@st.cache_resource
def initialize_system():
    """시스템을 초기화합니다."""
    # 1. 데이터 로드
    loader = MusicTheoryDataLoader()
    data = loader.load_data()
    
    if not data:
        st.error("데이터 로드 실패!")
        return None
    
    # 2. 임베딩 처리
    embedder = EmbeddingGenerator()
    
    # 기존 임베딩이 있는지 확인
    if not embedder.load_embeddings():
        chunks = loader.extract_text_chunks()
        embedder.generate_embeddings(chunks)
        embedder.save_embeddings()
    
    # 3. 검색기 초기화
    retriever = MusicKnowledgeRetriever()
    retriever.build_index(embedder.embeddings, embedder.chunks)
    
    # 4. RAG 모델 초기화
    rag_model = MusicRAGModel(retriever)
    
    return rag_model

def main():
    # 제목 및 설명
    st.title("🎼 음악 이론 Q&A 시스템")
    st.markdown("음악 이론에 대한 질문을 하시면 AI가 답변해드립니다!")
    
    # 시스템 로드
    with st.spinner("시스템 초기화 중..."):
        rag_model = initialize_system()
    
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
    
    for question in example_questions:
        if st.sidebar.button(question, key=f"example_{question}"):
            st.session_state.query = question
    
    # 메인 질문 입력
    query = st.text_input(
        "🎵 질문을 입력하세요:",
        value=st.session_state.get('query', ''),
        placeholder="예: 메이저 코드와 마이너 코드의 차이점은?"
    )
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        ask_button = st.button("🔍 질문하기", type="primary")
    
    with col2:
        if st.button("🗑️ 초기화"):
            st.session_state.clear()
            st.rerun()
    
    # 질문 처리
    if ask_button and query:
        with st.spinner("답변 생성 중..."):
            try:
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
                
                # 질문 기록
                if 'history' not in st.session_state:
                    st.session_state.history = []
                
                st.session_state.history.append({
                    'query': query,
                    'answer': response['answer']
                })
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")
    
    # 질문 기록 표시
    if 'history' in st.session_state and st.session_state.history:
        st.markdown("## 📝 질문 기록")
        for i, item in enumerate(reversed(st.session_state.history[-5:]), 1):
            with st.expander(f"질문 {i}: {item['query'][:50]}..."):
                st.markdown(f"**질문:** {item['query']}")
                st.markdown(f"**답변:** {item['answer'][:200]}...")

    # 푸터
    st.markdown("---")
    st.markdown("**🎵 음악 이론 Q&A 시스템** | AI Portfolio Project")

if __name__ == "__main__":
    main()
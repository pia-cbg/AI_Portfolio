"""
음악 이론 RAG 시스템 메인 실행 파일
"""
import os
import sys
from typing import Optional

# 상대 경로 임포트를 위한 경로 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 모듈 임포트
from data_processing.json_loader import MusicTheoryDataLoader
from data_processing.embedding_generator import EmbeddingGenerator
from models.retriever import MusicKnowledgeRetriever
from models.rag_model import MusicRAGModel
from utils.music_utils import extract_musical_terms, format_chord_name

def initialize_system():
    """시스템을 초기화합니다."""
    print("🎵 음악 지식 RAG 시스템 초기화 중...")
    
    # 1. 데이터 로드
    print("1. 데이터 로딩...")
    loader = MusicTheoryDataLoader()
    data = loader.load_data()
    
    if not data:
        print("❌ 데이터 로드 실패!")
        return None
    
    # 2. 임베딩 처리
    print("2. 임베딩 처리...")
    embedder = EmbeddingGenerator()
    
    # 기존 임베딩이 있는지 확인
    if not embedder.load_embeddings():
        print("   새로운 임베딩 생성 중...")
        chunks = loader.extract_text_chunks()
        embedder.generate_embeddings(chunks)
        embedder.save_embeddings()
    
    # 3. 검색기 초기화
    print("3. 검색기 초기화...")
    retriever = MusicKnowledgeRetriever()
    retriever.build_index(embedder.embeddings, embedder.chunks)
    
    # 4. RAG 모델 초기화
    print("4. RAG 모델 초기화...")
    rag_model = MusicRAGModel(retriever)
    
    print("✅ 시스템 초기화 완료!")
    return rag_model

def print_welcome_message():
    """환영 메시지를 출력합니다."""
    print("\n" + "="*60)
    print("🎼  음악 이론 Q&A 시스템에 오신 것을 환영합니다!  🎼")
    print("="*60)
    print("음악 이론에 관한 질문을 입력해주세요.")
    print("예시 질문:")
    print("  - 세븐스 코드가 뭐야?")
    print("  - 도미넌트 코드는 왜 토닉으로 해결되려고 하나요?")
    print("  - 세컨더리 도미넌트와 트라이톤 서브스티튜션의 차이점은?")
    print("-"*60)
    print("종료하려면 'quit', 'exit', '종료' 또는 'q'를 입력하세요.")
    print("="*60)

def main():
    """메인 실행 함수"""
    # 시스템 초기화
    rag_model = initialize_system()
    
    if rag_model is None:
        print("시스템 초기화에 실패했습니다.")
        return
    
    # 환영 메시지 출력
    print_welcome_message()
    
    # 대화 루프
    while True:
        try:
            # 사용자 입력 받기
            query = input("\n🎵 질문: ").strip()
            
            # 종료 명령 확인
            if query.lower() in ['quit', 'exit', '종료', 'q']:
                print("\n👋 시스템을 종료합니다. 감사합니다!")
                break
            
            # 빈 입력 처리
            if not query:
                print("질문을 입력해주세요.")
                continue
            
            # 질문에서 음악 용어 추출
            musical_terms = extract_musical_terms(query)
            if musical_terms:
                print(f"🔍 감지된 음악 용어: {', '.join(musical_terms)}")
            
            # 답변 생성
            print("\n⏳ 답변 생성 중...")
            response = rag_model.get_conversation_response(query)
            
            # 답변 출력
            print(f"\n💡 답변:")
            print(response['answer'])
            
            # 참고자료 출력
            print(f"\n📚 참고자료:")
            for i, source in enumerate(response['sources'], 1):
                print(f"  {i}. {source['title']} (유사도: {source['score']:.3f})")
            
        except KeyboardInterrupt:
            print("\n\n👋 시스템을 종료합니다. 감사합니다!")
            break
        except Exception as e:
            print(f"❌ 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    main()
"""
음악 이론 RAG 시스템 객체 초기화 모듈
(파인튜닝/운영/실험 스크립트에서 import해서 사용)
"""

import os
from src.data_processing.json_loader import MusicTheoryDataLoader
from src.data_processing.embedding_generator import EmbeddingGenerator
from src.models.retriever import VectorRetriever
from src.models.rag_model import RAGModel

def initialize_system(force_regenerate: bool = False):
    """
    RAG 모델+검색기 전체 시스템 객체 생성 (실패시 Exception)
    - 임베딩/인덱스 자동 로드, 필요시 재생성
    - 반환값: rag_model 객체 (get_conversation_response 등 인터페이스 지원)
    """
    print("🎵 음악 이론 RAG 시스템 초기화...")

    # 1. 데이터 로드
    loader = MusicTheoryDataLoader()
    data = loader.load_data()
    if not data:
        raise RuntimeError("음악이론 데이터 로드 실패!")

    # 2. 임베딩 처리
    embedder = EmbeddingGenerator()
    embedding_dir = 'data/embeddings'
    embedding_path = os.path.join(embedding_dir, 'music_theory_embeddings.pkl')
    json_path = 'data/raw/music_theory_curriculum.json'

    need_regen = force_regenerate
    if os.path.exists(embedding_path) and os.path.exists(json_path):
        if os.path.getmtime(json_path) > os.path.getmtime(embedding_path):
            need_regen = True
    if need_regen or not embedder.load_embeddings():
        print("   🔄 임베딩 생성 시작...")
        chunks = loader.extract_text_chunks()
        embedder.generate_embeddings(chunks)
        embedder.save_embeddings()
        print("   ✅ 임베딩 생성 완료!")
    else:
        print("   ✅ 임베딩 로드 완료!")

    # 3. 검색기(벡터) 초기화
    retriever = VectorRetriever()
    if not retriever.load_embeddings():
        raise RuntimeError("검색기 임베딩 로드 실패!")
    if not retriever.build_index():
        raise RuntimeError("검색기 인덱스 구축 실패!")

    # 4. RAG 모델 래퍼 초기화
    rag_model = RAGModel(retriever)
    print("✅ RAG 시스템 객체 생성 성공!")
    return rag_model
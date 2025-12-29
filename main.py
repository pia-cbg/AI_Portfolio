"""
음악 이론 RAG 시스템 전체 객체 초기화 및 (수동/자동/배치) 진입점
"""

import os
from src.data_processing.json_loader import MusicTheoryDataLoader
from src.data_processing.embedding_generator import EmbeddingGenerator
from src.models.retriever import VectorRetriever
from src.models.rag_model import RAGModel

def initialize_system(force_regenerate: bool = False):
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

def cli_launcher():
    """ (선택) CLI/manual 테스트 실행기 """
    rag_model = initialize_system()
    print("\n🌱 (음악 이론 RAG) 자유 입력 CLI 모드입니다. 종료: exit/quit 입력\n")
    try:
        while True:
            query = input("\n질문(종료: exit): ")
            if query.strip().lower() in ["exit", "quit"]:
                print("종료합니다.")
                break
            # 실제 rag_model/retriever_inner 동작 로그 보기!
            response = rag_model.get_conversation_response(query)
            topk_sources = response.get("sources", [])
            print("\n[답변]")
            print(response.get('answer', ''))
            print("\n[참고 passage 개수]:", len(topk_sources))

            # # === 🔍 상세 Top-K candidate 로그 확인 ===
            # if topk_sources:
            #     print(f"\n==== [검색 Top-K 후보 상세] ====")
            #     for idx, p in enumerate(topk_sources):
            #         print(f"{idx+1}. {p.get('concept.ko', p.get('concept.en'))} | node_id={p.get('node_id')} | type={p.get('concept_type')} | score={p.get('score',0):.3f} | rank={p.get('rank')}")

            # else:
            #     print("※ Top-K passage가 없음! (검색 miss)")
    except Exception as e:
        print("\n[오류] 실행 중 에러 발생:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # CLI/manual interactive 테스트 모드
    cli_launcher()

    # 자동평가/실험을 위해서는 이 파일이 아니라 run_experiment.py 등 (src/experiments/...)에서
    # from main import initialize_system
    # rag_model = initialize_system()  # import해서 사용!
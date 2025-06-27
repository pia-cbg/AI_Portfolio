import faiss
import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer

class MusicKnowledgeRetriever:
    def __init__(self, embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.index = None
        self.chunks = None
        self.embeddings = None
    
    def build_index(self, embeddings: np.ndarray, chunks: List[Dict]):
        """FAISS 인덱스를 구축합니다."""
        self.embeddings = embeddings
        self.chunks = chunks
        
        # FAISS 인덱스 생성 (코사인 유사도 사용)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product (코사인 유사도)
        
        # 정규화된 임베딩 추가
        normalized_embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        self.index.add(normalized_embeddings.astype('float32'))
        
        print(f"FAISS 인덱스 구축 완료: {self.index.ntotal}개 벡터")
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """쿼리와 가장 유사한 청크들을 검색합니다."""
        if self.index is None:
            raise ValueError("인덱스가 구축되지 않았습니다.")
        
        # 쿼리 임베딩 생성 및 정규화
        query_embedding = self.embedding_model.encode([query])
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        
        # 검색 수행
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # 결과 반환
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks):
                results.append((self.chunks[idx], float(score)))
        
        return results
    
    def format_search_results(self, results: List[Tuple[Dict, float]]) -> str:
        """검색 결과를 포맷팅합니다."""
        if not results:
            return "관련 정보를 찾을 수 없습니다."
        
        formatted_results = []
        for i, (chunk, score) in enumerate(results, 1):
            title = chunk.get("metadata", {}).get("title", "제목 없음")
            content = chunk.get("content", "")
            
            formatted_results.append(f"""
[결과 {i}] {title}
{content}
(유사도: {score:.3f})
""")
        
        return "\n".join(formatted_results)

if __name__ == "__main__":
    import pickle
    import numpy as np
    import os
    import sys
    
    # 현재 스크립트 경로를 기반으로 프로젝트 루트 경로 설정
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    
    # 임베딩 및 청크 로드 경로
    embeddings_path = os.path.join(project_root, "data/processed/embeddings/embeddings.npy")
    chunks_path = os.path.join(project_root, "data/processed/embeddings/chunks.pkl")
    
    # 임베딩 및 청크가 존재하는지 확인
    if os.path.exists(embeddings_path) and os.path.exists(chunks_path):
        # 저장된 임베딩과 청크 로드
        embeddings = np.load(embeddings_path)
        with open(chunks_path, 'rb') as f:
            chunks = pickle.load(f)
        
        # 검색기 초기화
        retriever = MusicKnowledgeRetriever()
        retriever.build_index(embeddings, chunks)
        
        # 테스트 검색
        test_query = "세븐스 코드가 뭐야?"
        results = retriever.search(test_query, top_k=3)
        print(retriever.format_search_results(results))
    else:
        print("임베딩 파일이 없습니다. 먼저 임베딩을 생성해주세요.")
        print(f"확인된 경로: {embeddings_path}")
import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

class VectorRetriever:
    def __init__(
        self,
        embedding_path: str = 'data/embeddings/music_theory_embeddings.pkl'
    ):
        self.embedding_path = embedding_path
        self.embeddings = None
        self.chunks = None
        self.model = None
        self.model_name = None
        self.index = None

        # ---- 임베딩 파일에서 embeddings, chunks, model_name 자동 로드 ----
        if os.path.exists(self.embedding_path):
            with open(self.embedding_path, 'rb') as f:
                obj = pickle.load(f)
            # embeddings는 np.array로 강제 변환
            arr = obj.get('embeddings', None)
            if arr is not None and not isinstance(arr, np.ndarray):
                arr = np.array(arr)
            self.embeddings = arr
            self.chunks = obj.get('chunks', None)
            self.model_name = obj.get('model_name', 'intfloat/multilingual-e5-large')
        else:
            raise FileNotFoundError(f"임베딩 파일이 존재하지 않습니다: {self.embedding_path}")

        # ---- 모델 자동 로딩 ----
        print(f"[VectorRetriever] 임베딩 모델 로딩: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)

    def load_embeddings(self) -> bool:
        """
        임베딩, 청크, 모델명을 재로드 (필요시)
        """
        try:
            with open(self.embedding_path, 'rb') as f:
                obj = pickle.load(f)
            arr = obj.get('embeddings', None)
            if arr is not None and not isinstance(arr, np.ndarray):
                arr = np.array(arr)
            self.embeddings = arr
            self.chunks = obj.get('chunks', None)
            self.model_name = obj.get('model_name', self.model_name)
            print(f"[VectorRetriever] 임베딩 재로드 완료, shape: {self.embeddings.shape}, 모델: {self.model_name}")
            return self.embeddings is not None and self.chunks is not None
        except Exception as e:
            print(f"[VectorRetriever][ERROR] 임베딩 로드 실패: {e}")
            self.embeddings = None
            self.chunks = None
            return False

    def build_index(self) -> bool:
        """
        FAISS 인덱스 구축
        """
        try:
            if self.embeddings is None:
                print("[VectorRetriever][ERROR] build_index: 임베딩 미존재")
                return False
            dim = self.embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dim)
            self.index.add(self.embeddings.astype(np.float32))
            print(f"[VectorRetriever] FAISS 인덱스 구축 성공 ({self.index.ntotal}개, dim={dim})")
            return True
        except Exception as e:
            print(f"[VectorRetriever][ERROR] build_index 실패: {e}")
            return False

    def search(self, query: str, top_k: int = 5, min_score: float = 0.0):
        """
        FAISS+임베딩 기반 질의 검색
        """
        if self.index is None:
            self.build_index()
            if self.index is None:
                print("[VectorRetriever][ERROR] 인덱스 구축 실패")
                return []

        # 쿼리 임베딩
        query_emb = self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True
        ).astype('float32').reshape(1, -1)

        # 유사도 검색
        scores, indices = self.index.search(query_emb, top_k)
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if score >= min_score and idx < len(self.chunks):
                chunk = self.chunks[idx]
                results.append({
                    'title': chunk.get('title', ''),
                    'content': chunk.get('content', ''),
                    'context': chunk.get('context', ''),
                    'metadata': chunk.get('metadata', {}),
                    'score': float(score),
                    'rank': i + 1
                })
        return results

    def get_stats(self):
        return {
            'model_name': self.model_name,
            'num_embeddings': len(self.embeddings) if self.embeddings is not None else 0,
            'embedding_dim': int(self.embeddings.shape[1]) if self.embeddings is not None else None
        }
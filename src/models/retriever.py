import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

def normalize(text):
    if not text: return ""
    text = text.lower().replace(" ", "").replace("-", "").replace("_", "").replace("/", "").strip()
    return text

def rerank_by_alias(query, results, alias_boost=0.05, partial_weight=0.5):
    """
    - alias/concept.ko/en과 쿼리가 "정확/부분/포함 일치"하면
    - 해당 청크의 score에 가중치(alias_boost)를 더함
    - partial_weight는 부분 일치 등일 때 가중치의 몇 퍼센트만 적용할지 결정
    """
    nq = normalize(query)
    for r in results:
        base_score = r['score']
        candidates = [
            normalize(r.get('concept.ko', '')),
            normalize(r.get('concept.en', ''))
        ] + [normalize(a) for a in (r.get('aliases') or '').split(';') if a]
        for c in candidates:
            if nq == c:  # 정확히 일치
                r['score'] = base_score + alias_boost
                break
            elif nq in c or c in nq:  # 부분/포함 일치
                r['score'] = base_score + (alias_boost * partial_weight)
                break
    # 유사도 score 기준으로 (내림차순) 다시 정렬
    results = sorted(results, key=lambda x: x['score'], reverse=True)
    return results

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

        if os.path.exists(self.embedding_path):
            with open(self.embedding_path, 'rb') as f:
                obj = pickle.load(f)
            arr = obj.get('embeddings', None)
            if arr is not None and not isinstance(arr, np.ndarray):
                arr = np.array(arr)
            self.embeddings = arr
            self.chunks = obj.get('chunks', None)
            self.model_name = obj.get('model_name', 'intfloat/multilingual-e5-large')
        else:
            raise FileNotFoundError(f"임베딩 파일이 존재하지 않습니다: {self.embedding_path}")

        # print(f"[VectorRetriever] 임베딩 모델 로딩: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)

    def load_embeddings(self) -> bool:
        try:
            with open(self.embedding_path, 'rb') as f:
                obj = pickle.load(f)
            arr = obj.get('embeddings', None)
            if arr is not None and not isinstance(arr, np.ndarray):
                arr = np.array(arr)
            self.embeddings = arr
            self.chunks = obj.get('chunks', None)
            self.model_name = obj.get('model_name', self.model_name)
            # print(f"[VectorRetriever] 임베딩 재로드 완료, shape: {self.embeddings.shape}, 모델: {self.model_name}")
            return self.embeddings is not None and self.chunks is not None
        except Exception as e:
            print(f"[VectorRetriever][ERROR] 임베딩 로드 실패: {e}")
            self.embeddings = None
            self.chunks = None
            return False

    def build_index(self) -> bool:
        try:
            if self.embeddings is None:
                # print("[VectorRetriever][ERROR] build_index: 임베딩 미존재")
                return False
            dim = self.embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dim)
            self.index.add(self.embeddings.astype(np.float32))
            # print(f"[VectorRetriever] FAISS 인덱스 구축 성공 ({self.index.ntotal}개, dim={dim})")
            return True
        except Exception as e:
            print(f"[VectorRetriever][ERROR] build_index 실패: {e}")
            return False

    def search(self, query: str, top_k: int = 5, min_score: float = 0.0):
        """
        질문(query) 관련 music chunk Top-N 검색 (최신 구조 반환)
        """
        if self.index is None:
            self.build_index()
            if self.index is None:
                print("[VectorRetriever][ERROR] 인덱스 구축 실패")
                return []

        query_orig = query
        query = query.lower().strip()

        # 쿼리 임베딩
        query_emb = self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True
        ).astype('float32').reshape(1, -1)

        # FAISS 유사도 검색
        scores, indices = self.index.search(query_emb, top_k)
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if score >= min_score and idx < len(self.chunks):
                chunk = self.chunks[idx]
                results.append({
                    'concept.ko': chunk.get('concept.ko', ''),
                    'concept.en': chunk.get('concept.en', ''),
                    'aliases': chunk.get('aliases', ''),
                    'definition': chunk.get('definition', ''),
                    'logic': chunk.get('logic', ''),
                    'examples.name': chunk.get('examples.name', ''),
                    'examples.description': chunk.get('examples.description', ''),
                    'tips': chunk.get('tips', ''),
                    'prerequisites.ko': chunk.get('prerequisites.ko', ''),
                    'prerequisites.en': chunk.get('prerequisites.en', ''),
                    'score': float(score),
                    'rank': i + 1
                })

        # === re-ranking by alias/concept match ===
        results = rerank_by_alias(query_orig, results)
        return results

    def get_stats(self):
        return {
            'model_name': self.model_name,
            'num_embeddings': len(self.embeddings) if self.embeddings is not None else 0,
            'embedding_dim': int(self.embeddings.shape[1]) if self.embeddings is not None else None
        }

# 디버깅용
if __name__ == "__main__":
#     retriever = VectorRetriever()
#     retriever.build_index()
#     query = "세컨더리 도미넌트에 대해서 알려줘"
#     results = retriever.search(query, top_k=5)
#     print(f"\n쿼리: '{query}'")
#     print("유사한 청크:")
#     for i, r in enumerate(results, 1):
#         print(f"\n{i}. 용어: {r['concept.ko'] or r['concept.en']}")
#         print(f"   정의: {r['definition'][:120]}...")
#         print(f"   유사도: {r['score']:.3f}")
#     if results:
#         from pprint import pprint
#         print("\n[1번 청크 전체 디버깅]")
#         pprint(results[0])
    pass
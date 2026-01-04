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
    nq = normalize(query)
    for r in results:
        base_score = r['score']
        candidates = [
            normalize(r.get('concept.ko', '')),
            normalize(r.get('concept.en', ''))
        ] + [normalize(a) for a in (r.get('aliases') or '').split(';') if a]
        for c in candidates:
            if nq == c:  # 정확 일치
                r['score'] = base_score + alias_boost
                break
            elif nq in c or c in nq:  # 부분/포함 일치
                r['score'] = base_score + (alias_boost * partial_weight)
                break
    results = sorted(results, key=lambda x: x['score'], reverse=True)
    # rank 필드 다시 업데이트 (정렬 후)
    for i, r in enumerate(results, 1):
        r['rank'] = i
    return results

class VectorRetriever:
    def __init__(self, embedding_path: str = 'data/musicqna/embeddings/music_theory_embeddings.pkl'):
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
            return self.embeddings is not None and self.chunks is not None
        except Exception as e:
            print(f"[VectorRetriever][ERROR] 임베딩 로드 실패: {e}")
            self.embeddings = None
            self.chunks = None
            return False

    def build_index(self) -> bool:
        try:
            if self.embeddings is None:
                return False
            dim = self.embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dim)
            self.index.add(self.embeddings.astype(np.float32))
            return True
        except Exception as e:
            print(f"[VectorRetriever][ERROR] build_index 실패: {e}")
            return False

    def search(self, query: str, top_k: int = 5, min_score: float = 0.0):
        """
        쿼리(query) 관련 music chunk Top-K 검색.
        반환 passage에는 node_id, concept_type, parent_id 등 평가/로그에 필요한 메타 정보가 포함됨.
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
                # 반드시 node_id, concept_type, parent_id 등 메타 정보 포함
                results.append({
                    'node_id': chunk.get('node_id'),
                    'concept_type': chunk.get('concept_type'),
                    'parent_id': chunk.get('parent_id'),
                    'concept.ko': chunk.get('concept.ko', '') or '',
                    'concept.en': chunk.get('concept.en', '') or '',
                    'aliases': chunk.get('aliases', '') or '',
                    'definition': chunk.get('definition', '') or '',
                    'logic': chunk.get('logic', '') or '',
                    'examples.name': chunk.get('examples.name', '') or '',
                    'examples.description': chunk.get('examples.description', '') or '',
                    'tips': chunk.get('tips', '') or '',
                    'prerequisites.ko': chunk.get('prerequisites.ko', '') or '',
                    'prerequisites.en': chunk.get('prerequisites.en', '') or '',
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

# if __name__ == "__main__":
#     retriever = VectorRetriever()
#     retriever.load_embeddings()
#     retriever.build_index()

#     query = "음표는 어떤 기호야?"
#     print(f"\n[실험 쿼리]: '{query}'")

#     results = retriever.search(query, top_k=5, min_score=0.0)
#     print("[Top-K 후보]:")
#     if not results:
#         print(" (0건) ➡️ 검색 miss!")
#     else:
#         for i, r in enumerate(results):
#             print(
#                 f" {i+1}. {r.get('concept.ko', r.get('concept.en'))} "
#                 f"| node_id={r.get('node_id')} | type={r.get('concept_type')} "
#                 f"| score={r.get('score', 0):.4f} | rank={r.get('rank', '-')}"
#             )
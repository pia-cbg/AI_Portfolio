import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import pickle
import os
import torch

class EmbeddingGenerator:
    def __init__(
        self, 
        model_name: str = None, 
        embedding_path: str = 'data/musicqna/embeddings/music_theory_embeddings.pkl'
    ):
        if model_name is None:
            model_name = "intfloat/multilingual-e5-large"
        print(f"🎵 임베딩 모델 로딩: {model_name}")

        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"🖥️ 사용 디바이스: {self.device}")

        self.model = SentenceTransformer(model_name, device=self.device)
        self.model_name = model_name
        self.embedding_path = embedding_path
        self.embeddings = None
        self.chunks = None

    def generate_embeddings(self, text_chunks: List[Dict]) -> np.ndarray:
        texts = []
        for chunk in text_chunks:
            # 용어 강조 + 주요 필드 조합 (태그 부여로 weighting 효과)
            parts = [
                f"[KEYWORD] {chunk.get('concept.ko', '')}",
                f"[KEYWORD_EN] {chunk.get('concept.en', '')}",
                f"[ALIAS] {chunk.get('aliases', '')}",
                f"[DEF] {chunk.get('definition', '')}",
                f"[LOGIC] {chunk.get('logic', '')}",
                f"[EX_NAME] {chunk.get('examples.name', '')}",
                f"[EX_DESC] {chunk.get('examples.description', '')}",
                f"[TIPS] {chunk.get('tips', '')}",
                f"[PREQ_KO] {chunk.get('prerequisites.ko', '')}",
                f"[PREQ_EN] {chunk.get('prerequisites.en', '')}"
            ]
            combined_text = ' '.join([part for part in parts if part and part != ''])
            texts.append(combined_text)
        
        print(f"🎵 {len(texts)}개의 텍스트에 대한 임베딩 생성 중...")
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        self.embeddings = embeddings
        self.chunks = text_chunks
        print(f"✅ 임베딩 생성 완료: shape {embeddings.shape}")
        return embeddings

    def save_embeddings(self):
        os.makedirs(os.path.dirname(self.embedding_path), exist_ok=True)
        embedding_data = {
            'embeddings': self.embeddings.tolist(),
            'chunks': self.chunks,
            'model_name': self.model_name
        }
        with open(self.embedding_path, 'wb') as f:
            pickle.dump(embedding_data, f)
        print(f"✅ 임베딩 저장 완료: {len(self.chunks)}개, {self.embedding_path}")

    def load_embeddings(self) -> bool:
        try:
            with open(self.embedding_path, 'rb') as f:
                embedding_data = pickle.load(f)
            self.embeddings = np.array(embedding_data['embeddings'])
            self.chunks = embedding_data['chunks']
            self.model_name = embedding_data.get('model_name', 'unknown')
            print(f"✅ 임베딩 로드 완료: {len(self.chunks)}개, 모델: {self.model_name}")
            return True
        except FileNotFoundError:
            print(f"❌ 임베딩 파일을 찾을 수 없습니다: {self.embedding_path}")
            return False
        except Exception as e:
            print(f"❌ 임베딩 로드 중 오류: {e}")
            return False

    def get_embeddings(self) -> Tuple[np.ndarray, List[Dict]]:
        if self.embeddings is None or self.chunks is None:
            raise ValueError("임베딩이 생성되거나 로드되지 않았습니다.")
        return self.embeddings, self.chunks

    def search_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        if self.embeddings is None:
            print("❌ 임베딩이 로드되지 않았습니다.")
            return []
        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        similarities = np.dot(self.embeddings, query_embedding)
        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = []
        for idx in top_indices:
            results.append({
                'chunk': self.chunks[idx],
                'score': float(similarities[idx])
            })
        return results

    def get_embedding_stats(self) -> Dict:
        if self.embeddings is None:
            return {"status": "No embeddings loaded"}
        stats = {
            'model_name': self.model_name,
            'num_embeddings': len(self.embeddings),
            'embedding_dim': self.embeddings.shape[1],
            'mean_norm': float(np.mean(np.linalg.norm(self.embeddings, axis=1))),
            'std_norm': float(np.std(np.linalg.norm(self.embeddings, axis=1))),
            'memory_size_mb': self.embeddings.nbytes / (1024 * 1024)
        }
        return stats

# ---- Main 실행 예시 ----

def main():
    from .json_loader import MusicTheoryDataLoader
    print("🎵 음악 이론 임베딩 생성 시작")

    print("\n1️⃣ 데이터 로딩...")
    loader = MusicTheoryDataLoader()
    loader.load_data()
    chunks = loader.extract_text_chunks()  # 최신 JSON에서 dict 리스트로 추출

    print("\n2️⃣ 임베딩 생성...")
    embedder = EmbeddingGenerator()
    embeddings = embedder.generate_embeddings(chunks)

    print("\n3️⃣ 임베딩 통계:")
    stats = embedder.get_embedding_stats()
    for key, value in stats.items():
        print(f"  - {key}: {value}")

    print("\n4️⃣ 임베딩 저장...")
    embedder.save_embeddings()

    print("\n5️⃣ 테스트 검색...")
    test_query = "세컨더리 도미넌트"
    results = embedder.search_similar(test_query, top_k=3)
    print(f"\n쿼리: '{test_query}'")
    print("유사한 청크:")
    for i, result in enumerate(results, 1):
        chunk = result['chunk']
        concept = chunk.get('concept.ko') or chunk.get('concept.en') or '[No concept]'
        definition = chunk.get('definition', '')[:100]
        print(f"\n{i}. 유사도: {result['score']:.3f}")
        print(f"   용어: {concept}")
        print(f"   정의: {definition}...")
    if results:
        print("\n[1번 chunk 전체 구조 디버깅]")
        import pprint
        pprint.pprint(results[0]['chunk'])

if __name__ == "__main__":
    main()
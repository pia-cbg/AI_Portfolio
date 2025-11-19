import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import pickle
import os
import torch
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.data_processing.json_loader import MusicTheoryDataLoader

class EmbeddingGenerator:
    def __init__(
        self, 
        model_name: str = None, 
        embedding_path: str = 'data/embeddings/music_theory_embeddings.pkl'
    ):
        """
        임베딩 생성기 초기화
        
        :param model_name: 사용할 sentence-transformer 모델
        :param embedding_path: 임베딩 저장 경로
        """
        # 최고 성능 다국어 모델 선택
        if model_name is None:
            model_name = "intfloat/multilingual-e5-large"
        
        print(f"🎵 임베딩 모델 로딩: {model_name}")
        
        # GPU 사용 가능 여부 확인
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"🖥️ 사용 디바이스: {self.device}")
        
        # 모델 로드
        self.model = SentenceTransformer(model_name, device=self.device)
        self.model_name = model_name
        
        # 임베딩 경로
        self.embedding_path = embedding_path
        
        # 임베딩 및 청크 초기화
        self.embeddings = None
        self.chunks = None
    
    def generate_embeddings(self, text_chunks: List[Dict]) -> np.ndarray:
        """
        텍스트 청크들에 대한 임베딩 생성
        
        :param text_chunks: 텍스트 청크 리스트
        :return: 임베딩 배열
        """
        # 텍스트 추출 및 전처리
        texts = []
        for chunk in text_chunks:
            # 제목과 내용을 결합하여 더 풍부한 임베딩 생성
            title = chunk.get('title', '')
            content = chunk.get('content', '')
            context = chunk.get('context', '')
            
            # 결합된 텍스트 생성
            combined_text = f"{title}. {context}. {content}"
            texts.append(combined_text)
        
        print(f"🎵 {len(texts)}개의 텍스트에 대한 임베딩 생성 중...")
        
        # 배치 처리로 임베딩 생성
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        
        # 임베딩 정보 저장
        self.embeddings = embeddings
        self.chunks = text_chunks
        
        print(f"✅ 임베딩 생성 완료: shape {embeddings.shape}")
        return embeddings
    
    def save_embeddings(self):
        """임베딩 및 청크 저장"""
        # 디렉토리 생성
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
        """
        저장된 임베딩 로드
        
        :return: 임베딩 로드 성공 여부
        """
        try:
            with open(self.embedding_path, 'rb') as f:
                embedding_data = pickle.load(f)
            
            # 임베딩을 NumPy 배열로 변환
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
        """
        현재 임베딩과 청크 반환
        
        :return: (임베딩 배열, 청크 리스트)
        """
        if self.embeddings is None or self.chunks is None:
            raise ValueError("임베딩이 생성되거나 로드되지 않았습니다.")
        
        return self.embeddings, self.chunks

    def update_embeddings(self, new_chunks: List[Dict]):
        """
        새로운 청크에 대한 임베딩 추가
        
        :param new_chunks: 새로운 텍스트 청크
        """
        if self.embeddings is None:
            print("기존 임베딩이 없습니다. 새로 생성합니다.")
            return self.generate_embeddings(new_chunks)
        
        # 새로운 텍스트 준비
        new_texts = []
        for chunk in new_chunks:
            title = chunk.get('title', '')
            content = chunk.get('content', '')
            context = chunk.get('context', '')
            combined_text = f"{title}. {context}. {content}"
            new_texts.append(combined_text)
        
        # 새로운 임베딩 생성
        new_embeddings = self.model.encode(
            new_texts,
            batch_size=32,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        
        # 기존 임베딩과 병합
        combined_embeddings = np.vstack([self.embeddings, new_embeddings])
        combined_chunks = self.chunks + new_chunks
        
        # 업데이트
        self.embeddings = combined_embeddings
        self.chunks = combined_chunks
        
        print(f"✅ 임베딩 업데이트 완료: {len(new_chunks)}개 추가")
        return combined_embeddings

    def search_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        쿼리와 유사한 청크 검색
        
        :param query: 검색 쿼리
        :param top_k: 반환할 상위 결과 수
        :return: 유사한 청크 리스트
        """
        if self.embeddings is None:
            print("❌ 임베딩이 로드되지 않았습니다.")
            return []
        
        # 쿼리 임베딩 생성
        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        
        # 코사인 유사도 계산
        similarities = np.dot(self.embeddings, query_embedding)
        
        # 상위 k개 인덱스
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # 결과 생성
        results = []
        
        for idx in top_indices:
            results.append({
                'chunk': self.chunks[idx],
                'score': float(similarities[idx])
            })
        
        return results

    def get_embedding_stats(self) -> Dict:
        """임베딩 통계 정보"""
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

def main():
    # 사용 예시
    from src.data_processing.json_loader import MusicTheoryDataLoader
    
    print("🎵 음악 이론 임베딩 생성 시작")
    
    # 1. 데이터 로드
    print("\n1️⃣ 데이터 로딩...")
    loader = MusicTheoryDataLoader()
    loader.load_data()
    chunks = loader.extract_text_chunks()
    
    # 2. 임베딩 생성
    print("\n2️⃣ 임베딩 생성...")
    embedder = EmbeddingGenerator()
    embeddings = embedder.generate_embeddings(chunks)
    
    # 3. 통계 출력
    print("\n3️⃣ 임베딩 통계:")
    stats = embedder.get_embedding_stats()
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    # 4. 저장
    print("\n4️⃣ 임베딩 저장...")
    embedder.save_embeddings()
    
    # 5. 테스트 검색
    print("\n5️⃣ 테스트 검색...")
    test_query = "세컨더리 도미넌트"
    results = embedder.search_similar(test_query, top_k=3)
    
    print(f"\n쿼리: '{test_query}'")
    print("유사한 청크:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. 유사도: {result['score']:.3f}")
        print(f"   제목: {result['chunk']['title']}")
        print(f"   내용: {result['chunk']['content'][:100]}...")

if __name__ == "__main__":
    main()
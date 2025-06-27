from sentence_transformers import SentenceTransformer
import numpy as np
import pickle
import os
from typing import List, Dict

class EmbeddingGenerator:
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """다국어 지원 임베딩 모델 초기화"""
        self.model = SentenceTransformer(model_name)
        self.embeddings = None
        self.chunks = None
    
    def generate_embeddings(self, chunks: List[Dict[str, str]]) -> np.ndarray:
        """텍스트 청크들에 대한 임베딩을 생성합니다."""
        texts = [chunk["content"] for chunk in chunks]
        
        print(f"임베딩 생성 중... ({len(texts)}개 청크)")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        self.embeddings = embeddings
        self.chunks = chunks
        
        return embeddings
    
    def save_embeddings(self, save_path: str = "data/processed/embeddings"):
        """임베딩과 청크를 저장합니다."""
        os.makedirs(save_path, exist_ok=True)
        
        # 임베딩 저장
        embedding_file = os.path.join(save_path, "embeddings.npy")
        np.save(embedding_file, self.embeddings)
        
        # 청크 저장
        chunks_file = os.path.join(save_path, "chunks.pkl")
        with open(chunks_file, 'wb') as f:
            pickle.dump(self.chunks, f)
        
        print(f"임베딩 저장 완료: {save_path}")
    
    def load_embeddings(self, load_path: str = "data/processed/embeddings"):
        """저장된 임베딩과 청크를 로드합니다."""
        embedding_file = os.path.join(load_path, "embeddings.npy")
        chunks_file = os.path.join(load_path, "chunks.pkl")
        
        if os.path.exists(embedding_file) and os.path.exists(chunks_file):
            self.embeddings = np.load(embedding_file)
            with open(chunks_file, 'rb') as f:
                self.chunks = pickle.load(f)
            print(f"임베딩 로드 완료: {load_path}")
            return True
        else:
            print(f"임베딩 파일이 없습니다: {load_path}")
            return False

if __name__ == "__main__":
    from json_loader import MusicTheoryDataLoader
    
    # 데이터 로드
    loader = MusicTheoryDataLoader()
    data = loader.load_data()
    chunks = loader.extract_text_chunks()
    
    # 임베딩 생성
    embedder = EmbeddingGenerator()
    embeddings = embedder.generate_embeddings(chunks)
    embedder.save_embeddings()
    
    print(f"임베딩 형태: {embeddings.shape}")
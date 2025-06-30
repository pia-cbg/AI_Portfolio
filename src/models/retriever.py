import numpy as np
import faiss
from typing import List, Dict, Tuple
import pickle
import os
from sentence_transformers import SentenceTransformer

class VectorRetriever:
    def __init__(
        self, 
        embedding_path: str = 'data/embeddings/music_theory_embeddings.pkl',
        metadata_file: str = 'data/embeddings/embeddings_metadata.json',
        index_path: str = 'data/embeddings/faiss_index.idx'
    ):
        """벡터 기반 검색기 초기화"""
        print(f"   🔧 VectorRetriever 초기화 시작")
        print(f"   - embedding_path: {embedding_path}")
        print(f"   - index_path: {index_path}")
        
        # 경로 설정
        self.embedding_path = embedding_path
        self.index_path = index_path
        
        # 속성 초기화
        self.embeddings = None
        self.chunks = None
        self.index = None
        self.model = None
        self.model_name = None
        
        print(f"   ✅ VectorRetriever 초기화 완료")
        # print(f"   - self: {self}")
    
    def load_embeddings(self):
        """저장된 임베딩 로드"""
        try:
            # 임베딩 파일 존재 확인
            if not os.path.exists(self.embedding_path):
                print(f"❌ 임베딩 파일을 찾을 수 없습니다: {self.embedding_path}")
                return False
            
            # 임베딩 로드
            with open(self.embedding_path, 'rb') as f:
                embedding_data = pickle.load(f)
            
            # 속성 설정
            self.embeddings = np.array(embedding_data['embeddings'])
            self.chunks = embedding_data['chunks']
            self.model_name = embedding_data.get('model_name', 'unknown')
            
            # 모델 로드 (검색 시 쿼리 임베딩 생성용)
            self.model = SentenceTransformer(self.model_name)
            
            print(f"✅ 임베딩 로드 완료: {len(self.chunks)}개 청크, 모델: {self.model_name}")
            return True
        
        except Exception as e:
            print(f"❌ 임베딩 로드 중 오류: {e}")
            return False
    
    def build_index(self, embeddings=None, chunks=None):
        """
        FAISS 인덱스 구축
        
        :param embeddings: 선택적 임베딩 배열
        :param chunks: 선택적 청크 데이터
        """
        print("🔧 build_index 호출됨")
        
        # 인자로 전달된 임베딩/청크 사용
        if embeddings is not None:
            print(f"   - 새 임베딩 전달됨: {type(embeddings)}")
            self.embeddings = embeddings
        if chunks is not None:
            print(f"   - 새 청크 전달됨: {len(chunks)}개")
            self.chunks = chunks
        
        # 임베딩 확인
        if self.embeddings is None:
            print("   ⚠️ 임베딩이 없습니다. 로드 시도...")
            if not self.load_embeddings():
                raise ValueError("임베딩을 로드할 수 없습니다.")
        
        # 임베딩 차원
        print(f"   - 임베딩 차원: {self.embeddings.shape}")
        dimension = self.embeddings.shape[1]
        
        # FAISS 인덱스 생성 (내적 기반)
        self.index = faiss.IndexFlatIP(dimension)
        
        # 임베딩을 float32로 변환 (FAISS 요구사항)
        embeddings_float32 = self.embeddings.astype('float32')
        
        # 인덱스에 임베딩 추가
        self.index.add(embeddings_float32)
        
        print(f"✅ FAISS 인덱스 구축 완료: {self.index.ntotal}개 벡터")
        return self.index
    
    def search(
        self, 
        query: str, 
        top_k: int = 5, 
        min_score: float = 0.0
    ) -> List[Dict]:
        """
        쿼리에 대한 유사 문서 검색
        
        :param query: 검색 쿼리
        :param top_k: 반환할 상위 결과 수
        :param min_score: 최소 유사도 점수
        :return: 검색 결과 리스트
        """
        print(f"   🔍 search 메서드 호출됨")
        print(f"   - self: {self}")
        print(f"   - self.index: {self.index}")
        print(f"   - self.model: {self.model}")
        
        # 인덱스와 모델 확인
        if self.index is None:
            print("   ⚠️ 인덱스가 없습니다. load_embeddings 시도...")
            if not self.load_embeddings():
                print("   ❌ 임베딩 로드 실패")
                return []
            
            # 인덱스 빌드
            if not self.build_index():
                print("   ❌ 인덱스 빌드 실패")
                return []
        
        if self.model is None:
            print(f"   ⚠️ 모델이 없습니다. 모델 로드 시도...")
            if self.model_name:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
            else:
                print("   ❌ 모델 이름을 알 수 없습니다.")
                return []
        
        try:
            # 쿼리 임베딩 생성
            print(f"   - 쿼리 임베딩 생성 중...")
            query_embedding = self.model.encode(
                query,
                normalize_embeddings=True,
                convert_to_numpy=True
            )
            
            # FAISS 검색
            query_vector = query_embedding.astype('float32').reshape(1, -1)
            scores, indices = self.index.search(query_vector, top_k)
            
            # 결과 생성
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if score >= min_score:
                    chunk = self.chunks[idx]
                    results.append({
                        'chunk_id': chunk.get('id', str(idx)),
                        'title': chunk.get('title', ''),
                        'content': chunk.get('content', ''),
                        'context': chunk.get('context', ''),
                        'metadata': chunk.get('metadata', {}),
                        'score': float(score),
                        'rank': i + 1
                    })
            
            print(f"   ✅ 검색 완료: {len(results)}개 결과")
            return results
            
        except Exception as e:
            print(f"   ❌ 검색 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def update_index(self, new_embeddings_path: str = None):
        """
        새로운 임베딩으로 인덱스 업데이트
        
        :param new_embeddings_path: 새로운 임베딩 파일 경로
        """
        if new_embeddings_path:
            self.embedding_path = new_embeddings_path
        
        # 임베딩 재로드
        self.load_embeddings()
        
        # 인덱스 재구축
        self.build_index()
        
        print("✅ 인덱스 업데이트 완료")
    
    def get_statistics(self) -> Dict:
        """검색기 통계 정보"""
        stats = {
            'total_chunks': len(self.chunks) if self.chunks else 0,
            'embedding_dimension': self.embeddings.shape[1] if self.embeddings is not None else 0,
            'model_name': self.model_name,
            'index_total': self.index.ntotal if self.index else 0,
            'embedding_file': self.embedding_path
        }
        
        if self.chunks:
            # 청크 길이 통계
            content_lengths = [len(chunk.get('content', '')) for chunk in self.chunks]
            stats.update({
                'avg_content_length': np.mean(content_lengths),
                'min_content_length': min(content_lengths),
                'max_content_length': max(content_lengths)
            })
        
        return stats
    
    def save_index(self, index_path: str = None):
        """
        FAISS 인덱스 저장
        
        :param index_path: 저장할 인덱스 경로 (기본값: 클래스 초기화 시 설정된 경로)
        """
        if index_path is None:
            index_path = self.index_path
        
        if self.index is None:
            print("❌ 저장할 인덱스가 없습니다.")
            return
        
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        faiss.write_index(self.index, index_path)
        print(f"✅ FAISS 인덱스 저장 완료: {index_path}")
    
    def load_index(self, index_path: str = None):
        """
        저장된 FAISS 인덱스 로드
        
        :param index_path: 로드할 인덱스 경로 (기본값: 클래스 초기화 시 설정된 경로)
        """
        if index_path is None:
            index_path = self.index_path
        
        if not os.path.exists(index_path):
            print(f"❌ 인덱스 파일을 찾을 수 없습니다: {index_path}")
            return False
        
        try:
            self.index = faiss.read_index(index_path)
            print(f"✅ FAISS 인덱스 로드 완료: {index_path}")
            return True
        except Exception as e:
            print(f"❌ 인덱스 로드 중 오류: {e}")
            return False

def main():
    """검색기 테스트"""
    print("🎵 음악 이론 검색기 테스트")
    
    try:
        # 검색기 초기화
        retriever = VectorRetriever()
        
        # 통계 출력
        stats = retriever.get_statistics()
        print("\n📊 검색기 통계:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")
        
        # 테스트 검색
        test_queries = [
            "세컨더리 도미넌트",
            "화성 진행",
            "메이저 스케일",
            "코드 진행"
        ]
        
        print("\n🔍 테스트 검색:")
        for query in test_queries:
            print(f"\n쿼리: '{query}'")
            results = retriever.search(query, top_k=3)
            
            for i, result in enumerate(results, 1):
                print(f"  {i}. 점수: {result['score']:.3f}")
                print(f"     제목: {result['title']}")
                print(f"     내용: {result['content'][:80]}...")
        
        # 인덱스 저장
        retriever.save_index()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()
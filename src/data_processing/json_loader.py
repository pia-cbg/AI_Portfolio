import json
import os
from typing import Dict, List, Any
import hashlib

class MusicTheoryDataLoader:
    def __init__(self, json_path: str = 'data/raw/music_theory_curriculum.json'):
        """
        음악 이론 JSON 데이터 로더
        
        :param json_path: JSON 파일 경로
        """
        self.json_path = json_path
        self.data = None
        self.chunks = []
    
    def load_data(self) -> Dict:
        """JSON 파일 로드"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✅ 데이터 로드 완료: {self.json_path}")
            return self.data
        except FileNotFoundError:
            print(f"❌ 파일을 찾을 수 없습니다: {self.json_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 오류: {e}")
            return {}
    
    def extract_text_chunks(self, min_length: int = 50) -> List[Dict]:
        if self.data is None:
            self.load_data()
        
        self.chunks = []
        
        def extract_chunks_recursive(obj, path="", parent_context=""):
            """재귀적으로 텍스트 청크 추출"""
            if isinstance(obj, dict):
                # 특정 키워드가 있는 섹션만 처리
                for key, value in obj.items():
                    # 메타데이터와 상수 제외
                    if key not in ['metadata', 'constants']:
                        current_path = f"{path}.{key}" if path else key
                        current_context = f"{parent_context} > {key}".strip(" >")
                        
                        # 텍스트 내용 추출
                        content = ""
                        if isinstance(value, dict):
                            # 딕셔너리라면 JSON으로 변환해서 텍스트로
                            content = json.dumps(value, ensure_ascii=False)
                        elif isinstance(value, (str, int, float, bool)):
                            # 기본 타입이면 문자열로 변환
                            content = str(value)
                        
                        # 청크 생성 (content 보장)
                        chunk = {
                            'id': self._generate_chunk_id(current_path),
                            'title': key.replace('_', ' ').title(),
                            'content': content,
                            'path': current_path,
                            'context': current_context
                        }
                        
                        # 최소 길이 체크
                        if len(content) >= min_length:
                            self.chunks.append(chunk)
                        
                        # 재귀적 탐색
                        if isinstance(value, dict):
                            extract_chunks_recursive(value, current_path, current_context)
                            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = f"{path}[{i}]"
                    extract_chunks_recursive(item, new_path, parent_context)
        
        # 최상위 레벨부터 재귀 시작
        extract_chunks_recursive(self.data)
        
        print(f"✅ {len(self.chunks)}개의 텍스트 청크 추출 완료")
        return self.chunks
    
    def _extract_chunks_recursive(self, obj: Any, path: str = "", parent_context: str = ""):
        """재귀적으로 청크 추출"""
        if isinstance(obj, dict):
            # 현재 레벨의 컨텍스트 구성
            current_context = self._build_context(obj, parent_context)
            
            # 의미있는 텍스트 필드 확인
            content_fields = ['description', 'explanation', 'definition', 'content', 'detailed_explanation']
            
            for field in content_fields:
                if field in obj and isinstance(obj[field], str) and obj[field].strip():
                    chunk = {
                        'id': self._generate_chunk_id(path + f".{field}"),
                        'content': obj[field],
                        'title': obj.get('title', obj.get('name', path.split('.')[-1])),
                        'path': path,
                        'context': current_context,
                        'metadata': self._extract_metadata(obj)
                    }
                    self.chunks.append(chunk)
            
            # 재귀적 탐색
            for key, value in obj.items():
                if key not in content_fields:
                    new_path = f"{path}.{key}" if path else key
                    self._extract_chunks_recursive(value, new_path, current_context)
                    
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                new_path = f"{path}[{idx}]"
                self._extract_chunks_recursive(item, new_path, parent_context)
    
    def _build_context(self, obj: Dict, parent_context: str) -> str:
        """현재 객체의 컨텍스트 구성"""
        context_parts = []
        
        if parent_context:
            context_parts.append(parent_context)
        
        # 제목이나 이름 추가
        if 'title' in obj:
            context_parts.append(f"주제: {obj['title']}")
        elif 'name' in obj:
            context_parts.append(f"개념: {obj['name']}")
        
        # 카테고리나 타입 정보
        if 'category' in obj:
            context_parts.append(f"카테고리: {obj['category']}")
        if 'type' in obj:
            context_parts.append(f"유형: {obj['type']}")
        
        return " > ".join(context_parts)
    
    def _extract_metadata(self, obj: Dict) -> Dict:
        """메타데이터 추출"""
        metadata = {}
        
        # 중요한 메타데이터 필드들
        metadata_fields = [
            'level', 'difficulty', 'category', 'type', 
            'prerequisites', 'related_concepts', 'examples'
        ]
        
        for field in metadata_fields:
            if field in obj:
                metadata[field] = obj[field]
        
        return metadata
    
    def _generate_chunk_id(self, path: str) -> str:
        """경로 기반 고유 ID 생성"""
        return hashlib.md5(path.encode()).hexdigest()[:8]
    
    def get_chunk_by_id(self, chunk_id: str) -> Dict:
        """ID로 청크 검색"""
        for chunk in self.chunks:
            if chunk['id'] == chunk_id:
                return chunk
        return None
    
    def search_chunks(self, keyword: str) -> List[Dict]:
        """키워드로 청크 검색"""
        keyword_lower = keyword.lower()
        matching_chunks = []
        
        for chunk in self.chunks:
            if (keyword_lower in chunk.get('content', '').lower() or
                keyword_lower in chunk.get('title', '').lower() or
                keyword_lower in chunk.get('context', '').lower()):
                matching_chunks.append(chunk)
        
        return matching_chunks
    
    def get_statistics(self) -> Dict:
        """데이터 통계"""
        if not self.chunks:
            self.extract_text_chunks()
        
        stats = {
            'total_chunks': len(self.chunks),
            'avg_chunk_length': sum(len(c['content']) for c in self.chunks) / len(self.chunks) if self.chunks else 0,
            'unique_titles': len(set(c.get('title', '') for c in self.chunks)),
            'paths': len(set(c['path'] for c in self.chunks))
        }
        
        return stats
    
    def save_chunks(self, output_path: str = 'data/processed/chunks.json'):
        """청크를 파일로 저장"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 청크 저장 완료: {output_path}")

def main():
    # 데이터 로더 테스트
    loader = MusicTheoryDataLoader()
    
    # 데이터 로드
    data = loader.load_data()
    
    # 청크 추출
    chunks = loader.extract_text_chunks()
    
    # 통계 출력
    stats = loader.get_statistics()
    print("\n📊 데이터 통계:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    # 샘플 청크 출력
    if chunks:
        print("\n📝 샘플 청크:")
        sample = chunks[0]
        print(f"  - ID: {sample['id']}")
        print(f"  - Title: {sample['title']}")
        print(f"  - Content: {sample['content'][:100]}...")
    
    # 청크 저장
    loader.save_chunks()

if __name__ == "__main__":
    main()
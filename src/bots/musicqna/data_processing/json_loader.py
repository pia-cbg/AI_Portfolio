import json
import os
from typing import Dict, List, Optional

class MusicTheoryDataLoader:
    def __init__(self, json_path: str = 'data/musicqna/processed/music_theory_curriculum.json'):
        """
        음악 이론 JSON 데이터 로더 (최신 포맷 대응)
        :param json_path: JSON 파일 경로
        """
        self.json_path = json_path
        self.data: Optional[List[Dict]] = None
        self.chunks: List[Dict] = []

    def load_data(self) -> List[Dict]:
        """JSON 파일 로드"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✅ 데이터 로드 완료: {self.json_path} ({len(self.data)}개 개념)")
            return self.data
        except FileNotFoundError:
            print(f"❌ 파일을 찾을 수 없습니다: {self.json_path}")
            self.data = []
            return []
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 오류: {e}")
            self.data = []
            return []

    def extract_text_chunks(self) -> List[Dict]:
        """
        최신 구조: 한 원소(dict)가 한 청크(개념)임. (불필요한 재귀, title/content 없음)
        :return: List[dict] (field는 concept.ko, definition, logic 등 유지)
        """
        if self.data is None:
            self.load_data()
        self.chunks = self.data
        print(f"✅ {len(self.chunks)}개의 청크 로드 완료")
        return self.chunks

    def get_chunk_by_id(self, node_id: int) -> Optional[Dict]:
        """node_id로 청크(개념) 검색"""
        for chunk in self.chunks:
            if chunk.get('node_id') == node_id:
                return chunk
        return None

    def search_chunks(self, keyword: str) -> List[Dict]:
        """키워드로 청크(개념) 검색: 한국어/영어/정의/로직 등 포함 여부"""
        if not self.chunks:
            self.extract_text_chunks()

        keyword_lower = keyword.lower()
        results = []
        for chunk in self.chunks:
            joined = ' '.join([
                str(chunk.get('concept.ko', '')),
                str(chunk.get('concept.en', '')),
                str(chunk.get('aliases', '')),
                str(chunk.get('definition', '')),
                str(chunk.get('logic', '')),
                str(chunk.get('examples.name', '')),
                str(chunk.get('examples.description', '')),
                str(chunk.get('tips', '')),
                str(chunk.get('prerequisites.ko', '')),
                str(chunk.get('prerequisites.en', ''))
            ]).lower()
            if keyword_lower in joined:
                results.append(chunk)
        return results

    def get_statistics(self) -> Dict:
        """데이터 통계"""
        if not self.chunks:
            self.extract_text_chunks()
        stats = {
            'total_chunks': len(self.chunks),
            'avg_definition_length': (
                sum(len(str(c.get('definition', ''))) for c in self.chunks) / len(self.chunks)
                if self.chunks else 0
            ),
            'unique_concepts_ko': len(set(c.get('concept.ko', '') for c in self.chunks)),
            'unique_concepts_en': len(set(c.get('concept.en', '') for c in self.chunks))
        }
        return stats

    def save_chunks(self, output_path: str = 'data/processed/chunks.json'):
        """청크를 파일로 저장"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        print(f"✅ 청크 저장 완료: {output_path}")

def main():
    loader = MusicTheoryDataLoader()
    data = loader.load_data()
    chunks = loader.extract_text_chunks()
    stats = loader.get_statistics()
    print("\n📊 데이터 통계:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    if chunks:
        print("\n📝 샘플 청크:")
        sample = chunks[0]
        print(json.dumps(sample, ensure_ascii=False, indent=2))
    loader.save_chunks()

if __name__ == "__main__":
    main()
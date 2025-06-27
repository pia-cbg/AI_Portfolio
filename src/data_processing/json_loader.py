import json
import os
from typing import Dict, List, Any

class MusicTheoryDataLoader:
    def __init__(self, data_path: str = "data/raw/music_theory_curriculum.json"):
        self.data_path = data_path
        self.data = None
    
    def load_data(self) -> Dict[str, Any]:
        """JSON 데이터를 로드합니다."""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as file:
                self.data = json.load(file)
            print(f"데이터 로드 완료: {self.data_path}")
            return self.data
        except FileNotFoundError:
            print(f"파일을 찾을 수 없습니다: {self.data_path}")
            return {}
        except json.JSONDecodeError:
            print(f"JSON 파싱 오류: {self.data_path}")
            return {}
    
    def extract_text_chunks(self, data: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """JSON 데이터에서 텍스트 청크를 추출합니다."""
        if data is None:
            data = self.data
        
        chunks = []
        
        def extract_recursive(obj, path="", parent_title=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # title이 있는 경우 제목으로 사용
                    if key == "title" and isinstance(value, str):
                        parent_title = value
                    
                    # description이 있는 경우 청크로 추가
                    elif key == "description" and isinstance(value, str) and len(value) > 10:
                        chunks.append({
                            "content": value,
                            "metadata": {
                                "path": current_path,
                                "title": parent_title,
                                "type": "description"
                            }
                        })
                    
                    # 다른 텍스트 필드들도 청크로 추가
                    elif isinstance(value, str) and len(value) > 50:
                        chunks.append({
                            "content": value,
                            "metadata": {
                                "path": current_path,
                                "title": parent_title,
                                "type": key
                            }
                        })
                    
                    # 재귀적으로 처리
                    elif isinstance(value, (dict, list)):
                        extract_recursive(value, current_path, parent_title)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_recursive(item, f"{path}[{i}]", parent_title)
        
        extract_recursive(data)
        return chunks

if __name__ == "__main__":
    loader = MusicTheoryDataLoader()
    data = loader.load_data()
    chunks = loader.extract_text_chunks()
    print(f"추출된 청크 수: {len(chunks)}")
    print(f"첫 번째 청크: {chunks[0] if chunks else 'None'}")
"""
데이터셋 검증 도구
"""
import json
from typing import Dict, List

class DatasetValidator:
    def __init__(self, data_path: str = 'data/raw/music_theory_curriculum.json'):
        """데이터셋 검증기 초기화"""
        self.data_path = data_path
        
    def validate_structure(self) -> Dict:
        """데이터 구조 검증"""
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        issues = []
        stats = {
            'total_entries': 0,
            'empty_fields': 0,
            'missing_definitions': 0,
            'short_content': 0
        }
        
        def check_entry(entry, path=""):
            if isinstance(entry, dict):
                stats['total_entries'] += 1
                
                # 필수 필드 체크
                if 'title' in entry and not entry.get('definition'):
                    issues.append(f"{path}: 정의 누락")
                    stats['missing_definitions'] += 1
                
                # 빈 필드 체크
                for key, value in entry.items():
                    if isinstance(value, str) and not value.strip():
                        issues.append(f"{path}.{key}: 빈 필드")
                        stats['empty_fields'] += 1
                    
                    # 너무 짧은 콘텐츠
                    if isinstance(value, str) and 0 < len(value) < 20:
                        issues.append(f"{path}.{key}: 콘텐츠 너무 짧음")
                        stats['short_content'] += 1
                
                # 재귀 탐색
                for key, value in entry.items():
                    check_entry(value, f"{path}.{key}")
                    
            elif isinstance(entry, list):
                for idx, item in enumerate(entry):
                    check_entry(item, f"{path}[{idx}]")
        
        check_entry(data)
        
        return {
            'valid': len(issues) == 0,
            'statistics': stats,
            'issues': issues[:20]  # 상위 20개만
        }

def main():
    validator = DatasetValidator()
    result = validator.validate_structure()
    
    print("📋 데이터셋 검증 결과:")
    print(f"  - 유효성: {'✅ 통과' if result['valid'] else '❌ 문제 발견'}")
    print(f"  - 총 항목: {result['statistics']['total_entries']}")
    print(f"  - 문제 발견: {len(result['issues'])}개")
    
    if result['issues']:
        print("\n주요 문제:")
        for issue in result['issues'][:5]:
            print(f"  - {issue}")

if __name__ == "__main__":
    main()
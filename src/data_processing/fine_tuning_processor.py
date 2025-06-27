import json
import os
from datetime import datetime

class FineTuningProcessor:
    def __init__(self, base_path='data/fine_tuning'):
        self.evaluations_path = os.path.join(base_path, 'evaluations')
        self.corrections_path = os.path.join(base_path, 'corrections')
        
        # 디렉토리 생성
        os.makedirs(self.evaluations_path, exist_ok=True)
        os.makedirs(self.corrections_path, exist_ok=True)
    
    def save_evaluation(self, evaluation_data):
        """평가 데이터 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluation_{timestamp}.json"
        filepath = os.path.join(self.evaluations_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(evaluation_data, f, ensure_ascii=False, indent=4)
    
    def save_correction(self, correction_data):
        """수정 데이터 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"correction_{timestamp}.json"
        filepath = os.path.join(self.corrections_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(correction_data, f, ensure_ascii=False, indent=4)
    
    def update_knowledge_base(self, correction_data):
        """
        실제 JSON 기반 지식베이스 업데이트
        1. 원본 JSON 파일 로드
        2. 수정 내용 적용
        3. 새로운 버전으로 저장
        """
        # 원본 지식베이스 로드
        with open('data/raw/music_theory_curriculum.json', 'r', encoding='utf-8') as f:
            knowledge_base = json.load(f)
        
        # 수정 로직 구현 (correction_data 기반)
        # 예: 특정 섹션 업데이트, 새로운 정보 추가 등
        
        # 수정된 지식베이스 저장
        with open('data/raw/music_theory_curriculum.json', 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, ensure_ascii=False, indent=4)
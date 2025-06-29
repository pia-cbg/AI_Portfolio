import json
import os
import re
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class ModelUpdater:
    def __init__(self, 
                 raw_data_path: str = 'data/raw/music_theory_curriculum.json',
                 base_path: str = 'data/fine_tuning'):
        """
        모델 업데이트 시스템 초기화
        
        :param raw_data_path: 원본 JSON 데이터 경로
        :param base_path: 파인튜닝 데이터 경로
        """
        self.raw_data_path = raw_data_path
        self.base_path = base_path
        self.corrections_path = os.path.join(base_path, 'phase2_model_training', 'corrections')
        
        # 원본 데이터 로드
        self.raw_data = self._load_raw_data()
        
        # 업데이트 이력
        self.update_history = []
    
    def _load_raw_data(self) -> Dict:
        """원본 JSON 데이터 로드"""
        try:
            with open(self.raw_data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"원본 데이터 로드 오류: {e}")
            return {}
    
    def _save_raw_data(self):
        """수정된 데이터 저장"""
        # 백업 생성
        self._create_backup()
        
        # 저장
        try:
            with open(self.raw_data_path, 'w', encoding='utf-8') as f:
                json.dump(self.raw_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 원본 데이터 업데이트 완료: {self.raw_data_path}")
        except Exception as e:
            print(f"❌ 데이터 저장 오류: {e}")
    
    def _create_backup(self):
        """원본 데이터 백업 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = "data/raw/backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_path = os.path.join(backup_dir, f"music_theory_curriculum_{timestamp}.json")
        shutil.copy2(self.raw_data_path, backup_path)
        print(f"📁 원본 데이터 백업 생성: {backup_path}")
    
    def process_corrections(self, evaluations: List[Dict]):
        """
        평가 결과에서 수정사항을 처리
        
        :param evaluations: 평가 데이터 리스트
        """
        corrections_made = 0
        
        for evaluation in evaluations:
            if evaluation.get('correction') and evaluation.get('avg_score', 0) < 7:
                try:
                    success = self._apply_correction(evaluation)
                    if success:
                        corrections_made += 1
                except Exception as e:
                    print(f"수정 적용 중 오류: {e}")
        
        if corrections_made > 0:
            # 데이터 저장
            self._save_raw_data()
            
            # 임베딩 재생성
            self._regenerate_embeddings()
            
            print(f"✅ {corrections_made}개의 수정사항이 적용되었습니다.")
        else:
            print("적용할 수정사항이 없습니다.")
    
    def _apply_correction(self, evaluation: Dict) -> bool:
        """단일 수정사항 적용"""
        question = evaluation.get('question', '')
        original_answer = evaluation.get('answer', '')
        corrected_answer = evaluation.get('correction', '')
        
        if not corrected_answer:
            return False
        
        # 관련 섹션 찾기
        target_section, section_path = self._find_related_section(question, original_answer)
        
        if target_section:
            # 업데이트 적용
            update_success = self._update_section(target_section, corrected_answer, question)
            
            if update_success:
                # 업데이트 이력 기록
                self.update_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'question': question,
                    'section_path': section_path,
                    'original_answer': original_answer[:100] + "...",
                    'corrected_answer': corrected_answer[:100] + "...",
                    'scores': evaluation.get('scores', {})
                })
                return True
        
        return False
    
    def _find_related_section(self, question: str, answer: str) -> Tuple[Optional[Dict], Optional[str]]:
        """질문과 답변에 관련된 JSON 섹션 찾기"""
        # 질문에서 키워드 추출
        keywords = self._extract_keywords_from_text(question + " " + answer)
        
        # 가장 관련성 높은 섹션 찾기
        best_section = None
        best_path = None
        best_score = 0
        
        def search_recursively(obj, path=""):
            nonlocal best_section, best_path, best_score
            
            if isinstance(obj, dict):
                # 현재 섹션의 관련성 점수 계산
                score = self._calculate_relevance_score(obj, keywords)
                
                if score > best_score:
                    best_score = score
                    best_section = obj
                    best_path = path
                
                # 재귀적 탐색
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    search_recursively(value, new_path)
                    
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_path = f"{path}[{i}]"
                    search_recursively(item, new_path)
        
        search_recursively(self.raw_data)
        
        return best_section, best_path
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출"""
        # 단순한 키워드 추출
        words = re.findall(r'\b[\w가-힣]+\b', text.lower())
        
        # 길이가 2 이상인 의미있는 단어만 선택
        keywords = [word for word in words if len(word) >= 2]
        
        # 중복 제거하고 빈도순 정렬
        from collections import Counter
        word_counts = Counter(keywords)
        
        return [word for word, count in word_counts.most_common(10)]
    
    def _calculate_relevance_score(self, section: Dict, keywords: List[str]) -> float:
        """섹션과 키워드의 관련성 점수 계산"""
        if not keywords:
            return 0
        
        # 섹션의 모든 텍스트 수집
        section_text = ""
        
        def collect_text(obj):
            nonlocal section_text
            
            if isinstance(obj, str):
                section_text += " " + obj.lower()
            elif isinstance(obj, dict):
                for value in obj.values():
                    collect_text(value)
            elif isinstance(obj, list):
                for item in obj:
                    collect_text(item)
        
        collect_text(section)
        
        # 키워드 매칭 점수 계산
        matches = 0
        for keyword in keywords:
            if keyword in section_text:
                matches += 1
        
        return matches / len(keywords) if keywords else 0
    
    def _update_section(self, section: Dict, corrected_answer: str, question: str) -> bool:
        """섹션 업데이트"""
        # 업데이트할 필드 찾기
        update_fields = ['description', 'explanation', 'detailed_explanation', 'definition']
        
        for field in update_fields:
            if field in section:
                # 기존 내용이 있다면 보강
                existing_content = section[field]
                
                # 내용 유사성 확인
                similarity = self._calculate_text_similarity(existing_content, corrected_answer)
                
                if similarity > 0.3:  # 유사도가 높으면 교체
                    section[field] = corrected_answer
                    print(f"필드 '{field}' 업데이트됨")
                    return True
                elif len(corrected_answer) > len(existing_content):  # 더 상세한 내용이면 교체
                    section[field] = corrected_answer
                    print(f"필드 '{field}' 확장됨")
                    return True
        
        # 적절한 필드가 없으면 새 필드 추가
        if 'improved_explanation' not in section:
            section['improved_explanation'] = corrected_answer
            print("새 필드 'improved_explanation' 추가됨")
            return True
        
        return False
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 간의 유사도 계산"""
        words1 = set(re.findall(r'\b[\w가-힣]+\b', text1.lower()))
        words2 = set(re.findall(r'\b[\w가-힣]+\b', text2.lower()))
        
        if not words1 or not words2:
            return 0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0
    
    def _regenerate_embeddings(self):
        """임베딩 재생성"""
        try:
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            
            from src.data_processing.json_loader import MusicTheoryDataLoader
            from src.data_processing.embedding_generator import EmbeddingGenerator
            
            print("🔄 임베딩 재생성 중...")
            
            # 데이터 로드
            loader = MusicTheoryDataLoader()
            loader.load_data()
            chunks = loader.extract_text_chunks()
            
            # 임베딩 생성
            embedder = EmbeddingGenerator()
            embedder.generate_embeddings(chunks)
            embedder.save_embeddings()
            
            print("✅ 임베딩 재생성 완료")
            return True
            
        except Exception as e:
            print(f"❌ 임베딩 재생성 오류: {e}")
            return False
    
    def get_update_history(self) -> List[Dict]:
        """업데이트 이력 반환"""
        return self.update_history
    
    def save_update_log(self):
        """업데이트 로그 저장"""
        if not self.update_history:
            return
        
        log_dir = os.path.join(self.base_path, 'phase2_model_training', 'update_logs')
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"model_update_{timestamp}.json")
        
        log_data = {
            'update_time': timestamp,
            'total_updates': len(self.update_history),
            'updates': self.update_history
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 업데이트 로그 저장: {log_file}")
    
    def rollback_to_backup(self, backup_timestamp: str):
        """백업으로 롤백"""
        backup_file = f"data/raw/backups/music_theory_curriculum_{backup_timestamp}.json"
        
        if not os.path.exists(backup_file):
            print(f"❌ 백업 파일을 찾을 수 없습니다: {backup_file}")
            return False
        
        try:
            shutil.copy2(backup_file, self.raw_data_path)
            print(f"✅ {backup_timestamp} 백업으로 롤백 완료")
            
            # 임베딩 재생성
            self._regenerate_embeddings()
            
            return True
        except Exception as e:
            print(f"❌ 롤백 중 오류: {e}")
            return False

def main():
    """모델 업데이터 테스트"""
    updater = ModelUpdater()
    
    # 샘플 평가 데이터
    sample_evaluations = [
        {
            'question': '세컨더리 도미넌트란 무엇인가?',
            'answer': '간단한 답변...',
            'correction': '세컨더리 도미넌트는 조성 내에서 다른 화음으로의 일시적 전조를 만드는 도미넌트 화음입니다...',
            'avg_score': 5.5,
            'scores': {'accuracy': 6, 'completeness': 5}
        }
    ]
    
    # 수정사항 처리
    updater.process_corrections(sample_evaluations)
    updater.save_update_log()

if __name__ == "__main__":
    main()
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import shutil

class ModelUpdater:
    def __init__(self, base_path='data/fine_tuning', raw_data_path='data/raw/music_theory_curriculum.json'):
        """
        모델 업데이트 시스템 초기화
        
        :param base_path: 파인튜닝 데이터 경로
        :param raw_data_path: 원본 JSON 데이터 경로
        """
        self.base_path = base_path
        self.corrections_path = os.path.join(base_path, 'corrections')
        self.keywords_path = os.path.join(base_path, 'keywords')
        self.raw_data_path = raw_data_path
        
        # 원본 데이터 로드
        self.raw_data = self._load_raw_data()
        
        # 파인튜닝 키워드 로드
        self.fine_tuning_keywords = self._load_fine_tuning_keywords()
        
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
    
    def _load_fine_tuning_keywords(self) -> List[str]:
        """파인튜닝 키워드 로드"""
        keywords_file = os.path.join(self.keywords_path, 'extracted_keywords.json')
        try:
            with open(keywords_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"키워드 파일을 찾을 수 없습니다: {keywords_file}")
            return []
    
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
            print(f"데이터 저장 오류: {e}")
    
    def _create_backup(self):
        """원본 데이터 백업 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = "data/raw/backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_path = os.path.join(backup_dir, f"music_theory_curriculum_{timestamp}.json")
        shutil.copy2(self.raw_data_path, backup_path)
        print(f"📁 원본 데이터 백업 생성: {backup_path}")
    
    def load_corrections(self) -> List[Dict]:
        """모든 수정 데이터 로드"""
        corrections = []
        
        if not os.path.exists(self.corrections_path):
            return corrections
        
        for filename in os.listdir(self.corrections_path):
            if filename.startswith('correction_'):
                filepath = os.path.join(self.corrections_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        corrections.append(json.load(f))
                except Exception as e:
                    print(f"수정 데이터 로드 오류 ({filename}): {e}")
        
        return sorted(corrections, key=lambda x: x.get('timestamp', ''))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        파인튜닝 키워드와 입력 텍스트 매칭
        
        :param text: 입력 텍스트
        :return: 매칭된 키워드 리스트
        """
        text_lower = text.lower()
        matched_keywords = []
        
        for keyword in self.fine_tuning_keywords:
            if keyword.lower() in text_lower:
                matched_keywords.append(keyword)
        
        return sorted(matched_keywords, key=len, reverse=True)
    
    def find_update_location(self, question: str, response: str) -> Tuple[Dict, str, Optional[str]]:
        """
        원본 데이터에서 업데이트 위치 찾기
        
        :param question: 질문
        :param response: 응답
        :return: (업데이트 위치, 키워드, 섹션 이름)
        """
        # 키워드 추출
        keywords = self._extract_keywords(question)
        
        # 가장 관련성 높은 키워드 선택
        main_keyword = keywords[0] if keywords else ""
        
        # 키워드로 관련 섹션 찾기
        target_section, section_name = self._find_related_section(main_keyword)
        
        return target_section, main_keyword, section_name
    
    def _find_related_section(self, keyword: str) -> Tuple[Dict, Optional[str]]:
        """키워드와 관련된 섹션 찾기"""
        def search_recursively(obj, path=""):
            if isinstance(obj, dict):
                # 제목이나 설명에 키워드가 있는지 확인
                for k in ['title', 'description', 'name', 'definition']:
                    if k in obj and isinstance(obj[k], str) and keyword.lower() in obj[k].lower():
                        return obj, path
                
                # 재귀적으로 탐색
                for k, v in obj.items():
                    result, found_path = search_recursively(v, f"{path}.{k}" if path else k)
                    if result is not None:
                        return result, found_path
                        
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    result, found_path = search_recursively(item, f"{path}[{i}]")
                    if result is not None:
                        return result, found_path
            
            return None, None
        
        # 키워드가 비어있는 경우
        if not keyword:
            return self.raw_data, None
        
        # 키워드로 관련 섹션 찾기
        section, path = search_recursively(self.raw_data)
        
        # 관련 섹션을 찾지 못한 경우 최상위 데이터 반환
        if section is None:
            return self.raw_data, None
        
        return section, path
    
    def update_model_data(self, correction: Dict):
        """모델 데이터 업데이트"""
        question = correction.get('question', '')
        original_response = correction.get('original_response', '')
        corrected_response = correction.get('corrected_response', '')
        
        if not corrected_response:
            print("수정된 응답이 없어 업데이트하지 않습니다.")
            return
        
        # 업데이트 위치 찾기
        target_section, keyword, section_name = self.find_update_location(question, original_response)
        
        # 업데이트 작업
        update_success = False
        
        # 1. 기존 필드 업데이트
        if isinstance(target_section, dict):
            for field in ['description', 'detailed_explanation', 'explanation', 'definition']:
                if field in target_section and isinstance(target_section[field], str):
                    # 필드 내용이 원본 응답과 유사한지 확인
                    similarity = self._calculate_text_similarity(target_section[field], original_response)
                    if similarity > 0.3:  # 유사도 임계값
                        print(f"'{field}' 필드 업데이트 (유사도: {similarity:.2f})")
                        target_section[field] = corrected_response
                        update_success = True
                        break
        
        # 2. 관련 섹션에 새 필드 추가
        if not update_success and keyword and isinstance(target_section, dict):
            if 'explanation' not in target_section:
                field_name = 'explanation'
            elif 'additional_info' not in target_section:
                field_name = 'additional_info'
            else:
                field_name = f'info_about_{keyword.lower()}'
            
            print(f"새 필드 '{field_name}' 추가")
            target_section[field_name] = corrected_response
            update_success = True
        
        # 3. 최상위 레벨에 새 섹션 추가
        if not update_success:
            if 'concept_corrections' not in self.raw_data:
                self.raw_data['concept_corrections'] = {}
            
            section_key = keyword.lower() if keyword else f"topic_{len(self.raw_data['concept_corrections']) + 1}"
            
            print(f"'concept_corrections' 섹션에 '{section_key}' 추가")
            self.raw_data['concept_corrections'][section_key] = {
                'question': question,
                'correct_explanation': corrected_response,
                'keyword': keyword
            }
            update_success = True
        
        # 업데이트 이력 추가
        if update_success:
            self.update_history.append({
                'timestamp': datetime.now().isoformat(),
                'question': question,
                'section': section_name,
                'keyword': keyword
            })
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트 간의 간단한 유사도 계산"""
        words1 = set(re.findall(r'\b[\w가-힣]+\b', text1.lower()))
        words2 = set(re.findall(r'\b[\w가-힣]+\b', text2.lower()))
        
        if not words1 or not words2:
            return 0
        
        common_words = words1.intersection(words2)
        return len(common_words) / max(len(words1), len(words2))
    
    def regenerate_embeddings(self):
        """임베딩 재생성"""
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            
            from src.data_processing.json_loader import MusicTheoryDataLoader
            from src.data_processing.embedding_generator import EmbeddingGenerator
            
            # 데이터 로드
            loader = MusicTheoryDataLoader()
            data = loader.load_data()
            chunks = loader.extract_text_chunks()
            
            # 임베딩 생성
            embedder = EmbeddingGenerator()
            embeddings = embedder.generate_embeddings(chunks)
            embedder.save_embeddings()
            
            print("✅ 임베딩 재생성 완료")
            return True
        except Exception as e:
            print(f"임베딩 재생성 오류: {e}")
            return False
    
    def process_all_corrections(self):
        """모든 수정 데이터 처리 및 모델 업데이트"""
        # 수정 데이터 로드
        corrections = self.load_corrections()
        
        if not corrections:
            print("처리할 수정 데이터가 없습니다.")
            return
        
        print(f"총 {len(corrections)}개의 수정 데이터 처리 중...")
        
        # 각 수정 적용
        for idx, correction in enumerate(corrections, 1):
            print(f"\n처리 중 {idx}/{len(corrections)}: {correction.get('question', '')[:50]}...")
            self.update_model_data(correction)
        
        # 데이터 저장
        self._save_raw_data()
        
        # 임베딩 재생성
        self.regenerate_embeddings()
        
        print(f"\n✅ 모델 업데이트 완료! 총 {len(self.update_history)}개의 변경사항 적용")

def main():
    updater = ModelUpdater()
    updater.process_all_corrections()

if __name__ == "__main__":
    main()
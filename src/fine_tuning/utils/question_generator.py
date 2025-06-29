import random
from typing import List, Set
import json
import os

class QuestionGenerator:
    def __init__(self, keywords: Set[str] = None):
        """
        키워드 기반 질문 생성기
        
        :param keywords: 키워드 세트 (None인 경우 승인된 키워드 로드)
        """
        self.keywords = keywords if keywords is not None else self._load_approved_keywords()
        self.question_templates = self._load_question_templates()
    
    def _load_approved_keywords(self) -> Set[str]:
        """승인된 키워드만 로드"""
        # 승인된 키워드 파일 경로
        approved_keywords_path = 'data/fine_tuning/keywords/approved_keywords.json'
        
        # 파일이 없으면 기본 키워드 파일 시도
        if not os.path.exists(approved_keywords_path):
            fallback_path = 'data/fine_tuning/keywords/extracted_keywords.json'
            print(f"승인된 키워드 파일이 없어 기본 키워드 파일 사용: {fallback_path}")
            approved_keywords_path = fallback_path
        
        try:
            with open(approved_keywords_path, 'r', encoding='utf-8') as f:
                keywords = json.load(f)
                print(f"✅ 키워드 로드 완료: {len(keywords)}개")
                return set(keywords)
        except FileNotFoundError:
            print(f"키워드 파일을 찾을 수 없습니다: {approved_keywords_path}")
            return set()
        except json.JSONDecodeError:
            print("키워드 파일 형식이 올바르지 않습니다.")
            return set()
    
    def _load_question_templates(self) -> List[str]:
        """자연스러운 질문 템플릿 로드"""
        templates_path = 'data/fine_tuning/question_templates.json'
        
        # 항상 새로운 자연스러운 템플릿 사용
        natural_templates = [
            # 기본 정의 (친근한 어투)
            "{}가 뭐야?",
            "{}에 대해 알려줘",
            "{}를 쉽게 설명해줄래?",
            "{}가 무엇인지 알고 싶어",
            
            # 실용적 질문
            "{}는 어떻게 쓰는 거야?",
            "{}를 어떻게 연주하면 돼?",
            "{}는 언제 사용하는 거야?",
            "{}를 어떻게 만들어?",
            
            # 호기심 기반
            "{}가 왜 중요해?",
            "{}를 배우면 뭐가 좋아?",
            "{}는 어떤 느낌이야?",
            "{}의 특징이 뭐야?",
            
            # 비교/관계
            "{}와 비슷한 게 또 있어?",
            "{}와 다른 점이 뭐야?",
            "{}와 {}의 차이점은?",
            
            # 실제 적용
            "{}가 들어간 곡 추천해줘",
            "{}를 실제로 어떻게 써?",
            "{}로 연습할 만한 곡 있어?",
            "{}의 예시를 들어줘",
            
            # 학습 관련
            "{}를 어떻게 연습해야 해?",
            "{}를 배우는 순서는?",
            "{}에서 주의할 점이 뭐야?",
            "{}를 이해하는 팁이 있어?"
        ]
        
        # 템플릿 저장 (선택적)
        if not os.path.exists(templates_path):
            os.makedirs(os.path.dirname(templates_path), exist_ok=True)
            with open(templates_path, 'w', encoding='utf-8') as f:
                json.dump(natural_templates, f, ensure_ascii=False, indent=2)
        
        return natural_templates
    
    def generate_questions(self, num_questions: int = 10) -> List[str]:
        """
        키워드 기반 질문 생성
        
        :param num_questions: 생성할 질문 수
        :return: 생성된 질문 리스트
        """
        if not self.keywords:
            print("사용 가능한 키워드가 없습니다.")
            return []
        
        if not self.question_templates:
            print("질문 템플릿이 없습니다.")
            return []
        
        # 키워드를 리스트로 변환
        keywords_list = list(self.keywords)
        
        # 질문 생성
        questions = []
        attempts = 0
        max_attempts = num_questions * 5  # 무한루프 방지
        
        while len(questions) < num_questions and attempts < max_attempts:
            # 랜덤 키워드 선택
            keyword = random.choice(keywords_list)
            
            # 랜덤 템플릿 선택
            template = random.choice(self.question_templates)
            
            # 질문 생성
            try:
                question = template.format(keyword)
                
                # 중복 방지 및 품질 검사
                if (question not in questions and 
                    self._is_valid_question(question, keyword)):
                    questions.append(question)
                    
            except Exception as e:
                print(f"질문 생성 중 오류: {e}")
            
            attempts += 1
        
        if len(questions) < num_questions:
            print(f"요청한 {num_questions}개 중 {len(questions)}개만 생성되었습니다.")
        
        return questions
    
    def _is_valid_question(self, question: str, keyword: str) -> bool:
        """질문 유효성 검사"""
        # 너무 짧은 질문 제외
        if len(question) < 5:
            return False
        
        # 키워드가 실제로 포함되어 있는지 확인
        if keyword not in question:
            return False
        
        # 조사 중복 확인 (예: "도미넌트는는")
        if any(dup in question for dup in ['은은', '는는', '이이', '가가', '을을', '를를']):
            return False
        
        return True
    
    def generate_questions_by_category(self, categories: dict) -> dict:
        """
        카테고리별 질문 생성
        
        :param categories: {'기본': 키워드세트, '고급': 키워드세트}
        :return: 카테고리별 질문 딕셔너리
        """
        categorized_questions = {}
        
        for category, category_keywords in categories.items():
            # 임시로 키워드 설정
            original_keywords = self.keywords
            self.keywords = category_keywords
            
            # 해당 카테고리 질문 생성
            questions = self.generate_questions(num_questions=10)
            categorized_questions[category] = questions
            
            # 원래 키워드로 복원
            self.keywords = original_keywords
        
        return categorized_questions
    
    def generate_questions_batch(self, num_batches: int = 5, batch_size: int = 10) -> List[List[str]]:
        """
        배치 단위로 질문 생성
        
        :param num_batches: 배치 수
        :param batch_size: 배치당 질문 수
        :return: 배치별 질문 리스트
        """
        batches = []
        
        for i in range(num_batches):
            batch = self.generate_questions(batch_size)
            batches.append(batch)
            print(f"배치 {i+1}/{num_batches} 생성 완료: {len(batch)}개 질문")
        
        return batches
    
    def save_questions(self, questions: List[str], filename: str = 'generated_questions.json'):
        """
        생성된 질문 저장
        
        :param questions: 질문 리스트
        :param filename: 저장할 파일명
        """
        output_dir = 'data/fine_tuning/phase1_question_improvement'
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, filename)
        
        # 기존 질문이 있다면 로드
        existing_questions = []
        if os.path.exists(output_path):
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_questions = json.load(f)
            except json.JSONDecodeError:
                existing_questions = []
        
        # 중복 제거하여 병합
        all_questions = list(dict.fromkeys(existing_questions + questions))
        
        # 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_questions, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 질문 저장 완료: {output_path}")
        print(f"   기존: {len(existing_questions)}개, 추가: {len(questions)}개, 총: {len(all_questions)}개")
    
    def filter_questions(self, questions: List[str], min_length: int = 8) -> List[str]:
        """
        생성된 질문 필터링
        
        :param questions: 질문 리스트
        :param min_length: 최소 길이
        :return: 필터링된 질문 리스트
        """
        filtered = []
        
        for question in questions:
            # 길이 체크
            if len(question) < min_length:
                continue
            
            # 유효성 체크
            if not any(keyword in question for keyword in self.keywords):
                continue
            
            # 조사 중복 체크
            if any(dup in question for dup in ['은은', '는는', '이이', '가가']):
                continue
            
            filtered.append(question)
        
        if len(filtered) < len(questions):
            print(f"필터링: {len(questions) - len(filtered)}개의 질문이 제거됨")
        
        return filtered
    
    def get_keyword_stats(self) -> dict:
        """키워드 통계 정보"""
        return {
            'total_keywords': len(self.keywords),
            'total_templates': len(self.question_templates),
            'max_possible_questions': len(self.keywords) * len(self.question_templates),
            'sample_keywords': list(self.keywords)[:10] if self.keywords else []
        }

def main():
    """질문 생성기 테스트"""
    print("🎵 음악 이론 질문 생성기 테스트")
    
    # 질문 생성기 초기화
    generator = QuestionGenerator()
    
    # 통계 출력
    stats = generator.get_keyword_stats()
    print(f"\n📊 키워드 통계:")
    print(f"  - 총 키워드: {stats['total_keywords']}개")
    print(f"  - 총 템플릿: {stats['total_templates']}개")
    print(f"  - 최대 생성 가능: {stats['max_possible_questions']}개")
    
    if stats['sample_keywords']:
        print(f"  - 샘플 키워드: {', '.join(stats['sample_keywords'])}")
    
    # 질문 생성
    questions = generator.generate_questions(num_questions=20)
    
    # 필터링
    filtered_questions = generator.filter_questions(questions)
    
    # 출력
    print(f"\n🎲 생성된 질문 ({len(filtered_questions)}개):")
    for idx, question in enumerate(filtered_questions[:10], 1):
        print(f"{idx:2d}. {question}")
    
    if len(filtered_questions) > 10:
        print(f"   ... 외 {len(filtered_questions) - 10}개")
    
    # 저장
    if filtered_questions:
        generator.save_questions(filtered_questions, 'raw_questions.json')
    else:
        print("❌ 생성된 질문이 없어 저장하지 않습니다.")

if __name__ == "__main__":
    main()
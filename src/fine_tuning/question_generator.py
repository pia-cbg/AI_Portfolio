import random
from typing import List, Set

class QuestionGenerator:
    def __init__(self, keywords: Set[str]):
        """
        키워드 기반 질문 생성기
        
        :param keywords: 키워드 세트
        """
        self.keywords = keywords
        self.question_templates = [
            # 정의 관련 질문
            "{}의 정의는 무엇인가?",
            "{}에 대해 자세히 설명해줄 수 있나요?",
            "{}의 기본 개념을 알려주세요.",
            
            # 특징/구조 관련 질문
            "{}의 주요 특징은 무엇인가?",
            "{}는 어떤 구조로 이루어져 있나요?",
            "{}의 핵심 구성 요소는 무엇인가?",
            
            # 응용/활용 관련 질문
            "{}는 음악에서 어떻게 활용되나요?",
            "실제 음악에서 {}는 어떤 역할을 하나요?",
            "{}의 실무적 적용 사례는 무엇인가?",
            
            # 비교/관계 관련 질문
            "{}와 다른 개념들과의 차이점은 무엇인가?",
            "{}는 다른 음악 이론 개념과 어떤 관계를 가지나요?",
            "{}와 유사한 다른 개념들을 설명해주세요.",
            
            # 심화 질문
            "{}에 대한 고급 음악 이론적 접근은 무엇인가?",
            "{}의 음악적 맥락과 중요성은 무엇인가?"
        ]
    
    def generate_questions(self, num_questions: int = 10) -> List[str]:
        """
        키워드 기반 질문 생성
        
        :param num_questions: 생성할 질문 수
        :return: 생성된 질문 리스트
        """
        # 키워드를 리스트로 변환
        keywords_list = list(self.keywords)
        
        # 질문 생성
        questions = []
        while len(questions) < num_questions:
            # 랜덤 키워드 선택
            keyword = random.choice(keywords_list)
            
            # 랜덤 템플릿 선택
            template = random.choice(self.question_templates)
            
            # 질문 생성
            question = template.format(keyword)
            
            # 중복 방지
            if question not in questions:
                questions.append(question)
        
        return questions
    
    def filter_questions(self, questions: List[str], min_length: int = 10) -> List[str]:
        """
        생성된 질문 필터링
        
        :param questions: 질문 리스트
        :param min_length: 최소 길이
        :return: 필터링된 질문 리스트
        """
        return [q for q in questions if len(q) >= min_length]

def main():
    # 키워드 추출기에서 키워드 가져오기
    from src.data_processing.keyword_extractor import KeywordExtractor
    
    # 키워드 추출
    extractor = KeywordExtractor()
    keywords = extractor.process()
    
    # 질문 생성기 초기화
    generator = QuestionGenerator(keywords)
    
    # 질문 생성
    questions = generator.generate_questions(num_questions=15)
    filtered_questions = generator.filter_questions(questions)
    
    print("생성된 질문들:")
    for idx, question in enumerate(filtered_questions, 1):
        print(f"{idx}. {question}")

if __name__ == "__main__":
    main()
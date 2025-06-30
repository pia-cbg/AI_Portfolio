import os
import random
import json
from typing import List, Set

class QuestionGenerator:
    def __init__(self, keywords: Set[str]):
        """
        키워드 기반 질문 생성기
        
        :param keywords: 키워드 세트
        """
        self.keywords = keywords
        self.question_templates = [
            # 정의 관련 질문 (이름 기반 템플릿 사용)
            "{keyword}{josa_i} 정의는 뭐야??",
            "{keyword}{josa_i} 대해 자세히 알려줄 수 있어?",
            "{keyword}{josa_i} 기본 개념을 알려줘.",
            
            # 특징/구조 관련 질문
            "{keyword}{josa_i} 주요 특징은 뭐야?",
            "{keyword}는 어떤 구조로 이루어져 있어?",
            "{keyword}{josa_i} 핵심 구성 요소는 뭐야?",
            
            # 응용/활용 관련 질문
            "{keyword}는 음악에서 어떻게 활용돼?",
            "{keyword}는 음악에서 어떤 역할을 해?",
            
            # 비교/관계 관련 질문,
            "{keyword}{josa_wa} 유사한 다른 개념들을 설명해줘.",
            
            # 심화 질문
            "{keyword}{josa_i} 왜 중요해?",
            "{keyword}{josa_eul} 배우는 이유는?",
            "{keyword}{josa_i} 무엇인지 알고 싶어",
            
            # 추가 질문들 (조사 없는 버전)
            "{keyword}에 대해 설명해줘",
            "{keyword} 관련 내용을 알려줘",
            "{keyword} 개념이 궁금해",
            "{keyword}를 이해하고 싶어"
        ]
    
    def get_josa(self, word: str, josa_type: str) -> str:
        """
        한국어 조사를 올바르게 선택하는 함수
        
        :param word: 단어
        :param josa_type: 조사 타입 ('이', '와', '을', '는')
        :return: 올바른 조사
        """
        if not word:
            return ''
            
        # 마지막 글자의 받침 확인
        last_char = word[-1]
        
        # 영어인 경우 발음 기준으로 처리
        if ord('A') <= ord(last_char) <= ord('z'):
            # 영어 단어의 경우 발음을 고려
            # 모음으로 끝나는 발음: A, E, I, O, U
            vowel_endings = ['a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U']
            has_batchim = last_char not in vowel_endings
        else:
            # 한글인 경우 받침 확인
            try:
                char_code = ord(last_char) - 0xAC00
                # 한글 범위 확인 (가~힣)
                if 0 <= char_code <= 11171:
                    has_batchim = char_code % 28 != 0
                else:
                    # 한글이 아닌 경우 받침이 있는 것으로 처리
                    has_batchim = True
            except:
                # 예외 발생 시 받침이 있는 것으로 처리
                has_batchim = True
        
        # 조사 선택
        josa_map = {
            '이': '이' if has_batchim else '가',
            '은': '은' if has_batchim else '는',
            '을': '을' if has_batchim else '를',
            '와': '과' if has_batchim else '와',
            '로': '으로' if has_batchim else '로',
            '의': '의'  # 의는 변하지 않음
        }
        
        return josa_map.get(josa_type, '')
    
    def generate_questions(self, num_questions: int = 10) -> List[str]:
        """
        키워드 기반 질문 생성
        
        :param num_questions: 생성할 질문 수
        :return: 생성된 질문 리스트
        """
        if not self.keywords:
            print("경고: 사용 가능한 키워드가 없습니다.")
            return []
            
        # 키워드를 리스트로 변환
        keywords_list = list(self.keywords)
        
        # 질문 생성
        questions = []
        max_attempts = num_questions * 3  # 무한 루프 방지
        attempts = 0
        
        while len(questions) < num_questions and attempts < max_attempts:
            attempts += 1
            
            # 랜덤 키워드 선택
            keyword = random.choice(keywords_list)
            
            # 랜덤 템플릿 선택
            template = random.choice(self.question_templates)
            
            # 템플릿에 따라 적절한 조사 생성
            josa_i = self.get_josa(keyword, '이')
            josa_wa = self.get_josa(keyword, '와')
            josa_eul = self.get_josa(keyword, '을')
            josa_eun = self.get_josa(keyword, '은')
            
            # 질문 생성
            try:
                question = template.format(
                    keyword=keyword,
                    josa_i=josa_i,
                    josa_wa=josa_wa,
                    josa_eul=josa_eul,
                    josa_eun=josa_eun
                )
            except KeyError:
                # 조사 없는 템플릿인 경우
                question = template.format(keyword=keyword)
            
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

    def save_questions(self, questions: List[str], filename: str = None):
        """
        질문을 JSON 파일로 저장 (누적 방식)
        
        :param questions: 저장할 질문 리스트
        :param filename: 저장할 파일명 (기본값: raw_questions.json)
        """
        if filename is None:
            filename = 'data/fine_tuning/phase1_question_improvement/raw_questions.json'
        else:
            # 파일명만 전달된 경우 기본 경로 추가
            if '/' not in filename and '\\' not in filename:
                filename = f'data/fine_tuning/phase1_question_improvement/{filename}'
        
        # 디렉토리 생성
        directory = os.path.dirname(filename)
        if directory:  # 디렉토리가 있는 경우만 생성
            os.makedirs(directory, exist_ok=True)
        
        # 기존 질문이 있다면 로드
        existing_questions = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_questions = json.load(f)
                print(f"🔄 기존 질문 {len(existing_questions)}개 로드됨")
            except (json.JSONDecodeError, FileNotFoundError):
                print("⚠️ 기존 파일을 로드할 수 없어 새로 시작합니다.")
        
        # 새 질문 추가 (중복 제거)
        # 더 엄격한 중복 체크 (대소문자, 공백 무시)
        normalized_existing = [q.lower().strip() for q in existing_questions]
        new_questions_added = []
        
        for q in questions:
            normalized_q = q.lower().strip()
            if normalized_q not in normalized_existing:
                existing_questions.append(q)
                new_questions_added.append(q)
                normalized_existing.append(normalized_q)
        
        # 저장
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_questions, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 질문 저장 완료: {len(new_questions_added)}개 추가, 총 {len(existing_questions)}개")
        print(f"   저장 위치: {filename}")
        
        return existing_questions
        
    def load_questions(self, filename: str = None) -> List[str]:
        """
        저장된 질문 로드
        
        :param filename: 로드할 파일명
        :return: 로드된 질문 리스트
        """
        if filename is None:
            filename = 'data/fine_tuning/phase1_question_improvement/raw_questions.json'
        else:
            # 파일명만 전달된 경우 기본 경로 추가
            if '/' not in filename and '\\' not in filename:
                filename = f'data/fine_tuning/phase1_question_improvement/{filename}'
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            print(f"✅ 질문 로드 완료: {len(questions)}개")
            return questions
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ 질문 로드 실패: {e}")
            return []

def main():
    # 테스트
    test_keywords = {'음정', '더블샾', '화음', 'scale', 'chord', '도미넌트', '메이저', '마이너'}
    generator = QuestionGenerator(test_keywords)
    
    print("=== 조사 테스트 ===")
    for keyword in test_keywords:
        print(f"- {keyword}{generator.get_josa(keyword, '이')} 무엇인가?")
        print(f"- {keyword}{generator.get_josa(keyword, '와')} 관련된 것은?")
        print(f"- {keyword}{generator.get_josa(keyword, '을')} 배우려면?")
        print()
    
    print("\n=== 자동 생성된 질문 ===")
    questions = generator.generate_questions(15)
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}")

if __name__ == "__main__":
    main()

import os
import random
import json
from typing import List, Set, Dict, Optional

class QuestionGenerator:
    QUESTION_TEMPLATES = [
        "{keyword}{josa_i} 정의는 뭐야?",
        "{keyword}{josa_i} 대해 설명해줘.",
        "{keyword}{josa_i} 구조를 알려줘.",
        "{keyword}는 음악에서 어떻게 쓰이나요?",
        "{keyword}{josa_wa} 비슷한 개념은 뭐가 있어?",
        "{keyword}{josa_i} 특징은 뭐야?",
        "{keyword}{josa_eul} 배워야 하는 이유는?",
        "{keyword}{josa_wa} 차이점은?",
        "{keyword}란 무엇인가요?",
        "{keyword}의 역할을 알려줘.",
        "{keyword}에 대해 알려줘.",
        "{keyword} 관련 설명 부탁해.",
        "{keyword} 개념이 뭐야?"
    ]
    JOSA_MAP = {
        '이': ('이', '가'),
        '와': ('과', '와'),
        '을': ('을', '를'),
        '은': ('은', '는')
    }

    def __init__(self, keywords: Set[str]):
        self.keywords = list(keywords)

    def _has_batchim(self, word: str) -> bool:
        if not word:
            return False
        last = word[-1]
        # 영어 처리
        if 'A' <= last <= 'z':
            return last.lower() not in "aeiou"
        # 한글 처리
        c = ord(last) - 0xAC00
        return 0 <= c <= 11171 and c % 28 != 0

    def _josa(self, word: str, typ: str) -> str:
        if typ not in self.JOSA_MAP or not word:
            return ''
        pair = self.JOSA_MAP[typ]
        return pair[0] if self._has_batchim(word) else pair[1]

    def make_question(self, keyword: str, template: Optional[str]=None) -> str:
        pads = {
            'josa_i': self._josa(keyword, '이'),
            'josa_wa': self._josa(keyword, '와'),
            'josa_eul': self._josa(keyword, '을'),
            'josa_eun': self._josa(keyword, '은')
        }
        template = template or random.choice(self.QUESTION_TEMPLATES)
        try:
            return template.format(keyword=keyword, **pads)
        except Exception:
            return f"{keyword}에 대해 설명해줘."

    def generate_questions_for_keyword(self, keyword: str, n: int = 3) -> List[str]:
        pool = set()
        attempts = 0
        while len(pool) < n and attempts < n * 5:
            pool.add(self.make_question(keyword))
            attempts += 1
        return list(pool)

    def generate_questions(self, per_keyword: int = 3, return_dict: bool = True) -> List:
        results = []
        for kw in self.keywords:
            for q in self.generate_questions_for_keyword(kw, per_keyword):
                if return_dict:
                    results.append({"keyword": kw, "question": q})
                else:
                    results.append(q)
        return results

    @staticmethod
    def save_questions(questions: List[Dict], filename: str):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        print(f"저장 완료: {filename} ({len(questions)}개)")

    @staticmethod
    def load_questions(filename: str) -> List[Dict]:
        with open(filename, encoding="utf-8") as f:
            return json.load(f)

if __name__ == "__main__":
    # 실전 키워드 예시 파일에서 불러오기!
    KW_PATH = "data/fine_tuning/keywords/extracted_keywords.json"
    if os.path.exists(KW_PATH):
        with open(KW_PATH, encoding="utf-8") as f:
            keywords = set(json.load(f))
    else:
        # 그냥 샘플
        keywords = {"Cmaj7", "음계", "서브도미넌트", "화음", "페달포인트"}

    print(f"키워드 개수: {len(keywords)}")
    generator = QuestionGenerator(keywords)
    questions = generator.generate_questions(per_keyword=2)  # per_keyword 원하는 만큼!
    print("총 질문 수:", len(questions))
    generator.save_questions(questions, "data/fine_tuning/questions/raw_questions.json")
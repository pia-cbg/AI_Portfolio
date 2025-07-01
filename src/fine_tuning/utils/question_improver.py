import os
import json

GRADE_MAP = {
    "1": "pass",        # 통과, 파인튜닝 질문에 사용
    "2": "hold",        # 보류, 추후 검토
    "3": "advanced",    # 심화질문/내용 확장
    "4": "fail"         # 부적합, 미사용
}
GRADE_PRINT = """등급을 입력하세요:
1: pass(통과/사용) [엔터: pass]
2: hold(보류/수정 필요)
3: advanced(심화질문/내용확장)
4: fail(미사용/부적합)
"""

class QuestionImprover:
    def __init__(self,
                 question_file="data/fine_tuning/questions/raw_questions.json",
                 evaluation_file="data/fine_tuning/questions/question_evaluations.json"):
        self.question_file = question_file
        self.evaluation_file = evaluation_file
        os.makedirs(os.path.dirname(self.question_file), exist_ok=True)

    def evaluate_questions_incremental(self):
        with open(self.question_file, encoding='utf-8') as f:
            questions = json.load(f)
        # 이전 평가 이력 불러오기
        if os.path.exists(self.evaluation_file):
            with open(self.evaluation_file, encoding='utf-8') as f:
                results = json.load(f)
            evaluated_set = set((r['keyword'], r.get('question')) for r in results)
            print(f"[INFO] 기존 평가/교정 질문 {len(results)}개")
        else:
            results = []
            evaluated_set = set()
            print("[INFO] 새 평가 시작!")

        new_count = 0
        for i, item in enumerate(questions):
            q_key = (item['keyword'], item['question'])
            if q_key in evaluated_set:
                continue  # 중복 질문 건너뜀
            print("\n-----")
            print(f"[{i+1}/{len(questions)}] 키워드: {item['keyword']}")
            print(f"  원본 질문: {item['question']}")
            improved = input("개선된 질문(improved_question, 빈칸시 원본 유지): ").strip()
            if not improved:
                improved = item['question']
            print(GRADE_PRINT)
            grade = input("등급 번호 선택 (엔터시 1-pass): ").strip()
            if not grade:
                grade = "1"
            feedback = input("피드백(옵션): ").strip()
            exclude = input("완전 제외(y=제외, 엔터=사용): ").strip().lower()
            if exclude == 'y' or grade == "4":
                continue

            results.append({
                "keyword": item['keyword'],
                "question": item['question'],
                "improved_question": improved,
                "grade": int(grade),
                "grade_label": GRADE_MAP.get(grade, "pass"),
                "feedback": feedback
            })
            new_count += 1
            with open(self.evaluation_file, "w", encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"{new_count}개 신규 평가/교정 질문이 저장됨 → {self.evaluation_file}")

if __name__ == "__main__":
    improver = QuestionImprover()
    improver.evaluate_questions_incremental()
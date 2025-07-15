import os
import sys
import json
import random
from datetime import datetime

from src.main import initialize_system
from utils.passages_formatter import format_passages
from src.prompts.prompts import GROUNDING_SYSTEM_PROMPT
# print(GROUNDING_SYSTEM_PROMPT)

FEEDBACK_TAGS = {
    "0": {"name": "통과", "for_training": True},
    "1": {"name": "정정", "for_training": True},
    "2": {"name": "불합격", "for_training": True}, # <- 파인튜닝에도 사용
    "3": {"name": "보류", "for_training": True},   # <- 필요시 파인튜닝에도 사용
    "4": {"name": "추가", "for_training": True},
    "5": {"name": "기타", "for_training": False}
}

FINAL_JUDGEMENTS = {
    "0": "합격",
    "1": "불합격",
    "2": "보완"
}
PASS_JUDGEMENT_FOR_TRAINING = {"0", "1", "2"}  # 모두 파인튜닝에 사용, 필요시 subset으로 수정

class ModelTrainer:
    def __init__(self):
        self.FT_BASE = 'data/fine_tuning'
        self.questions_file = os.path.join(self.FT_BASE, 'questions', 'question_evaluations.json')
        self.session_log_dir = os.path.join(self.FT_BASE, 'training_logs')
        self.finetune_dir = os.path.join(self.FT_BASE, 'finetune_data')
        os.makedirs(self.session_log_dir, exist_ok=True)
        os.makedirs(self.finetune_dir, exist_ok=True)
        self.rag_model = None
        self.session_data = {
            'start_time': datetime.now().isoformat(),
            'results': []
        }

    def run(self):
        print("="*60 + "\n[RAG Grounded QA 평가 세션]\n" + "="*60)
        self._initialize_rag_model()
        questions = self._load_questions()
        if not questions:
            print("❌ 사용할 질문이 없습니다.")
            return
        self._interactive_loop(questions)
        session_path = self._save_session_log()
        jsonl_path = self._save_finetune_jsonl()
        print("\n✅ 세션 평가 및 파인튜닝 데이터 모두 저장 완료!")
        print(f"📝 세션 평가: {session_path}")
        print(f"🔑 파인튜닝 데이터: {jsonl_path}")

    def _initialize_rag_model(self):
        try:
            self.rag_model = initialize_system()
            assert self.rag_model, "RAG 모델 초기화 실패"
            print("✅ RAG 시스템 초기화 완료")
        except Exception as e:
            print(f"❌ RAG 시스템 초기화 실패: {e}")
            raise

    def _load_questions(self):
        if not os.path.exists(self.questions_file):
            print(f"❌ 질문 파일 없음: {self.questions_file}")
            return []
        with open(self.questions_file, encoding='utf-8') as f:
            data = json.load(f)
        questions = [
            entry['improved_question']
            for entry in data
            if entry.get('grade') in (1, 3) and entry.get('improved_question')
        ]
        print(f"✅ {len(questions)}개 질문 로드")
        return questions

    def _get_model_answer(self, question):
        response = self.rag_model.get_conversation_response(question)
        answer = response.get('answer', '')
        passages = []
        sources = response.get('sources', [])
        for doc in sources:
            passage = doc.get('content', '')
            if passage:
                passages.append(passage)
        return answer, passages

    def _input_feedback(self):
        print("\n[피드백 태그 선택]")
        for k, v in FEEDBACK_TAGS.items():
            print(f"{k}: {v['name']}")
        tag = input("피드백번호 (0-통과, 1-정정, 2-불합격, 3-보류, 4-추가, 5-기타) [기본:0]: ").strip()
        tag = tag if tag in FEEDBACK_TAGS else "0"
        detail = ""
        if tag != "0":
            detail = input("구체적 설명/정정/보강 (간단히): ").strip()
        return tag, FEEDBACK_TAGS[tag]["name"], detail

    def _input_final_judgement(self):
        print("\n[최종 평가 코드 선택]")
        for code, label in FINAL_JUDGEMENTS.items():
            print(f"{code}: {label}")
        ans = input("최종 평가번호 (0-합격/1-불합격/2-보완, 기본:0): ").strip()
        ans = ans if ans in FINAL_JUDGEMENTS else "0"
        comment = input("최종 평가 코멘트/의견 (옵션): ").strip()
        return ans, FINAL_JUDGEMENTS[ans], comment

    def _interactive_loop(self, questions):
        random.shuffle(questions)
        default_limit = 10
        ans = input(f"\n▶ 평가할 질문 개수 (기본 {default_limit}, all=전체): ").strip()
        if ans == "all":
            target_questions = questions
        else:
            target_questions = questions[:int(ans) if ans else default_limit]

        for idx, q_text in enumerate(target_questions, 1):
            print(f"\n{'='*80}\nQ{idx:02d}: {q_text}")

            # 1차 답변
            answer1, passages = self._get_model_answer(q_text)
            print("\n[모델 1차 답변]\n" + answer1)
            print("\n[참고자료 전체 Passage (구조화)]")
            print(format_passages(passages, max_keys=7, maxlen=120, max_passages=4))

            tag, tag_name, detail = self._input_feedback()
            answer2 = None

            # 2차 재생성 (정정/추가 등 수정 있으면)
            if tag in ("1", "2", "3", "4"):
                composite_input = q_text
                if passages:
                    composite_input += "\n\n참고자료:\n" + "\n---\n".join([p.strip() for p in passages if p.strip()])
                if tag == "1":  # 정정
                    composite_input += "\n정정: " + detail
                elif tag == "4":  # 추가
                    composite_input += "\n추가: " + detail
                elif tag == "2":  # 불합격
                    composite_input += "\n불합격: " + detail
                elif tag == "3":  # 보류
                    composite_input += "\n보류: " + detail
                print("\n[피드백 반영 후 모델 2차 답변 생성 중...]")
                answer2, _ = self._get_model_answer(composite_input)
                print("\n[모델 2차 답변]\n" + answer2)

            final_judgement_code, final_judgement_label, final_comment = self._input_final_judgement()

            # 세션 정보 전체 기록
            self.session_data['results'].append({
                "question": q_text,
                "retrieved_passages": passages,
                "model_answer_1": answer1,
                "feedback_tag": tag,
                "feedback_label": tag_name,
                "feedback_detail": detail,
                "model_answer_2": answer2,
                "final_judgement_code": final_judgement_code,
                "final_judgement_label": final_judgement_label,
                "final_comment": final_comment
            })

    def _save_session_log(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(self.session_log_dir, f"trainer_session_{ts}.json")
        with open(save_path, "w", encoding="utf-8") as wf:
            json.dump(self.session_data, wf, ensure_ascii=False, indent=2)
        print(f"✅ 세션 로그 저장: {save_path}")
        return save_path

    def _save_finetune_jsonl(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(self.finetune_dir, f"finetune_messages_{ts}.jsonl")
        records = []
        stat = {"total": 0, "excluded": 0, "train_samples": 0, "by_judgement": {}}

        for entry in self.session_data["results"]:
            final_judgement_code = entry.get("final_judgement_code", "0")
            final_judgement_label = entry.get("final_judgement_label", "")
            stat["by_judgement"][final_judgement_label] = stat["by_judgement"].get(final_judgement_label, 0) + 1
            stat["total"] += 1

            # 필요한 judgement 코드만 파인튜닝 데이터로 추출
            if final_judgement_code not in PASS_JUDGEMENT_FOR_TRAINING:
                stat["excluded"] += 1
                continue

            tag = entry.get("feedback_tag")
            user_content = entry.get("question", "").strip()
            passages = entry.get("retrieved_passages", [])
            if passages:
                user_content += "\n\n참고자료:\n" + "\n---\n".join([p.strip() for p in passages if p.strip()])
            # Feedback 있으면 user 메시지 추가
            if tag in ("1", "2", "3", "4") and entry.get("feedback_detail", ""):
                ftype = FEEDBACK_TAGS[tag]["name"]
                user_content += f"\n{ftype}: " + entry.get("feedback_detail","").strip()

            messages = [
                {"role": "system", "content": GROUNDING_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ]

            # 답변: 불합격/보류는 항상 2차(피드백 반영 결과) 저장, 통과는 1차/2차 중 실제 답변 우선
            assistant_content = ""
            if tag in ("1", "2", "3", "4") and entry.get("model_answer_2"):
                assistant_content = entry.get("model_answer_2").strip()
            else:
                assistant_content = entry.get("model_answer_1", "").strip()

            messages.append({"role": "assistant", "content": assistant_content})

            records.append({"messages": messages})
            stat["train_samples"] += 1

        if not records:
            print("⚠️ 추출된 파인튜닝 샘플이 없습니다.")
            return None
        with open(save_path, "w", encoding="utf-8") as wf:
            for rec in records:
                wf.write(json.dumps(rec, ensure_ascii=False) + "\n")

        print(f"✅ 파인튜닝 jsonl 저장: {save_path}")
        print(json.dumps(stat, indent=2, ensure_ascii=False))
        return save_path

def main():
    trainer = ModelTrainer()
    trainer.run()

if __name__ == "__main__":
    main()
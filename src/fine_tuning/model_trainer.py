import os
import sys
import json
import random
from datetime import datetime

# project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# sys.path.insert(0, project_root)

from src.main import initialize_system
from utils.passages_formatter import format_passages

GROUNDING_SYSTEM_PROMPT = (
    "You are a music theory expert. For each question, use the retrieved passages only as evidence "
    "if their context—such as key, chord function, or topic—matches the question. "
    "Before using any passage, always check whether it properly applies to the question based on context (e.g. same key, correct chord function, relevant topic). "
    "If a passage is about a different key or context than the question, explicitly state that it does not apply and do not use it as justification for your answer. "
    "Always answer in your own words with clear reasoning, grounding your response only in contextually correct references, and explicitly list your sources if you use them. "
    "If no retrieved passage fully matches the question’s context, answer using your own expertise and state that the evidence did not cover this case. "
    "If additional user feedback is present (correction/comment), use it as guidance to improve your answer. "
    "Do not copy text verbatim."
)

FEEDBACK_TAGS = {
    "0": {"name": "통과", "for_training": True},
    "1": {"name": "정정", "for_training": True},
    "2": {"name": "불합격", "for_training": False},
    "3": {"name": "보류", "for_training": False},
    "4": {"name": "추가", "for_training": True},
    "5": {"name": "기타", "for_training": False}
}
_FEEDBACK_KEYS_FOR_EXCLUDE = {k for k, v in FEEDBACK_TAGS.items() if not v["for_training"]}

class ModelTrainer:
    def __init__(self):
        self.FT_BASE = 'data/fine_tuning'
        self.MODEL_LOG_FILE = 'models/fine_tuned/version_log.json'
        self.MODEL_BASE_DIR = 'models/fine_tuned'
        self.questions_file = os.path.join(self.FT_BASE, 'questions', 'question_evaluations.json')
        self.finetune_data_dir = os.path.join(self.FT_BASE, 'finetune_data')
        self.session_log_dir = os.path.join(self.FT_BASE, 'training_logs')
        os.makedirs(self.finetune_data_dir, exist_ok=True)
        os.makedirs(self.session_log_dir, exist_ok=True)
        os.makedirs(self.MODEL_BASE_DIR, exist_ok=True)
        self.rag_model = None
        self.session_data = {
            'start_time': datetime.now().isoformat(),
            'results': []
        }
        self.version_id = None
        self.model_path = None
        self.finetune_path = None
        self.stats = {}

    def run(self):
        print("="*60 + "\n[RAG Grounded QA 파인튜닝 세션]\n" + "="*60)
        print(f"initialize_system() 반환값: {self.rag_model}")  # 추가
        self._initialize_rag_model()
        questions = self._load_questions()
        if not questions:
            print("❌ 사용할 질문이 없습니다.")
            return
        self._interactive_loop(questions)
        self.finetune_path, self.stats = self._save_finetune_dataset()
        # 아래 부분에서 실제 파인튜닝 실행 및 가중치 저장하면 self.model_path 경로 반환!
        self.version_id = f"music_rag_ft_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.model_path = os.path.join(self.MODEL_BASE_DIR, self.version_id)
        # 실제 파인튜닝 저장 코드 필요시 여기에!
        os.makedirs(self.model_path, exist_ok=True)
        self._save_session_log()
        self._append_version_log(
            model_version=self.version_id,
            model_path=self.model_path,
            finetune_data_path=self.finetune_path,
            feedback_stats=self.stats,
            status="draft",  # 항상 draft로 기록!
            approved_by="",
            comment=""
        )
        print(f"\n✅ 파인튜닝 데이터/로그/모델 버전 기록 저장 완료! [version: {self.version_id}]")
        print("\n⚠️ 승인된(approved) 모델만 실제 서비스/배포에 사용해야 합니다. (추후 승인해야 함)")

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
            answer, passages = self._get_model_answer(q_text)
            print("\n[모델 답변]\n" + answer)
            
            # 🔽🔽🔽 여기부터 교체! 🔽🔽🔽
            print("\n[참고자료 전체 Passage (구조화)]")
            print(format_passages(passages, max_keys=7, maxlen=120, max_passages=4))
            # 🔼🔼🔼 여기까지 한 줄로!
            
            tag, tag_name, detail = self._input_feedback()
            self.session_data['results'].append({
                "question": q_text, "retrieved_passages": passages,
                "model_answer": answer, "feedback_tag": tag, "feedback_label": tag_name, "feedback_detail": detail
            })

    def _save_finetune_dataset(self):
        finetune_records = []
        stat = {"train_samples": 0, "excluded": 0, "by_tag": {}}
        for entry in self.session_data['results']:
            tag = entry.get("feedback_tag") or "0"
            tag_name = entry.get("feedback_label") or FEEDBACK_TAGS.get(tag, {}).get("name", "")
            stat["by_tag"][tag_name] = stat["by_tag"].get(tag_name, 0) + 1
            if tag in _FEEDBACK_KEYS_FOR_EXCLUDE:
                stat["excluded"] += 1
                continue
            messages = [
                {"role": "system", "content": GROUNDING_SYSTEM_PROMPT},
                {"role": "user", "content": f"{entry['question']}\n\n참고자료:\n" + "\n---\n".join(entry["retrieved_passages"])}
            ]
            if tag != "0" and entry.get("feedback_detail"):
                messages.append({"role": "user", "content": f"운영자 피드백({tag_name}): {entry['feedback_detail']}"})
            messages.append({"role": "assistant", "content": entry["model_answer"]})
            finetune_records.append({"messages": messages, "feedback_tag": tag, "feedback_label": tag_name, "feedback_detail": entry.get("feedback_detail")})
            stat["train_samples"] += 1
        if not finetune_records:
            print("⚠️ 남은 파인튜닝 샘플이 없습니다.")
            return None, stat
        save_path = os.path.join(self.finetune_data_dir, f"finetune_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")
        with open(save_path, "w", encoding="utf-8") as wf:
            for record in finetune_records:
                wf.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"✅ 파인튜닝 messages 데이터 저장: {save_path}")
        print(f"샘플 수: {stat['train_samples']}, 제외: {stat['excluded']}, 태그별: {stat['by_tag']}")
        return save_path, stat

    def _save_session_log(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(self.session_log_dir, f"trainer_session_{ts}.json")
        with open(save_path, "w", encoding="utf-8") as wf:
            json.dump(self.session_data, wf, ensure_ascii=False, indent=2)
        print(f"✅ 세션 로그 저장: {save_path}")

    def _append_version_log(self, model_version, model_path, finetune_data_path, feedback_stats, status="draft", approved_by="", comment=""):
        log_data = []
        if os.path.exists(self.MODEL_LOG_FILE):
            with open(self.MODEL_LOG_FILE, encoding='utf-8') as f:
                try:
                    log_data = json.load(f)
                except Exception:
                    log_data = []
        record = {
            "timestamp": datetime.now().isoformat(),
            "model_version": model_version,
            "model_path": model_path,
            "finetune_data_path": finetune_data_path,
            "base_model": "music_rag_base_v1.1",  # 필요시 동적 적용
            "feedback_stats": feedback_stats,
            "status": status,             # draft/approved/rejected/deleted
            "approved_by": approved_by,   # admin 등
            "comments": comment
        }
        log_data.append(record)
        with open(self.MODEL_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 버전 로그(임시 draft) 갱신: {self.MODEL_LOG_FILE}")

def main():
    trainer = ModelTrainer()
    trainer.run()

if __name__ == "__main__":
    main()
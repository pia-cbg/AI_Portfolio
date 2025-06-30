import os
import sys
import json
from typing import List, Dict, Set
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.fine_tuning.utils.question_generator import QuestionGenerator

class Phase1QuestionImprovement:
    def __init__(self):
        """Phase 1: 질문 개선 시스템 초기화"""
        self.base_dir = 'data/fine_tuning/questions'
        os.makedirs(self.base_dir, exist_ok=True)
        
        # 파일 경로들 업데이트
        self.raw_questions_file = os.path.join(self.base_dir, 'raw_questions.json')
        self.refined_questions_file = os.path.join(self.base_dir, 'refined_questions.json')
        self.question_criteria_file = os.path.join(self.base_dir, 'question_criteria.json')
        self.evaluations_file = os.path.join(self.base_dir, 'question_evaluations.json')
        
        # 평가 기준 로드
        self.evaluation_criteria = self._load_evaluation_criteria()
        
        # 현재 세션 데이터
        self.session_data = {
            'start_time': datetime.now().isoformat(),
            'evaluations': [],
            'improved_questions': []
        }
    
    def _load_evaluation_criteria(self) -> List[Dict]:
        """질문 평가 기준 로드"""
        criteria_path = os.path.join(self.base_dir, 'question_criteria.json')
        
        if os.path.exists(criteria_path):
            with open(criteria_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 기본 평가 기준
            default_criteria = [
                {
                    "key": "clarity",
                    "name": "명확성",
                    "description": "질문이 명확하고 이해하기 쉬운가"
                },
                {
                    "key": "relevance",
                    "name": "관련성",
                    "description": "키워드와 질문의 관련성이 높은가"
                },
                {
                    "key": "difficulty",
                    "name": "난이도",
                    "description": "적절한 난이도의 질문인가"
                },
                {
                    "key": "specificity",
                    "name": "구체성",
                    "description": "구체적이고 답변 가능한 질문인가"
                },
                {
                    "key": "educational",
                    "name": "교육적 가치",
                    "description": "학습에 도움이 되는 질문인가"
                }
            ]
            
            # 저장
            with open(criteria_path, 'w', encoding='utf-8') as f:
                json.dump(default_criteria, f, ensure_ascii=False, indent=2)
            
            return default_criteria
    
    def run_phase1(self):
        """Phase 1 전체 프로세스 실행"""
        print("🎵 Phase 1: 질문 개선 프로세스 시작")
        print("="*60)
        
        # 1. 승인된 키워드 로드
        print("\n1️⃣ 승인된 키워드 로드 중...")
        keywords = self._load_approved_keywords()
        
        if not keywords:
            print("❌ 승인된 키워드가 없습니다.")
            return
        
        # 2. 질문 생성
        print("\n2️⃣ 질문 생성 중...")
        raw_questions = self._generate_questions(keywords)
        
        # 3. 질문 평가 및 개선
        print("\n3️⃣ 질문 평가 및 개선...")
        improved_questions = self._evaluate_and_improve_questions(raw_questions)
        
        # 4. 결과 저장
        print("\n4️⃣ 결과 저장 중...")
        self._save_results(improved_questions)
        
        print("\n✅ Phase 1 완료!")
        self._print_summary()
    
    def _load_approved_keywords(self) -> Set[str]:
        """승인된 키워드 로드"""
        approved_path = 'data/fine_tuning/keywords/approved_keywords.json'
        fallback_path = 'data/fine_tuning/keywords/extracted_keywords.json'
        
        # 승인된 키워드 파일 우선 시도
        for path in [approved_path, fallback_path]:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        keywords = set(json.load(f))
                        print(f"✅ 키워드 로드 완료: {len(keywords)}개 (출처: {path})")
                        
                        # 상위 10개 키워드 미리보기
                        sample_keywords = list(keywords)[:10]
                        print(f"   샘플 키워드: {', '.join(sample_keywords)}")
                        
                        return keywords
                except json.JSONDecodeError:
                    print(f"❌ 키워드 파일 형식 오류: {path}")
                    continue
        
        print("❌ 사용 가능한 키워드 파일을 찾을 수 없습니다.")
        print("다음 파일 중 하나를 생성해주세요:")
        print(f"  - {approved_path}")
        print(f"  - {fallback_path}")
        return set()
    
    def _generate_questions(self, keywords: Set[str]) -> List[str]:
        """
        키워드 기반 질문 생성
        
        :param keywords: 키워드 세트
        :return: 생성된 질문 리스트
        """
        print("\n2️⃣ 질문 생성 중...")
        
        # 이미 생성된 질문 로드 (추가 방식)
        existing_questions = []
        raw_questions_file = os.path.join(self.base_dir, 'raw_questions.json')
        
        if os.path.exists(raw_questions_file):
            try:
                with open(raw_questions_file, 'r', encoding='utf-8') as f:
                    existing_questions = json.load(f)
                    print(f"✅ 기존 질문 {len(existing_questions)}개 로드 완료")
            except json.JSONDecodeError:
                print("⚠️ 기존 질문 파일 손상. 새로 시작합니다.")
        
        # 생성할 질문 수 결정 (기존 질문이 충분하면 적게 생성)
        if len(existing_questions) >= 200:  # 최대 질문 수
            print(f"⚠️ 이미 충분한 질문({len(existing_questions)}개)이 있습니다.")
            return existing_questions
            
        # 필요한 추가 질문 수 계산
        target_total = 100  # 목표 질문 수
        num_to_generate = max(10, target_total - len(existing_questions))  # 최소 10개는 생성
        
        print(f"🎲 {num_to_generate}개의 새 질문 생성 중...")
        
        # 질문 생성기 초기화
        generator = QuestionGenerator(keywords)
        
        # 질문 생성
        questions = generator.generate_questions(num_questions=num_to_generate)
        
        # 질문 필터링
        filtered_questions = generator.filter_questions(questions)
        
        # 질문 저장 (기존 + 새로운 질문들)
        all_questions = existing_questions + [q for q in filtered_questions if q not in existing_questions]
        
        # 저장
        save_path = os.path.join(self.base_dir, 'raw_questions.json')
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(all_questions, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 질문 저장 완료: {len(filtered_questions)}개 추가, 총 {len(all_questions)}개")
        
        return all_questions
    
    def _evaluate_and_improve_questions(self, questions: List[str]) -> List[Dict]:
        """질문 평가 및 개선"""
        if not questions:
            print("평가할 질문이 없습니다.")
            return []
        
        improved_questions = []
        
        print(f"\n총 {len(questions)}개의 질문을 평가합니다.")
        print("각 질문에 대해 평가하고 필요시 개선해주세요.\n")
        
        # 평가할 질문 범위 선택
        try:
            start_idx = int(input(f"시작 번호 (1-{len(questions)}, 기본 1): ") or 1) - 1
            end_idx = int(input(f"끝 번호 (1-{len(questions)}, 기본 {min(30, len(questions))}): ") or min(30, len(questions)))
            
            # 범위 검증
            start_idx = max(0, start_idx)
            end_idx = min(len(questions), end_idx)
            
        except ValueError:
            start_idx = 0
            end_idx = min(30, len(questions))
        
        selected_questions = questions[start_idx:end_idx]
        print(f"\n📝 {len(selected_questions)}개 질문을 평가합니다 ({start_idx+1}번부터 {end_idx}번까지)")
        
        for idx, question in enumerate(selected_questions, start_idx + 1):
            print(f"\n{'='*60}")
            print(f"질문 {idx}: {question}")
            print('='*60)
            
            # 평가 수집
            evaluation = self._collect_evaluation(question, idx)
            
            # 개선된 질문 처리
            if evaluation['status'] == 'improved':
                improved_questions.append({
                    'original': question,
                    'improved': evaluation['improved_question'],
                    'scores': evaluation['scores'],
                    'feedback': evaluation['feedback']
                })
            elif evaluation['status'] == 'accepted':
                improved_questions.append({
                    'original': question,
                    'improved': question,  # 원본 그대로
                    'scores': evaluation['scores'],
                    'feedback': evaluation['feedback']
                })
            # 'rejected'인 경우는 추가하지 않음
            
            self.session_data['evaluations'].append(evaluation)
            
            # 계속 진행 여부 (마지막 질문이 아닌 경우)
            if idx < start_idx + len(selected_questions):
                cont = input("\n다음 질문으로 진행하시겠습니까? (y/n, 기본 y): ").lower()
                if cont == 'n':
                    print("평가를 중단합니다.")
                    break
        
        return improved_questions
    
    def _collect_evaluation(self, question: str, question_id: int) -> Dict:
        """단일 질문에 대한 평가 수집"""
        print("\n📊 질문 평가:")
        
        scores = {}
        
        # 각 기준별 점수 입력
        for criterion in self.evaluation_criteria:
            print(f"\n{criterion['name']} - {criterion['description']}")
            while True:
                try:
                    score_input = input(f"점수 (0-10, 기본 7): ").strip()
                    score = int(score_input) if score_input else 7
                    
                    if 0 <= score <= 10:
                        scores[criterion['key']] = score
                        break
                    else:
                        print("0-10 사이의 점수를 입력하세요.")
                except ValueError:
                    print("숫자를 입력하세요.")
        
        # 평균 점수 계산
        avg_score = sum(scores.values()) / len(scores)
        
        print(f"\n평균 점수: {avg_score:.1f}/10")
        
        # 처리 방법 선택
        print("\n처리 방법을 선택하세요:")
        print("1. 유지 (그대로 사용)")
        print("2. 개선 (수정해서 사용)")
        print("3. 제외 (사용하지 않음)")
        
        while True:
            action = input("선택 (1/2/3, 기본 1): ").strip()
            if action in ['1', '2', '3', '']:
                action = action or '1'
                break
            print("1, 2, 3 중 하나를 선택하세요.")
        
        # 피드백 수집
        feedback = input("\n피드백 (선택사항): ").strip()
        
        evaluation = {
            'question_id': question_id,
            'question': question,
            'scores': scores,
            'avg_score': avg_score,
            'feedback': feedback,
            'timestamp': datetime.now().isoformat()
        }
        
        # 처리 방법에 따른 추가 작업
        if action == '2':  # 개선
            improved = input("개선된 질문을 입력하세요: ").strip()
            if improved:
                evaluation['improved_question'] = improved
                evaluation['status'] = 'improved'
            else:
                evaluation['status'] = 'accepted'  # 개선안 없으면 유지
        elif action == '3':  # 제외
            evaluation['status'] = 'rejected'
        else:  # 유지
            evaluation['status'] = 'accepted'
        
        return evaluation
    
    def _save_results(self, improved_questions: List[Dict]):
        """결과 저장"""
        if not improved_questions:
            print("⚠️ 저장할 개선된 질문이 없습니다.")
            return
        
        # 1. 개선된 질문만 추출
        refined_questions = [q['improved'] for q in improved_questions]
        
        # 2. 최종 질문 저장
        output_path = os.path.join(self.base_dir, 'refined_questions.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(refined_questions, f, ensure_ascii=False, indent=2)
        
        # 3. 전체 평가 데이터 저장
        self.session_data['end_time'] = datetime.now().isoformat()
        self.session_data['improved_questions'] = improved_questions
        
        evaluation_path = os.path.join(self.base_dir, 'question_evaluations.json')
        with open(evaluation_path, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, ensure_ascii=False, indent=2)
        
        # 4. 개선 이력 저장
        improvement_path = os.path.join(self.base_dir, 'improvement_history.json')
        with open(improvement_path, 'w', encoding='utf-8') as f:
            json.dump(improved_questions, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {len(refined_questions)}개의 개선된 질문 저장 완료")
        print(f"   - 최종 질문: {output_path}")
        print(f"   - 평가 데이터: {evaluation_path}")
        print(f"   - 개선 이력: {improvement_path}")
    
    def _print_summary(self):
        """평가 결과 요약 출력"""
        evaluations = self.session_data['evaluations']
        
        if not evaluations:
            print("평가된 질문이 없습니다.")
            return
        
        print("\n" + "="*60)
        print("📊 Phase 1 결과 요약")
        print("="*60)
        
        # 기본 통계
        total_evaluated = len(evaluations)
        accepted = len([e for e in evaluations if e['status'] == 'accepted'])
        improved = len([e for e in evaluations if e['status'] == 'improved'])
        rejected = len([e for e in evaluations if e['status'] == 'rejected'])
        
        print(f"총 평가 질문: {total_evaluated}개")
        print(f"  - 유지: {accepted}개 ({accepted/total_evaluated*100:.1f}%)")
        print(f"  - 개선: {improved}개 ({improved/total_evaluated*100:.1f}%)")
        print(f"  - 제외: {rejected}개 ({rejected/total_evaluated*100:.1f}%)")
        
        # 평균 점수
        print(f"\n기준별 평균 점수:")
        for criterion in self.evaluation_criteria:
            key = criterion['key']
            scores = [e['scores'][key] for e in evaluations if key in e['scores']]
            if scores:
                avg = sum(scores) / len(scores)
                print(f"  - {criterion['name']}: {avg:.1f}/10")
        
        # 전체 평균
        all_avg_scores = [e['avg_score'] for e in evaluations]
        if all_avg_scores:
            total_avg = sum(all_avg_scores) / len(all_avg_scores)
            print(f"\n전체 평균 점수: {total_avg:.1f}/10")
        
        # 최종 질문 수
        final_count = accepted + improved
        print(f"\n✨ 최종 사용 가능한 질문: {final_count}개")
        
        if final_count > 0:
            print("\n다음 단계: model_trainer - 답변 평가를 진행하세요.")
            print("python /src/fine_tuning/model_trainer.py")

def main():
    phase1 = Phase1QuestionImprovement()
    phase1.run_phase1()

if __name__ == "__main__":
    main()
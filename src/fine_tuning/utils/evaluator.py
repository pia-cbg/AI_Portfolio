"""
파인튜닝 평가 시스템
- 답변 평가 및 저장
- 세션 관리
- 개선 리포트 생성
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class FineTuningEvaluator:
    def __init__(self, base_path='data/fine_tuning'):
        """
        평가 데이터 관리 시스템 초기화
        
        :param base_path: 파인튜닝 데이터 저장 경로
        """
        self.base_path = base_path
        self.evaluations_path = os.path.join(base_path, 'evaluations')
        self.corrections_path = os.path.join(base_path, 'corrections')
        
        # 디렉토리 생성
        self._create_directories()
        
        # 평가 기준 로드
        self.criteria = self._load_evaluation_criteria()
        
        # 평가 데이터 캐시
        self.current_session_evaluations = []
    
    def _create_directories(self):
        """필요한 디렉토리 생성"""
        for path in [self.evaluations_path, self.corrections_path]:
            os.makedirs(path, exist_ok=True)
    
    def _load_evaluation_criteria(self) -> List[Dict]:
        """평가 기준 로드 - 딕셔너리 리스트로 반환"""
        # 평가 기준 파일 경로
        criteria_path = os.path.join(self.base_path, 'evaluation_criteria.json')
        
        # 파일이 존재하면 로드
        if os.path.exists(criteria_path):
            try:
                with open(criteria_path, 'r', encoding='utf-8') as f:
                    criteria_data = json.load(f)
                    
                # 데이터 구조 확인 및 변환
                if isinstance(criteria_data, dict) and 'answer_criteria' in criteria_data:
                    # 딕셔너리 형태면 리스트로 변환
                    return criteria_data['answer_criteria']
                elif isinstance(criteria_data, list):
                    # 이미 리스트면 그대로 사용
                    return criteria_data
                else:
                    print("⚠️ 평가 기준 형식 오류. 기본 기준 사용.")
            except Exception as e:
                print(f"⚠️ 평가 기준 로드 오류: {e}. 기본 기준 사용.")
        
        # 기본 평가 기준
        return [
            {
                'key': 'source_accuracy',
                'name': '참고자료 정확성',
                'description': '참고자료를 정확히 인용했는가'
            },
            {
                'key': 'source_citation',
                'name': '출처 표시',
                'description': '모든 정보에 출처가 표시되었는가'
            },
            {
                'key': 'no_hallucination',
                'name': '환각 없음',
                'description': '참고자료에 없는 내용을 생성하지 않았는가'
            },
            {
                'key': 'clarity',
                'name': '명확성',
                'description': '답변이 명확하고 이해하기 쉬운가'
            },
            {
                'key': 'completeness',
                'name': '완전성',
                'description': '질문에 충분히 답변했는가'
            }
        ]
    
    def evaluate_answer(self, question: str, answer: str, sources: List[Dict]) -> Dict:
        """점수별 전략을 고려한 답변 평가"""
        
        print(f"\n📋 답변 평가: {question}")
        print(f"\n💡 현재 답변:\n{answer}")
        
        # 점수별 전략 안내
        print(f"\n📊 점수별 업데이트 전략:")
        print(f"  🔴 0-3점: 업데이트 안함")
        print(f"  🟡 4-5점: 완전 교체 (새로 작성 필요)")  
        print(f"  🟢 6-7점: 미세 조정 (원본 + 수정사항)")
        print(f"  🔵 8-10점: 선택적 개선 (원본 유지 + 약간 보완)")
        
        # 간편 평가
        print(f"\n⚡ 빠른 평가:")
        print(f"1. 완전히 틀림 (1-3점) - 업데이트 안함")
        print(f"2. 많이 틀림 (4-5점) - 새로 작성")
        print(f"3. 괜찮지만 아쉬움 (6-7점) - 미세 조정")  
        print(f"4. 거의 완벽 (8-10점) - 약간만 보완")
        
        choice = input("선택 (1-4): ").strip()
        
        if choice == '1':
            # 업데이트 안함
            scores = {criterion['key']: 2 for criterion in self.criteria}
            feedback = "답변이 부적절하여 업데이트하지 않음"
            correction = ""
            
        elif choice == '2':
            # 완전 교체
            scores = {criterion['key']: 4 for criterion in self.criteria}
            feedback = input("어떤 점이 문제인가요? ")
            print("💡 완전히 새로운 답변을 작성해주세요:")
            correction = input("새로운 답변: ")
            
        elif choice == '3':
            # 미세 조정 - 가장 많이 사용될 케이스
            scores = {criterion['key']: 6 for criterion in self.criteria}
            feedback = input("어떤 부분을 개선하면 좋을까요? ")
            print("💡 추가하거나 수정할 내용만 입력해주세요:")
            correction = input("미세 조정 내용: ")
            
        elif choice == '4':
            # 선택적 개선
            scores = {criterion['key']: 8 for criterion in self.criteria}
            feedback = input("더 좋게 만들 수 있는 점이 있다면? ")
            correction = input("약간의 보완 내용 (선택사항): ")
            
        else:
            # 수동 입력
            print("\n상세 평가 모드:")
            scores = {}
            for criterion in self.criteria:
                while True:
                    try:
                        score = int(input(f"{criterion['name']} (0-10): "))
                        if 0 <= score <= 10:
                            scores[criterion['key']] = score
                            break
                    except ValueError:
                        print("숫자를 입력해주세요.")
            
            avg_score = sum(scores.values()) / len(scores)
            print(f"\n현재 평균 점수: {avg_score:.1f}")
            
            if avg_score >= 8:
                print("💡 높은 점수입니다. 약간의 보완만 입력하세요.")
            elif avg_score >= 6:
                print("💡 중간 점수입니다. 미세 조정 내용을 입력하세요.")
            else:
                print("💡 낮은 점수입니다. 새로운 답변이나 대폭 수정이 필요합니다.")
                
            feedback = input("피드백: ")
            correction = input("수정/보완 내용: ")
        
        avg_score = sum(scores.values()) / len(scores)
        
        return {
            'question': question,
            'answer': answer,
            'sources': sources,
            'scores': scores,
            'avg_score': avg_score,
            'feedback': feedback,
            'correction': correction,
            'timestamp': datetime.now().isoformat()
        }
        
    def save_evaluation(self, evaluation: Dict):
        """
        평가 데이터 저장 (누적 방식)
        
        :param evaluation: 평가 데이터
        """
        # 타임스탬프 추가
        evaluation['timestamp'] = datetime.now().isoformat()
        
        # 세션 캐시에 추가
        self.current_session_evaluations.append(evaluation)
        
        # 누적 파일에 추가
        evaluations_file = os.path.join(self.evaluations_path, "all_evaluations.json")
        
        # 기존 데이터 로드
        existing_evaluations = []
        if os.path.exists(evaluations_file):
            try:
                with open(evaluations_file, 'r', encoding='utf-8') as f:
                    existing_evaluations = json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ 손상된 평가 파일 발견. 새 파일 생성합니다.")
        
        # 새 평가 데이터 추가
        existing_evaluations.append(evaluation)
        
        # 전체 데이터 저장
        with open(evaluations_file, 'w', encoding='utf-8') as f:
            json.dump(existing_evaluations, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 평가 데이터 추가 완료 (총 {len(existing_evaluations)}개)")
        
        # 낮은 점수 평가는 별도로 처리
        if evaluation.get('avg_score', 0) < 7 and evaluation.get('correction'):
            self._handle_low_score_evaluation(evaluation)
    
    def _handle_low_score_evaluation(self, evaluation: Dict):
        """
        낮은 점수 평가 처리
        
        :param evaluation: 평가 데이터
        """
        # 수정이 필요한 경우 corrections 폴더에 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"correction_{timestamp}.json"
        filepath = os.path.join(self.corrections_path, filename)
        
        correction_data = {
            'question': evaluation['question'],
            'original_response': evaluation['answer'],
            'corrected_response': evaluation['correction'],
            'scores': evaluation['scores'],
            'feedback': evaluation['feedback'],
            'timestamp': evaluation['timestamp']
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(correction_data, f, ensure_ascii=False, indent=2)
        
        print(f"📝 수정 데이터 저장 완료: {filename}")
    
    def save_session(self):
        """현재 세션 데이터 저장"""
        if not self.current_session_evaluations:
            print("저장할 세션 데이터가 없습니다.")
            return
        
        # 세션 요약
        session_summary = {
            'session_date': datetime.now().isoformat(),
            'total_evaluations': len(self.current_session_evaluations),
            'avg_score': sum(e.get('avg_score', 0) for e in self.current_session_evaluations) / len(self.current_session_evaluations),
            'evaluations': self.current_session_evaluations
        }
        
        # 세션 요약 파일 경로
        summaries_file = os.path.join(self.evaluations_path, "session_summaries.json")
        
        # 기존 세션 요약 로드
        existing_summaries = []
        if os.path.exists(summaries_file):
            try:
                with open(summaries_file, 'r', encoding='utf-8') as f:
                    existing_summaries = json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ 손상된 세션 요약 파일 발견. 새 파일 생성합니다.")
        
        # 새 세션 요약 추가
        existing_summaries.append(session_summary)
        
        # 전체 데이터 저장
        with open(summaries_file, 'w', encoding='utf-8') as f:
            json.dump(existing_summaries, f, ensure_ascii=False, indent=2)
        
        print(f"📊 세션 요약 추가 완료 (총 {len(existing_summaries)}개 세션)")
        
        # 개별 세션 파일도 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_file = os.path.join(self.evaluations_path, f"session_{timestamp}.json")
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_summary, f, ensure_ascii=False, indent=2)
    
    def get_low_score_evaluations(self, threshold: float = 7.0) -> List[Dict]:
        """
        낮은 점수의 평가 데이터 가져오기
        
        :param threshold: 점수 임계값
        :return: 낮은 점수의 평가 데이터 리스트
        """
        low_score_evals = []
        
        # 전체 평가 데이터 로드
        evaluations_file = os.path.join(self.evaluations_path, "all_evaluations.json")
        if os.path.exists(evaluations_file):
            try:
                with open(evaluations_file, 'r', encoding='utf-8') as f:
                    all_evaluations = json.load(f)
                    
                # 낮은 점수 필터링
                low_score_evals = [
                    e for e in all_evaluations 
                    if e.get('avg_score', 0) < threshold
                ]
            except Exception as e:
                print(f"평가 데이터 로드 오류: {e}")
        
        return low_score_evals
    
    def get_all_corrections(self) -> List[Dict]:
        """
        모든 수정 데이터 가져오기
        
        :return: 모든 수정 데이터 리스트
        """
        corrections = []
        
        # corrections 디렉토리의 모든 파일 로드
        if os.path.exists(self.corrections_path):
            for filename in os.listdir(self.corrections_path):
                if filename.startswith('correction_') and filename.endswith('.json'):
                    filepath = os.path.join(self.corrections_path, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            correction = json.load(f)
                            corrections.append(correction)
                    except Exception as e:
                        print(f"수정 데이터 로드 오류 ({filename}): {e}")
        
        return corrections
    
    def generate_improvement_report(self, output_path: Optional[str] = None) -> Dict:
        """
        개선 리포트 생성
        
        :param output_path: 출력 파일 경로 (없으면 저장하지 않음)
        :return: 리포트 데이터
        """
        # 모든 평가 데이터 로드
        all_evaluations = []
        evaluations_file = os.path.join(self.evaluations_path, "all_evaluations.json")
        if os.path.exists(evaluations_file):
            try:
                with open(evaluations_file, 'r', encoding='utf-8') as f:
                    all_evaluations = json.load(f)
            except Exception as e:
                print(f"평가 데이터 로드 오류: {e}")
        
        # 모든 수정 데이터 로드
        all_corrections = self.get_all_corrections()
        
        # 통계 계산
        total_evals = len(all_evaluations)
        avg_score = sum(e.get('avg_score', 0) for e in all_evaluations) / total_evals if total_evals > 0 else 0
        low_score_count = len([e for e in all_evaluations if e.get('avg_score', 0) < 7])
        
        # 기준별 평균 점수
        criteria_scores = {}
        for evaluation in all_evaluations:
            scores = evaluation.get('scores', {})
            for key, score in scores.items():
                if key not in criteria_scores:
                    criteria_scores[key] = []
                criteria_scores[key].append(score)
        
        criteria_avgs = {
            key: sum(scores) / len(scores) if scores else 0 
            for key, scores in criteria_scores.items()
        }
        
        # 리포트 생성
        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_evaluations': total_evals,
                'average_score': avg_score,
                'low_score_count': low_score_count,
                'correction_count': len(all_corrections)
            },
            'criteria_averages': criteria_avgs,
            'improvement_areas': [
                {
                    'criterion': key,
                    'average_score': avg,
                    'priority': 'high' if avg < 6 else ('medium' if avg < 7.5 else 'low')
                }
                for key, avg in sorted(criteria_avgs.items(), key=lambda x: x[1])
            ]
        }
        
        # 저장
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"📊 개선 리포트 저장 완료: {output_path}")
        
        return report

def main():
    """테스트용 메인 함수"""
    evaluator = FineTuningEvaluator()
    
    # 평가 기준 출력
    print("📋 평가 기준:")
    for criterion in evaluator.criteria:
        print(f"- {criterion.get('name')}: {criterion.get('description')}")
    
    # 개선 리포트 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = evaluator.generate_improvement_report(f"data/fine_tuning/improvement_report_{timestamp}.json")
    
    print("\n📊 개선 리포트 요약:")
    print(f"총 평가: {report['statistics']['total_evaluations']}개")
    print(f"평균 점수: {report['statistics']['average_score']:.2f}/10")
    print(f"개선 필요: {report['statistics']['low_score_count']}개")

if __name__ == "__main__":
    main()
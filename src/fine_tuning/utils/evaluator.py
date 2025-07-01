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
        평가 데이터 관리 시스템 초기화 (세션별 관리)
        
        :param base_path: 파인튜닝 데이터 저장 경로
        """
        self.base_path = base_path
        self.sessions_path = os.path.join(base_path, 'sessions')
        self.aggregated_path = os.path.join(base_path, 'aggregated')
        
        # 현재 세션 설정
        self.current_session = self._get_or_create_session()
        self.session_dir = os.path.join(self.sessions_path, self.current_session)
        
        # 세션별 경로
        self.evaluations_path = os.path.join(self.session_dir, 'evaluations')
        self.corrections_path = os.path.join(self.session_dir, 'corrections')
        
        # 디렉토리 생성
        self._create_directories()
        
        # 평가 기준 로드
        self.criteria = self._load_evaluation_criteria()
        
        # 평가 데이터 캐시
        self.current_session_evaluations = []
        
        print(f"📁 현재 세션: {self.current_session}")
    
    def _get_or_create_session(self) -> str:
        """현재 세션 가져오기 또는 새 세션 생성"""
        os.makedirs(self.sessions_path, exist_ok=True)
        
        # 기존 세션들 확인
        existing_sessions = [d for d in os.listdir(self.sessions_path) 
                           if d.startswith('session_') and os.path.isdir(os.path.join(self.sessions_path, d))]
        
        if existing_sessions:
            latest_session = sorted(existing_sessions)[-1]
            print(f"\n📋 기존 세션들:")
            for i, session in enumerate(sorted(existing_sessions), 1):
                marker = " (최신)" if session == latest_session else ""
                print(f"  {i}. {session}{marker}")
            
            choice = input(f"\n새 세션을 시작하시겠습니까? (y: 새 세션, n: 최신 세션 계속): ").lower()
            
            if choice != 'y':
                print(f"✅ 기존 세션 계속: {latest_session}")
                return latest_session
        
        # 새 세션 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_count = len(existing_sessions) + 1
        new_session = f"session_{session_count:03d}_{timestamp}"
        
        print(f"🆕 새 세션 생성: {new_session}")
        return new_session
    
    def _create_directories(self):
        """필요한 디렉토리 생성"""
        os.makedirs(self.evaluations_path, exist_ok=True)
        os.makedirs(self.corrections_path, exist_ok=True)
        os.makedirs(self.aggregated_path, exist_ok=True)
    
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
        """점수별 전략을 고려한 답변 평가 (원본 방식 유지)"""
        
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
            'timestamp': datetime.now().isoformat(),
            'session': self.current_session
        }
        
    def save_evaluation(self, evaluation: Dict):
        """
        평가 데이터 저장 (세션별 + 통합)
        
        :param evaluation: 평가 데이터
        """
        # 타임스탬프 및 세션 정보 추가
        evaluation['timestamp'] = datetime.now().isoformat()
        evaluation['session'] = self.current_session
        
        # 세션 캐시에 추가
        self.current_session_evaluations.append(evaluation)
        
        # 1. 세션별 평가 파일에 저장
        session_evaluations_file = os.path.join(self.evaluations_path, "session_evaluations.json")
        
        existing_evaluations = []
        if os.path.exists(session_evaluations_file):
            try:
                with open(session_evaluations_file, 'r', encoding='utf-8') as f:
                    existing_evaluations = json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ 세션 평가 파일 손상. 새 파일 생성합니다.")
        
        existing_evaluations.append(evaluation)
        
        with open(session_evaluations_file, 'w', encoding='utf-8') as f:
            json.dump(existing_evaluations, f, ensure_ascii=False, indent=2)
        
        # 2. 통합 파일에도 저장
        self._save_to_aggregated(evaluation)
        
        print(f"✅ 평가 데이터 저장 완료 (세션: {self.current_session})")
        
        # 3. correction이 있으면 별도 처리
        if evaluation.get('avg_score', 0) >= 4 and evaluation.get('correction'):
            self._handle_correction(evaluation)
    
    def _save_to_aggregated(self, evaluation: Dict):
        """통합 파일에 평가 저장"""
        aggregated_file = os.path.join(self.aggregated_path, 'all_evaluations.json')
        
        existing_evaluations = []
        if os.path.exists(aggregated_file):
            try:
                with open(aggregated_file, 'r', encoding='utf-8') as f:
                    existing_evaluations = json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ 통합 평가 파일 손상. 새 파일 생성합니다.")
        
        existing_evaluations.append(evaluation)
        
        with open(aggregated_file, 'w', encoding='utf-8') as f:
            json.dump(existing_evaluations, f, ensure_ascii=False, indent=2)
    
    def _handle_correction(self, evaluation: Dict):
        """correction 처리 (세션별 + 통합) - 원본 로직 유지"""
        if not evaluation.get('correction'):
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        correction_data = {
            'question': evaluation['question'],
            'original_response': evaluation['answer'],
            'corrected_response': evaluation['correction'],
            'scores': evaluation['scores'],
            'feedback': evaluation['feedback'],
            'avg_score': evaluation['avg_score'],
            'timestamp': evaluation['timestamp'],
            'session': self.current_session
        }
        
        # 1. 세션별 correction 저장 (개별 파일)
        session_correction_file = os.path.join(self.corrections_path, f"correction_{timestamp}.json")
        with open(session_correction_file, 'w', encoding='utf-8') as f:
            json.dump(correction_data, f, ensure_ascii=False, indent=2)
        
        # 2. 통합 corrections에도 저장
        aggregated_corrections_file = os.path.join(self.aggregated_path, 'all_corrections.json')
        
        existing_corrections = []
        if os.path.exists(aggregated_corrections_file):
            try:
                with open(aggregated_corrections_file, 'r', encoding='utf-8') as f:
                    existing_corrections = json.load(f)
            except json.JSONDecodeError:
                print("⚠️ all_corrections.json 파일 손상. 새로 생성합니다.")
        
        existing_corrections.append(correction_data)
        
        with open(aggregated_corrections_file, 'w', encoding='utf-8') as f:
            json.dump(existing_corrections, f, ensure_ascii=False, indent=2)
    
    def save_session(self):
        """현재 세션 요약 저장"""
        if not self.current_session_evaluations:
            print("저장할 세션 데이터가 없습니다.")
            return
        
        # 세션 요약 생성
        session_summary = {
            'session_id': self.current_session,
            'session_date': datetime.now().isoformat(),
            'total_evaluations': len(self.current_session_evaluations),
            'avg_score': sum(e.get('avg_score', 0) for e in self.current_session_evaluations) / len(self.current_session_evaluations),
            'score_distribution': self._calculate_score_distribution(),
            'corrections_count': len([e for e in self.current_session_evaluations if e.get('correction')]),
            'evaluations': self.current_session_evaluations
        }
        
        # 세션 요약 저장
        summary_file = os.path.join(self.session_dir, 'session_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(session_summary, f, ensure_ascii=False, indent=2)
        
        # 통합 세션 요약에도 저장
        summaries_file = os.path.join(self.aggregated_path, "session_summaries.json")
        
        existing_summaries = []
        if os.path.exists(summaries_file):
            try:
                with open(summaries_file, 'r', encoding='utf-8') as f:
                    existing_summaries = json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ 손상된 세션 요약 파일 발견. 새 파일 생성합니다.")
        
        existing_summaries.append(session_summary)
        
        with open(summaries_file, 'w', encoding='utf-8') as f:
            json.dump(existing_summaries, f, ensure_ascii=False, indent=2)
        
        # 세션 인덱스 업데이트
        self._update_session_index(session_summary)
        
        print(f"✅ 세션 요약 저장 완료: {self.current_session}")
        print(f"   - 총 평가: {session_summary['total_evaluations']}개")
        print(f"   - 평균 점수: {session_summary['avg_score']:.1f}/10")
        print(f"   - Corrections: {session_summary['corrections_count']}개")
    
    def _calculate_score_distribution(self) -> Dict:
        """점수 분포 계산"""
        scores = [e.get('avg_score', 0) for e in self.current_session_evaluations]
        
        return {
            'excellent': len([s for s in scores if s >= 8]),
            'good': len([s for s in scores if 6 <= s < 8]),
            'poor': len([s for s in scores if 4 <= s < 6]),
            'very_poor': len([s for s in scores if s < 4])
        }
    
    def _update_session_index(self, session_summary: Dict):
        """세션 인덱스 업데이트"""
        index_file = os.path.join(self.aggregated_path, 'session_index.json')
        
        existing_index = []
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    existing_index = json.load(f)
            except json.JSONDecodeError:
                existing_index = []
        
        # 기존 세션 정보 업데이트 또는 새로 추가
        session_info = {
            'session_id': session_summary['session_id'],
            'date': session_summary['session_date'],
            'total_evaluations': session_summary['total_evaluations'],
            'avg_score': session_summary['avg_score'],
            'corrections_count': session_summary['corrections_count']
        }
        
        # 기존 세션 찾아서 업데이트
        updated = False
        for i, existing_session in enumerate(existing_index):
            if existing_session['session_id'] == session_summary['session_id']:
                existing_index[i] = session_info
                updated = True
                break
        
        if not updated:
            existing_index.append(session_info)
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(existing_index, f, ensure_ascii=False, indent=2)
    
    def get_low_score_evaluations(self, threshold: float = 7.0) -> List[Dict]:
        """
        낮은 점수의 평가 데이터 가져오기
        
        :param threshold: 점수 임계값
        :return: 낮은 점수의 평가 데이터 리스트
        """
        low_score_evals = []
        
        # 통합 평가 데이터 로드
        evaluations_file = os.path.join(self.aggregated_path, "all_evaluations.json")
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
        모든 수정 데이터 가져오기 (통합 파일에서)
        
        :return: 모든 수정 데이터 리스트
        """
        corrections = []
        
        # 통합 corrections 파일에서 로드
        all_corrections_file = os.path.join(self.aggregated_path, 'all_corrections.json')
        if os.path.exists(all_corrections_file):
            try:
                with open(all_corrections_file, 'r', encoding='utf-8') as f:
                    corrections = json.load(f)
            except Exception as e:
                print(f"통합 수정 데이터 로드 오류: {e}")
        
        return corrections
    
    def get_all_sessions(self) -> List[str]:
        """모든 세션 목록 반환"""
        if not os.path.exists(self.sessions_path):
            return []
        
        sessions = [d for d in os.listdir(self.sessions_path) 
                   if d.startswith('session_') and os.path.isdir(os.path.join(self.sessions_path, d))]
        
        return sorted(sessions)
    
    def show_session_stats(self):
        """세션 통계 표시"""
        sessions = self.get_all_sessions()
        
        if not sessions:
            print("📊 세션 데이터가 없습니다.")
            return
        
        print(f"\n📊 세션 통계 (총 {len(sessions)}개 세션):")
        
        index_file = os.path.join(self.aggregated_path, 'session_index.json')
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    session_index = json.load(f)
                
                for session in session_index:
                    print(f"  📁 {session['session_id']}")
                    print(f"     평가: {session['total_evaluations']}개, 평균: {session['avg_score']:.1f}/10, 수정: {session['corrections_count']}개")
                    
            except Exception as e:
                print(f"세션 인덱스 로드 오류: {e}")
    
    def generate_improvement_report(self, output_path: Optional[str] = None) -> Dict:
        """
        개선 리포트 생성
        
        :param output_path: 출력 파일 경로 (없으면 저장하지 않음)
        :return: 리포트 데이터
        """
        # 모든 평가 데이터 로드 (통합 파일에서)
        all_evaluations = []
        evaluations_file = os.path.join(self.aggregated_path, "all_evaluations.json")
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
                'correction_count': len(all_corrections),
                'total_sessions': len(self.get_all_sessions())
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
    
    # 세션 통계 표시
    evaluator.show_session_stats()
    
    # 개선 리포트 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(evaluator.aggregated_path, f"improvement_report_{timestamp}.json")
    report = evaluator.generate_improvement_report(report_path)
    
    print("\n📊 개선 리포트 요약:")
    print(f"총 평가: {report['statistics']['total_evaluations']}개")
    print(f"평균 점수: {report['statistics']['average_score']:.2f}/10")
    print(f"개선 필요: {report['statistics']['low_score_count']}개")
    print(f"총 세션: {report['statistics']['total_sessions']}개")

if __name__ == "__main__":
    main()
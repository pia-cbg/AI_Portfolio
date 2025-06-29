import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

class FineTuningEvaluator:
    def __init__(self, base_path: str = 'data/fine_tuning'):
        """
        파인튜닝 평가 시스템 초기화
        
        :param base_path: 파인튜닝 데이터 저장 경로
        """
        self.base_path = base_path
        self.phase2_path = os.path.join(base_path, 'phase2_model_training')
        self.evaluations_path = os.path.join(self.phase2_path, 'evaluations')
        self.corrections_path = os.path.join(self.phase2_path, 'corrections')
        
        # 디렉토리 생성
        self._create_directories()
        
        # 평가 기준 로드
        self.evaluation_criteria = self._load_evaluation_criteria()
        
        # 현재 세션 데이터
        self.current_session = {
            'start_time': datetime.now().isoformat(),
            'evaluations': [],
            'corrections': []
        }
    
    def _create_directories(self):
        """필요한 디렉토리 생성"""
        for path in [self.evaluations_path, self.corrections_path]:
            os.makedirs(path, exist_ok=True)
    
    def _load_evaluation_criteria(self) -> List[Dict]:
        """답변 평가 기준 로드"""
        criteria_path = os.path.join(self.phase2_path, 'answer_criteria.json')
        
        if os.path.exists(criteria_path):
            with open(criteria_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 기본 답변 평가 기준
            default_criteria = [
                {
                    "key": "accuracy",
                    "name": "정확성",
                    "description": "음악 이론적으로 정확한 정보를 제공하는가"
                },
                {
                    "key": "completeness",
                    "name": "완전성",
                    "description": "질문에 대해 충분히 포괄적으로 답변했는가"
                },
                {
                    "key": "clarity",
                    "name": "명확성",
                    "description": "설명이 명확하고 이해하기 쉬운가"
                },
                {
                    "key": "relevance",
                    "name": "관련성",
                    "description": "질문에 직접적으로 관련된 답변인가"
                },
                {
                    "key": "examples",
                    "name": "예시의 적절성",
                    "description": "적절한 음악적 예시를 제공했는가"
                }
            ]
            
            # 저장
            with open(criteria_path, 'w', encoding='utf-8') as f:
                json.dump(default_criteria, f, ensure_ascii=False, indent=2)
            
            return default_criteria
    
    def evaluate_answer(self, question: str, answer: str, sources: List[Dict]) -> Dict:
        """
        단일 답변에 대한 평가 수집
        
        :param question: 질문
        :param answer: 모델의 답변
        :param sources: 참고자료
        :return: 평가 결과
        """
        print(f"\n{'='*60}")
        print(f"📋 답변 평가")
        print(f"{'='*60}")
        print(f"질문: {question}")
        print(f"\n답변:\n{answer}")
        
        # 참고자료 출력
        if sources:
            print(f"\n📚 참고자료:")
            for i, source in enumerate(sources, 1):
                print(f"{i}. {source.get('title', '제목 없음')} (유사도: {source.get('score', 0):.3f})")
                content = source.get('content', '')
                print(f"   {content[:100]}...")
        
        print(f"\n{'='*60}")
        
        # 평가 점수 수집
        scores = {}
        for criterion in self.evaluation_criteria:
            print(f"\n{criterion['name']} - {criterion['description']}")
            while True:
                try:
                    score = int(input(f"점수 (0-10): "))
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
        
        # 상세 피드백
        feedback = input("\n상세 피드백 (문제점, 개선사항): ")
        
        # 수정 제안
        correction = ""
        if avg_score < 7:
            print("\n⚠️ 개선이 필요한 답변입니다.")
            correction = input("수정된 답변 제안 (선택사항): ")
        
        # 평가 데이터 구성
        evaluation = {
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'answer': answer,
            'sources': sources,
            'scores': scores,
            'avg_score': avg_score,
            'feedback': feedback,
            'correction': correction,
            'needs_improvement': avg_score < 7
        }
        
        return evaluation
    
    def save_evaluation(self, evaluation: Dict):
        """평가 결과 저장"""
        # 세션 데이터에 추가
        self.current_session['evaluations'].append(evaluation)
        
        # 개별 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluation_{timestamp}.json"
        filepath = os.path.join(self.evaluations_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(evaluation, f, ensure_ascii=False, indent=2)
        
        # 개선이 필요한 경우 수정 데이터 저장
        if evaluation.get('needs_improvement') and evaluation.get('correction'):
            self._save_correction(evaluation)
        
        print(f"✅ 평가 저장 완료: {filename}")
    
    def _save_correction(self, evaluation: Dict):
        """수정 데이터 저장"""
        correction_data = {
            'timestamp': evaluation['timestamp'],
            'question': evaluation['question'],
            'original_answer': evaluation['answer'],
            'corrected_answer': evaluation['correction'],
            'scores': evaluation['scores'],
            'feedback': evaluation['feedback']
        }
        
        # 세션 데이터에 추가
        self.current_session['corrections'].append(correction_data)
        
        # 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"correction_{timestamp}.json"
        filepath = os.path.join(self.corrections_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(correction_data, f, ensure_ascii=False, indent=2)
    
    def save_session(self):
        """현재 세션 저장"""
        if not self.current_session['evaluations']:
            print("저장할 평가 데이터가 없습니다.")
            return
        
        # 세션 요약 계산
        evaluations = self.current_session['evaluations']
        session_summary = {
            'session_info': {
                'start_time': self.current_session['start_time'],
                'end_time': datetime.now().isoformat(),
                'total_evaluations': len(evaluations),
                'total_corrections': len(self.current_session['corrections'])
            },
            'statistics': self._calculate_session_stats(evaluations),
            'evaluations': evaluations,
            'corrections': self.current_session['corrections']
        }
        
        # 세션 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_{timestamp}.json"
        filepath = os.path.join(self.phase2_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_summary, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 세션 저장 완료: {filename}")
        self._print_session_summary(session_summary['statistics'])
    
    def _calculate_session_stats(self, evaluations: List[Dict]) -> Dict:
        """세션 통계 계산"""
        if not evaluations:
            return {}
        
        # 기본 통계
        total_count = len(evaluations)
        avg_overall = sum(e['avg_score'] for e in evaluations) / total_count
        
        # 기준별 평균
        criteria_averages = {}
        for criterion in self.evaluation_criteria:
            key = criterion['key']
            scores = [e['scores'][key] for e in evaluations if key in e['scores']]
            if scores:
                criteria_averages[criterion['name']] = sum(scores) / len(scores)
        
        # 품질 분포
        excellent = len([e for e in evaluations if e['avg_score'] >= 8])
        good = len([e for e in evaluations if 6 <= e['avg_score'] < 8])
        poor = len([e for e in evaluations if e['avg_score'] < 6])
        
        return {
            'total_evaluations': total_count,
            'avg_overall_score': avg_overall,
            'criteria_averages': criteria_averages,
            'quality_distribution': {
                'excellent': {'count': excellent, 'percentage': excellent/total_count*100},
                'good': {'count': good, 'percentage': good/total_count*100},
                'poor': {'count': poor, 'percentage': poor/total_count*100}
            }
        }
    
    def _print_session_summary(self, stats: Dict):
        """세션 요약 출력"""
        print("\n" + "="*60)
        print("📊 Phase 2 평가 세션 요약")
        print("="*60)
        
        print(f"총 평가 수: {stats['total_evaluations']}")
        print(f"전체 평균: {stats['avg_overall_score']:.2f}/10")
        
        print("\n기준별 평균:")
        for criterion, avg in stats['criteria_averages'].items():
            print(f"  - {criterion}: {avg:.2f}/10")
        
        print("\n품질 분포:")
        dist = stats['quality_distribution']
        print(f"  - 우수 (8점 이상): {dist['excellent']['count']}개 ({dist['excellent']['percentage']:.1f}%)")
        print(f"  - 양호 (6-8점): {dist['good']['count']}개 ({dist['good']['percentage']:.1f}%)")
        print(f"  - 개선 필요 (6점 미만): {dist['poor']['count']}개 ({dist['poor']['percentage']:.1f}%)")
    
    def load_corrections(self) -> List[Dict]:
        """저장된 수정 데이터 로드"""
        corrections = []
        
        if not os.path.exists(self.corrections_path):
            return corrections
        
        for filename in os.listdir(self.corrections_path):
            if filename.startswith('correction_') and filename.endswith('.json'):
                filepath = os.path.join(self.corrections_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        corrections.append(json.load(f))
                except Exception as e:
                    print(f"수정 데이터 로드 오류 ({filename}): {e}")
        
        return sorted(corrections, key=lambda x: x.get('timestamp', ''))
    
    def generate_improvement_report(self) -> Dict:
        """개선 리포트 생성"""
        corrections = self.load_corrections()
        
        if not corrections:
            return {"message": "개선 데이터가 없습니다."}
        
        # 공통 문제점 분석
        common_issues = self._analyze_common_issues(corrections)
        
        # 개선 제안 생성
        suggestions = self._generate_improvement_suggestions(corrections)
        
        report = {
            'report_date': datetime.now().isoformat(),
            'total_corrections': len(corrections),
            'common_issues': common_issues,
            'improvement_suggestions': suggestions,
            'correction_details': corrections
        }
        
        # 리포트 저장
        report_path = os.path.join(self.phase2_path, 'improvement_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 개선 리포트 생성: {report_path}")
        return report
    
    def _analyze_common_issues(self, corrections: List[Dict]) -> Dict:
        """공통 문제점 분석"""
        # 낮은 점수 기준 분석
        low_criteria = {}
        
        for correction in corrections:
            scores = correction.get('scores', {})
            for criterion, score in scores.items():
                if score < 7:
                    low_criteria[criterion] = low_criteria.get(criterion, 0) + 1
        
        # 피드백 키워드 분석
        feedback_keywords = {}
        for correction in corrections:
            feedback = correction.get('feedback', '').lower()
            # 간단한 키워드 추출
            keywords = ['부정확', '불완전', '불명확', '예시', '설명']
            for keyword in keywords:
                if keyword in feedback:
                    feedback_keywords[keyword] = feedback_keywords.get(keyword, 0) + 1
        
        return {
            'low_score_criteria': low_criteria,
            'feedback_keywords': feedback_keywords
        }
    
    def _generate_improvement_suggestions(self, corrections: List[Dict]) -> List[str]:
        """개선 제안 생성"""
        suggestions = []
        
        # 분석 결과 기반 제안
        common_issues = self._analyze_common_issues(corrections)
        
        low_criteria = common_issues['low_criteria']
        if 'accuracy' in low_criteria:
            suggestions.append("음악 이론 정확성 향상이 필요합니다.")
        
        if 'examples' in low_criteria:
            suggestions.append("구체적인 음악 예시 추가가 필요합니다.")
        
        if 'clarity' in low_criteria:
            suggestions.append("더 명확하고 이해하기 쉬운 설명이 필요합니다.")
        
        return suggestions

def main():
    """평가기 테스트"""
    evaluator = FineTuningEvaluator()
    
    # 샘플 평가
    sample_question = "세컨더리 도미넌트란 무엇인가?"
    sample_answer = "세컨더리 도미넌트는 조성 내에서 다른 화음으로의 일시적 전조를 만드는 도미넌트 화음입니다."
    sample_sources = []
    
    evaluation = evaluator.evaluate_answer(sample_question, sample_answer, sample_sources)
    evaluator.save_evaluation
import json
import os
from datetime import datetime
from typing import Dict, List
import pandas as pd

class Evaluator:
    def __init__(self, base_path='data/fine_tuning'):
        """
        평가 데이터 관리 시스템 초기화
        
        :param base_path: 파인튜닝 데이터 저장 경로
        """
        self.base_path = base_path
        self.evaluations_path = os.path.join(base_path, 'evaluations')
        self.corrections_path = os.path.join(base_path, 'corrections')
        self.keywords_path = os.path.join(base_path, 'keywords')
        
        # 디렉토리 생성
        self._create_directories()
        
        # 평가 데이터 캐시
        self.current_session_evaluations = []
    
    def _create_directories(self):
        """
        필요한 디렉토리 생성
        """
        for path in [self.evaluations_path, self.corrections_path, self.keywords_path]:
            os.makedirs(path, exist_ok=True)
    
    def save_evaluation(self, evaluation_data: Dict):
        """
        평가 데이터 저장
        
        :param evaluation_data: 평가 데이터
        """
        # 타임스탬프 추가
        evaluation_data['timestamp'] = datetime.now().isoformat()
        
        # 세션 캐시에 추가
        self.current_session_evaluations.append(evaluation_data)
        
        # 개별 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eval_{timestamp}_{len(self.current_session_evaluations)}.json"
        filepath = os.path.join(self.evaluations_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(evaluation_data, f, ensure_ascii=False, indent=2)
        
        # 낮은 점수 평가는 별도로 처리
        if evaluation_data.get('avg_score', 0) < 7:
            self._handle_low_score_evaluation(evaluation_data)
        
        print(f"✅ 평가 데이터 저장 완료: {filename}")
    
    def _handle_low_score_evaluation(self, evaluation_data: Dict):
        """
        낮은 점수 평가 처리
        
        :param evaluation_data: 평가 데이터
        """
        # 수정이 필요한 경우 corrections 폴더에 저장
        if evaluation_data.get('correction'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"correction_{timestamp}.json"
            filepath = os.path.join(self.corrections_path, filename)
            
            correction_data = {
                'question': evaluation_data['question'],
                'original_response': evaluation_data['response'],
                'corrected_response': evaluation_data['correction'],
                'scores': evaluation_data['scores'],
                'feedback': evaluation_data['feedback'],
                'timestamp': evaluation_data['timestamp']
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(correction_data, f, ensure_ascii=False, indent=2)
    
    def save_session_summary(self):
        """
        현재 세션의 전체 평가 요약 저장
        """
        if not self.current_session_evaluations:
            print("저장할 평가 데이터가 없습니다.")
            return
        
        # 세션 요약 생성
        session_summary = {
            'session_date': datetime.now().isoformat(),
            'total_evaluations': len(self.current_session_evaluations),
            'avg_score': sum(e['avg_score'] for e in self.current_session_evaluations) / len(self.current_session_evaluations),
            'criteria_averages': self._calculate_criteria_averages(),
            'low_score_questions': self._get_low_score_questions(),
            'evaluations': self.current_session_evaluations
        }
        
        # 요약 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_summary_{timestamp}.json"
        filepath = os.path.join(self.evaluations_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_summary, f, ensure_ascii=False, indent=2)
        
        print(f"📊 세션 요약 저장 완료: {filename}")
    
    def _calculate_criteria_averages(self) -> Dict[str, float]:
        """
        기준별 평균 점수 계산
        
        :return: 기준별 평균 점수
        """
        criteria = ['accuracy', 'completeness', 'clarity', 'expertise', 'practicality']
        averages = {}
        
        for criterion in criteria:
            scores = [e['scores'][criterion] for e in self.current_session_evaluations]
            averages[criterion] = sum(scores) / len(scores) if scores else 0
        
        return averages
    
    def _get_low_score_questions(self) -> List[Dict]:
        """
        낮은 점수를 받은 질문들 추출
        
        :return: 낮은 점수 질문 리스트
        """
        return [
            {
                'question': e['question'],
                'avg_score': e['avg_score'],
                'feedback': e['feedback']
            }
            for e in self.current_session_evaluations
            if e['avg_score'] < 7
        ]
    
    def load_evaluation_history(self, limit: int = 10) -> List[Dict]:
        """
        과거 평가 이력 로드
        
        :param limit: 로드할 평가 수
        :return: 평가 데이터 리스트
        """
        evaluations = []
        
        # 모든 평가 파일 로드
        eval_files = sorted(
            [f for f in os.listdir(self.evaluations_path) if f.startswith('eval_')],
            reverse=True
        )[:limit]
        
        for filename in eval_files:
            filepath = os.path.join(self.evaluations_path, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                evaluations.append(json.load(f))
        
        return evaluations
    
    def generate_improvement_report(self):
        """
        모델 개선을 위한 리포트 생성
        """
        # 모든 수정 데이터 로드
        corrections = []
        for filename in os.listdir(self.corrections_path):
            if filename.startswith('correction_'):
                filepath = os.path.join(self.corrections_path, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    corrections.append(json.load(f))
        
        if not corrections:
            print("수정 데이터가 없습니다.")
            return
        
        # 리포트 생성
        report = {
            'report_date': datetime.now().isoformat(),
            'total_corrections': len(corrections),
            'common_issues': self._analyze_common_issues(corrections),
            'improvement_suggestions': self._generate_suggestions(corrections),
            'corrections': corrections
        }
        
        # 리포트 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"improvement_report_{timestamp}.json"
        filepath = os.path.join(self.base_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 개선 리포트 생성 완료: {filename}")
    
    def _analyze_common_issues(self, corrections: List[Dict]) -> Dict:
        """
        공통 문제점 분석
        
        :param corrections: 수정 데이터 리스트
        :return: 공통 문제점 분석 결과
        """
        # 낮은 점수를 받은 기준들 분석
        low_score_criteria = {}
        
        for correction in corrections:
            scores = correction.get('scores', {})
            for criterion, score in scores.items():
                if score < 7:
                    low_score_criteria[criterion] = low_score_criteria.get(criterion, 0) + 1
        
        return low_score_criteria
    
    def _generate_suggestions(self, corrections: List[Dict]) -> List[str]:
        """
        개선 제안사항 생성
        
        :param corrections: 수정 데이터 리스트
        :return: 개선 제안사항 리스트
        """
        suggestions = []
        
        # 피드백 분석
        feedbacks = [c.get('feedback', '') for c in corrections if c.get('feedback')]
        
        # 키워드 기반 제안
        if any('용어' in f for f in feedbacks):
            suggestions.append("음악 이론 용어 사용의 정확성 개선 필요")
        
        if any('예시' in f for f in feedbacks):
            suggestions.append("구체적인 예시 추가 필요")
        
        if any('설명' in f for f in feedbacks):
            suggestions.append("더 명확하고 상세한 설명 필요")
        
        return suggestions

def main():
    # 테스트용
    evaluator = Evaluator()
    
    # 샘플 평가 데이터
    sample_evaluation = {
        'question': '세컨더리 도미넌트란 무엇인가?',
        'response': '세컨더리 도미넌트는...',
        'sources': [],
        'scores': {
            'accuracy': 8,
            'completeness': 7,
            'clarity': 9,
            'expertise': 8,
            'practicality': 7
        },
        'feedback': '더 구체적인 예시가 필요합니다.',
        'correction': '',
        'avg_score': 7.8
    }
    
    # 평가 저장
    evaluator.save_evaluation(sample_evaluation)
    evaluator.save_session_summary()
    evaluator.generate_improvement_report()

if __name__ == "__main__":
    main()
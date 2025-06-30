"""
데이터 갭 분석 및 확장 추천 도구
"""
import json
import os
from collections import Counter
from typing import List, Dict, Tuple
from datetime import datetime

class GapAnalyzer:
    def __init__(self):
        """갭 분석기 초기화"""
        self.gaps_dir = 'data/fine_tuning/gaps'
        self.raw_data_path = 'data/raw/music_theory_curriculum.json'
        
    def analyze_all_gaps(self) -> Dict:
        """모든 갭 리포트 종합 분석"""
        all_gaps = []
        
        # 모든 갭 리포트 로드
        if os.path.exists(self.gaps_dir):
            for filename in os.listdir(self.gaps_dir):
                if filename.startswith('gap_report_'):
                    with open(os.path.join(self.gaps_dir, filename), 'r') as f:
                        report = json.load(f)
                        all_gaps.extend(report['gaps'])
        
        # 분석
        analysis = {
            'total_gaps': len(all_gaps),
            'by_type': Counter(gap['type'] for gap in all_gaps),
            'frequent_topics': self._analyze_topics(all_gaps),
            'missing_terms': self._analyze_terms(all_gaps),
            'recommendations': self._generate_recommendations(all_gaps)
        }
        
        return analysis
    
    def _analyze_topics(self, gaps: List[Dict]) -> List[Tuple[str, int]]:
        """자주 요청된 주제 분석"""
        topic_counter = Counter()
        
        for gap in gaps:
            query = gap.get('query', '').lower()
            # 간단한 토픽 추출
            if '도미넌트' in query:
                topic_counter['dominant'] += 1
            if '스케일' in query or '음계' in query:
                topic_counter['scales'] += 1
            if '코드' in query or '화음' in query:
                topic_counter['chords'] += 1
            if '진행' in query:
                topic_counter['progression'] += 1
                
        return topic_counter.most_common(10)
    
    def _analyze_terms(self, gaps: List[Dict]) -> List[Tuple[str, int]]:
        """누락된 음악 용어 분석"""
        term_counter = Counter()
        
        for gap in gaps:
            terms = gap.get('musical_terms', [])
            term_counter.update(terms)
            
        return term_counter.most_common(20)
    
    def _generate_recommendations(self, gaps: List[Dict]) -> List[Dict]:
        """데이터셋 확장 추천"""
        recommendations = []
        
        # 타입별 추천
        gap_types = Counter(gap['type'] for gap in gaps)
        
        if gap_types['no_coverage'] > 5:
            recommendations.append({
                'priority': 'high',
                'action': 'add_new_topics',
                'description': f"{gap_types['no_coverage']}개의 완전히 누락된 주제 추가 필요",
                'topics': self._get_missing_topics(gaps)
            })
        
        if gap_types['partial_coverage'] > 10:
            recommendations.append({
                'priority': 'medium',
                'action': 'expand_existing',
                'description': f"{gap_types['partial_coverage']}개의 부분적 주제 확장 필요",
                'topics': self._get_partial_topics(gaps)
            })
        
        return recommendations
    
    def _get_missing_topics(self, gaps: List[Dict]) -> List[str]:
        """완전히 누락된 주제들"""
        return list(set(
            gap['query'] for gap in gaps 
            if gap['type'] == 'no_coverage'
        ))[:10]
    
    def _get_partial_topics(self, gaps: List[Dict]) -> List[str]:
        """부분적으로만 다뤄진 주제들"""
        return list(set(
            gap['query'] for gap in gaps 
            if gap['type'] == 'partial_coverage'
        ))[:10]
    
    def generate_expansion_template(self, topic: str) -> Dict:
        """주제별 확장 템플릿 생성"""
        return {
            'title': topic,
            'definition': f"{topic}의 정의",
            'theoretical_structure': f"{topic}의 이론적 구조",
            'harmonic_function': f"{topic}의 화성적 기능",
            'voice_leading': f"{topic}의 성부 진행",
            'practical_usage': f"{topic}의 실제 활용",
            'related_concepts': f"{topic}와 관련된 개념들"
        }
    
    def save_analysis_report(self):
        """분석 리포트 저장"""
        analysis = self.analyze_all_gaps()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'data/fine_tuning/gap_analysis_{timestamp}.json'
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 갭 분석 리포트 저장: {filename}")
        
        # 요약 출력
        print("\n📊 갭 분석 요약:")
        print(f"  - 총 갭: {analysis['total_gaps']}")
        print(f"  - 완전 누락: {analysis['by_type'].get('no_coverage', 0)}")
        print(f"  - 부분 누락: {analysis['by_type'].get('partial_coverage', 0)}")
        
        print("\n🎯 우선 추가할 주제:")
        for topic, count in analysis['frequent_topics'][:5]:
            print(f"  - {topic}: {count}회 요청")

def main():
    analyzer = GapAnalyzer()
    analyzer.save_analysis_report()

if __name__ == "__main__":
    main()
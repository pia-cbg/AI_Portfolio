import os
import sys
import json
from typing import Dict, List
from datetime import datetime
from dotenv import load_dotenv
import openai

# 프로젝트 루트 경로 및 .env 설정
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

openai.api_key = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

from utils.music_utils import extract_musical_terms, format_chord_name

class RAGModel:
    def __init__(self, retriever, model_name: str = DEFAULT_MODEL, min_similarity_score: float = 0.7):
        self.retriever = retriever
        self.model_name = model_name
        self.min_similarity_score = min_similarity_score
        self.session_gaps = []
        self.stats = {
            'total_queries': 0,
            'successful_answers': 0,
            'partial_answers': 0,
            'no_data_answers': 0
        }

    def get_conversation_response(self, query: str) -> Dict:
        self.stats['total_queries'] += 1
        musical_terms = extract_musical_terms(query)

        try:
            sources = self.retriever.search(query, top_k=5) if self.retriever else []

            high_quality = [s for s in sources if s.get('score', 0) >= self.min_similarity_score]
            medium_quality = [s for s in sources if 0.5 <= s.get('score', 0) < self.min_similarity_score]

            if high_quality:
                return self._generate_complete_response(query, high_quality, musical_terms)
            elif medium_quality:
                return self._generate_partial_response(query, medium_quality, musical_terms)
            else:
                return self._generate_no_data_response(query, musical_terms)

        except Exception as e:
            return self._create_error_response(f"오류: {e}")
        
    def _generate_complete_response(self, query: str, sources: List[Dict], musical_terms: List[str]) -> Dict:
        """충분한 데이터가 있을 때 응답 생성"""
        sources_text = self._format_sources_for_prompt(sources)

        prompt = f"""
당신은 음악 이론 교육 시스템의 AI 어시스턴트입니다.

사용자 질문: {query}

참고자료:
{sources_text}

위 참고자료만을 사용하여 질문에 답변하세요.
각 정보마다 [참고자료 번호]를 표시하세요.
참고자료에 없는 내용은 절대 추가하지 마세요.
        """

        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )

            answer = response.choices[0].message.content.strip()

            self.stats['successful_answers'] += 1

            return {
                'answer': answer,
                'sources': sources,
                'model': self.model_name,
                'musical_terms': musical_terms,
                'confidence': 'high',
                'data_coverage': 'complete'
            }
        except Exception as e:
            return self._create_error_response(f"API 호출 중 오류가 발생했습니다: {e}")

    def _generate_partial_response(self, query: str, sources: List[Dict], musical_terms: List[str]) -> Dict:
        """부분적 데이터가 있을 때 응답 생성"""
        answer = "참고자료에 일부 관련 정보가 있습니다. 그러나 충분한 데이터가 아닙니다.\n"
        answer += self._format_sources_for_prompt(sources)
        self.stats['partial_answers'] += 1

        return {
            'answer': answer,
            'sources': sources,
            'model': self.model_name,
            'musical_terms': musical_terms,
            'confidence': 'medium',
            'data_coverage': 'partial'
        }

    def _generate_no_data_response(self, query: str, musical_terms: List[str]) -> Dict:
        """데이터가 없을 때 응답 생성"""
        gap = {
            'query': query,
            'type': 'no_coverage',
            'musical_terms': musical_terms,
            'timestamp': datetime.now().isoformat()
        }
        self.session_gaps.append(gap)
        self.stats['no_data_answers'] += 1

        answer = f"""
죄송합니다. 현재 데이터셋에 "{query}"에 대한 정보가 없습니다.

🔍 감지된 음악 용어: {', '.join(musical_terms) if musical_terms else '없음'}

이 주제는 향후 데이터셋 확장 시 추가될 예정입니다.
다른 음악 이론 관련 질문을 해주시면 답변 가능 여부를 확인하겠습니다.
        """

        return {
            'answer': answer,
            'sources': [],
            'model': self.model_name,
            'musical_terms': musical_terms,
            'confidence': 'none',
            'data_coverage': 'none',
            'gap_recorded': True
        }

    def _format_sources_for_prompt(self, sources: List[Dict]) -> str:
        """프롬프트용 소스 포맷팅"""
        formatted = ""
        for idx, source in enumerate(sources, 1):
            title = source.get('title', '제목 없음')
            content = source.get('content', '내용 없음')
            score = source.get('score', 0)
            if len(content) > 500:
                content = content[:500] + "..."
            formatted += f"\n[참고자료 {idx}]\n"
            formatted += f"제목: {title}\n"
            formatted += f"내용: {content}\n"
            formatted += f"관련도: {score:.3f}\n"
            formatted += "-" * 40
        return formatted

    def _create_error_response(self, error_message: str) -> Dict:
        """에러 응답 생성"""
        return {
            'answer': f"시스템 오류: {error_message}",
            'sources': [],
            'model': self.model_name,
            'musical_terms': [],
            'confidence': 'error',
            'data_coverage': 'error'
        }

    def get_session_stats(self) -> Dict:
        """현재 세션 통계 반환"""
        return {
            'statistics': self.stats,
            'gaps_identified': len(self.session_gaps),
            'gap_details': self.session_gaps
        }
        
    def save_gaps_report(self, filename: str = None):
        """데이터 갭 리포트 저장"""
        if not self.session_gaps:
            print("기록된 갭이 없습니다.")
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'data/fine_tuning/gaps/gap_report_{timestamp}.json'

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        report = {
            'session_date': datetime.now().isoformat(),
            'statistics': self.stats,
            'total_gaps': len(self.session_gaps),
            'gaps': self.session_gaps
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"✅ 갭 리포트 저장: {filename}")
        print(f"   - 총 질문: {self.stats['total_queries']}")
        print(f"   - 완전 답변: {self.stats['successful_answers']}")
        print(f"   - 부분 답변: {self.stats['partial_answers']}")
        print(f"   - 답변 불가: {self.stats['no_data_answers']}")

def main():
    """RAG 모델 테스트"""
    try:
        from src.models.retriever import VectorRetriever
        retriever = VectorRetriever()

        print("검색기 초기화 중...")
        retriever.load_embeddings()
        retriever.build_index()

        rag_model = RAGModel(retriever)

        # 테스트 질문들
        test_queries = [
            "세컨더리 도미넌트란?",
            "12 equal temperament에 대해 설명해줘",
            "평균율과 순정률의 차이는?"
        ]

        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"질문: {query}")
            print('='*60)

            response = rag_model.get_conversation_response(query)

            print("\n답변:")
            print(response['answer'])
            print(f"\n신뢰도: {response['confidence']}")
            print(f"데이터 커버리지: {response['data_coverage']}")

        # 세션 통계 및 갭 리포트
        print("\n📊 세션 통계:")
        stats = rag_model.get_session_stats()
        print(json.dumps(stats['statistics'], indent=2))

        # 갭 리포트 저장
        rag_model.save_gaps_report()

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
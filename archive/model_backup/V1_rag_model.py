import os
import sys
import json
from typing import Dict, List
from datetime import datetime
import openai
from dotenv import load_dotenv, find_dotenv

# .env 파일을 상위 폴더에서 자동 탐색해서 로드
load_dotenv(find_dotenv())
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from utils.music_utils import extract_musical_terms

# system prompt import
from src.prompts.prompts import GROUNDING_SYSTEM_PROMPT

class RAGModel:
    def __init__(self, retriever, model_name: str = DEFAULT_MODEL, min_similarity_score: float = 0.7):
        self.retriever = retriever
        self.model_name = model_name
        self.min_similarity_score = min_similarity_score
        self.gap_logs = []  # gap 케이스 기록
        self.stats = {
            'total_queries': 0,
            'response_errors': 0,
            'gap_cases': 0
        }
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)

    def get_conversation_response(self, query: str) -> Dict:
        """모든 답변을 LLM이 reasoning. 필요시 gap 로그도 남김."""
        self.stats['total_queries'] += 1
        musical_terms = extract_musical_terms(query)

        try:
            sources = self.retriever.search(query, top_k=2) if self.retriever else []

            # gap(자료 없음) 여부 기록
            is_gap = len(sources) == 0 or all(s.get("score", 0) < self.min_similarity_score for s in sources)
            if is_gap:
                self.stats['gap_cases'] += 1
                self._log_gap_case(query, musical_terms)

            # 항상 LLM이 extrapolation/reasoning하게 넘김
            return self._generate_llm_response(query, sources, musical_terms)
        except Exception as e:
            self.stats['response_errors'] += 1
            return self._create_error_response(f"오류: {e}")

    def _generate_llm_response(self, query: str, sources: List[Dict], musical_terms: List[str]) -> Dict:
        """항상 LLM이 자료충분/불일치/부족/자료 없음 등 모두 reasoning하게 유도."""
        user_content = self._format_user_message(query, sources)
        try:
            chat = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": GROUNDING_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            answer = chat.choices[0].message.content.strip()
            return {
                'answer': answer,
                'sources': sources,
                'model': self.model_name,
                'musical_terms': musical_terms,
                'timestamp': datetime.now().isoformat(),
                'used_grounding_prompt': True
            }
        except Exception as e:
            self.stats['response_errors'] += 1
            return self._create_error_response(f"API 오류: {e}")

    def _format_sources_for_prompt(self, sources: List[Dict]) -> str:
        """
        여러 passage를 프롬프트용 block으로 포맷.
        - passage 최대 2개까지만 포함
        - 각 passage는 200자(또는 원하시는 자릿수) 이내로 잘라줌
        - 불필요한 타이틀/점수 등은 생략, 진짜 내용만
        """
        if not sources:
            return ""
        formatted = ""
        max_passage = 2    # 참고자료 최대 개수
        max_length = 150   # passage 별 최대 길이(자 수)
        for idx, source in enumerate(sources[:max_passage], 1):
            content = source.get('content', '내용 없음').strip()
            # 본문 길이 제한
            if len(content) > max_length:
                content = content[:max_length] + "..."
            # block format (title, score 등 생략)
            formatted += f"\n[참고자료 {idx}]\n내용: {content}\n"
            formatted += "-" * 32
        return formatted

    def _format_user_message(self, query: str, sources: List[Dict]) -> str:
        """질문 + 참고 passage를 묶어 user 프롬프트화"""
        sources_text = self._format_sources_for_prompt(sources)
        if sources_text.strip():
            return f"{query}\n\n참고자료:\n{sources_text}"
        else:
            return query

    def _log_gap_case(self, query: str, musical_terms: List[str]):
        """gap(근거 없음/불충분) 상황 기록(통계, DB 보강 용도)"""
        self.gap_logs.append({
            "query": query,
            "musical_terms": musical_terms,
            "timestamp": datetime.now().isoformat()
        })

    def save_gap_report(self, filename: str = None):
        """gap 케이스 리포트 저장(데이터셋 보강/운영진 피드백 용)"""
        if not self.gap_logs:
            print("gap 케이스가 없습니다.")
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'data/fine_tuning/gaps/gap_report_{timestamp}.json'

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.gap_logs, f, ensure_ascii=False, indent=2)
        print(f"✅ gap 리포트 저장: {filename} (총 {len(self.gap_logs)}건)")

    def _create_error_response(self, error_message: str) -> Dict:
        return {
            'answer': f"시스템 오류: {error_message}",
            'sources': [],
            'model': self.model_name,
            'musical_terms': [],
            'confidence': 'error',
            'data_coverage': 'error'
        }

    def get_session_stats(self) -> Dict:
        return {
            'statistics': self.stats,
            'gaps_logged': len(self.gap_logs)
        }


def main():
    try:
        from src.models.backup.V1_retriever import VectorRetriever
        retriever = VectorRetriever()

        print("검색기 초기화 중...")
        retriever.load_embeddings()
        retriever.build_index()

        rag_model = RAGModel(retriever)

        # 다양한 테스트 질문
        test_queries = [
            "세컨더리 도미넌트란?",
            "12 equal temperament에 대해 설명해줘",
            "평균율과 순정률의 차이는?",
            "Abm7(b5)는 어떻게 표기하는거야?"  # 일부러 자료 없을법한 질의
        ]

        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"질문: {query}")
            print('='*60)

            response = rag_model.get_conversation_response(query)

            print("\n[답변]")
            print(response['answer'])
            print(f"\n[참고 passage 개수]: {len(response['sources'])}")
            print(f"[모델]: {response['model']}")
            print(f"[타임스탬프]: {response['timestamp']}")

        # 세션 통계 및 gap 리포트 저장
        print("\n📊 세션 통계 및 gap 로그:")
        stats = rag_model.get_session_stats()
        print(json.dumps(stats, indent=2))
        rag_model.save_gap_report()

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
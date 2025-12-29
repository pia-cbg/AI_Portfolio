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
from src.prompts.prompts import GROUNDING_SYSTEM_PROMPT

class RAGModel:
    def __init__(self, retriever, model_name: str = DEFAULT_MODEL, min_similarity_score: float = 0.7):
        self.retriever = retriever
        self.model_name = model_name
        self.min_similarity_score = min_similarity_score
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)

    def get_conversation_response(self, query: str) -> Dict:
        """LLM이 reasoning, 필요시 error만 리턴(gap 기능 제거)."""
        # self.stats['total_queries'] += 1
        musical_terms = extract_musical_terms(query)

        try:
            sources = self.retriever.search(query, top_k=2) if self.retriever else []

            return self._generate_llm_response(query, sources, musical_terms)
        except Exception as e:
            return self._create_error_response(f"오류: {e}")

    def _generate_llm_response(self, query: str, sources: List[Dict], musical_terms: List[str]) -> Dict:
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
            # self.stats['response_errors'] += 1
            return self._create_error_response(f"API 오류: {e}")

    def _format_sources_for_prompt(self, sources: List[Dict]) -> str:
        if not sources:
            return ""
        formatted = ""
        max_passage = 2
        max_length = 300     # 정의, 원리, 예시까지 감당할 수 있게 더 확대
        for idx, source in enumerate(sources[:max_passage], 1):
            concept_ko = source.get('concept.ko', '')
            concept_en = source.get('concept.en', '')
            aliases = source.get('aliases', '')
            definition = source.get('definition', '')
            logic = source.get('logic', '')
            example_name = source.get('examples.name', '')
            example_desc = source.get('examples.description', '')
            tips = source.get('tips', '')

            definition = (definition[:max_length] + "...") if len(definition) > max_length else definition
            logic = (logic[:max_length] + "...") if len(logic) > max_length else logic

            formatted += (
                f"\n[참고자료 {idx}]\n"
                f"용어(한글): {concept_ko}\n"
                f"용어(영문): {concept_en}\n"
                f"동의어·유사 표기: {aliases}\n"
                f"[정의]: {definition}\n"
                f"[원리]: {logic}\n"
            )
            if example_name:
                formatted += f"예시: {example_name}\n"
                if example_desc:
                    formatted += f"예시 설명: {example_desc}\n"
            if tips:
                formatted += f"[팁]: {tips}\n"
            formatted += "-"*28
        return formatted

    def _format_user_message(self, query: str, sources: List[Dict]) -> str:
        sources_text = self._format_sources_for_prompt(sources)
        # 디버깅용 print 모두 제거 (실서비스에선 비추)
        if sources_text.strip():
            return (
                f"질문: {query}\n\n"
                "아래 참고자료의 [정의]와 [원리]를 반드시 포함해서 답하세요. "
                "참고자료에 없는 용어나 잘못된 정보를 임의로 생성하지 마세요. "
                "정의/원리가 제대로 없는 경우에만 '자료 부족'임을 밝혀주세요.\n"
                f"{sources_text}"
            )
        else:
            return (
                f"질문: {query}\n"
                "참고자료가 없어 자세한 정보를 제공하지 못할 수 있습니다."
            )

    def _create_error_response(self, error_message: str) -> Dict:
        return {
            'answer': f"시스템 오류: {error_message}",
            'sources': [],
            'model': self.model_name,
            'musical_terms': [],
            'confidence': 'error',
            'data_coverage': 'error'
        }

def main():
    try:
        from src.models.retriever import VectorRetriever
        retriever = VectorRetriever()

        print("검색기 초기화 중...")
        retriever.load_embeddings()
        retriever.build_index()

        rag_model = RAGModel(retriever)
        while True:
            query = input("\n질문을 입력하세요 (종료: exit): ")
            if query.lower() in ["exit", "quit"]:
                break
            response = rag_model.get_conversation_response(query)
            print("\n[답변]")
            print(response['answer'])
            print(f"\n[참고 passage 개수]: {len(response['sources'])}")

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    pass

if __name__ == "__main__":
    main()
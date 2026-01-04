import os
from typing import Dict, List
from datetime import datetime
import openai
from dotenv import load_dotenv, find_dotenv

# .env 파일을 상위 폴더에서 자동 탐색해서 로드
load_dotenv(find_dotenv())
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
parallelism = os.getenv("TOKENIZERS_PARALLELISM", "false")
os.environ["TOKENIZERS_PARALLELISM"] = parallelism

from src.bots.musicqna.prompts.prompts import MUSICQNA_SYSTEM_PROMPT

class RAGModel:
    def __init__(self, retriever, model_name: str = DEFAULT_MODEL, min_similarity_score: float = 0.7):
        self.retriever = retriever
        self.model_name = model_name
        self.min_similarity_score = min_similarity_score
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)

    def get_conversation_response(self, query: str) -> Dict:
        # sources = self.retriever.search(query, top_k=5, min_score=0.0)
        # print("[DEBUG] sources:", sources)
        # user_content = self._format_user_message(query, sources)
        # print("[DEBUG] after format, sources:", sources)
        try:
            sources = self.retriever.search(query, top_k=2) if self.retriever else []
            return self._generate_llm_response(query, sources)
        except Exception as e:
            return self._create_error_response(f"오류: {e}")

    def _generate_llm_response(self, query: str, sources: List[Dict]) -> Dict:
        user_content = self._format_user_message(query, sources)
        try:
            chat = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": MUSICQNA_SYSTEM_PROMPT},
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
                'timestamp': datetime.now().isoformat(),
                'used_system_prompt': True
            }
        except Exception as e:
            return self._create_error_response(f"API 오류: {e}")

    def _format_sources_for_prompt(self, sources: List[Dict]) -> str:
        if not sources:
            return ""
        formatted = ""
        max_passage = 2
        max_length = 300    
        for idx, source in enumerate(sources[:max_passage], 1):
            concept_ko = source.get('concept.ko', '') or ''
            concept_en = source.get('concept.en', '') or ''
            aliases = source.get('aliases', '') or ''
            definition = source.get('definition', '') or ''
            logic = source.get('logic', '') or ''
            example_name = source.get('examples.name', '') or ''
            example_desc = source.get('examples.description', '') or ''
            tips = source.get('tips', '') or ''

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
        if sources_text.strip():
            return f"질문: {query}\n\n{sources_text}"
        else:
            return f"질문: {query}\n\n(참고자료가 없습니다.)"
        
    def _create_error_response(self, error_message: str) -> Dict:
        return {
            'answer': f"시스템 오류: {error_message}",
            'sources': [],
            'model': self.model_name,
            'confidence': 'error',
            'data_coverage': 'error'
        }

def main():
    try:
        from src.bots.musicqna.models.retriever import VectorRetriever
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
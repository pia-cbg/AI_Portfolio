import os
from typing import List, Dict, Tuple, Any
import anthropic
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class MusicRAGModel:
    def __init__(self, retriever):
        self.retriever = retriever
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model_name = "claude-3-haiku-20240307"  # 또는 "claude-3-opus-20240229", "claude-3-sonnet-20240229"
    
    def generate_answer(self, query: str, top_k: int = 3) -> str:
        """RAG를 사용하여 답변을 생성합니다."""
        # 1. 관련 문서 검색
        search_results = self.retriever.search(query, top_k=top_k)
        
        # 2. 검색된 컨텍스트 준비
        context = self._prepare_context(search_results)
        
        # 3. 프롬프트 생성
        prompt = self._create_prompt(query, context)
        
        # 4. Claude API로 답변 생성
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=1000,
                temperature=0.7,
                system="당신은 음악 이론 전문가입니다. 주어진 컨텍스트를 바탕으로 정확하고 이해하기 쉬운 답변을 제공해주세요.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            answer = response.content[0].text
            return answer
            
        except Exception as e:
            return f"답변 생성 중 오류가 발생했습니다: {str(e)}"
    
    def _prepare_context(self, search_results: List[Tuple[Dict, float]]) -> str:
        """검색 결과를 컨텍스트로 변환합니다."""
        if not search_results:
            return "관련 정보를 찾을 수 없습니다."
        
        context_parts = []
        for i, (chunk, score) in enumerate(search_results, 1):
            title = chunk.get("metadata", {}).get("title", "")
            content = chunk.get("content", "")
            
            context_parts.append(f"""
참고자료 {i}: {title}
{content}
""")
        
        return "\n".join(context_parts)
    
    def _create_prompt(self, query: str, context: str) -> str:
        """프롬프트를 생성합니다."""
        return f"""
다음은 음악 이론에 관한 질문입니다:
{query}

아래 참고자료를 바탕으로 답변해주세요:
{context}

답변 시 다음 사항을 고려해주세요:
1. 음악 이론 초보자도 이해할 수 있도록 쉽게 설명해주세요
2. 구체적인 예시를 포함해주세요 (코드명, 스케일 등)
3. 참고자료의 내용을 바탕으로 정확한 정보를 제공해주세요
4. 한국어로 친근하게 답변해주세요

답변:
"""

    def get_conversation_response(self, query: str) -> Dict[str, Any]:
        """대화형 응답을 생성합니다."""
        # 검색 결과도 함께 반환
        search_results = self.retriever.search(query, top_k=3)
        answer = self.generate_answer(query)
        
        return {
            "query": query,
            "answer": answer,
            "sources": [
                {
                    "title": chunk.get("metadata", {}).get("title", ""),
                    "content": chunk.get("content", "")[:200] + "..." if len(chunk.get("content", "")) > 200 else chunk.get("content", ""),
                    "score": float(score)
                }
                for chunk, score in search_results
            ]
        }

if __name__ == "__main__":
    # 테스트용 코드
    import os
    import sys
    import numpy as np
    import pickle
    
    # 현재 스크립트 경로를 기반으로 프로젝트 루트 경로 설정
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    sys.path.append(project_root)
    
    from src.models.retriever import MusicKnowledgeRetriever
    
    # 임베딩 및 청크 로드 경로
    embeddings_path = os.path.join(project_root, "data/processed/embeddings/embeddings.npy")
    chunks_path = os.path.join(project_root, "data/processed/embeddings/chunks.pkl")
    
    if os.path.exists(embeddings_path) and os.path.exists(chunks_path):
        # 저장된 임베딩과 청크 로드
        embeddings = np.load(embeddings_path)
        with open(chunks_path, 'rb') as f:
            chunks = pickle.load(f)
        
        # 검색기 초기화
        retriever = MusicKnowledgeRetriever()
        retriever.build_index(embeddings, chunks)
        
        # RAG 모델 초기화
        rag_model = MusicRAGModel(retriever)
        
        # 테스트 질문
        test_query = "세컨더리 도미넌트가 뭐야?"
        response = rag_model.get_conversation_response(test_query)
        
        print(f"\n질문: {response['query']}")
        print(f"\n답변: {response['answer']}")
        print("\n참고자료:")
        for i, source in enumerate(response['sources'], 1):
            print(f"  {i}. {source['title']} (유사도: {source['score']:.3f})")
    else:
        print("임베딩 파일이 없습니다. 먼저 임베딩을 생성해주세요.")
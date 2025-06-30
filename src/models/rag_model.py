"""
음악 이론 RAG 모델
- 오직 데이터셋 기반 답변만 제공
- 외부 지식 사용 금지
- 데이터 부족 시 명확히 표시
"""
import os
import sys
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dotenv import load_dotenv
import anthropic

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# utils 폴더의 music_utils 임포트
from utils.music_utils import extract_musical_terms, format_chord_name

class RAGModel:
    def __init__(self, retriever, min_similarity_score: float = 0.7):
        """
        RAG 모델 초기화
        
        :param retriever: 벡터 검색기
        :param min_similarity_score: 최소 유사도 점수 (기본 0.7)
        """
        # 환경 변수 로드
        env_path = os.path.join(project_root, '.env')
        load_dotenv(env_path)
        
        # API 키 및 모델 설정
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.model_name = os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307')
        self.min_similarity_score = min_similarity_score
        
        # Anthropic 클라이언트 초기화
        self.client = self._initialize_client()
        
        # 검색기 설정
        self.retriever = retriever
        
        # 시스템 프롬프트 준비
        self.system_prompt = self._prepare_system_prompt()
        
        # 데이터 갭 추적 (세션별)
        self.session_gaps = []
        
        # 통계 추적
        self.stats = {
            'total_queries': 0,
            'successful_answers': 0,
            'partial_answers': 0,
            'no_data_answers': 0
        }
    
    def _initialize_client(self):
        """Anthropic API 클라이언트 초기화"""
        try:
            if not self.api_key:
                print("❌ API 키가 설정되지 않았습니다.")
                return None
            
            clean_key = self.api_key.strip()
            client = anthropic.Anthropic(api_key=clean_key)
            
            print("✅ Anthropic 클라이언트 초기화 성공")
            return client
        except Exception as e:
            print(f"❌ Anthropic 클라이언트 초기화 실패: {e}")
            return None
    
    def _prepare_system_prompt(self) -> str:
        """시스템 프롬프트"""
        return """
당신은 음악 이론 교육 시스템의 AI 어시스턴트입니다.

## 핵심 원칙
1. **오직 제공된 참고자료만 사용**: 참고자료에 명시된 내용만 답변에 포함하세요.
2. **외부 지식 절대 금지**: 당신이 알고 있는 일반적인 음악 지식을 절대 사용하지 마세요.
3. **투명성**: 답변할 수 없는 부분은 명확히 표시하세요.

## 답변 규칙
- 모든 정보는 참고자료에서 직접 인용
- 각 문장 끝에 [참고자료 번호] 표시
- 추론이나 유추 금지
- 정보가 없거나 부족할 시 "현재 데이터셋이 부족해서 더 열심히 배우겠습니다. | 이모티콘 사용" 명시
- 문단별 마침표가 있을 경우 다음 줄로 출력

## 답변 구조
1. 참고자료에 있는 핵심 정보 요약
2. 세부 설명 (참고자료 표시)
3. 부족한 정보 명시

## 용어 사용
- 참고자료의 용어 그대로 사용
- 번역체 금지
- 영어 용어는 원문 유지
        """
    
    def get_conversation_response(self, query: str) -> Dict:
        """RAG 기반 응답 생성"""
        self.stats['total_queries'] += 1
        
        try:
            # 클라이언트 확인
            if self.client is None:
                return self._create_error_response("API 클라이언트가 초기화되지 않았습니다.")
            
            # 음악 용어 추출
            musical_terms = extract_musical_terms(query)
            
            # 검색 수행 (더 많은 결과 검색)
            sources = []
            if self.retriever is not None:
                try:
                    sources = self.retriever.search(query, top_k=5)
                    # print(f"✅ 검색 완료: {len(sources)}개 결과")
                except Exception as search_error:
                    print(f"⚠️ 검색 중 오류: {search_error}")
                    return self._create_error_response(f"검색 중 오류 발생: {search_error}")
            
            # 소스 분류
            high_quality_sources = [s for s in sources if s.get('score', 0) >= self.min_similarity_score]
            medium_quality_sources = [s for s in sources if 0.5 <= s.get('score', 0) < self.min_similarity_score]
            
            # 응답 생성 로직
            if high_quality_sources:
                # 충분한 데이터가 있는 경우
                return self._generate_complete_response(query, high_quality_sources, musical_terms)
            elif medium_quality_sources:
                # 부분적 데이터만 있는 경우
                return self._generate_partial_response(query, medium_quality_sources, musical_terms)
            else:
                # 데이터가 없는 경우
                return self._generate_no_data_response(query, musical_terms)
                
        except Exception as e:
            print(f"❌ 응답 생성 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_response(f"오류 발생: {e}")
    
    def _generate_complete_response(self, query: str, sources: List[Dict], musical_terms: List[str]) -> Dict:
        """충분한 데이터가 있을 때 응답 생성"""
        
        # 디버깅: 입력 데이터 확인
        # print(f"DEBUG: _generate_complete_response 호출됨")
        # print(f"DEBUG: 질문: {query}")
        # print(f"DEBUG: 소스 개수: {len(sources)}")
        # print(f"DEBUG: 음악 용어: {musical_terms}")
        
        # 소스 텍스트 생성
        sources_text = self._format_sources_for_prompt(sources)
        
        # print(f"DEBUG: 포맷된 소스 텍스트 길이: {len(sources_text)}")
        # print(f"DEBUG: 소스 텍스트 미리보기:\n{sources_text[:500]}...")
        
        # 프롬프트 구성
        prompt = f"""
    사용자 질문: {query}

    참고자료:
    {sources_text}

    위 참고자료만을 사용하여 질문에 답변하세요.
    각 정보마다 [참고자료 번호]를 표시하세요.
    참고자료에 없는 내용은 절대 추가하지 마세요.
        """
        
        # print(f"DEBUG: 전체 프롬프트 길이: {len(prompt)}")
        # print(f"DEBUG: API 호출 준비 - 모델: {self.model_name}")
        
        try:
            # API 호출
            # print("DEBUG: Anthropic API 호출 시작...")
            
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=1000,
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # print("DEBUG: API 응답 수신 완료")
            # print(f"DEBUG: 응답 타입: {type(response)}")
            # print(f"DEBUG: 응답 내용 타입: {type(response.content)}")
            # print(f"DEBUG: 응답 내용 개수: {len(response.content) if hasattr(response, 'content') else 'N/A'}")
            
            # 응답 추출
            if hasattr(response, 'content') and len(response.content) > 0:
                answer = response.content[0].text
                # print(f"DEBUG: 추출된 답변 길이: {len(answer)}")
                # print(f"DEBUG: 답변 처음 200자: {answer[:200]}...")
            else:
                # print("DEBUG: 응답에서 텍스트를 추출할 수 없음")
                answer = "응답 생성에 실패했습니다."
            
            # 통계 업데이트
            self.stats['successful_answers'] += 1
            
            # 결과 반환
            result = {
                'answer': answer,
                'sources': sources,
                'model': self.model_name,
                'musical_terms': musical_terms,
                'confidence': 'high',
                'data_coverage': 'complete'
            }
            
            # print(f"DEBUG: 반환할 결과 타입: {type(result)}")
            # print(f"DEBUG: 결과 키: {result.keys()}")
            
            return result
            
        except Exception as e:
            # print(f"DEBUG: API 호출 중 오류 발생: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            
            # 오류 발생 시 기본 응답 반환
            return {
                'answer': f"API 호출 중 오류가 발생했습니다: {e}",
                'sources': sources,
                'model': self.model_name,
                'musical_terms': musical_terms,
                'confidence': 'error',
                'data_coverage': 'error'
            }
    
    def _generate_no_data_response(self, query: str, musical_terms: List[str]) -> Dict:
        """데이터가 없을 때 응답 생성"""
        
        # 갭 기록
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
            
            # 내용이 너무 길면 잘라내기
            if len(content) > 500:
                content = content[:500] + "..."
            
            formatted += f"\n[참고자료 {idx}]\n"
            formatted += f"제목: {title}\n"
            formatted += f"내용: {content}\n"
            formatted += f"관련도: {score:.3f}\n"
            formatted += "-" * 40
        
        # 디버깅
        # print(f"DEBUG: 포맷된 소스 개수: {len(sources)}")
        # print(f"DEBUG: 포맷된 텍스트 총 길이: {len(formatted)}")
        
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
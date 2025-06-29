import os
import sys
import json
from typing import Dict, List
from dotenv import load_dotenv
import anthropic

class RAGModel:
    def __init__(self, retriever):
        """
        RAG 모델 초기화
        
        :param retriever: 벡터 검색기
        """
        # 프로젝트 루트 경로 설정 (절대 경로 사용)
        project_root = '/Users/cbg/github/AI_Portfolio'
        
        # utils 폴더 경로 추가
        sys.path.insert(0, project_root)
        
        # 절대 경로로 .env 파일 로드
        env_path = os.path.join(project_root, '.env')
        load_dotenv(dotenv_path=env_path)
        
        # 직접 API 키 출력해보기 (실제 키는 노출되지 않게 길이만)
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        print(f"🔑 API 키 확인:")
        print(f"   - .env 경로: {env_path}")
        print(f"   - .env 파일 존재: {os.path.exists(env_path)}")
        print(f"   - API 키 길이: {len(self.api_key) if self.api_key else 0}")
        
        # API 키가 없으면 직접 입력 요청 (테스트용)
        if not self.api_key:
            print("⚠️ API 키를 찾을 수 없습니다. 테스트를 위해 직접 입력하시겠습니까? (y/n)")
            choice = input()
            if choice.lower() == 'y':
                self.api_key = input("API 키 입력: ").strip()
                print(f"API 키 길이: {len(self.api_key)}")
        
        # 모델 이름 설정
        self.model_name = os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307')
        
        # 검색기 설정
        self.retriever = retriever
        
        # utils 모듈 임포트
        try:
            from utils.music_utils import extract_musical_terms, format_chord_name
            self.extract_musical_terms = extract_musical_terms
            self.format_chord_name = format_chord_name
            print("✅ utils.music_utils 모듈 로드 성공")
        except ImportError as e:
            print(f"❌ utils.music_utils 모듈 로드 실패: {e}")
            # 기본 함수 정의
            self.extract_musical_terms = lambda text: []
        
        # Anthropic 클라이언트 초기화
        self.client = self._initialize_client()
        
        # 시스템 프롬프트 준비
        self.system_prompt = self._prepare_system_prompt()
    
    def _initialize_client(self):
        """Anthropic API 클라이언트 초기화"""
        try:
            if not self.api_key:
                print("❌ API 키가 설정되지 않았습니다.")
                return None
            
            # 키 공백 제거 및 디버깅
            clean_key = self.api_key.strip()
            
            # API 키 마스킹하여 출력
            masked_key = clean_key[:4] + '*' * (len(clean_key) - 8) + clean_key[-4:]
            print(f"   - 마스킹된 API 키: {masked_key}")
            
            # 클라이언트 생성
            client = anthropic.Anthropic(api_key=clean_key)
            
            print("✅ Anthropic 클라이언트 초기화 성공")
            return client
        except Exception as e:
            print(f"❌ Anthropic 클라이언트 초기화 실패: {e}")
            return None
    
    def _prepare_system_prompt(self) -> str:
        """시스템 프롬프트 준비"""
        return """
당신은 음악 이론 전문가 AI 어시스턴트입니다. 다음 가이드라인을 준수하세요:

1. 답변은 명확하고 전문적이어야 합니다.
2. 음악 이론적 관점에서 정확하고 심도있는 설명을 제공하세요.
3. 복잡한 개념은 쉽게 풀어서 설명하되, 전문성을 잃지 마세요.
4. 필요한 경우 실제 음악 예시나 실무적 적용 사례를 포함하세요.
5. 학습자의 이해 수준을 고려하여 적절한 깊이로 설명하세요.

제공된 참고자료를 바탕으로 답변하되, 자신의 음악 이론 지식도 활용하세요.
        """
    
    def get_conversation_response(self, query: str) -> Dict:
        """대화형 응답 생성"""
        try:
            # 클라이언트 확인
            if self.client is None:
                return {
                    'answer': "API 클라이언트가 초기화되지 않았습니다. API 키를 확인해주세요.",
                    'sources': [],
                    'model': self.model_name,
                    'musical_terms': []
                }
            
            # 음악 용어 추출
            musical_terms = self.extract_musical_terms(query)
            
            # 벡터 검색
            sources = []
            if self.retriever is not None:
                try:
                    sources = self.retriever.search(query, top_k=3)
                    print(f"✅ 검색 성공: {len(sources)}개 결과")
                except Exception as search_error:
                    print(f"⚠️ 검색 중 오류: {search_error}")
                    sources = []
            
            # 소스 텍스트 생성
            sources_text = self._generate_sources_text(sources)
            
            # 프롬프트 구성
            full_prompt = (
                f"질문: {query}\n\n"
                f"추출된 음악 용어: {', '.join(musical_terms) if musical_terms else '없음'}\n\n"
                f"{sources_text}\n\n"
                "위 정보를 바탕으로 질문에 대해 상세하고 전문적으로 답변해주세요."
            )
            
            print("🚀 Anthropic API 호출 중...")
            
            # API 호출
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=1000,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            print("✅ API 응답 받음")
            
            return {
                'answer': response.content[0].text,
                'sources': sources,
                'model': self.model_name,
                'musical_terms': musical_terms
            }
        
        except anthropic.APIError as e:
            print(f"❌ Anthropic API 오류: {e}")
            return {
                'answer': f"API 오류가 발생했습니다: {e}",
                'sources': [],
                'model': self.model_name,
                'musical_terms': []
            }
        
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            import traceback
            traceback.print_exc()
            return {
                'answer': f"오류가 발생했습니다: {e}",
                'sources': [],
                'model': self.model_name,
                'musical_terms': []
            }
    
    def _generate_sources_text(self, sources: List[Dict]) -> str:
        """검색된 소스를 텍스트로 변환"""
        if not sources:
            return "참고할 수 있는 소스가 없습니다."
        
        sources_text = "참고 자료:\n"
        for idx, source in enumerate(sources, 1):
            sources_text += f"{idx}. {source.get('title', '제목 없음')}\n"
            sources_text += f"   내용: {source.get('content', '내용 없음')[:200]}...\n"
            sources_text += f"   유사도: {source.get('score', 0):.3f}\n\n"
        
        return sources_text
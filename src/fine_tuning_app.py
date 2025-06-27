import sys
import os
import json
from typing import Dict

# 현재 스크립트의 절대 경로 출력
print("Current script path:", os.path.abspath(__file__))
# 프로젝트 루트 경로 출력
print("Project root path:", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import initialize_system
from src.data_processing.fine_tuning_processor import FineTuningProcessor
from src.models.fine_tuning_model import FineTuningModel

class FineTuningCLI:
    def __init__(self):
        self.rag_model = initialize_system()
        self.fine_tuning_processor = FineTuningProcessor()
        self.fine_tuning_model = FineTuningModel(self.rag_model)
    
    def start(self):
        print("🎵 음악 이론 Q&A 모델 파인튜닝 CLI")
        print("'quit' 입력 시 종료")
        
        while True:
            query = input("\n📝 질문을 입력하세요: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            # 모델 응답 생성
            response = self.rag_model.get_conversation_response(query)
            
            print("\n🤖 모델 응답:")
            print(response['answer'])
            
            # 참고자료 출력
            print("\n📚 참고자료:")
            for i, source in enumerate(response['sources'], 1):
                print(f"\n참고자료 {i}:")
                print(f"제목: {source.get('title', '제목 없음')}")
                print(f"유사도: {source.get('score', '알 수 없음')}")
                print(f"내용 미리보기: {source.get('content', '').split('.')[:2]}...")
            
            # 평가 프로세스
            evaluation_data = self.get_evaluation(query, response['answer'], response['sources'])
            
            # 평가 데이터 저장 및 처리
            self.fine_tuning_processor.save_evaluation(evaluation_data)
            self.fine_tuning_model.process_evaluation(evaluation_data)
    
    def get_evaluation(self, query: str, response: str, sources: list):
        """사용자로부터 평가 입력받기"""
        print("\n📊 응답 평가")
        
        while True:
            try:
                accuracy = int(input("정확성 점수 (0-10): "))
                completeness = int(input("완전성 점수 (0-10): "))
                clarity = int(input("명확성 점수 (0-10): "))
                
                if all(0 <= score <= 10 for score in [accuracy, completeness, clarity]):
                    break
                else:
                    print("점수는 0-10 사이여야 합니다.")
            except ValueError:
                print("숫자를 입력해주세요.")
        
        feedback = input("상세 피드백 (선택사항): ")
        
        return {
            'query': query,
            'response': response,
            'sources': sources,
            'accuracy': accuracy,
            'completeness': completeness,
            'clarity': clarity,
            'feedback': feedback
        }

def main():
    fine_tuning_cli = FineTuningCLI()
    fine_tuning_cli.start()

if __name__ == "__main__":
    main()
class FineTuningModel:
    def __init__(self, rag_model):
        """
        RAG 모델을 기반으로 파인튜닝 모델 초기화
        
        :param rag_model: 원본 RAG 모델
        """
        self.rag_model = rag_model
        self.evaluation_history = []
        self.correction_history = []
    
    def process_evaluation(self, evaluation_data):
        """
        평가 데이터 처리
        - 점수 분석
        - 낮은 점수의 평가 트래킹
        
        :param evaluation_data: 평가 데이터 딕셔너리
        :return: 수정 필요 여부 (bool)
        """
        # 정확성, 완전성, 명확성 중 하나라도 7점 미만이면 수정 필요
        if (evaluation_data['accuracy'] < 7 or 
            evaluation_data['completeness'] < 7 or 
            evaluation_data['clarity'] < 7):
            
            # 평가 히스토리에 추가
            self.evaluation_history.append(evaluation_data)
            
            print("\n🚨 모델 수정 필요:")
            print(f"질문: {evaluation_data['query']}")
            print(f"정확성: {evaluation_data['accuracy']}/10")
            print(f"완전성: {evaluation_data['completeness']}/10")
            print(f"명확성: {evaluation_data['clarity']}/10")
            
            return True
        
        return False
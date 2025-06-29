import os
import sys
import json
from typing import List, Dict
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 절대 경로 방식으로 import
from src.main import initialize_system
from src.fine_tuning.utils.evaluator import FineTuningEvaluator
from src.fine_tuning.utils.model_updater import ModelUpdater


class Phase2ModelTraining:
    def __init__(self):
        """Phase 2: 모델 파인튜닝 시스템 초기화"""
        self.base_dir = 'data/fine_tuning/phase2_model_training'
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Phase 1 결과 경로
        self.phase1_dir = 'data/fine_tuning/phase1_question_improvement'
        
        # 컴포넌트 초기화
        self.rag_model = None
        self.evaluator = FineTuningEvaluator()
        self.model_updater = ModelUpdater()
        
        # 세션 데이터
        self.session_data = {
            'start_time': datetime.now().isoformat(),
            'questions_used': [],
            'evaluations': [],
            'improvements_made': []
        }
    
    def run_phase2(self):
        """Phase 2 전체 프로세스 실행"""
        print("🎵 Phase 2: 모델 파인튜닝 프로세스 시작")
        print("="*60)
        
        # 1. 시스템 초기화
        print("\n1️⃣ RAG 시스템 초기화...")
        self._initialize_rag_system()
        
        # 2. 개선된 질문 로드
        print("\n2️⃣ Phase 1 결과 로드...")
        questions = self._load_refined_questions()
        
        if not questions:
            print("❌ Phase 1에서 개선된 질문을 찾을 수 없습니다.")
            print("먼저 Phase 1을 완료해주세요.")
            return
        
        # 3. 답변 생성 및 평가
        print("\n3️⃣ 답변 생성 및 평가...")
        self._evaluate_answers(questions)
        
        # 4. 세션 저장
        print("\n4️⃣ 평가 결과 저장...")
        self.evaluator.save_session()
        self._save_session_data()
        
        # 5. 모델 업데이트
        print("\n5️⃣ 모델 업데이트...")
        self._update_model_if_needed()
        
        print("\n✅ Phase 2 완료!")
        self._print_summary()
    
    def _initialize_rag_system(self):
        """RAG 시스템 초기화"""
        try:
            print("🎵 음악 지식 RAG 시스템 초기화 중...")
            
            # 1. 데이터 로딩
            print("1. 데이터 로딩...")
            from src.data_processing.json_loader import MusicTheoryDataLoader
            loader = MusicTheoryDataLoader()
            data = loader.load_data()
            
            # 2. 임베딩 처리
            print("2. 임베딩 처리...")
            from src.data_processing.embedding_generator import EmbeddingGenerator
            embedder = EmbeddingGenerator()
            
            # 기존 임베딩이 있는지 확인
            if not embedder.load_embeddings():
                print("   새로운 임베딩 생성 중...")
                chunks = loader.extract_text_chunks()
                embedder.generate_embeddings(chunks)
                embedder.save_embeddings()
            
            # 3. 검색기 초기화
            print("3. 검색기 초기화...")
            from src.models.retriever import VectorRetriever
            retriever = VectorRetriever()
            
            # 검색기가 직접 임베딩 로드하도록 설정
            print("   - 검색기 설정 완료")
            
            # 4. RAG 모델 초기화
            print("4. RAG 모델 초기화...")
            
            # 프로젝트 루트 경로 추가 (utils 접근용)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            sys.path.insert(0, project_root)
            
            # RAG 모델 생성
            from src.models.rag_model import RAGModel
            self.rag_model = RAGModel(retriever)
            
            print("✅ RAG 시스템 초기화 완료")
            
        except Exception as e:
            print(f"❌ RAG 시스템 초기화 실패: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _load_refined_questions(self) -> List[str]:
        """Phase 1에서 개선된 질문들 로드"""
        questions_file = os.path.join(self.phase1_dir, 'refined_questions.json')
        
        if not os.path.exists(questions_file):
            print(f"❌ 개선된 질문 파일을 찾을 수 없습니다: {questions_file}")
            return []
        
        try:
            with open(questions_file, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            
            print(f"✅ {len(questions)}개의 개선된 질문 로드 완료")
            self.session_data['questions_used'] = questions
            return questions
            
        except Exception as e:
            print(f"❌ 질문 로드 중 오류: {e}")
            return []
    
    def _evaluate_answers(self, questions: List[str]):
        """답변 생성 및 평가"""
        print(f"\n총 {len(questions)}개의 질문에 대한 답변을 평가합니다.")
        
        # 평가할 질문 범위 선택
        try:
            start_idx = int(input(f"시작 번호 (1-{len(questions)}, 기본 1): ") or 1) - 1
            end_idx = int(input(f"끝 번호 (1-{len(questions)}, 기본 {min(10, len(questions))}): ") or min(10, len(questions)))
        except ValueError:
            start_idx = 0
            end_idx = min(10, len(questions))
        
        selected_questions = questions[start_idx:end_idx]
        
        for idx, question in enumerate(selected_questions, start_idx + 1):
            print(f"\n{'='*80}")
            print(f"질문 {idx}/{len(questions)}: {question}")
            print('='*80)
            
            # RAG 모델로 답변 생성
            print("\n🤖 답변 생성 중...")
            try:
                response = self.rag_model.get_conversation_response(question)
                answer = response['answer']
                sources = response.get('sources', [])
                
                # 답변 평가 (질문은 평가하지 않음)
                evaluation = self.evaluator.evaluate_answer(question, answer, sources)
                
                # 평가 저장
                self.evaluator.save_evaluation(evaluation)
                self.session_data['evaluations'].append(evaluation)
                
                print(f"\n평가 완료: {evaluation['avg_score']:.1f}/10")
                
                # 계속 진행 여부
                if idx < end_idx:
                    cont = input("\n다음 질문으로 진행하시겠습니까? (y/n): ")
                    if cont.lower() != 'y':
                        break
                        
            except Exception as e:
                print(f"❌ 답변 생성 중 오류: {e}")
                continue
    
    def _save_session_data(self):
        """세션 데이터 저장"""
        self.session_data['end_time'] = datetime.now().isoformat()
        
        # 평가 통계 계산
        evaluations = self.session_data['evaluations']
        if evaluations:
            avg_score = sum(e['avg_score'] for e in evaluations) / len(evaluations)
            low_quality_count = len([e for e in evaluations if e['avg_score'] < 7])
            
            self.session_data['statistics'] = {
                'total_evaluations': len(evaluations),
                'average_score': avg_score,
                'low_quality_count': low_quality_count,
                'improvement_needed': low_quality_count > 0
            }
        
        # 세션 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_file = os.path.join(self.base_dir, f'phase2_session_{timestamp}.json')
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 세션 데이터 저장: {session_file}")
    
    def _update_model_if_needed(self):
        """필요시 모델 업데이트"""
        # 개선이 필요한 평가 확인
        poor_evaluations = [
            e for e in self.session_data['evaluations'] 
            if e.get('avg_score', 0) < 7 and e.get('correction')
        ]
        
        if not poor_evaluations:
            print("✅ 모델 업데이트가 필요하지 않습니다.")
            return
        
        print(f"\n⚠️ {len(poor_evaluations)}개의 답변이 개선이 필요합니다.")
        
        # 사용자 확인
        update_choice = input("모델을 업데이트하시겠습니까? (y/n): ")
        
        if update_choice.lower() == 'y':
            try:
                # 모델 업데이트 실행
                print("\n🔄 모델 업데이트 중...")
                self.model_updater.process_corrections(poor_evaluations)
                
                # 업데이트 결과 기록
                self.session_data['improvements_made'] = self.model_updater.get_update_history()
                
                print("✅ 모델 업데이트 완료!")
                
                # 재평가 옵션
                retest = input("\n업데이트된 모델로 재평가하시겠습니까? (y/n): ")
                if retest.lower() == 'y':
                    self._retest_improved_questions(poor_evaluations)
                    
            except Exception as e:
                print(f"❌ 모델 업데이트 중 오류: {e}")
        else:
            print("모델 업데이트를 건너뜁니다.")
    
    def _retest_improved_questions(self, poor_evaluations: List[Dict]):
        """개선된 질문들 재평가"""
        print("\n🔄 개선된 모델로 재평가 중...")
        
        # RAG 시스템 재초기화 (업데이트된 데이터 반영)
        self._initialize_rag_system()
        
        retest_results = []
        
        for eval_data in poor_evaluations:
            question = eval_data['question']
            print(f"\n재평가: {question}")
            
            try:
                # 새로운 답변 생성
                response = self.rag_model.get_conversation_response(question)
                new_answer = response['answer']
                
                print(f"새로운 답변:\n{new_answer}")
                
                # 간단한 개선 확인
                better = input("답변이 개선되었나요? (y/n): ")
                
                retest_results.append({
                    'question': question,
                    'old_score': eval_data['avg_score'],
                    'new_answer': new_answer,
                    'improved': better.lower() == 'y'
                })
                
            except Exception as e:
                print(f"재평가 중 오류: {e}")
        
        # 재평가 결과 저장
        self.session_data['retest_results'] = retest_results
        
        improved_count = len([r for r in retest_results if r['improved']])
        print(f"\n✅ 재평가 완료: {improved_count}/{len(retest_results)}개 답변 개선됨")
    
    def _print_summary(self):
        """Phase 2 결과 요약"""
        print("\n" + "="*60)
        print("📊 Phase 2 결과 요약")
        print("="*60)
        
        stats = self.session_data.get('statistics', {})
        
        if stats:
            print(f"총 평가 질문: {stats['total_evaluations']}개")
            print(f"평균 점수: {stats['average_score']:.2f}/10")
            print(f"개선 필요: {stats['low_quality_count']}개")
            
            if self.session_data.get('improvements_made'):
                print(f"모델 업데이트: {len(self.session_data['improvements_made'])}개 변경사항 적용")
            
            if self.session_data.get('retest_results'):
                retest = self.session_data['retest_results']
                improved = len([r for r in retest if r['improved']])
                print(f"재평가 결과: {improved}/{len(retest)}개 개선됨")
        
        print("\n다음 단계:")
        print("- 만족스러운 결과라면 웹 앱 실행: python app.py")
        print("- 추가 개선이 필요하다면 Phase 2 재실행")

def main():
    """Phase 2 메인 실행"""
    try:
        phase2 = Phase2ModelTraining()
        phase2.run_phase2()
    except KeyboardInterrupt:
        print("\n\n👋 Phase 2 프로세스가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ Phase 2 실행 중 오류: {e}")

if __name__ == "__main__":
    main()
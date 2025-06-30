import os
import sys
import json
from typing import List, Dict
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.main import initialize_system
from src.fine_tuning.utils.evaluator import FineTuningEvaluator
from src.fine_tuning.utils.model_updater import ModelUpdater

class ModelTrainer:  # 클래스명 변경
    def __init__(self):
        """모델 파인튜닝 시스템 초기화"""
        # 새로운 구조에 맞춰 경로 변경
        self.fine_tuning_base = 'data/fine_tuning'
        self.questions_dir = os.path.join(self.fine_tuning_base, 'questions')
        self.evaluations_dir = os.path.join(self.fine_tuning_base, 'evaluations')
        self.reports_dir = os.path.join(self.fine_tuning_base, 'reports')
        
        # 필요한 디렉토리 생성
        os.makedirs(self.evaluations_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
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
    
    def run_training(self):  # 메서드명 변경
        """모델 파인튜닝 프로세스 실행"""
        print("🎵 음악 이론 모델 파인튜닝 프로세스 시작")
        print("="*60)
        
        # 1. 시스템 초기화
        print("\n1️⃣ RAG 시스템 초기화...")
        self._initialize_rag_system()
        
        # 2. 질문 로드
        print("\n2️⃣ 생성된 질문 로드...")
        questions = self._load_questions()
        
        if not questions:
            print("❌ 사용할 질문을 찾을 수 없습니다.")
            print("먼저 질문 생성을 완료해주세요.")
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
        
        print("\n✅ 모델 파인튜닝 완료!")
        self._print_summary()
    
    def _initialize_rag_system(self):
        """RAG 시스템 초기화"""
        try:
            # initialize_system 사용 (main.py에서)
            self.rag_model = initialize_system()
            
            if self.rag_model is None:
                raise Exception("RAG 모델 초기화 실패")
            
            print("✅ RAG 시스템 초기화 완료")
            
        except Exception as e:
            print(f"❌ RAG 시스템 초기화 실패: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _load_questions(self) -> List[str]:
        """생성된 질문들 로드"""
        # 새로운 구조에서 질문 파일 위치
        possible_files = [
            os.path.join(self.questions_dir, 'refined_questions.json'),
            os.path.join(self.questions_dir, 'raw_questions.json'),
        ]
        
        for questions_file in possible_files:
            if os.path.exists(questions_file):
                try:
                    with open(questions_file, 'r', encoding='utf-8') as f:
                        questions = json.load(f)
                    
                    print(f"✅ {len(questions)}개의 질문 로드 완료: {questions_file}")
                    self.session_data['questions_used'] = questions
                    return questions
                    
                except Exception as e:
                    print(f"❌ 질문 로드 중 오류 ({questions_file}): {e}")
                    continue
        
        print(f"❌ 질문 파일을 찾을 수 없습니다. 확인된 경로:")
        for file_path in possible_files:
            print(f"   - {file_path}: {'존재' if os.path.exists(file_path) else '없음'}")
        
        return []
    
    def _evaluate_answers(self, questions: List[str]):
        """답변 생성 및 평가"""
        print(f"\n총 {len(questions)}개의 질문에 대한 답변을 평가합니다.")
        print("⚠️  데이터셋 기반 답변만 생성되며, 데이터 부족 시 명확히 표시됩니다.")
        
        # 평가할 질문 범위 선택
        try:
            start_idx = int(input(f"시작 번호 (1-{len(questions)}, 기본 1): ") or 1) - 1
            end_idx = int(input(f"끝 번호 (1-{len(questions)}, 기본 {min(10, len(questions))}): ") or min(10, len(questions)))
        except ValueError:
            start_idx = 0
            end_idx = min(10, len(questions))
        
        # 범위 검증
        start_idx = max(0, start_idx)
        end_idx = min(len(questions), end_idx)
        
        selected_questions = questions[start_idx:end_idx]
        
        for idx, question in enumerate(selected_questions, start_idx + 1):
            print(f"\n{'='*80}")
            print(f"질문 {idx}/{len(questions)}: {question}")
            print('='*80)
            
            # RAG 모델로 답변 생성
            print("\n🤖 답변 생성 중...")
            try:
                response = self.rag_model.get_conversation_response(question)
                
                # 응답이 딕셔너리인지 확인
                if isinstance(response, dict):
                    answer = response.get('answer', '응답을 생성할 수 없습니다.')
                    sources = response.get('sources', [])
                    confidence = response.get('confidence', 'unknown')
                    coverage = response.get('data_coverage', 'unknown')
                    
                    # 답변 출력
                    print(f"\n💡 모델 응답:")
                    print(answer)
                    
                    # 참고자료 출력
                    if sources:
                        print(f"\n📚 참고자료:")
                        for i, source in enumerate(sources, 1):
                            title = source.get('title', '제목 없음')
                            content = source.get('content', '내용 없음')
                            score = source.get('score', 0)
                            
                            # 내용이 너무 길면 일부만 표시
                            if len(content) > 200:
                                content_preview = content[:200] + "..."
                            else:
                                content_preview = content
                            
                            print(f"\n  [{i}] {title} (유사도: {score:.3f})")
                            print(f"      내용: {content_preview}")
                    else:
                        print("\n📚 참고자료: 없음")
                    
                    # 메타데이터 출력
                    print(f"\n📊 메타정보:")
                    print(f"  - 신뢰도: {confidence}")
                    print(f"  - 데이터 커버리지: {coverage}")
                    
                    # 데이터 커버리지에 따른 처리
                    if coverage == 'none':
                        print("\nℹ️  이 질문은 데이터셋에 정보가 없어 답변할 수 없었습니다.")
                        skip_eval = input("평가를 건너뛰시겠습니까? (y/n): ").lower() == 'y'
                        
                        if skip_eval:
                            # 갭 데이터로 기록
                            gap_data = {
                                'question': question,
                                'skipped': True,
                                'reason': 'no_data',
                                'timestamp': datetime.now().isoformat()
                            }
                            self.session_data['evaluations'].append(gap_data)
                            continue
                    
                    # 답변 평가
                    evaluation = self.evaluator.evaluate_answer(question, answer, sources)
                    
                    # 평가 저장
                    self.evaluator.save_evaluation(evaluation)
                    self.session_data['evaluations'].append(evaluation)
                    
                    print(f"\n✅ 평가 완료: {evaluation['avg_score']:.1f}/10")
                    
                else:
                    print(f"❌ 응답 형식 오류: {type(response)}")
                    print(f"응답 내용: {response}")
                    continue
                
                # 계속 진행 여부
                if idx < start_idx + len(selected_questions):
                    cont = input("\n다음 질문으로 진행하시겠습니까? (y/n): ").lower()
                    if cont != 'y':
                        break
                        
            except Exception as e:
                print(f"❌ 답변 생성 중 오류: {e}")
                import traceback
                traceback.print_exc()
                
                # 오류 발생 시에도 계속 진행할지 선택
                cont = input("오류가 발생했습니다. 다음 질문으로 진행하시겠습니까? (y/n): ").lower()
                if cont != 'y':
                    break
                continue
    
    def _save_session_data(self):
        """세션 데이터 저장"""
        self.session_data['end_time'] = datetime.now().isoformat()
        
        # 평가 통계 계산
        evaluations = [e for e in self.session_data['evaluations'] if not e.get('skipped', False)]
        
        if evaluations:
            avg_score = sum(e.get('avg_score', 0) for e in evaluations) / len(evaluations)
            low_quality_count = len([e for e in evaluations if e.get('avg_score', 0) < 7])
            
            self.session_data['statistics'] = {
                'total_evaluations': len(evaluations),
                'average_score': avg_score,
                'low_quality_count': low_quality_count,
                'skipped_count': len(self.session_data['evaluations']) - len(evaluations),
                'improvement_needed': low_quality_count > 0
            }
        
        # 세션 파일을 reports 폴더에 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_file = os.path.join(self.reports_dir, f'training_session_{timestamp}.json')
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 세션 데이터 저장: {session_file}")
    
    def _update_model_if_needed(self):
        """필요시 모델 업데이트"""
        # 개선이 필요한 평가 확인
        evaluations = [e for e in self.session_data['evaluations'] if not e.get('skipped', False)]
        poor_evaluations = [
            e for e in evaluations 
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
                
                # poor_evaluations를 correction 형태로 변환하여 처리
                corrections = []
                for eval_data in poor_evaluations:
                    correction = {
                        'question': eval_data.get('question', ''),
                        'original_response': eval_data.get('answer', ''),
                        'corrected_response': eval_data.get('correction', ''),
                        'avg_score': eval_data.get('avg_score', 0),
                        'scores': eval_data.get('scores', {}),
                        'feedback': eval_data.get('feedback', ''),
                        'timestamp': eval_data.get('timestamp', datetime.now().isoformat())
                    }
                    corrections.append(correction)
                
                # 모델 업데이트 실행 (수정된 방식)
                for correction in corrections:
                    self.model_updater.update_model_data(correction)
                
                # 업데이트 결과 기록
                self.session_data['improvements_made'] = self.model_updater.update_history
                
                print("✅ 모델 업데이트 완료!")
                
            except Exception as e:
                print(f"❌ 모델 업데이트 중 오류: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("모델 업데이트를 건너뜁니다.")
    
    def _print_summary(self):
        """파인튜닝 결과 요약"""
        print("\n" + "="*60)
        print("📊 모델 파인튜닝 결과 요약")
        print("="*60)
        
        stats = self.session_data.get('statistics', {})
        
        if stats:
            print(f"총 평가 질문: {stats.get('total_evaluations', 0)}개")
            print(f"평균 점수: {stats.get('average_score', 0):.2f}/10")
            print(f"개선 필요: {stats.get('low_quality_count', 0)}개")
            print(f"건너뛴 질문: {stats.get('skipped_count', 0)}개")
            
            if self.session_data.get('improvements_made'):
                print(f"모델 업데이트: {len(self.session_data['improvements_made'])}개 변경사항 적용")
        
        print("\n다음 단계:")
        print("- 만족스러운 결과라면 웹 앱 실행: python app.py")
        print("- 추가 개선이 필요하다면 모델 파인튜닝 재실행")
        print("- 데이터 갭이 많다면 원본 데이터 확장 고려")

def main():
    """모델 파인튜닝 메인 실행"""
    try:
        trainer = ModelTrainer()  # 변경된 클래스명
        trainer.run_training()   # 변경된 메서드명
    except KeyboardInterrupt:
        print("\n\n👋 모델 파인튜닝 프로세스가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 모델 파인튜닝 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
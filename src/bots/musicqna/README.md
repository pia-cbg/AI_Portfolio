# 🎵 MusicQnA (음악 이론 질의응답 AI 모듈)

음악 이론 QnA를 위한 RAG 기반 AI 시스템입니다.  
자체 구축 데이터, 임베딩, 자동질문 생성, 정량평가 등  
연구 및 실제 교육 응용에 적합한 기능을 포함합니다.

---

## 📁 폴더 및 파일 설명

### cli/
- **실험/테스트용 실행 진입점**  
  개발자가 CLI에서 음악 QnA 전체 플로우를 테스트하는 인터페이스

### data_processing/
- **add_concept_type.py**  
  - raw_to_json에서 생성된 JSON을  
    정량평가 가능한 컬럼 구조로 재구조화하여 저장
- **auto_question_generator.py**  
  - Json 노드를 기반으로 자동 질문셋 생성
- **embedding_generator.py**  
  - json_loader로 불러온 json을 임베딩
- **json_loader.py**  
  - 재구조화된 json 데이터 로딩
- **raw_to_json.py**  
  - 음악 이론 csv를 json 형태로 저장

### eval/
- **evaluate_batch_cli.py**  
  - 자동질문셋을 기반으로 배치 평가 실행
- **evaluator.py**  
  - (미구현) 수동 질문 평가 기능용 스크립트

### models/
- **rag_model.py**  
  - RAG(검색+생성) QnA 모델
- **retriever.py**  
  - SentenceTransformer+FAISS 기반 검색 엔진

### prompts/
- **prompts.py**
  - LLM 시스템 프롬프트/템플릿 모음

### utils/
- **passages_formatter.py**
  - RAG 임베딩 근거자료를 보기 좋게 포맷팅

### main.py (미구현)
- 오케스트레이션/통합 서비스를 위한  
  **메인 엔트리포인트 (구현 예정)**
- 외부 오케스트레이터에서 import하여 전체 QnA 체인/엔진 실행 예정

---

## 🔎 추가 안내
- 데이터셋, 평가 결과, 임베딩 등은 `data/musicqna/` 하위 참조
- 상세 실행법 및 최종 통합 안내는 상위(오케스트레이션/루트) README 참고
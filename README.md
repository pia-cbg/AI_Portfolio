# 🎵 AI 음악 이론 교육 시스템

**RAG 기반 음악 이론 Q&A 시스템

자체 구축된 음악 이론 데이터를 활용한 지능형 질의응답 시스템입니다.
사용자 질문을 벡터화하여 관련 음악 이론 정보를 검색하고, OpenAI GPT 기반 LLM을 통해 교육적이고 정확한 답변을 제공합니다.

---

## 🚀 주요 기능

- **RAG 기반 Q&A**: 자체 구축 음악 이론 데이터베이스에서 유사 정보를 검색, 근거 기반 답변 생성

- **데이터셋 기반 답변**: 외부 검색이나 서드파티 지식이 아닌, 직접 구축한 DB 정보만을 활용
- **자동 질문 생성**: 음악 이론 용어 분석 및 질문 템플릿 기반 학습용 데이터 자동 생성
- **웹 인터페이스**: 사용자 친화적 데모/운영용 UI (디스코드 API 연계 준비중)

---

## 🛠 기술 스택

- **Python 3.11.13**
- **AI/LLM**: OpenAI API (GPT)
- **RAG**: Sentence Transformers + FAISS
- **ML/AI**: scikit-learn, numpy
- **Vector DB**: FAISS (Facebook AI Similarity Search)

---

## 📋 설치 및 실행

### 1. 환경 설정
```bash
git clone https://github.com/bogyeongchoi/AI_Portfolio.git
cd AI_Portfolio

# 가상환경 생성
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 파일 생성
cp .env.example .env
```
### 2. API 키 설정
```
# .env 파일에 OpenAI API 키 입력
OPENAI_API_KEY=your_openai_key_here
```
```
# 임베딩 생성 (최초 1회)
python -m src.data_processing.embedding_generator

# main 및 웹 인터페이스
python -m src.main
streamlit run app.py
```

### 3. 시스템 파이프라인
```
Phase 1: 데이터 처리
음악이론.json → 텍스트 청크 분할 → 벡터 임베딩 → FAISS 인덱스

Phase 2: 질의응답
사용자 질문 → 벡터 검색 → 음악 용어 추출 → OpenAI AI GPT 기반 LLM → 답변 생성

Phase 3: 파인튜닝 (선택사항) - (리팩토링중)
# 질문 품질 개선 및 화이트리스트 생성
python -m src.fine_tuning.question_improver

# 답변 품질 개선
python -m src.fine_tuning.model_training
```
### 4. 폴더 트리 - 현재까지 진행상황)
```
AI_Portfolio/
├── LICENSE
├── README.md
├── main.py                      # 실행 진입점
├── requirements.txt
│
├── src/
│   ├── __init__.py
│
│   ├── data_processing/         # 데이터 전처리 & 질문 생성
│   │   ├── json_loader.py
│   │   ├── embedding_generator.py
│   │   └── auto_question_generator.py
│
│   ├── models/                  # RAG 핵심 모델
│   │   ├── rag_model.py
│   │   └── retriever.py
│
│   ├── evaluator.py             # 평가 시스템 (응답 판단 로직)
│   └── run_experiment.py        # 실험 실행 파이프라인
│
├── utils/
│   └── passages_formatter.py    # 문서/패시지 포맷 유틸
│
├── data/
│   ├── raw/                     # 기준 데이터 & 자동 생성 질문
│   │   ├── music_theory_curriculum.json
│   │   ├── music_theory.csv
│   │   ├── auto_concept.py
│   │   ├── auto_questions.json
│   │   └── rawtojson.py
│
│   ├── embeddings/              # 임베딩 결과 (재사용 목적)
│   │   └── music_theory_embeddings.pkl
│
│   └── logs/                    # 평가 시스템 산출물 (평가표 데이터)
│       ├── 1226_1149/
│       │   ├── all.json
│       │   ├── success.json
│       │   ├── partial_fail.json
│       │   └── fail.json
│       ├── 1226_1335/
│       ├── 1226_1425/
│       └── 1226_1456/
│
├── archive/                     # 실험/모델/데이터 백업
│   ├── embeddings/
│   │   └── music_theory_embeddings.pkl
│   ├── model_backup/
│   │   ├── V1_rag_model.py
│   │   ├── V1_retriever.py
│   │   └── V2_rag_model.py
│   └── raw/
│       └── backups/
│           ├── v1_original.json
│           ├── v2_updated.json
│           ├── v3_modifying.json
│           ├── v4_modifying_2.json
│           ├── v5_modifying_3.json
│           └── music_theory_curriculum_2.json

```
# 🎯 핵심 특징

- 음악 용어 인식: 질문에서 음악 이론 관련 용어 자동 추출
- 컨텍스트 기반 검색: 질문과 관련도가 높은 음악 이론 정보 우선 검색
- 품질 관리 시스템: 질문/답변의 정확성, 완전성, 명확성 평가
- 자동 질문 생성: 음악 이론 키워드 기반 학습용 질문 자동 생성
- OpenAI API를 활용한 고품질 답변 생성
- RAG 기반 정확도 향상
- 자체 구축 데이터셋: 구조화된 음악 이론 교육과정 JSON 활용

# 💡 사용 예시
질문: "세컨더리 도미넌트가 뭐야?"

시스템 처리:
질문 벡터화 및 "도미넌트" 키워드 추출
관련 음악 이론 데이터 검색
OpenAI GPT를 통한 전문적 답변 생성

답변: 세컨더리 도미넌트에 대한 상세하고 정확한 설명 제공

# 🔧 시스템 워크플로우
## 데이터 처리
음악이론.json → 텍스트 청크 분할 → 벡터 임베딩 → FAISS 인덱스

## 질의응답
사용자 질문 → 벡터 검색 → 음악 용어 추출 → GPT AI(LLM) → 데이터 기반 답변

## 평가 시스템 (Evaluation System)
평가용 질문 → RAG 응답 생성 → 응답 평가 로직 → 성공 / 부분 실패 / 실패 분류 → 평가 데이터(JSON)

## 🔧 개발자 정보

이 프로젝트는 AI/ML을 활용한 교육 시스템 개발 역량을 보여주는 포트폴리오입니다.

**개발자**: Choi Bo Gyeong

**프로젝트 기간**: 2025.06 - 2025.~~ (진행중)

**핵심 구현 기술**:
- RAG (Retrieval-Augmented Generation) 아키텍처 설계 및 구현
- FAISS 벡터 데이터베이스를 활용한 효율적인 검색 시스템
- Open AI API 연동 및 프롬프트 엔지니어링
- 자동 질문 생성 및 품질 평가 시스템 구축
- Streamlit 기반 웹 인터페이스 개발

**Contact**:
- Email: cbg1704@gmail.com
- GitHub: [@bogyeongchoi](https://github.com/bogyeongchoi)

**Tech Stack**:
`Python` `RAG` `FAISS` `OpenAI` `Streamlit` `Sentence-Transformers` `Fine-tuning`

## 📄 라이센스
MIT License

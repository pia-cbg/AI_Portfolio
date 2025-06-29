# 🎵 AI 음악 이론 교육 시스템

**RAG 기반 음악 이론 Q&A 시스템 with Fine-tuning**

음악 이론 JSON 데이터를 활용한 지능형 질의응답 시스템입니다. 사용자 질문을 벡터화하여 관련 음악 이론을 검색하고, Claude AI를 통해 정확한 답변을 제공합니다.

---

## 🚀 주요 기능

- **RAG 기반 Q&A**: 음악 이론 데이터베이스에서 관련 정보를 검색하여 정확한 답변 제공
- **질문 품질 관리**: 음악 용어 필터링 및 질문 자동 생성
- **파인튜닝 시스템**: 질문/답변 품질 평가 및 모델 개선
- **웹 인터페이스**: Streamlit 기반 사용자 친화적 UI

---

## 🛠 기술 스택

- **Python 3.11**
- **AI/LLM**: Anthropic API
- **RAG**: Sentence Transformers + FAISS + Claude AI
- **ML/AI**: scikit-learn, numpy
- **Web**: Streamlit
- **Vector DB**: FAISS (Facebook AI Similarity Search)

---

## 📋 설치 및 실행

### 1. 환경 설정
```bash
git clone https://github.com/yourusername/AI_Portfolio.git
cd AI_Portfolio

# 가상환경 생성 (Python 3.11)
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 파일 생성
cp .env.example .env

```
### 2. API 키 설정
```
# .env 파일에 Anthropic API 키 입력
ANTHROPIC_API_KEY=your_api_key_here
```
```
# 임베딩 생성 (최초 1회)
python src/data_processing/embedding_generator.py

# CLI 버전
python src/main.py

# 웹 인터페이스
streamlit run app.py
```

### 3. 시스템 파이프라인
```
Phase 1: 데이터 처리
음악이론.json → 텍스트 청크 분할 → 벡터 임베딩 → FAISS 인덱스

Phase 2: 질의응답
사용자 질문 → 벡터 검색 → 음악 용어 추출 → Claude AI → 답변 생성

Phase 3: 파인튜닝 (선택사항)
# 질문 품질 개선
python src/fine_tuning/phase1_question_improvement.py

# 답변 품질 개선
python src/fine_tuning/phase2_model_training.py
```
### 4. 폴더 트리
```
AI_Portfolio/
├── src/
│   ├── data_processing/     # 데이터 처리 및 임베딩
│   ├── models/             # RAG 모델 및 검색기
│   ├── fine_tuning/        # 파인튜닝 시스템
│   └── main.py            # CLI 실행
├── utils/                  # 음악 이론 유틸리티
├── data/                   # 데이터 저장소
└── app.py                 # 웹 인터페이스
```
# 🎯 핵심 특징

- 음악 용어 인식: 질문에서 음악 이론 관련 용어 자동 추출
- 컨텍스트 기반 검색: 질문과 관련도가 높은 음악 이론 정보 우선 검색
- 품질 관리 시스템: 질문/답변의 정확성, 완전성, 명확성 평가
- 자동 질문 생성: 음악 이론 키워드 기반 학습용 질문 자동 생성
- Anthropic Claude API를 활용한 고품질 답변 생성
- RAG 아키텍처로 정확도 향상
- 자체 파인튜닝 시스템 구현

# 💡 사용 예시
질문: "세컨더리 도미넌트가 뭐야?"
시스템 처리:

질문 벡터화 및 "도미넌트" 키워드 추출
관련 음악 이론 데이터 검색
Claude AI를 통한 전문적 답변 생성

답변: 세컨더리 도미넌트에 대한 상세하고 정확한 설명 제공

## 🔧 개발자 정보

이 프로젝트는 AI/ML을 활용한 교육 시스템 개발 역량을 보여주는 포트폴리오입니다.

**개발자**: Choi Bo Gyeong

**프로젝트 기간**: 2025.06 - 2025.07

**핵심 구현 기술**:
- RAG (Retrieval-Augmented Generation) 아키텍처 설계 및 구현
- FAISS 벡터 데이터베이스를 활용한 효율적인 검색 시스템
- Claude AI API 연동 및 프롬프트 엔지니어링
- 자동 질문 생성 및 품질 평가 시스템 구축
- Streamlit 기반 웹 인터페이스 개발

**Contact**:
- Email: cbg1704@gmail.com
- GitHub: [@bogyeongchoi](https://github.com/bogyeongchoi)

**Tech Stack**:
`Python` `RAG` `FAISS` `Claude AI` `Streamlit` `Sentence-Transformers`

## 📄 라이센스
MIT License

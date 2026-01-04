# 🎶 AI 음악 이론 Q&A & 일정 파서 멀티에이전트 데모

**RAG 기반 음악 이론 Q&A + 자연어 일정추출 스케쥴러 · CLI 오케스트레이터 — 즉시 실행 AI 포트폴리오**

_자체 구축 데이터와 사전 임베딩(벡터DB)·자동 질문·자동 평가까지 모두 내장!  
설치 후 바로 실습/테스트 가능한 All-in-One 멀티에이전트 AI 데모입니다._

---

## 🚀 주요 기능

- **에이전트 멀티 시스템**:  
  뮤직QnA(음악 이론 질의응답) & 스케쥴러(자연어 일정 추출) 독립 메뉴 운영
- **RAG 기반 Q&A**:  
  음악 이론 데이터에서 유사 정보 검색 + 근거 기반 GPT 답변
- **자연어 일정 파서**:  
  일정/명령문 자연어 입력 → 이벤트(JSON) 구조 추출 (Google API 연동 준비)
- **자동 질문 생성/평가**:  
  자체 템플릿으로 다양한 질문 생성, 자동 배치 평가/결과 저장
- **즉시 실행 데모**:  
  임베딩 등 데이터 이미 동봉, OPENAI_API_KEY 한 줄만 입력하면 모든 파이프라인 실습 가능
- **CLI/오케스트레이터**:  
  직관적 메뉴 기반 인터페이스; QnA/스케쥴러/자동평가/수동평가
- **향후 확장성**:  
  실시간 평가, Discord·Google Calendar 등 연동 예정

---

## 🛠️ 기술 스택

- **Python 3.11+**
- **OpenAI GPT (LLM)**
- **Sentence Transformers, FAISS (Vector DB)**
- **Numpy, Scikit-learn, Pandas**
- **CLI/Orchestration**: 메뉴 인터페이스, 확장형 오케스트레이션 구조
- **자동 평가**: 질문/답변 품질 자동 채점·결과 누적
- **(확장 중)** Discord Bot, Google API 연동 로드맵

---

## 📋 빠른 실행법
- **항상 프로젝트 루트(root)에서 실행하세요.**

```bash
git clone https://github.com/bogyeongchoi/AI_Portfolio.git
cd AI_Portfolio
conda create -n myenv python=3.11
conda activate myenv
pip install -r requirements.txt
cp .env.example .env

# .env에 OpenAI 키만 입력해 주세요!
# OPENAI_API_KEY=your_openai_key
python demo.py

임베딩/질문/평가 데이터 모두 내장, 별도 빌드/사전처리 필요 없음!
```

## 🏗️ 시스템 파이프라인/구조

### 🎵 뮤직QnA 챗봇
- 질문 입력 → 임베딩 → 벡터/FAISS 검색 → 근거 데이터 Top-K 추출 → OpenAI GPT 기반 답변 (RAG) → 자동 질문/평가 로직 → 배치 평가 결과 저장

- 자동질문 생성/평가:
음악 이론 토픽별 질문셋 생성 → RAG 응답 자동 평가(성공/실패/부분성공) → JSON 저장

### 🗓️ 스케쥴러
- 자연어 일정 입력 → GPT 호출 → 이벤트/누락 필드 자동 추출(JSON)
→ 배치 평가 및 로그 저장

- 구글 캘린더/디스코드 등 외부 서비스 연동 로드맵

### 📦 폴더 구조 예시 (주요 경로만)
```
AI_Portfolio/
│
├── demo.py              # 메인 오케스트레이터
├── requirements.txt
├── .env.example
│
├── data/
│   ├── musicqna/
│   │   ├── embeddings/      # 임베딩 포함!
│   │   ├── batch_logs/      # 평가 산출물
│   │   ├── processed/
│   └── scheduler/
│       ├── batch_logs/
│       ├── processed/
│
└── src/
    └── ... (QnA, Scheduler, 평가 등 전체 코드)
```

### 💡 사용 예시

```
1) 뮤직QnA 시스템 실행
2) 스케쥴러 실행
3) 실시간 평가(수동 입력) - 개발 중
4) 자동질문/배치 평가
q) 종료
> 
```
---
- 음악(RAG) 질문 - 1) 뮤직 QnA 시스템
```
input : 세컨더리 도미넌트가 뭐야?
LLM 답변 : 세컨더리 도미넌트(Secondary Dominant)는 현재 조성의 프라이머리 도미넌트(기본 도미넌트) 이외의 다이어토닉 코드 각각에 임시로 적용되는 도미넌트 코드입니다. ....
```
---
- 스케쥴러 입력 CLI 2) 스케쥴러 실행
```
input : 12월 10일 15시 홍대 미팅
LLM 답변 : {
  "summary": "미팅",
  "start": {
    "dateTime": "12월 10일 15시"
  },
  "end": {
    "dateTime": "12월 10일 16시"
  },
  "description": "홍대"
}
-> 현재는 자연어만 파싱하여 JSON 구조화만 진행시킨 형태
```
---
- 실시간 평가(수동 입력) - 기능 개발 중
---
- 자동 질문 배치 평가 - 4) 자동질문/배치 평가
```
==================================================
   🏷️ CLI 자동질문(배치) 평가 오케스트레이터
==================================================
```
```

[평가 대상]
1) 뮤직QnA 자동질문 셋
2) 스케쥴러 자동질문 셋
q) 종료
```
```
1. 뮤직 QnA 자동 질문
평가할 질문 개수를 입력하세요 : 자동 질문 생성 완료
샘플링 랜덤 시드값을 입력하세요 (엔터시 현재 시각 기준): 추후 배치평가를 통한 시스템 개선시 필요한 시드값

[1/20] 질문: 세컨더리 도미넌트의 원리(원칙)는?
   → 평가결과: success
```
```
2. 스케쥴러 자동 질문
평가할 질문 개수를 입력하세요 : 자동 질문 생성 완료
샘플링 랜덤 시드값을 입력하세요 (엔터시 현재 시각 기준) : 추후 배치평가를 통한 시스템 개선시 필요한 시드값

[1/500] 질문: 3월 14일 16시 30분 강남 카페 상담
   → 평가결과: success
```


## 🎯 아키텍처/워크플로우

### 🎼 뮤직QnA
```
질문 → 임베딩 → FAISS 검색 → RAG(GPT) 답변 → 평가/결과 저장 (자체 DB/임베딩/질문집/평가 내장)
```

### 🗓️ 스케쥴러
```
자연어 일정 → GPT 파서 → JSON 파싱/누락 평가 → 로그 (Google API, Discord 등 외부 연동 예정)
```

## 🌱 향후 발전/로드맵

- 수동 평가시스템/CLI 오케스트레이터 완성
- 실 서비스용 FastAPI+Discord+GoogleAPI형 에이전트(챗봇·일정봇) 구현/배포
- 유저 로그 기반 품질 개선/분석/실데이터 모델 튜닝
- 운영 품질/실시간 모니터링(UI/지표/알림/리포트 등) 도입

## 🔧 개발자 정보


**개발자**: Choi Bo Gyeong

**프로젝트 기간**: 2025.06 - 2025.~~ (진행중)

**핵심 구현 기술**:
- RAG (Retrieval-Augmented Generation) 아키텍처 설계 및 구현
- FAISS 벡터 데이터베이스를 활용한 효율적인 검색 시스템
- Open AI API 연동 및 프롬프트 엔지니어링
- 자동 질문 생성 및 품질 평가 시스템 구축
- 직관적인 CLI 오케스트레이터 구현   (뮤직QnA, 스케쥴러, 평가 자동화 통합 제어)

**Contact**:
- Email: cbg1704@gmail.com
- GitHub: [@bogyeongchoi](https://github.com/bogyeongchoi)

**Tech Stack**:
`Python` `RAG` `FAISS` `OpenAI` `Sentence-Transformers` `Evaluation-driven Pipeline` `Prompt Engineering`


## 📄 라이센스
MIT License

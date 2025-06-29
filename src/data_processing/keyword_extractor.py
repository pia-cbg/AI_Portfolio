import numpy as np
import json
import re
import os
from typing import List, Dict, Set
from sklearn.feature_extraction.text import TfidfVectorizer

class KeywordExtractor:
    def __init__(self, json_path='data/raw/music_theory_curriculum.json'):
        """
        JSON 파일에서 키워드 추출을 위한 초기화
        
        :param json_path: JSON 파일 경로
        """
        self.json_path = json_path
        self.data = self.load_json_data()
        self.keywords = set()
        
        # 음악 이론 화이트리스트
        self.music_whitelist = self._load_music_whitelist()
    
    def _load_music_whitelist(self) -> Set[str]:
        """음악 이론 핵심 용어 화이트리스트"""
        return {
            # 기본 음악 용어
            '코드', '화음', '스케일', '음계', '조성', '화성', '진행', '음정', '리듬', '멜로디', '박자',
            
            # 화성학 용어
            '도미넌트', '토닉', '서브도미넌트', '펑션', '기능', '트라이어드', '세븐스', '트라이톤',
            
            # 코드 종류
            '메이저', '마이너', '디미니쉬드', '어그멘티드', '서스펜디드', '익스텐디드',
            
            # 고급 화성학
            '세컨더리도미넌트', '논다이아토닉', '다이아토닉', '리하모나이제이션', '모드', '모달',
            '트라이톤서브스티튜션', '펜타토닉', '블루스', '텐션', '얼터레이션',
            
            # 진행/움직임
            '강진행', '약진행', '순차진행', '도약진행', '병진행', '반진행', '사성부',
            
            # 음악 형식
            '프레이즈', '모티브', '케이던스', '종지', '아르페지오', '보이싱', '인버전', '전위',
            
            # 리듬/박자
            '싱코페이션', '헤미올라', '폴리리듬', '스윙', '셔플', '그루브',
            
            # 기타 중요 용어
            '가이드톤', '크로매틱', '다이아토닉', '엔하모닉', '모듈레이션', '트랜스포지션',
            '페달포인트', '오스티나토', '카운터포인트', '대위법'
        }
    
    def load_json_data(self) -> Dict:
        """JSON 파일 로드"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"파일을 찾을 수 없습니다: {self.json_path}")
            return {}
        except json.JSONDecodeError:
            print(f"JSON 파싱 오류: {self.json_path}")
            return {}
    
    def extract_text_corpus(self) -> List[str]:
        """JSON 데이터에서 모든 텍스트 추출"""
        corpus = []
        
        def extract_text_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # 키 이름도 중요한 정보로 포함
                    if key not in ['metadata', 'constants']:
                        corpus.append(key.replace('_', ' '))
                    
                    if isinstance(value, str) and len(value.strip()) > 5:
                        corpus.append(value.strip())
                    elif isinstance(value, (dict, list)):
                        extract_text_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_text_recursive(item)
        
        extract_text_recursive(self.data)
        print(f"추출된 텍스트 문서 수: {len(corpus)}")
        return corpus
    
    def extract_keywords_with_tfidf(self, corpus: List[str], top_n: int = 100) -> Set[str]:
        """
        TF-IDF를 사용한 키워드 추출 (음악 이론 특화)
        
        :param corpus: 텍스트 코퍼스
        :param top_n: 추출할 상위 키워드 수
        :return: 추출된 키워드 세트
        """
        # 텍스트 전처리
        def preprocess(text):
            text = re.sub(r'[^\w\s#♭♯°]', ' ', text)
            return text.lower()
        
        # 확장된 불용어
        korean_stopwords = [
            '의', '를', '은', '는', '이', '가', '에', '서', '로', '과', '와', '등', '및', '또한', '때문에', 
            '통해', '위해', '때', '있습니다', '됩니다', '합니다', '줍니다', '말합니다', '느낌을', 
            '사용됩니다', '적용됩니다', '예를', '들어', '같은', '다른', '매우', '특히', '가장', '모든', 
            '어떤', '또는', '그리고', '있는', '없는', '있고', '있으며', '있어', '에서는', '로서', '으로'
        ]
        english_stopwords = ['a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        all_stopwords = korean_stopwords + english_stopwords
        
        # 코퍼스 전처리
        preprocessed_corpus = [preprocess(doc) for doc in corpus]
        
        # TF-IDF 벡터화
        vectorizer = TfidfVectorizer(
            stop_words=all_stopwords,
            max_features=300,  # 여유있게 300개
            min_df=2,
            max_df=0.7,
            ngram_range=(1, 2)
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(preprocessed_corpus)
        except ValueError as e:
            print(f"TF-IDF 벡터화 오류: {e}")
            return set()
        
        # 단어별 TF-IDF 점수 계산
        feature_names = vectorizer.get_feature_names_out()
        tfidf_scores = tfidf_matrix.sum(axis=0).A1
        
        # 점수 기준으로 정렬
        word_scores = list(zip(feature_names, tfidf_scores))
        word_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 화이트리스트 우선 선택
        whitelist_keywords = []
        tfidf_keywords = []
        
        for word, score in word_scores:
            cleaned_word = self._clean_keyword(word)
            
            # 화이트리스트에 있는 단어 우선
            if any(white_term in cleaned_word for white_term in self.music_whitelist):
                whitelist_keywords.append(cleaned_word)
            # 음악 기호나 코드 패턴
            elif self._is_music_pattern(cleaned_word):
                tfidf_keywords.append(cleaned_word)
            # 일반 TF-IDF 키워드
            elif len(cleaned_word) >= 3 and score > 0:
                tfidf_keywords.append(cleaned_word)
        
        # 최종 키워드 선택 (화이트리스트 우선)
        final_keywords = set()
        
        # 화이트리스트 키워드 모두 포함
        final_keywords.update(whitelist_keywords[:top_n])
        
        # 남은 공간을 TF-IDF 키워드로 채움
        remaining = top_n - len(final_keywords)
        if remaining > 0:
            final_keywords.update(tfidf_keywords[:remaining])
        
        print(f"화이트리스트 키워드: {len(whitelist_keywords)}개")
        print(f"패턴 매칭 키워드: {len(tfidf_keywords)}개")
        print(f"최종 선택 키워드: {len(final_keywords)}개")
        
        return final_keywords
    
    def _is_music_pattern(self, word: str) -> bool:
        """음악 패턴 매칭"""
        # 코드 패턴 (C, Dm7, G7sus4 등)
        if re.match(r'^[A-G][#♭]?(maj|min|m|M|dim|aug|sus|add)?\d*$', word):
            return True
        
        # 로마 숫자 패턴 (I, ii, V7 등)
        if re.match(r'^[ivIV]+[m]?\d*$', word):
            return True
        
        # 음악 기호 포함
        if re.search(r'[#♭♯°]', word):
            return True
        
        return False
    
    def _clean_keyword(self, keyword: str) -> str:
        """키워드 정제"""
        # 조사 제거
        particles = ['은', '는', '이', '가', '을', '를', '와', '과', '로', '으로', '에', '에서', '의', '도', '만']
        
        for particle in particles:
            if keyword.endswith(particle) and len(keyword) > len(particle) + 1:
                keyword = keyword[:-len(particle)]
        
        # 공백 정리
        keyword = ' '.join(keyword.split())
        
        return keyword.strip()
    
    def extract_named_entities(self) -> Set[str]:
        """JSON에서 명시적으로 정의된 개념들 추출"""
        entities = set()
        
        def extract_entities_recursive(obj, key_path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # 메타데이터, 상수 제외
                    if key not in ['metadata', 'constants']:
                        # 키 이름을 엔티티로 추가
                        clean_key = key.replace('_', ' ').strip()
                        if len(clean_key) > 2:
                            entities.add(clean_key)
                    
                    # 재귀적 탐색
                    if isinstance(value, (dict, list)):
                        extract_entities_recursive(value, f"{key_path}.{key}")
                        
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_entities_recursive(item, f"{key_path}[{i}]")
        
        extract_entities_recursive(self.data)
        
        # 화이트리스트와 매칭되는 엔티티만 필터링
        filtered_entities = set()
        for entity in entities:
            if any(white_term in entity for white_term in self.music_whitelist):
                filtered_entities.add(entity)
        
        print(f"명시적 개념 추출: {len(filtered_entities)}개")
        return filtered_entities
    
    def process(self, top_n: int = 100) -> Set[str]:
        """
        키워드 추출 전체 프로세스
        
        :param top_n: 추출할 상위 키워드 수
        :return: 최종 추출된 키워드
        """
        # 1. 텍스트 코퍼스 추출
        corpus = self.extract_text_corpus()
        
        if not corpus:
            print("추출할 텍스트가 없습니다.")
            return set()
        
        # 2. TF-IDF 기반 키워드 추출
        tfidf_keywords = self.extract_keywords_with_tfidf(corpus, top_n)
        
        # 3. 명시적 개념 추출
        named_entities = self.extract_named_entities()
        
        # 4. 두 결과 합치기
        all_keywords = tfidf_keywords.union(named_entities)
        
        # 5. 화이트리스트 키워드 보장
        for white_term in self.music_whitelist:
            # 코퍼스에 존재하는 화이트리스트 용어는 무조건 포함
            if any(white_term in doc.lower() for doc in corpus):
                all_keywords.add(white_term)
        
        # 6. 최종 필터링
        final_keywords = self._final_filter(all_keywords, top_n)
        
        print(f"\n최종 키워드: {len(final_keywords)}개")
        
        return final_keywords
    
    def _final_filter(self, keywords: Set[str], top_n: int) -> Set[str]:
        """최종 필터링 및 우선순위 정렬"""
        scored_keywords = []
        
        for keyword in keywords:
            score = 0
            
            # 화이트리스트 점수
            if keyword in self.music_whitelist:
                score += 10
            elif any(white_term in keyword for white_term in self.music_whitelist):
                score += 5
            
            # 길이 점수 (너무 짧거나 긴 것 페널티)
            if 3 <= len(keyword) <= 15:
                score += 2
            
            # 음악 패턴 점수
            if self._is_music_pattern(keyword):
                score += 3
            
            if score > 0:
                scored_keywords.append((keyword, score))
        
        # 점수 기준 정렬
        scored_keywords.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 N개 선택
        return set(kw[0] for kw in scored_keywords[:top_n])
    
    def save_keywords(self, keywords: Set[str]):
        """추출된 키워드를 파일로 저장"""
        keywords_dir = 'data/fine_tuning/keywords'
        os.makedirs(keywords_dir, exist_ok=True)
        
        keywords_file = os.path.join(keywords_dir, 'extracted_keywords.json')
        
        # Set을 List로 변환하여 저장 (길이순 정렬)
        keywords_list = sorted(list(keywords), key=lambda x: (-len(x.split()), x))
        
        with open(keywords_file, 'w', encoding='utf-8') as f:
            json.dump(keywords_list, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 키워드 {len(keywords_list)}개 저장 완료: {keywords_file}")
        
        # 샘플 출력
        print("\n📌 주요 키워드 (상위 20개):")
        for i, keyword in enumerate(keywords_list[:20], 1):
            print(f"{i:2d}. {keyword}")
        
        return keywords_list

def main():
    extractor = KeywordExtractor()
    keywords = extractor.process(top_n=100)
    
    # 키워드 저장
    extractor.save_keywords(keywords)

if __name__ == "__main__":
    main()
class KeywordExtractor:
    def __init__(self, json_path='data/raw/music_theory_curriculum.json'):
        """
        JSON 파일에서 키워드 추출을 위한 초기화
        
        :param json_path: JSON 파일 경로
        """
        self.json_path = json_path
        self.data = self.load_json_data()
        self.keywords = set()
    
    def load_json_data(self) -> Dict:
        """JSON 파일 로드"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"파일을 찾을 수 없습니다: {self.json_path}")
            return {}
        except json.JSONDecodeError:
            print(f"JSON 파싱 오류: {self.json_path}")
            return {}
    
    def extract_text_corpus(self) -> List[str]:
        """JSON 데이터에서 모든 텍스트 추출"""
        corpus = []
        
        def extract_text_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and len(value.strip()) > 5:  # 의미있는 텍스트만
                        corpus.append(value.strip())
                    elif isinstance(value, (dict, list)):
                        extract_text_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_text_recursive(item)
        
        extract_text_recursive(self.data)
        print(f"추출된 텍스트 문서 수: {len(corpus)}")
        return corpus
    
    def extract_keywords_with_tfidf(self, corpus: List[str], top_n: int = 200) -> Set[str]:
        """
        TF-IDF를 사용한 키워드 추출 (음악 이론 특화)
        
        :param corpus: 텍스트 코퍼스
        :param top_n: 추출할 상위 키워드 수
        :return: 추출된 키워드 세트
        """
        # 텍스트 전처리
        def preprocess(text):
            # 음악 기호 보존
            text = re.sub(r'[^\w\s#♭♯°]', ' ', text)  # 음악 기호는 보존
            return text.lower()
        
        # 한국어 + 영어 불용어
        korean_stopwords = ['의', '를', '은', '는', '이', '가', '에', '서', '로', '과', '와', '등', '및', '또한', '때문에', '통해', '위해', '때']
        english_stopwords = ['a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        all_stopwords = korean_stopwords + english_stopwords
        
        # 코퍼스 전처리
        preprocessed_corpus = [preprocess(doc) for doc in corpus]
        
        # TF-IDF 벡터화 (설정 대폭 확장)
        vectorizer = TfidfVectorizer(
            stop_words=all_stopwords,
            max_features=500,  # 100 → 500으로 증가
            min_df=2,          # 최소 2번 이상 나타나는 단어
            max_df=0.8,        # 80% 이상 문서에 나타나는 단어 제외
            ngram_range=(1, 2) # 1-gram, 2-gram 모두 사용
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(preprocessed_corpus)
        except ValueError as e:
            print(f"TF-IDF 벡터화 오류: {e}")
            return set()
        
        # 단어별 TF-IDF 점수 계산
        feature_names = vectorizer.get_feature_names_out()
        tfidf_scores = tfidf_matrix.sum(axis=0).A1
        
        # 점수 기준으로 정렬
        word_scores = list(zip(feature_names, tfidf_scores))
        word_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 음악 이론 관련 키워드 우선 선택
        music_keywords = []
        general_keywords = []
        
        for word, score in word_scores:
            # 음악 이론 키워드 판별 (더 포괄적으로)
            if self._is_music_theory_keyword(word):
                music_keywords.append(word)
            else:
                general_keywords.append(word)
        
        # 음악 키워드 우선, 부족하면 일반 키워드로 채움
        selected_keywords = music_keywords[:int(top_n * 0.8)]  # 80%는 음악 키워드
        if len(selected_keywords) < top_n:
            remaining = top_n - len(selected_keywords)
            selected_keywords.extend(general_keywords[:remaining])
        
        print(f"음악 이론 키워드: {len(music_keywords)}개")
        print(f"일반 키워드: {len(general_keywords)}개")
        print(f"선택된 키워드: {len(selected_keywords)}개")
        
        return set(selected_keywords)
    
    
    def _is_music_theory_keyword(self, word: str) -> bool:
        """음악 이론 키워드인지 판별"""
        # JSON 데이터에서 음악 패턴 동적 추출
        music_patterns = self._extract_music_patterns()
        
        # 음악 기호나 숫자 조합
        if re.search(r'[#♭♯°]', word) or re.search(r'\d+', word):
            return True
            
        # 패턴 매칭
        for pattern in music_patterns:
            if re.search(pattern, word, re.IGNORECASE):
                return True
                
        return False
    
    def _extract_music_patterns(self) -> List[str]:
        """JSON 데이터에서 음악 관련 패턴 추출"""
        patterns = set()
        
        def extract_patterns_recursive(obj):
            if isinstance(obj, dict):
                for key in ['title', 'name', 'concept', 'term']:
                    if key in obj and isinstance(obj[key], str):
                        # 핵심 단어 추출
                        words = re.findall(r'\b[\w가-힣]+\b', obj[key])
                        for word in words:
                            if len(word) > 2:
                                patterns.add(f'.*{word}.*')
                
                for value in obj.values():
                    extract_patterns_recursive(value)
                    
            elif isinstance(obj, list):
                for item in obj:
                    extract_patterns_recursive(item)
        
        extract_patterns_recursive(self.data)
        return list(patterns)
    
    def extract_named_entities(self) -> Set[str]:
        """JSON에서 명시적으로 정의된 개념들 추출"""
        entities = set()
        
        def extract_entities_recursive(obj, key_path=""):
            if isinstance(obj, dict):
                # 제목, 이름, 정의 등의 필드에서 직접 추출
                for key in ['title', 'name', 'concept', 'definition', 'term']:
                    if key in obj and isinstance(obj[key], str):
                        entity = obj[key].strip()
                        if len(entity) > 1:
                            entities.add(entity)
                
                # 재귀적 탐색
                for k, v in obj.items():
                    extract_entities_recursive(v, f"{key_path}.{k}")
                    
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_entities_recursive(item, f"{key_path}[{i}]")
        
        extract_entities_recursive(self.data)
        print(f"명시적 개념 추출: {len(entities)}개")
        return entities
    
    def process(self, top_n: int = 200) -> Set[str]:
        """
        키워드 추출 전체 프로세스
        
        :param top_n: 추출할 상위 키워드 수
        :return: 최종 추출된 키워드
        """
        # 1. 텍스트 코퍼스 추출
        corpus = self.extract_text_corpus()
        
        if not corpus:
            print("추출할 텍스트가 없습니다.")
            return set()
        
        # 2. TF-IDF 기반 키워드 추출
        tfidf_keywords = self.extract_keywords_with_tfidf(corpus, top_n)
        
        # 3. 명시적 개념 추출
        named_entities = self.extract_named_entities()
        
        # 4. 두 결과 합치기
        all_keywords = tfidf_keywords.union(named_entities)
        
        print(f"TF-IDF 키워드: {len(tfidf_keywords)}개")
        print(f"명시적 개념: {len(named_entities)}개")
        print(f"총 키워드: {len(all_keywords)}개")
        
        return all_keywords
    
    def save_keywords(self, keywords: Set[str]):
        """추출된 키워드를 파일로 저장"""
        keywords_dir = 'data/fine_tuning/keywords'
        os.makedirs(keywords_dir, exist_ok=True)
        
        keywords_file = os.path.join(keywords_dir, 'extracted_keywords.json')
        
        # Set을 List로 변환하여 저장 (길이순 정렬)
        keywords_list = sorted(list(keywords), key=len, reverse=True)
        
        with open(keywords_file, 'w', encoding='utf-8') as f:
            json.dump(keywords_list, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 키워드 {len(keywords_list)}개 저장 완료: {keywords_file}")
        return keywords_list

def main():
    extractor = KeywordExtractor()
    keywords = extractor.process(top_n=200)  # 200개로 증가
    
    print("\n추출된 키워드 (상위 20개):")
    sorted_keywords = sorted(keywords, key=len, reverse=True)
    for i, keyword in enumerate(sorted_keywords[:20], 1):
        print(f"{i:2d}. {keyword}")
    
    # 키워드 저장
    extractor.save_keywords(keywords)

if __name__ == "__main__":
    main()
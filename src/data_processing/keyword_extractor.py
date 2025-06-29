import json
import re
from typing import List, Dict, Set
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class KeywordExtractor:
    def __init__(self, json_path='data/raw/music_theory_curriculum.json'):
        self.json_path = json_path
        self.data = self.load_json_data()
        self.keywords = set()
    
    def load_json_data(self) -> Dict:
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
        """
        JSON 데이터에서 모든 텍스트 추출
        
        :return: 텍스트 코퍼스 리스트
        """
        corpus = []
        
        def extract_text_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str):
                        corpus.append(value)
                    elif isinstance(value, (dict, list)):
                        extract_text_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_text_recursive(item)
        
        extract_text_recursive(self.data)
        return corpus
    
    def extract_keywords_with_tfidf(self, corpus: List[str], top_n: int = 50) -> Set[str]:
        """
        TF-IDF를 사용한 키워드 추출
        
        :param corpus: 텍스트 코퍼스
        :param top_n: 추출할 상위 키워드 수
        :return: 추출된 키워드 세트
        """
        # 텍스트 전처리
        def preprocess(text):
            # 특수문자 제거, 공백 정리
            text = re.sub(r'[^\w\s]', '', text)
            return text.lower()
        
        # 코퍼스 전처리
        preprocessed_corpus = [preprocess(doc) for doc in corpus]
        
        # TF-IDF 벡터화
        vectorizer = TfidfVectorizer(
            stop_words=['의', '를', '은', '는', '이', '가'],  # 한국어 불용어 추가
            max_features=100  # 최대 피처 수 제한
        )
        tfidf_matrix = vectorizer.fit_transform(preprocessed_corpus)
        
        # 단어별 TF-IDF 점수 계산
        feature_names = vectorizer.get_feature_names_out()
        tfidf_scores = tfidf_matrix.sum(axis=0).A1
        
        # 상위 키워드 추출
        top_indices = tfidf_scores.argsort()[-top_n:][::-1]
        keywords = {feature_names[i] for i in top_indices}
        
        return keywords
    
    def process(self, top_n: int = 50) -> Set[str]:
        """
        키워드 추출 전체 프로세스
        
        :param top_n: 추출할 상위 키워드 수
        :return: 최종 추출된 키워드
        """
        # 텍스트 코퍼스 추출
        corpus = self.extract_text_corpus()
        
        # TF-IDF 기반 키워드 추출
        keywords = self.extract_keywords_with_tfidf(corpus, top_n)
        
        print(f"총 추출된 키워드 수: {len(keywords)}")
        return keywords

    def save_keywords(self, keywords: Set[str]):
        """추출된 키워드를 파일로 저장"""
        os.makedirs('data/fine_tuning/keywords', exist_ok=True)
        
        keywords_file = 'data/fine_tuning/keywords/extracted_keywords.json'
        with open(keywords_file, 'w', encoding='utf-8') as f:
            json.dump(list(keywords), f, ensure_ascii=False, indent=2)
        
        print(f"키워드 저장 완료: {keywords_file}")
        
def main():
    extractor = KeywordExtractor()
    keywords = extractor.process()
    
    print("\n추출된 키워드:")
    for keyword in sorted(keywords):
        print(keyword)

if __name__ == "__main__":
    main()
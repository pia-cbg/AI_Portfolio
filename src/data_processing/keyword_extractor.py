import numpy as np
import json
import re
import os
from typing import List, Dict, Set
from sklearn.feature_extraction.text import TfidfVectorizer

class KeywordExtractor:
    def __init__(self, json_path='data/raw/music_theory_curriculum.json'):
        self.json_path = json_path
        self.data = self.load_json_data()
        self.music_whitelist = self._load_music_whitelist()

    def _load_music_whitelist(self) -> Set[str]:
        """주요 음악 이론 용어 리스트"""
        return {
            "코드", "화음", "스케일", "음계", "조성", "화성", "진행", "음정", "리듬", "멜로디", "박자",
            "도미넌트", "토닉", "서브도미넌트", "펑션", "기능", "트라이어드", "세븐스", "트라이톤",
            "메이저", "마이너", "디미니쉬드", "어그멘티드", "서스펜디드", "익스텐디드",
            "세컨더리도미넌트", "논다이아토닉", "다이아토닉", "리하모나이제이션", "모드", "모달",
            "트라이톤서브스티튜션", "펜타토닉", "블루스", "텐션", "얼터레이션",
            "강진행", "약진행", "순차진행", "도약진행", "병진행", "반진행", "사성부",
            "프레이즈", "모티브", "케이던스", "종지", "아르페지오", "보이싱", "인버전", "전위",
            "싱코페이션", "헤미올라", "폴리리듬", "스윙", "셔플", "그루브",
            "가이드톤", "크로매틱", "엔하모닉", "모듈레이션", "트랜스포지션",
            "페달포인트", "오스티나토", "카운터포인트", "대위법", "AP 노트", "페달", "서스4",
            # 필요 시 확장
        }

    def load_json_data(self) -> Dict:
        try:
            with open(self.json_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"❌ 파일 없음: {self.json_path}")
            return {}
        except json.JSONDecodeError:
            print(f"❌ JSON 파싱 오류: {self.json_path}")
            return {}

    def extract_text_corpus(self) -> List[str]:
        """JSON 데이터에서 모든 텍스트 추출"""
        corpus = []
        def extract(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # 키 이름도 정보로 포함
                    if key not in ['metadata', 'constants']:
                        corpus.append(key.replace('_', ' '))
                    if isinstance(value, str) and len(value.strip()) > 5:
                        corpus.append(value.strip())
                    elif isinstance(value, (dict, list)):
                        extract(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract(item)
        extract(self.data)
        print(f"📦 추출된 텍스트 개수: {len(corpus)}")
        return corpus

    def is_music_word(self, word: str, whitelist: Set[str]) -> bool:
        word = word.lower().strip()
        return any(w in word or word in w for w in whitelist)

    def extract_keywords_with_tfidf(self, corpus: List[str], top_n: int = 200) -> Set[str]:
        """TF-IDF로 음악적 용어만 우선 추출, 비음악어 최소화"""
        def preprocess(text):
            text = re.sub(r'[^\w\s#♭♯°]', ' ', text)
            return text.lower()
        korean_stopwords = ['의','를','은','는','이','가','에','서','로','과','와','등','및','또한','때문에','통해','위해','때']
        english_stopwords = ['a','an','the','and','or','but','in','on','at','to','for','of','with','by']
        stopwords = korean_stopwords + english_stopwords

        pre_corpus = [preprocess(doc) for doc in corpus]

        vectorizer = TfidfVectorizer(
            stop_words=stopwords,
            max_features=500,
            min_df=2,
            max_df=0.8,
            ngram_range=(1,2)
        )
        try:
            tfidf_matrix = vectorizer.fit_transform(pre_corpus)
        except ValueError as e:
            print(f"TF-IDF 오류: {e}")
            return set()
        feature_names = vectorizer.get_feature_names_out()
        tfidf_scores = tfidf_matrix.sum(axis=0).A1
        word_scores = list(zip(feature_names, tfidf_scores))
        word_scores.sort(key=lambda x: x[1], reverse=True)

        whitelist = self.music_whitelist
        wh_items, music_items, other_items = [], [], []
        for word, score in word_scores:
            w = word.strip().lower()
            if self.is_music_word(w, whitelist):
                wh_items.append(w)
            elif self._is_music_pattern(w):
                music_items.append(w)
            else:
                other_items.append(w)
        # 우선순위: 1) 화이트리스트 2) 음악패턴 3) 나머지
        result = list(dict.fromkeys(wh_items))
        need = top_n - len(result)
        if need > 0:
            result.extend([w for w in music_items if w not in result][:need])
        need = top_n - len(result)
        if need > 0:
            result.extend([w for w in other_items if w not in result][:need])
        return set(result[:top_n])

    def _is_music_pattern(self, word: str) -> bool:
        # 코드명, 로마숫자, 음악 특수문자 등
        if re.match(r'^[A-G][#♭b]?(\w+)?\d*$', word): return True
        if re.match(r'^[ivIV]+[mM]?\d*$', word): return True
        if re.search(r'[#♭♯°]', word): return True
        # 영어 약어나 특수 용어도 추가 확대
        for pat in ['sus', 'dim', 'aug', 'maj', 'min', 'triad', 'tension', 'voice', 'mode', 'arpeggio']:
            if pat in word: return True
        return False

    def extract_named_entities(self) -> Set[str]:
        """JSON에서 화이트리스트만 통과하도록"""
        entities = set()
        def recursive(obj):
            if isinstance(obj, dict):
                for key in ['title','name','concept','definition','term']:
                    if key in obj and isinstance(obj[key], str):
                        e = obj[key].strip()
                        if len(e) > 1 and self.is_music_word(e, self.music_whitelist):
                            entities.add(e)
                for v in obj.values():
                    recursive(v)
            elif isinstance(obj, list):
                for item in obj:
                    recursive(item)
        recursive(self.data)
        print(f"🎼 명시적 음악 개념 추출: {len(entities)}개")
        return entities

    def process(self, top_n: int = 200) -> Set[str]:
        corpus = self.extract_text_corpus()
        if not corpus:
            print("❌ 추출할 텍스트 없음.")
            return set()
        tfidf_keywords = self.extract_keywords_with_tfidf(corpus, top_n)
        named_entities = self.extract_named_entities()
        # 화이트리스트 단어는 corpus에 등장하지 않아도 무조건 넣음(음악적 용어 최대 확보)
        for white in self.music_whitelist:
            tfidf_keywords.add(white)
        all_keywords = tfidf_keywords.union(named_entities)
        print(f"🎵 최종 키워드 (중복제거): {len(all_keywords)}개")
        return all_keywords

    def save_keywords(self, keywords: Set[str]):
        keywords_dir = "data/fine_tuning/keywords"
        os.makedirs(keywords_dir, exist_ok=True)
        file_path = os.path.join(keywords_dir, "extracted_keywords.json")
        kw_list = sorted(list(keywords), key=lambda x: (-len(x.split()), x))
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(kw_list, f, ensure_ascii=False, indent=2)
        print(f"✅ 키워드 {len(kw_list)}개 저장 완료: {file_path}")
        print("샘플:", ", ".join(kw_list[:10]))
        return kw_list

def main():
    extractor = KeywordExtractor()
    keywords = extractor.process(top_n=200)
    extractor.save_keywords(keywords)

if __name__ == "__main__":
    main()
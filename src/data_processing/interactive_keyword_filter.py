import json
import os
import re
from typing import Set, List, Dict
from collections import Counter

class InteractiveKeywordFilter:
    def __init__(self, json_path='data/raw/music_theory_curriculum.json'):
        self.json_path = json_path
        self.data = self.load_json_data()
        
        # 저장 경로
        self.approved_keywords = set()
        self.rejected_keywords = set()
        self.save_path = 'data/fine_tuning/keywords/approved_keywords.json'
        self.rejected_path = 'data/fine_tuning/keywords/rejected_keywords.json'
        
        # 기존 선별 결과 로드
        self._load_previous_selections()
    
    def load_json_data(self) -> Dict:
        """JSON 데이터 로드"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"JSON 로드 오류: {e}")
            return {}
    
    def _load_previous_selections(self):
        """이전 선별 결과 로드"""
        # 승인된 키워드
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, 'r', encoding='utf-8') as f:
                    self.approved_keywords = set(json.load(f))
                print(f"기존 승인 키워드: {len(self.approved_keywords)}개")
            except:
                pass
        
        # 거부된 키워드
        if os.path.exists(self.rejected_path):
            try:
                with open(self.rejected_path, 'r', encoding='utf-8') as f:
                    self.rejected_keywords = set(json.load(f))
                print(f"기존 거부 키워드: {len(self.rejected_keywords)}개")
            except:
                pass
    
    def extract_all_candidates(self) -> List[tuple]:
        """JSON에서 모든 후보 키워드 추출 (빈도와 함께)"""
        candidates = []
        
        # 1. JSON 구조에서 키 이름 추출
        structure_terms = self._extract_from_structure()
        
        # 2. 텍스트 내용에서 용어 추출
        content_terms = self._extract_from_content()
        
        # 3. 빈도 계산
        all_terms = structure_terms + content_terms
        term_frequency = Counter(all_terms)
        
        # 4. 정리 및 필터링
        for term, freq in term_frequency.items():
            clean_term = self._clean_term(term)
            
            # 기본 필터링
            if (len(clean_term) >= 2 and 
                not clean_term.isdigit() and
                not self._is_common_word(clean_term)):
                
                candidates.append((clean_term, freq))
        
        # 빈도순 정렬
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 중복 제거
        seen = set()
        unique_candidates = []
        for term, freq in candidates:
            if term not in seen:
                seen.add(term)
                unique_candidates.append((term, freq))
        
        return unique_candidates
    
    def _extract_from_structure(self) -> List[str]:
        """JSON 구조에서 키워드 추출"""
        terms = []
        
        def recursive_extract(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key not in ['metadata', 'constants']:
                        # 키 이름 추가
                        clean_key = key.replace('_', ' ').strip()
                        terms.append(clean_key)
                        
                        # 키를 단어별로 분해
                        words = re.findall(r'[a-zA-Z가-힣]+', clean_key)
                        terms.extend(words)
                        
                        # 재귀 호출
                        recursive_extract(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for item in obj:
                    recursive_extract(item, path)
        
        recursive_extract(self.data)
        return terms
    
    def _extract_from_content(self) -> List[str]:
        """텍스트 내용에서 키워드 추출"""
        terms = []
        
        def extract_text_content(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and len(value) > 10:
                        # 텍스트에서 의미있는 단어 추출
                        words = re.findall(r'[a-zA-Z가-힣]{2,}', value)
                        terms.extend(words)
                    elif isinstance(value, (dict, list)):
                        extract_text_content(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_text_content(item)
        
        extract_text_content(self.data)
        return terms
    
    def _clean_term(self, term: str) -> str:
        """용어 정제"""
        # 공백 정리
        term = ' '.join(term.split())
        
        # 특수문자 정리 (음악 기호는 보존)
        term = re.sub(r'[^\w\s#♭♯°가-힣]', '', term)
        
        return term.strip()
    
    def _is_common_word(self, word: str) -> bool:
        """일반적인 단어 필터링"""
        common_words = {
            '있습니다', '됩니다', '합니다', '때문', '경우', '같은', '다른', '매우', '특히',
            '예를', '들어', '통해', '위해', '대해', '에서', '으로', '로서', '그리고',
            '또는', '하지만', '그러나', '따라서', '이러한', '그런', '이런', '저런'
        }
        return word.lower() in common_words
    
    def start_interactive_filtering(self):
        """인터랙티브 키워드 선별 시작"""
        print("🎵 음악 용어 선별 시스템")
        print("="*50)
        
        # 후보 키워드 추출
        candidates = self.extract_all_candidates()
        
        # 이미 처리된 것들 제외
        new_candidates = [
            (term, freq) for term, freq in candidates 
            if term not in self.approved_keywords and term not in self.rejected_keywords
        ]
        
        print(f"전체 후보: {len(candidates)}개")
        print(f"새로운 후보: {len(new_candidates)}개")
        
        if not new_candidates:
            print("✅ 모든 키워드가 이미 처리되었습니다.")
            return
        
        print("\n명령어:")
        print("y = 음악 용어임 (승인)")
        print("n = 음악 용어 아님 (거부)")
        print("s = 저장하고 종료")
        print("q = 저장하지 않고 종료")
        print("show = 현재까지 승인된 키워드 보기")
        print("-"*50)
        
        # 하나씩 확인
        for i, (term, freq) in enumerate(new_candidates):
            # 원본 형태들도 찾아서 보여주기
            original_forms = self._find_original_forms(term)
            
            print(f"\n[{i+1}/{len(new_candidates)}]")
            print(f"정제된 용어: '{term}' (빈도: {freq})")
            
            if original_forms:
                print(f"원본 형태들: {', '.join(original_forms[:5])}")  # 상위 5개만
            
            while True:
                choice = input("선택 (y/n/s/q/show): ").lower().strip()
                
                if choice == 'y':
                    self.approved_keywords.add(term)
                    print(f"✅ '{term}' 승인됨")
                    break
                elif choice == 'n':
                    self.rejected_keywords.add(term)
                    print(f"❌ '{term}' 거부됨")
                    break
                elif choice == 's':
                    self._save_selections()
                    print("💾 저장 완료!")
                    return
                elif choice == 'q':
                    print("👋 종료")
                    return
                elif choice == 'show':
                    self._show_approved()
                else:
                    print("올바른 명령어를 입력하세요 (y/n/s/q/show)")
        
        # 모든 후보 처리 완료
        print(f"\n✅ 모든 후보 처리 완료!")
        print(f"승인된 키워드: {len(self.approved_keywords)}개")
        print(f"거부된 키워드: {len(self.rejected_keywords)}개")
        
        save_choice = input("\n결과를 저장하시겠습니까? (y/n): ")
        if save_choice.lower() == 'y':
            self._save_selections()
            
    def _find_original_forms(self, cleaned_term: str) -> List[str]:
        """정제된 용어의 원본 형태들 찾기"""
        originals = []
        
        # 모든 텍스트에서 이 용어가 어떤 형태로 나타났는지 찾기
        def search_in_text(obj):
            if isinstance(obj, str):
                # 정제된 용어가 포함된 단어들 찾기
                words = re.findall(r'[가-힣]+', obj)
                for word in words:
                    if cleaned_term in self._remove_korean_particles(word):
                        originals.append(word)
            elif isinstance(obj, dict):
                for value in obj.values():
                    search_in_text(value)
            elif isinstance(obj, list):
                for item in obj:
                    search_in_text(item)
        
        search_in_text(self.data)
        
        # 중복 제거 및 빈도순 정렬
        from collections import Counter
        original_counts = Counter(originals)
        return [word for word, count in original_counts.most_common(10)]
    
    def _show_approved(self):
        """현재까지 승인된 키워드 보기"""
        if not self.approved_keywords:
            print("아직 승인된 키워드가 없습니다.")
            return
        
        print(f"\n✅ 승인된 키워드 ({len(self.approved_keywords)}개):")
        for i, keyword in enumerate(sorted(self.approved_keywords), 1):
            print(f"{i:2d}. {keyword}")
        print()
    
    def _save_selections(self):
        """선별 결과 저장"""
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        
        # 승인된 키워드 저장
        with open(self.save_path, 'w', encoding='utf-8') as f:
            json.dump(sorted(list(self.approved_keywords)), f, ensure_ascii=False, indent=2)
        
        # 거부된 키워드 저장
        with open(self.rejected_path, 'w', encoding='utf-8') as f:
            json.dump(sorted(list(self.rejected_keywords)), f, ensure_ascii=False, indent=2)
        
        print(f"✅ 승인 키워드 저장: {self.save_path}")
        print(f"✅ 거부 키워드 저장: {self.rejected_path}")
    def _clean_term(self, term: str) -> str:
        """용어 정제 (조사 제거 포함)"""
        # 1단계: 기본 정리
        term = ' '.join(term.split())
        term = re.sub(r'[^\w\s#♭♯°가-힣]', '', term)
        
        # 2단계: 한국어 조사 제거
        term = self._remove_korean_particles(term)
        
        return term.strip()

    def _remove_korean_particles(self, word: str) -> str:
        """한국어 조사 제거"""
        # 조사 목록 (빈도 높은 순서)
        particles = [
            '을', '를', '이', '가', '은', '는', '에', '에서', '으로', '로', 
            '와', '과', '의', '도', '만', '부터', '까지', '처럼', '같이', 
            '부터', '마저', '조차', '라도', '이나', '나', '든지', '거나'
        ]
        
        original_word = word
        
        for particle in particles:
            if word.endswith(particle) and len(word) > len(particle) + 1:
                # 조사 제거
                candidate = word[:-len(particle)]
                
                # 제거 후 유효한 단어인지 확인
                if self._is_valid_after_particle_removal(candidate, particle):
                    word = candidate
                    break
        
        return word

    def _is_valid_after_particle_removal(self, candidate: str, removed_particle: str) -> bool:
        """조사 제거 후 유효성 검증"""
        # 1. 너무 짧으면 안됨
        if len(candidate) < 2:
            return False
        
        # 2. 숫자만 남으면 안됨
        if candidate.isdigit():
            return False
        
        # 3. 특정 조사는 더 엄격하게
        if removed_particle in ['을', '를']:
            # "음을" → "음" 같은 경우는 OK
            # "소음을" → "소음" 같은 경우도 일단 허용 (나중에 사용자가 판단)
            return True
        
        return True
    
    
def main():
    filter_system = InteractiveKeywordFilter()
    filter_system.start_interactive_filtering()

if __name__ == "__main__":
    main()
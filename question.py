import json
from collections import Counter

# json 데이터를 data 변수에 저장했다고 가정
data = json.load(open('/Users/cbg/github/AI_Portfolio/data/fine_tuning/questions/question_evaluations.json','r'))


# 1. 각 dict에서 'keyword'만 추출
keywords = [item['keyword'] for item in data]

# 2. Counter로 개수 집계
keyword_counts = Counter(keywords)

# 3. 결과 출력
for keyword, count in keyword_counts.most_common():
    print(f"{keyword}: {count}")
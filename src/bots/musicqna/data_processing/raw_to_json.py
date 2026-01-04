import pandas as pd
import numpy as np

# CSV 파일 읽기 (경로와 파일명 맞게 설정)
df = pd.read_csv('data/raw/music_theory.csv')

# node_id, parent_id 모두 int로 변환 (NA는 None으로)
df['node_id'] = df['node_id'].astype('Int64')   # pandas의 Nullable Integer 타입 사용
df['parent_id'] = df['parent_id'].astype('Int64')


# JSON 파일로 저장 (utf-8, 들여쓰기 포함, 한글 깨짐 방지)
df.to_json('data/raw/music_theory.json', orient='records', force_ascii=False, indent=2)

print("변환 완료: data/raw/music_theory.json")
#!/usr/bin/env python
import sys
import os

# 현재 스크립트 위치에서 src 디렉토리 찾기
current_file = os.path.abspath(__file__)
src_dir = os.path.dirname(os.path.dirname(current_file))  # src 디렉토리
project_root = os.path.dirname(src_dir)  # 프로젝트 루트

# sys.path에 src 디렉토리 추가
sys.path.insert(0, src_dir)

print(f"현재 파일: {current_file}")
print(f"src 디렉토리: {src_dir}")
print(f"프로젝트 루트: {project_root}")

try:
    from data_processing.keyword_extractor import KeywordExtractor
    from fine_tuning.fine_tuning_cli import FineTuningCLI
    from fine_tuning.evaluator import Evaluator
    from fine_tuning.model_updater import ModelUpdater
    print("✅ 모든 모듈 import 성공")
except ImportError as e:
    print(f"❌ Import 오류: {e}")
    print("개별 파일을 직접 실행해주세요:")
    print(f"python {src_dir}/data_processing/keyword_extractor.py")
    print(f"python {src_dir}/fine_tuning/fine_tuning_cli.py")
    sys.exit(1)

def main():
    print("🎵 음악 이론 파인튜닝 프로세스 시작")
    
    # 1. 키워드 추출
    print("\n1️⃣ 키워드 추출 중...")
    extractor = KeywordExtractor()
    keywords = extractor.process()
    extractor.save_keywords(keywords)
    
    # 2. 파인튜닝 CLI 실행
    print("\n2️⃣ 파인튜닝 평가 시작...")
    cli = FineTuningCLI()
    cli.start()
    
    print("\n✅ 파인튜닝 프로세스 완료!")

if __name__ == "__main__":
    main()
"""
CLI 자동질문/배치 평가 오케스트레이터
- 각 시스템의 독립적인 batch 평가 CLI(main)을 직접 호출
"""

import sys

# 실제 평가 CLI에서 main 함수 import
try:
    from src.bots.musicqna.eval.evaluate_batch_cli import main as musicqna_batch_main
except Exception as e:
    print(f"[IMPORT ERROR] musicqna 평가 모듈 불러오기 실패: {e}")
    musicqna_batch_main = None

try:
    from src.bots.scheduler.eval.evaluate_batch_cli import main as scheduler_batch_main
except Exception as f:
    print(f"[IMPORT ERROR] scheduler 평가 모듈 불러오기 실패: {f}")
    scheduler_batch_main = None

def main():
    print("=" * 50)
    print("   🏷️ CLI 자동질문(배치) 평가 오케스트레이터")
    print("=" * 50)
    print("\n[평가 대상]")
    print("1) 뮤직QnA 자동질문 셋")
    print("2) 스케쥴러 자동질문 셋")
    print("q) 종료")
    sel = input("> ").strip()
    if sel == "1":
        if musicqna_batch_main:
            musicqna_batch_main()
        else:
            print("뮤직QnA 평가 모듈이 없습니다.")
    elif sel == "2":
        if scheduler_batch_main:
            scheduler_batch_main()
        else:
            print("스케쥴러 평가 모듈이 없습니다.")
    elif sel.lower() in ("q", "quit", "exit"):
        print("종료합니다.")
        return
    else:
        print("올바른 옵션을 입력하세요.")

if __name__ == "__main__":
    main()
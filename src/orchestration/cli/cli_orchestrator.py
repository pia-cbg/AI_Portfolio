# src/orchestration/cli/cli_orchestrator.py

import sys

from src.bots.musicqna.cli.cli_main import main as qna_cli_main
from src.bots.scheduler.cli.cli_main import main as scheduler_cli_main
from src.orchestration.cli.cli_eval_orchestrator import main as eval_cli_main
from src.orchestration.cli.cli_eval_batch import main as eval_batch_main

def main():
    print("="*40)
    print(" UNIFIED CLI ORCHESTRATOR")
    print("="*40)

    while True:
        print("\n어떤 기능을 실행하시겠습니까?")
        print("1) 뮤직QnA 시스템 실행")
        print("2) 스케쥴러(일정파서) 실행")
        print("3) 실시간 평가(수동 입력)")
        print("4) 자동질문/배치 평가")
        print("q) 종료")
        sel = input("> ").strip()

        if sel == "1":
            qna_cli_main()
        elif sel == "2":
            scheduler_cli_main()
        elif sel == "3":
            eval_cli_main()
        elif sel == "4":
            eval_batch_main()
        elif sel.lower() in ["q","quit","exit"]:
            print("프로그램을 종료합니다.")
            sys.exit(0)
        else:
            print("올바른 선택지를 입력하세요.")

if __name__ == "__main__":
    main()
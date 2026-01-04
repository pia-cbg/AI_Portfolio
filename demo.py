import os
import sys

SRC_PATH = os.path.join(os.path.dirname(__file__), 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

def check_env_files():
    print("=== 환경설정 체크 ===")
    if not os.path.isfile('.env'):
        print("⚠️  .env 파일이 없습니다. 환경 설정이 필요할 수 있습니다.")
        print("-> 환경 변수 파일(.env)은 외부에 공개되지 않으니, 각자 준비 및 README를 참고하세요.")
    else:
        print(f"✅ .env 파일이 정상적으로 존재합니다.")

def run_cli_orchestrator():
    print("🚀 Orchestration 데모를 실행합니다")
    from src.orchestration.cli.cli_orchestrator import main
    main()

if __name__ == "__main__":
    check_env_files()
    run_cli_orchestrator()
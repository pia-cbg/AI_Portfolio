import random
import json
import os

YEARS = [f"{y}년" for y in range(2023, 2027)]  # 예: 2023년~2026년
MONTHS = [f"{i}월" for i in range(1, 13)]
DAYS = [f"{i}일" for i in range(1, 32)]
HOURS = [f"{h}시" for h in range(8, 22)]        # 8시~21시
MINUTES = [f"{m}분" for m in [0, 15, 30, 45]]
PLACES = ["강남 카페", "회사", "도서관", "서울역", "회의실", "집", "온라인", "미용실", "피시방", " "]
CONTENTS = ["미팅", "회의", "점심", "저녁식사", "병원예약", "스터디", "상담", "세미나", "면접", "동호회", " "]

NOISES = [
    "약속 잡아줘", "회의 일정 잡아달라니까", "오전 중에 예약해줘",
    "점심 때 추가해줘", "주말에 시간 돼?", "빠른 시간에 회의해줘",
    "언제든 미팅 잡아줘", "추후 일정 추가", "7월 8일 예약해줘",
    "도서관 스터디", "회사", "적당한 시간에 회의 추가", "오늘쯤 만날까"
]

def perfect_case():
    use_year = random.random() < 0.3  # 30%만 년도 포함
    slots = []
    if use_year:
        slots.append(random.choice(YEARS))
    slots += [
        random.choice(MONTHS),
        random.choice(DAYS),
        random.choice(HOURS),
        random.choice(MINUTES),
        random.choice(PLACES),
        random.choice(CONTENTS)
    ]
    # 공백 정리: 빈 PLACE 처리는 자동 제외
    return " ".join([x for x in slots if x.strip()])

def drop_year_case():
    slots = [
        random.choice(MONTHS),
        random.choice(DAYS),
        random.choice(HOURS),
        random.choice(MINUTES) if random.random() < 0.5 else "",
        random.choice(PLACES),
        random.choice(CONTENTS)
    ]
    return " ".join([x for x in slots if x.strip()])

def partial_case():
    kind = random.choice([0, 1])   # 0: 장소 빠짐, 1: 시간 빠짐
    if kind == 0:
        # 장소 빠진 케이스
        slots = [
            random.choice(MONTHS),
            random.choice(DAYS),
            random.choice(HOURS),
            random.choice(MINUTES) if random.random() < 0.5 else "",
            random.choice(CONTENTS)
        ]
    else:
        # 시간 빠진 케이스
        slots = [
            random.choice(MONTHS),
            random.choice(DAYS),
            random.choice(PLACES),
            random.choice(CONTENTS)
        ]
    return " ".join([x for x in slots if x.strip()])

def noise_case():
    return random.choice(NOISES)

def generate_dataset(num=1000):
    n_perfect = int(num * 0.4)
    n_dropyear = int(num * 0.3)
    n_partial = int(num * 0.2)
    n_noise = num - n_perfect - n_dropyear - n_partial
    dataset = (
        [perfect_case() for _ in range(n_perfect)] +
        [drop_year_case() for _ in range(n_dropyear)] +
        [partial_case() for _ in range(n_partial)] +
        [noise_case() for _ in range(n_noise)]
    )
    random.shuffle(dataset)
    return dataset

if __name__ == "__main__":
    samples = generate_dataset(1000)
    save_dir = os.path.join("data", "scheduler", "processed")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, "auto_schedule_questions.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    print(f"샘플 20개:\n", "\n".join(samples[:20]))
    print(f"총 {len(samples)}개를 저장했습니다: {save_path}")
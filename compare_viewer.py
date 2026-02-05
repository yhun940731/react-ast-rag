import json
import random
from pathlib import Path

# --- [설정] 파일 경로 설정 ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "dataset"

def load_data():
    """구축된 데이터셋(JSON)을 메모리로 로드합니다."""
    # 1. Baseline 데이터 로드
    with (DATA_DIR / "dataset_baseline.json").open("r", encoding="utf-8") as f:
        baseline = json.load(f)
    # 2. 제안 방법(Ours) 데이터 로드
    with (DATA_DIR / "dataset_ours.json").open("r", encoding="utf-8") as f:
        ours = json.load(f)
    return baseline, ours

def print_separator(char="=", length=80):
    """구분선을 출력하여 가독성을 높입니다."""
    print(char * length)

def compare_academic_view():
    """
    논문 삽입용(Figure 1) 비교 결과를 출력하는 메인 함수입니다.
    무작위로 하나의 파일을 선정하여 두 가지 청킹 방식의 결과를 대조합니다.
    """
    base_data, our_data = load_data()
    
    # [타겟 선정] 비교 효과가 좋은 복잡한 파일(Hook이나 Provider 포함)을 우선 탐색
    target_files = list(set(d['filepath'] for d in our_data))
    candidates = [f for f in target_files if "use" in f or "Provider" in f]
    
    # 후보가 없으면 전체 파일 중 선택
    if not candidates: candidates = target_files
    
    # 랜덤 선택
    target_file = random.choice(candidates)
    
    # --- [출력 시작] ---
    print("\n")
    print_separator("=")
    print(f" [그림 1] 청킹 전략에 따른 코드 분할 결과 비교 사례")
    print(f" 분석 대상 파일: {target_file}")
    print_separator("=")
    
    # 1. 기존 방식(Baseline) 시각화
    print(f"\n (a) 기존 고정 크기 청킹 방식 (Baseline, Chunk Size=500)")
    print_separator("-")
    
    base_chunks = [d for d in base_data if d['filepath'] == target_file]
    
    # 지면 관계상 상위 3개 청크만 출력
    for i, chunk in enumerate(base_chunks[:3]): 
        # 줄바꿈을 공백으로 치환하여 한 줄로 표현
        content = chunk['content'].replace('\n', ' ')
        # 너무 길면 75자에서 자름 (...)
        truncated_content = (content[:75] + '...') if len(content) > 75 else content
        
        print(f"  [청크 {i+1}] 메타데이터: {chunk['metadata']}")
        print(f"      내용: \"{truncated_content}\"")
        
        # 첫 번째 청크에서 문맥 단절이 발생할 수 있음을 주석으로 명시
        if i == 0 and len(base_chunks) > 1:
            print("      -> 주석: 경계면에서 구문적/의미적 문맥 단절 발생 가능")
            
    print(f"  ... (총 {len(base_chunks)}개의 파편화된 청크 생성됨)")

    print("\n")
    
    # 2. 제안 방식(Proposed) 시각화
    print(f" (b) 제안하는 AST 기반 의미론적 청킹 (Proposed Method)")
    print_separator("-")
    
    our_chunks = [d for d in our_data if d['filepath'] == target_file]
    
    for i, chunk in enumerate(our_chunks):
        # 학술적 용어로 라벨링 변경
        category = chunk['type']
        if "Hook" in category: category_label = "로직 단위 (Hook)"
        elif "JSX" in category: category_label = "뷰 단위 (JSX)"
        else: category_label = "컴포넌트 선언부 (Signature)"
        
        content = chunk['content'].replace('\n', ' ')
        truncated_content = (content[:75] + '...') if len(content) > 75 else content
        
        print(f"  [청크 {i+1}] 유형: {category_label}")
        print(f"      메타데이터 (상위 문맥): {chunk['parent_component']}")
        print(f"      내용: \"{truncated_content}\"")
        
    print(f"  ... (총 {len(our_chunks)}개의 의미론적 청크 생성됨)")
    print_separator("=")
    print("\n")

if __name__ == "__main__":
    compare_academic_view()
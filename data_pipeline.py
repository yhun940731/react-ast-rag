import json
from pathlib import Path
from tree_sitter import Language, Parser
import tree_sitter_typescript as tst

# --- [설정] ---
BASE_DIR = Path(__file__).resolve().parent
TS_LANGUAGE = Language(tst.language_typescript())
TSX_LANGUAGE = Language(tst.language_tsx())

def get_parser_for_file(filepath):
    parser = Parser()
    if str(filepath).endswith(".tsx"):
        parser.language = TSX_LANGUAGE
    else:
        parser.language = TS_LANGUAGE
    return parser

# --- [Baseline Algorithm] 고정 크기 청킹 (Fixed-size Chunking) ---
def chunk_baseline(code, chunk_size=500, overlap=50):
    """
    코드를 단순 텍스트로 간주하여 고정된 길이로 분할합니다.
    - chunk_size: 청크 당 문자 수
    - overlap: 경계면 정보 손실 방지를 위한 중첩 구간
    """
    chunks = []
    for i in range(0, len(code), chunk_size - overlap):
        chunk_content = code[i : i + chunk_size]
        if len(chunk_content) < 50: continue # 너무 짧은 노이즈 제거
        chunks.append({
            "type": "Baseline (Fixed)",
            "content": chunk_content,
            "metadata": "None (Context Lost)" # 문맥 정보 부재 명시
        })
    return chunks

# --- [Proposed Algorithm] AST 기반 의미론적 청킹 (Semantic Chunking) ---
def chunk_ours(tree, code):
    """
    AST를 순회하며 코드의 기능적 단위(Hook, JSX)를 추출하고 구조적 메타데이터를 부여합니다.
    """
    chunks = []
    code_bytes = bytes(code, "utf8")
    
    def get_text(node):
        return code_bytes[node.start_byte : node.end_byte].decode("utf8")

    def traverse(node, parent_name):
        # 1. Hook 추출
        if node.type == "call_expression":
            func_node = node.child_by_field_name("function")
            if func_node and get_text(func_node).startswith("use"):
                chunks.append({
                    "id": f"{parent_name}_hook_{node.start_point[0]}",
                    "type": "Logic (Hook)",
                    "parent_component": parent_name,
                    "content": get_text(node),
                    "line": node.start_point[0] + 1
                })
                return

        # 2. JSX 추출
        if node.type == "return_statement":
            for child in node.children:
                if child.type in ["parenthesized_expression", "jsx_element", "jsx_fragment"]:
                    chunks.append({
                        "id": f"{parent_name}_jsx_{node.start_point[0]}",
                        "type": "View (JSX)",
                        "parent_component": parent_name,
                        "content": get_text(child),
                        "line": node.start_point[0] + 1
                    })
                    return

        for child in node.children:
            traverse(child, parent_name)

    cursor = tree.walk()
    visited_children = False
    
    while True:
        node = cursor.node
        if node.type in ["function_declaration", "lexical_declaration"]:
            name = "Unknown"
            if node.type == "function_declaration":
                n = node.child_by_field_name("name")
                if n: name = get_text(n)
            elif node.type == "lexical_declaration":
                for child in node.children:
                    if child.type == "variable_declarator":
                        n = child.child_by_field_name("name")
                        if n: name = get_text(n)
            
            if name and name[0].isupper():
                chunks.append({
                    "id": f"{name}_sig_{node.start_point[0]}",
                    "type": "Component Signature",
                    "parent_component": name,
                    "content": f"Component: {name}",
                    "line": node.start_point[0] + 1
                })
                traverse(node, name)

        if not visited_children and cursor.goto_first_child():
            visited_children = False
        elif cursor.goto_next_sibling():
            visited_children = False
        elif cursor.goto_parent():
            visited_children = True
        else:
            break
            
    return chunks

# --- [실행 파이프라인] ---
def run_pipeline():
    print("[Process] 데이터셋 구축 파이프라인(Dataset Pipeline) 가동 시작...")
    
    # 전체 파일 탐색 (재귀적)
    search_dir = BASE_DIR / "base-ui"
    raw_files = list(search_dir.rglob("*.tsx"))
    
    # 노이즈 필터링: 테스트 코드, 의존성 모듈 제외
    target_files = []
    for f in raw_files:
        f_str = str(f)
        if "node_modules" in f_str: continue
        if ".test." in f_str or ".spec." in f_str: continue
        # 필요 시 예제 코드(docs) 포함/제외 결정
        if "docs" in f_str: continue 
        target_files.append(f)

    # 타겟 파일 부족 시 예외 처리 (실험용 데이터 확보를 위해 범위 확장)
    if len(target_files) < 10:
        print("[Info] 소스 코드 수량이 부족하여 docs(예제) 디렉토리를 포함합니다.")
        target_files = [f for f in raw_files if "node_modules" not in str(f) and ".test." not in str(f)]

    print(f"[Info] 수집된 분석 대상 파일: {len(target_files)}개")

    dataset_baseline = []
    dataset_ours = []

    for filepath in target_files:
        try:
            with filepath.open("r", encoding="utf-8") as f:
                code = f.read()
            
            parser = get_parser_for_file(filepath)
            tree = parser.parse(bytes(code, "utf8"))
            
            # A. Baseline 처리
            base_chunks = chunk_baseline(code)
            for c in base_chunks: c['filepath'] = filepath.name
            dataset_baseline.extend(base_chunks)
            
            # B. Proposed 처리
            our_chunks = chunk_ours(tree, code)
            unique_ours = {v['id']: v for v in our_chunks}.values() # ID 기반 중복 제거
            for c in unique_ours: c['filepath'] = filepath.name
            dataset_ours.extend(unique_ours)
            
        except Exception as e:
            # 인코딩 오류 등은 무시
            pass

    # 결과 저장
    output_dir = BASE_DIR / "dataset"
    output_dir.mkdir(exist_ok=True)

    with (output_dir / "dataset_baseline.json").open("w", encoding="utf-8") as f:
        json.dump(dataset_baseline, f, indent=2, ensure_ascii=False)
        
    with (output_dir / "dataset_ours.json").open("w", encoding="utf-8") as f:
        json.dump(list(dataset_ours), f, indent=2, ensure_ascii=False)

    print("\n[Success] 데이터셋 구축 완료.")
    print(f"   - Baseline(Fixed-size) 데이터: {len(dataset_baseline)}개 청크 생성")
    print(f"   - Proposed(AST-based) 데이터: {len(dataset_ours)}개 청크 생성")
    print(f"   - 저장 경로: {output_dir}")

if __name__ == "__main__":
    run_pipeline()
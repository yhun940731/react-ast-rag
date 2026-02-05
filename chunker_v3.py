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

# --- [타겟 선정] ---
# 실제 소스 코드(Source Code)만을 대상으로 함 (테스트, 인덱스, 데모 제외)
search_dir = BASE_DIR / "base-ui"
all_files = list(search_dir.rglob("*.tsx"))

target_file = None
for f in all_files:
    if not any(x in str(f) for x in [".spec.", ".test.", "index.", "demo"]):
        target_file = f
        break

if not target_file:
    print("[Warning] 적합한 소스 파일을 찾지 못하여 대체 파일을 사용합니다.")
    target_file = all_files[0]

print(f"[Target] 최종 알고리즘 적용 대상: {target_file.name}")
print("-" * 70)

# --- [파싱] ---
with target_file.open("r", encoding="utf-8") as f:
    code_text = f.read()
lines = code_text.split('\n')
code_bytes = bytes(code_text, "utf8")
parser = get_parser_for_file(target_file)
tree = parser.parse(code_bytes)

# --- [제안 알고리즘: AST-based Chunking with Metadata] ---
chunks = []

def get_text(node):
    return code_bytes[node.start_byte : node.end_byte].decode("utf8")

def traverse_component(node, parent_name):
    """
    컴포넌트 내부를 순회하며 기능적 단위(Hook, JSX)를 추출하고 메타데이터를 결합합니다.
    """
    # 1. Hook 추출 (Logic Unit)
    if node.type == "call_expression":
        func_node = node.child_by_field_name("function")
        if func_node:
            func_name = get_text(func_node)
            if func_name.startswith("use"):
                chunks.append({
                    "type": "Logic (Hook)",
                    "parent_component": parent_name, # 상위 문맥 보존
                    "content": get_text(node),
                    "line_number": node.start_point[0] + 1
                })
                return

    # 2. JSX 추출 (View Unit)
    if node.type == "return_statement":
        for child in node.children:
            if child.type in ["parenthesized_expression", "jsx_element", "jsx_fragment"]:
                chunks.append({
                    "type": "View (JSX)",
                    "parent_component": parent_name, # 상위 문맥 보존
                    "content": get_text(child)[:100] + " ... (생략)",
                    "line_number": node.start_point[0] + 1
                })
                return

    for child in node.children:
        traverse_component(child, parent_name)

# 최상위 순회: 컴포넌트 선언부 식별
cursor = tree.walk()
visited_children = False

while True:
    node = cursor.node
    # 함수형 컴포넌트 정의 식별
    if node.type in ["function_declaration", "lexical_declaration"]:
        comp_name = "Unknown"
        
        # Case A: function ComponentName() {}
        if node.type == "function_declaration":
            name_node = node.child_by_field_name("name")
            if name_node: comp_name = get_text(name_node)
            
        # Case B: const ComponentName = () => {}
        elif node.type == "lexical_declaration":
            for child in node.children:
                if child.type == "variable_declarator":
                    name_node = child.child_by_field_name("name")
                    if name_node: comp_name = get_text(name_node)
        
        # PascalCase(대문자 시작)를 컴포넌트로 간주
        if comp_name[0].isupper(): 
            print(f"[Component Identified] '{comp_name}' 내부 구조 분석 시작...")
            chunks.append({
                "type": "Component Signature",
                "parent_component": comp_name,
                "content": f"Component Definition: {comp_name}",
                "line_number": node.start_point[0] + 1
            })
            traverse_component(node, comp_name)

    # 트리 순회 이동
    if not visited_children and cursor.goto_first_child():
        visited_children = False
    elif cursor.goto_next_sibling():
        visited_children = False
    elif cursor.goto_parent():
        visited_children = True
    else:
        break

# --- [결과 출력] ---
print("\n[Output] RAG 시스템 임베딩을 위한 정형 데이터(JSON)")
print(json.dumps(chunks, indent=2, ensure_ascii=False))
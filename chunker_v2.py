import os
import glob
from tree_sitter import Language, Parser

# --- [설정] ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TS_GRAMMAR_PATH = os.path.join(BASE_DIR, "vendor", "tree-sitter-typescript", "tsx")
BUILD_DIR = os.path.join(BASE_DIR, "build")
LIB_FILE = os.path.join(BUILD_DIR, "my-languages.so")

TSX_LANGUAGE = Language(LIB_FILE, 'tsx')
parser = Parser()
parser.set_language(TSX_LANGUAGE)

# --- [타겟 선정] 복잡도가 높은 파일 탐색 ---
# Hook 사용 빈도가 높은 파일(예: 'use' 접두사 파일)을 우선 선정하여 분할 성능 테스트
search_pattern = os.path.join(BASE_DIR, "base-ui", "**", "*.tsx")
all_files = glob.glob(search_pattern, recursive=True)

target_file = None
# 1순위: 'use' 키워드가 포함된 파일 (Hook 로직 검증용)
for f in all_files:
    if "use" in os.path.basename(f) and "test" not in f:
        target_file = f
        break

if not target_file and all_files:
    target_file = all_files[0]

print(f"[Target] 정밀 분석 대상: {os.path.basename(target_file)}")

# --- [파싱] ---
with open(target_file, "r", encoding="utf-8") as f:
    code_text = f.read()
lines = code_text.split('\n')
tree = parser.parse(bytes(code_text, "utf8"))

# --- [분석 로직] 컴포넌트 내부 구조(Internal Structure) 식별 ---
print("\n[Deep Analysis] 컴포넌트 내부의 논리(Logic) 및 뷰(View) 영역 식별")
print("=" * 70)

def get_code_snippet(node):
    start = node.start_point[0]
    return lines[start].strip()[:60] + "..."

def traverse(node, depth=0):
    """
    재귀적 트리 순회(Recursive Traversal)를 통해 Hook과 JSX 노드를 탐색합니다.
    """
    # 1. React Hook 식별: 'use'로 시작하는 함수 호출(Call Expression)
    if node.type == "call_expression":
        func_name_node = node.child_by_field_name("function")
        if func_name_node:
            func_name = code_text[func_name_node.start_byte : func_name_node.end_byte]
            if func_name.startswith("use"):
                print(f"{'  ' * depth}⚡ [Logic] Hook 호출 식별: {func_name} (Line {node.start_point[0]+1})")
                return # Hook 내부는 단일 청크로 간주하여 하위 탐색 중단

    # 2. UI 요소 식별: JSX Element
    if node.type in ["jsx_element", "jsx_self_closing_element"]:
        print(f"{'  ' * depth}🎨 [View] JSX 렌더링 블록 식별 (Line {node.start_point[0]+1})")
        print(f"{'  ' * depth}    ㄴ 내용: {get_code_snippet(node)}")
        return # JSX 내부는 단일 청크로 간주하여 하위 탐색 중단

    # 3. 컴포넌트 진입점 확인
    if node.type in ["function_declaration", "lexical_declaration"]:
        pass

    # 자식 노드 재귀 탐색
    for child in node.children:
        traverse(child, depth + 1)

traverse(tree.root_node)
print("=" * 70)
print("[Complete] 코드의 의미론적 분할(Semantic Segmentation) 가능성 검증 완료.")
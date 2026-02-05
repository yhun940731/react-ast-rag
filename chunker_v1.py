from pathlib import Path
from tree_sitter import Language, Parser
import tree_sitter_typescript as tst

# --- [설정] 기본 경로 및 파서 설정 ---
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

# --- [타겟 선정] 유의미한 분석 대상 파일 탐색 ---
# 단순 인덱스(index.tsx) 파일이 아닌, 실제 로직이 포함된 컴포넌트 파일(Button 등)을 우선 탐색
search_dir = BASE_DIR / "base-ui" / "packages" / "react" / "src"
found_files = list(search_dir.rglob("*.tsx"))

if not found_files:
    search_dir = BASE_DIR / "base-ui"
    found_files = list(search_dir.rglob("*.tsx"))

target_file = None
for f in found_files:
    # 테스트 파일 및 단순 export 파일 제외
    if "index.tsx" not in f.name and "test" not in f.name:
        target_file = f
        break

if not target_file:
    target_file = found_files[0]

print(f"[Target] 분석 대상 파일: {target_file.name}")
print(f"         (경로: {target_file})")

# --- [AST 파싱] ---
with target_file.open("r", encoding="utf-8") as f:
    code_text = f.read()

parser = get_parser_for_file(target_file)
tree = parser.parse(bytes(code_text, "utf8"))
root_node = tree.root_node
lines = code_text.split('\n')

# --- [분석 로직] 주요 구문 구조(Syntactic Structure) 추출 ---
print("\n[Analysis] 코드의 주요 선언부(Declaration) 식별 시뮬레이션")
print("=" * 70)

def print_chunk_info(node, label):
    """
    식별된 노드의 메타데이터(타입, 라인 범위, 미리보기)를 출력합니다.
    """
    start_line = node.start_point[0]
    end_line = node.end_point[0]
    first_line_code = lines[start_line].strip()
    
    print(f"[{label}] 식별됨 (Line {start_line+1} ~ {end_line+1})")
    print(f"   ㄴ 코드 미리보기: {first_line_code[:60]}...")
    print("-" * 70)

# 트리 순회(Traversal)를 통해 최상위 선언부 탐색
cursor = tree.walk()
visited_children = False

while True:
    if visited_children:
        if cursor.goto_next_sibling():
            visited_children = False
        elif cursor.goto_parent():
            visited_children = True
        else:
            break
    else:
        node = cursor.node
        
        # 1. 함수 선언 (Function Declaration)
        if node.type == "function_declaration":
            print_chunk_info(node, "함수 선언(Function Declaration)")
            
        # 2. 어휘적 선언 (Lexical Declaration - const/let)
        # 주로 화살표 함수형 컴포넌트나 상수 정의에 사용됨
        elif node.type == "lexical_declaration":
            print_chunk_info(node, "변수/컴포넌트 선언(Lexical Declaration)")
            
        # 3. 임포트 구문 (Import Statement) - 필요 시 필터링 가능
        elif node.type == "import_statement":
            pass

        if cursor.goto_first_child():
            visited_children = False
        else:
            visited_children = True

print("\n[Complete] 주요 의미 단위(Semantic Unit)의 후보군 추출 완료.")
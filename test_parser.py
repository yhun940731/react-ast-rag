from pathlib import Path
from tree_sitter import Language, Parser
import tree_sitter_typescript as tst

# --- [설정] 경로 및 환경 변수 초기화 ---
# 현재 스크립트의 위치를 기준으로 절대 경로를 설정하여 실행 환경의 일관성 보장
BASE_DIR = Path(__file__).resolve().parent

print(f"[System] 현재 작업 디렉토리: {BASE_DIR}")

# --- 1. 언어 로드 (tree-sitter 0.25+ API) ---
# - tree-sitter 0.25.x에서는 Parser.set_language / Language.build_library가 제거됨
# - tree-sitter-typescript 패키지가 제공하는 PyCapsule을 Language로 래핑하여 사용
print("[Process] Tree-sitter 언어 로드 중...")
TS_LANGUAGE = Language(tst.language_typescript())
TSX_LANGUAGE = Language(tst.language_tsx())

def get_parser_for_file(filepath):
    parser = Parser()
    if str(filepath).endswith(".tsx"):
        parser.language = TSX_LANGUAGE
    else:
        parser.language = TS_LANGUAGE
    return parser

# --- 3. 검증용 타겟 파일 탐색 ---
# Base-UI 라이브러리 내의 임의의 .tsx 파일을 선정하여 파싱 테스트 수행
search_pattern = BASE_DIR / "base-ui" / "packages" / "react" / "src"
found_files = list(search_pattern.rglob("*.tsx"))

if not found_files:
    print("[Error] .tsx 파일을 찾을 수 없습니다. 'base-ui' 디렉토리 및 소스 코드를 확인하십시오.")
    exit()

target_file = found_files[0]
print(f"[Target] 분석 대상 파일 선정: {target_file.name}")
print(f"         (경로: {target_file})")

# --- 2. 파서(Parser) 초기화 ---
parser = get_parser_for_file(target_file)

# --- 4. 구문 분석(Parsing) 수행 ---
with target_file.open("r", encoding="utf-8") as f:
    code_text = f.read()

# 소스 코드를 바이트로 변환하여 파싱 수행 후 AST 생성
tree = parser.parse(bytes(code_text, "utf8"))
root_node = tree.root_node

# --- 5. 결과 검증 ---
print("\n[Result] 추상 구문 트리(AST) 구조 확인 (상위 500자)")
print("=" * 60)
# S-expression (Lisp-like notation) 형태로 트리 구조 시각화
print(str(root_node)[:500] + " ... (생략)")
print("=" * 60)

print(f"\n[Success] 파싱 검증 완료.")
print(f"   - 루트 노드 타입: {root_node.type} (Expected: program)")
print(f"   - 최상위 자식 노드 개수: {len(root_node.children)}개")
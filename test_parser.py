import os
import glob
from tree_sitter import Language, Parser

# --- [설정] 경로 및 환경 변수 초기화 ---
# 현재 스크립트의 위치를 기준으로 절대 경로를 설정하여 실행 환경의 일관성 보장
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. 언어 정의 파일(Grammar) 경로 (vendor/tree-sitter-typescript/tsx)
TS_GRAMMAR_PATH = os.path.join(BASE_DIR, "vendor", "tree-sitter-typescript", "tsx")

# 2. 컴파일된 언어 라이브러리(.so) 저장 경로
BUILD_DIR = os.path.join(BASE_DIR, "build")
if not os.path.exists(BUILD_DIR):
    os.makedirs(BUILD_DIR)
LIB_FILE = os.path.join(BUILD_DIR, "my-languages.so")

print(f"[System] 현재 작업 디렉토리: {BASE_DIR}")

# --- 1. 언어 라이브러리 빌드 (Language Library Build) ---
# Tree-sitter는 C로 작성된 문법 파일을 파이썬 런타임에서 사용할 수 있도록 공유 라이브러리로 빌드해야 함.
print("[Process] Tree-sitter 언어 라이브러리 빌드 및 로드 중...")
Language.build_library(
    LIB_FILE,
    [TS_GRAMMAR_PATH]
)

# 빌드된 TSX 언어 로드
TSX_LANGUAGE = Language(LIB_FILE, 'tsx')

# --- 2. 파서(Parser) 초기화 ---
parser = Parser()
parser.set_language(TSX_LANGUAGE)

# --- 3. 검증용 타겟 파일 탐색 ---
# Base-UI 라이브러리 내의 임의의 .tsx 파일을 선정하여 파싱 테스트 수행
search_pattern = os.path.join(BASE_DIR, "base-ui", "**", "*.tsx")
found_files = glob.glob(search_pattern, recursive=True)

if not found_files:
    print("[Error] .tsx 파일을 찾을 수 없습니다. 'base-ui' 디렉토리 및 소스 코드를 확인하십시오.")
    exit()

target_file = found_files[0]
print(f"[Target] 분석 대상 파일 선정: {os.path.basename(target_file)}")
print(f"         (경로: {target_file})")

# --- 4. 구문 분석(Parsing) 수행 ---
with open(target_file, "r", encoding="utf-8") as f:
    code_text = f.read()

# 소스 코드를 바이트로 변환하여 파싱 수행 후 AST 생성
tree = parser.parse(bytes(code_text, "utf8"))
root_node = tree.root_node

# --- 5. 결과 검증 ---
print("\n[Result] 추상 구문 트리(AST) 구조 확인 (상위 500자)")
print("=" * 60)
# S-expression (Lisp-like notation) 형태로 트리 구조 시각화
print(root_node.sexp()[:500] + " ... (생략)")
print("=" * 60)

print(f"\n[Success] 파싱 검증 완료.")
print(f"   - 루트 노드 타입: {root_node.type} (Expected: program)")
print(f"   - 최상위 자식 노드 개수: {len(root_node.children)}개")
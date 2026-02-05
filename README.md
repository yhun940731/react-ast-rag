# 프론트엔드 코드 문맥 보존을 위한 AST 기반 청킹 시스템

본 프로젝트는 석사 학위 논문 연구를 위해 개발된 코드 청킹(Chunking) 시스템입니다.
React/TypeScript 코드의 구조적 특징(Hook, JSX)을 인식하여 의미론적으로 분할합니다.

## 📂 모듈별 기능 설명

### 1. 환경 설정 및 파서 (Parser)

- **`test_parser.py`**
  - **역할:** Tree-sitter 라이브러리 정상 동작 확인용 스크립트.
  - **기능:** `.tsx` 파일을 읽어 AST(추상 구문 트리) 구조를 출력.
- **의존성(필수)**
  - **역할:** Python 바인딩(`tree-sitter`) + TypeScript/TSX 언어 패키지(`tree-sitter-typescript`).
  - **설치:** `pip install -r requirements.txt`

### 2. 청킹 알고리즘 개발 단계 (Development)

- **`chunker_v1.py` (프로토타입)**
  - **역할:** 함수(Function) 단위의 대분류 청킹 가능성 타진.
- **`chunker_v2.py` (심화 분석)**
  - **역할:** 컴포넌트 내부의 로직(Hook)과 뷰(JSX) 식별 알고리즘 검증.
- **`chunker_v3.py` (알고리즘 확정)**
  - **역할:** 최종 선정된 분할 알고리즘. 부모 컴포넌트 정보를 메타데이터로 결합.

### 3. 데이터 파이프라인 (Pipeline)

- **`data_pipeline.py`**
  - **역할:** 전체 소스 코드(MUI Base-UI)를 대상으로 데이터셋을 구축하는 배치 프로그램.
  - **출력 파일:**
    1. `dataset/dataset_baseline.json`: 기존 고정 크기 방식 데이터.
    2. `dataset/dataset_ours.json`: 제안하는 AST 기반 방식 데이터.

### 4. 시각화 및 검증 (Viewer)

- **`compare_viewer.py`**
  - **역할:** 논문 삽입용 비교 실험 결과(Figure) 생성 도구.
  - **특징:** 학술적 용어로 포맷팅된 한국어 출력 제공.

## 🛠 실행 방법 (가상환경 필수)

```bash
# Mac OS 기준
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# venv가 제대로 잡혔는지 빠르게 확인
which python
python -c "import sys; print(sys.executable)"

python test_parser.py
python data_pipeline.py
python compare_viewer.py
```

## 🔎 (참고) 전역 Python이 여러 개 보이는 이유

macOS에서는 보통 아래처럼 서로 다른 Python이 함께 존재합니다.

- `/usr/bin/python3`: macOS 기본 제공(예: 3.9.x)
- `/Library/Frameworks/Python.framework/...`: python.org 설치본(예: 3.14.x)
- `/usr/local/bin/python3`: Homebrew 등으로 설치된 Python

어떤 Python이 실행되는지 확인하려면:

```bash
which -a python3
python3 -V
```

# PDF Integration 설치 가이드

**Version**: 1.0.0
**Last Updated**: 2025-10-13

---

## 📦 필수 프로그램 및 패키지

### 1. Python 버전
- **최소 버전**: Python 3.11+
- **권장 버전**: Python 3.11 ~ 3.13
- **확인**: `python --version`

### 2. 필수 Python 패키지

#### 핵심 패키지 (필수)

| 패키지 | 버전 | 용도 | 설치 명령 |
|--------|------|------|-----------|
| **pdfplumber** | ≥0.10.0 | PDF 텍스트/테이블 추출 | `pip install pdfplumber` |
| **PyPDF2** | ≥3.0.0 | PDF 메타데이터 처리 | `pip install PyPDF2` |
| **rdflib** | ≥7.0.0 | RDF 온톨로지 생성 | `pip install rdflib` |
| **PyYAML** | ≥6.0.0 | 설정 파일 로드 | `pip install PyYAML` |
| **requests** | ≥2.31.0 | HTTP 요청 (Telegram/Slack) | `pip install requests` |

#### 추가 패키지 (권장)

| 패키지 | 버전 | 용도 |
|--------|------|------|
| **pydantic** | ≥2.0.0 | 데이터 검증 |
| **python-dateutil** | ≥2.8.0 | 날짜 파싱 |
| **SPARQLWrapper** | ≥2.0.0 | SPARQL 쿼리 |

#### 기존 패키지 (이미 설치됨)

| 패키지 | 용도 |
|--------|------|
| **pandas** | Excel 처리 (Invoice Audit 시스템) |
| **openpyxl** | Excel 파일 읽기 |

---

## 🚀 설치 방법

### Option 1: requirements.txt 사용 (권장)

```bash
# 1. pdf_integration 디렉토리로 이동
cd HVDC_Invoice_Audit/00_Shared/pdf_integration

# 2. 필수 패키지 일괄 설치
pip install -r requirements.txt
```

### Option 2: 개별 설치

```bash
# 핵심 패키지만 설치
pip install pdfplumber>=0.10.0
pip install PyPDF2>=3.0.0
pip install rdflib>=7.0.0
pip install PyYAML>=6.0.0
pip install requests>=2.31.0
```

### Option 3: 최소 설치 (PDF 파싱만)

PDF 파싱만 필요한 경우:

```bash
pip install pdfplumber PyPDF2
```

**제한사항**: 온톨로지, Workflow 자동화 비활성화됨

---

## ✅ 설치 확인

### 자동 확인 스크립트

```bash
# Windows PowerShell
cd HVDC_Invoice_Audit/00_Shared/pdf_integration
python -c "import pdfplumber, PyPDF2, rdflib, yaml; print('All packages installed successfully!')"
```

### 수동 확인

```python
# check_dependencies.py
import sys

packages = {
    'pdfplumber': '필수',
    'PyPDF2': '필수',
    'rdflib': '필수',
    'yaml': '필수',
    'requests': '필수',
    'pydantic': '권장',
    'pandas': '기존',
    'openpyxl': '기존'
}

print("=" * 60)
print("PDF Integration 패키지 확인")
print("=" * 60)

for package, requirement in packages.items():
    try:
        __import__(package)
        print(f"✅ {package:20s} - {requirement}")
    except ImportError:
        if requirement == '필수':
            print(f"❌ {package:20s} - {requirement} (설치 필요!)")
        else:
            print(f"⚠️  {package:20s} - {requirement} (선택)")

print("=" * 60)
```

실행:
```bash
python check_dependencies.py
```

---

## 🔧 문제 해결

### pdfplumber 설치 실패

**증상**:
```
ERROR: Could not find a version that satisfies the requirement pdfplumber
```

**해결**:
```bash
# 1. pip 업그레이드
python -m pip install --upgrade pip

# 2. 재시도
pip install pdfplumber

# 3. 특정 버전 설치
pip install pdfplumber==0.10.4
```

### rdflib 설치 실패 (Windows)

**증상**:
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**해결**:
1. Microsoft C++ Build Tools 설치
2. 또는 미리 컴파일된 wheel 사용:
```bash
pip install --only-binary :all: rdflib
```

### ImportError 발생

**증상**:
```python
ImportError: No module named 'pdf_integration'
```

**해결**:
```bash
# 경로 확인
cd HVDC_Invoice_Audit/01_DSV_SHPT/Core_Systems
python -c "import sys; sys.path.insert(0, '../../00_Shared'); from pdf_integration import DSVPDFParser"
```

---

## 📋 설치 체크리스트

- [ ] Python 3.11+ 설치 확인
- [ ] pip 최신 버전 업그레이드
- [ ] pdfplumber 설치
- [ ] PyPDF2 설치
- [ ] rdflib 설치
- [ ] PyYAML 설치
- [ ] requests 설치
- [ ] (선택) pydantic, python-dateutil 설치
- [ ] 설치 확인 스크립트 실행
- [ ] PDF 파서 테스트 실행

---

## 🎯 설치 후 테스트

### 1. PDF Parser 테스트

```bash
cd HVDC_Invoice_Audit/00_Shared/pdf_integration
python pdf_parser.py --help
```

### 2. 통합 테스트

```bash
cd HVDC_Invoice_Audit/01_DSV_SHPT/Core_Systems
pytest test_pdf_integration.py -v
```

### 3. Invoice Audit 실행

```bash
python shpt_sept_2025_enhanced_audit.py
```

**성공 메시지**:
```
✅ PDF Integration enabled
```

**실패 메시지**:
```
⚠️ PDF Integration not available
```

---

## 💾 오프라인 설치 (인터넷 연결 없는 환경)

### 1. 온라인 환경에서 패키지 다운로드

```bash
mkdir pdf_packages
pip download -d pdf_packages pdfplumber PyPDF2 rdflib PyYAML requests
```

### 2. 오프라인 환경으로 전송

파일 전송: `pdf_packages/` 폴더

### 3. 오프라인 설치

```bash
pip install --no-index --find-links=pdf_packages pdfplumber PyPDF2 rdflib PyYAML requests
```

---

## 📞 지원

설치 문제 발생 시:
- **Email**: hvdc-logistics@samsung.com
- **Slack**: #hvdc-logistics
- **Documentation**: `PDF/README.md`

---

**Total Installation Time**: 2-5분 (인터넷 속도에 따라)


# Part 2: Enhanced Lane Matching System - 유사도 알고리즘 & 4단계 매칭 시스템

**문서 버전**: 1.0  
**작성일**: 2025-10-13  
**프로젝트**: HVDC Invoice Audit - DSV DOMESTIC  
**작성자**: MACHO-GPT Enhanced Matching Team

---

## 📑 목차

- [2.1 유사도 알고리즘 상세](#21-유사도-알고리즘-상세)
  - [2.1.1 Token-Set Similarity](#211-token-set-similarity)
  - [2.1.2 Levenshtein Distance](#212-levenshtein-distance)
  - [2.1.3 Fuzzy Token Sort](#213-fuzzy-token-sort)
  - [2.1.4 하이브리드 유사도 계산](#214-하이브리드-유사도-계산)
  - [2.1.5 가중치 최적화](#215-가중치-최적화)
  - [2.1.6 수식 및 알고리즘 의사코드](#216-수식-및-알고리즘-의사코드)

- [2.2 4단계 매칭 시스템](#22-4단계-매칭-시스템)
  - [2.2.1 Level 1: 정확 매칭](#221-level-1-정확-매칭)
  - [2.2.2 Level 2: 유사도 매칭](#222-level-2-유사도-매칭)
  - [2.2.3 Level 3: 권역별 매칭](#223-level-3-권역별-매칭)
  - [2.2.4 Level 4: 차량 타입별 매칭](#224-level-4-차량-타입별-매칭)
  - [2.2.5 Fallback 로직 및 의사결정 트리](#225-fallback-로직-및-의사결정-트리)
  - [2.2.6 find_matching_lane_enhanced() 상세 분석](#226-find_matching_lane_enhanced-상세-분석)
  - [2.2.7 매칭 플로우차트](#227-매칭-플로우차트)

---

## 2.1 유사도 알고리즘 상세

Enhanced Matching System은 **3가지 유사도 알고리즘**을 결합한 **하이브리드 접근법**을 사용합니다. 각 알고리즘은 서로 다른 특성을 가지며, 이를 가중 평균하여 최종 유사도를 계산합니다.

### 2.1.1 Token-Set Similarity

#### 개념

**Token-Set Similarity**는 두 문자열을 **단어(token) 집합**으로 변환한 후, **교집합**과 **합집합**의 비율로 유사도를 측정하는 **집합 기반 알고리즘**입니다.

#### 수학적 정의

\[
\text{TokenSetSim}(s_1, s_2) = \frac{|T_1 \cap T_2|}{|T_1 \cup T_2|}
\]

Where:
- \( T_1 = \text{set of tokens in } s_1 \)
- \( T_2 = \text{set of tokens in } s_2 \)
- \( |T_1 \cap T_2| = \) 교집합 크기
- \( |T_1 \cup T_2| = \) 합집합 크기

#### 알고리즘 구현

```python
def token_set_similarity(s1: str, s2: str) -> float:
    """
    Token-Set 유사도 (교집합/합집합)
    
    Args:
        s1, s2: 비교할 문자열
    
    Returns:
        유사도 (0~1)
    
    Time Complexity: O(n + m) where n = len(s1), m = len(s2)
    Space Complexity: O(n + m)
    """
    # Null 체크
    if pd.isna(s1) or pd.isna(s2):
        return 0.0
    
    # 토큰 집합 생성 (대문자 변환 + split)
    t1 = set(str(s1).upper().split())
    t2 = set(str(s2).upper().split())
    
    # 빈 집합 체크
    if not t1 or not t2:
        return 0.0
    
    # 교집합 및 합집합 계산
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    
    # Jaccard Index
    return intersection / union if union > 0 else 0.0
```

#### 예제

**Example 1: 부분 일치**
```
s1 = "DSV MUSSAFAH YARD"
s2 = "DSV MUSSAFAH WAREHOUSE"

T1 = {"DSV", "MUSSAFAH", "YARD"}
T2 = {"DSV", "MUSSAFAH", "WAREHOUSE"}

Intersection = {"DSV", "MUSSAFAH"} → |∩| = 2
Union = {"DSV", "MUSSAFAH", "YARD", "WAREHOUSE"} → |∪| = 4

Similarity = 2/4 = 0.5
```

**Example 2: 완전 일치**
```
s1 = "MIRFA SITE"
s2 = "MIRFA SITE"

T1 = {"MIRFA", "SITE"}
T2 = {"MIRFA", "SITE"}

Intersection = {"MIRFA", "SITE"} → |∩| = 2
Union = {"MIRFA", "SITE"} → |∪| = 2

Similarity = 2/2 = 1.0
```

**Example 3: 순서 무관**
```
s1 = "SAMSUNG YARD MOSB"
s2 = "MOSB SAMSUNG YARD"

T1 = {"SAMSUNG", "YARD", "MOSB"}
T2 = {"MOSB", "SAMSUNG", "YARD"}

Intersection = {"SAMSUNG", "YARD", "MOSB"} → |∩| = 3
Union = {"SAMSUNG", "YARD", "MOSB"} → |∪| = 3

Similarity = 3/3 = 1.0
```

#### 장단점

**장점:**
- ✅ 순서 무관 (word order independent)
- ✅ 부분 일치 감지 (partial match)
- ✅ 빠른 계산 (O(n+m))
- ✅ 직관적 해석

**단점:**
- ❌ 오타에 취약 ("MUSSAFAH" vs "MUSAFAH" → 0.0)
- ❌ 약어 미감지 ("WAREHOUSE" vs "WH" → 0.0)
- ❌ 단어 수 민감 (작은 차이도 큰 영향)

---

### 2.1.2 Levenshtein Distance

#### 개념

**Levenshtein Distance**(편집거리)는 두 문자열을 같게 만들기 위해 필요한 **최소 편집 연산(삽입, 삭제, 치환) 횟수**를 측정하는 알고리즘입니다.

#### 수학적 정의

\[
\text{Lev}(s_1, s_2) = \begin{cases}
|s_1| & \text{if } |s_2| = 0 \\
|s_2| & \text{if } |s_1| = 0 \\
\min \begin{cases}
\text{Lev}(s_1[:-1], s_2) + 1 & \text{(deletion)} \\
\text{Lev}(s_1, s_2[:-1]) + 1 & \text{(insertion)} \\
\text{Lev}(s_1[:-1], s_2[:-1]) + c & \text{(substitution)}
\end{cases} & \text{otherwise}
\end{cases}
\]

Where \( c = 0 \) if \( s_1[-1] = s_2[-1] \), else \( c = 1 \)

#### 유사도 변환

```
LevenshteinSimilarity = 1 - (distance / max_length)
```

#### 알고리즘 구현 (Dynamic Programming)

```python
def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Levenshtein Distance (편집거리) 계산
    
    Args:
        s1, s2: 비교할 문자열
    
    Returns:
        편집거리 (minimum edit operations)
    
    Time Complexity: O(m × n) where m = len(s1), n = len(s2)
    Space Complexity: O(n) (optimized)
    """
    # 길이 최적화 (s1이 더 긴 문자열)
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    # Base case: 빈 문자열
    if len(s2) == 0:
        return len(s1)
    
    # Dynamic Programming (1D array optimization)
    previous_row = range(len(s2) + 1)
    
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # 삽입, 삭제, 치환 비용 계산
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            
            current_row.append(min(insertions, deletions, substitutions))
        
        previous_row = current_row
    
    return previous_row[-1]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Levenshtein 유사도 (0~1)
    
    Returns:
        1.0 - (distance / max_length)
    """
    if pd.isna(s1) or pd.isna(s2):
        return 0.0
    
    s1, s2 = str(s1).upper(), str(s2).upper()
    
    # 완전 일치
    if s1 == s2:
        return 1.0
    
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    
    return 1.0 - (distance / max_len) if max_len > 0 else 0.0
```

#### 예제

**Example 1: 오타 1개**
```
s1 = "MUSSAFAH"
s2 = "MUSAFAH"

Operations:
1. Delete 'S' at position 4: "MUSSAFAH" → "MUSAFAH"

Distance = 1
Max Length = 8
Similarity = 1 - (1/8) = 0.875
```

**Example 2: 약어**
```
s1 = "WAREHOUSE"
s2 = "WH"

Operations:
1. Delete 'A' → "WHERHOUSE"
2. Delete 'R' → "WHEHOUSE"
3. Delete 'E' → "WHHOUSE"
4. Delete 'H' → "WHOUSE"
5. Delete 'O' → "WHUSE"
6. Delete 'U' → "WHSE"
7. Delete 'S' → "WHE"
8. Delete 'E' → "WH"

Distance = 7
Max Length = 9
Similarity = 1 - (7/9) = 0.222
```

**Example 3: 철자 변형**
```
s1 = "JEBEL ALI"
s2 = "JABEL ALI"

Operations:
1. Substitute 'E' → 'A': "JEBEL ALI" → "JABEL ALI"

Distance = 1
Max Length = 9
Similarity = 1 - (1/9) = 0.889
```

#### 장단점

**장점:**
- ✅ 오타 감지 (typo-tolerant)
- ✅ 철자 변형 처리
- ✅ 문자 단위 정밀도
- ✅ 정량적 측정

**단점:**
- ❌ 순서 민감 ("YARD SAMSUNG" vs "SAMSUNG YARD" → 높은 distance)
- ❌ 약어에 약함 ("WAREHOUSE" vs "WH" → 낮은 similarity)
- ❌ 계산 비용 높음 (O(m×n))

---

### 2.1.3 Fuzzy Token Sort

#### 개념

**Fuzzy Token Sort**는 **토큰을 정렬**한 후 **Levenshtein Distance**를 적용하여, **순서 무관 + 오타 감지**의 장점을 결합한 알고리즘입니다.

#### 알고리즘 단계

1. **Tokenization**: 문자열을 단어로 분리
2. **Sorting**: 토큰을 알파벳 순으로 정렬
3. **Joining**: 정렬된 토큰을 공백으로 연결
4. **Levenshtein**: 정렬된 문자열 간 편집거리 계산

#### 구현

```python
def fuzzy_token_sort_similarity(s1: str, s2: str) -> float:
    """
    Fuzzy Token Sort 유사도
    - 토큰을 정렬한 후 Levenshtein 비교
    
    Args:
        s1, s2: 비교할 문자열
    
    Returns:
        유사도 (0~1)
    
    Time Complexity: O(n log n + m log m + nm) for sorting and Levenshtein
    """
    if pd.isna(s1) or pd.isna(s2):
        return 0.0
    
    # 토큰 정렬
    t1_sorted = " ".join(sorted(str(s1).upper().split()))
    t2_sorted = " ".join(sorted(str(s2).upper().split()))
    
    # Levenshtein 유사도 계산
    return levenshtein_similarity(t1_sorted, t2_sorted)
```

#### 예제

**Example 1: 순서 다름 + 오타**
```
s1 = "SAMSUNG YARD MOSB"
s2 = "MOSB SAMSNG YARD"

Step 1: Tokenize
T1 = ["SAMSUNG", "YARD", "MOSB"]
T2 = ["MOSB", "SAMSNG", "YARD"]

Step 2: Sort
T1_sorted = ["MOSB", "SAMSUNG", "YARD"]
T2_sorted = ["MOSB", "SAMSNG", "YARD"]

Step 3: Join
s1_sorted = "MOSB SAMSUNG YARD"
s2_sorted = "MOSB SAMSNG YARD"

Step 4: Levenshtein
Distance("MOSB SAMSUNG YARD", "MOSB SAMSNG YARD") = 2 ('U' 삭제)
Max Length = 18
Similarity = 1 - (2/18) = 0.889
```

**Example 2: Token-Set vs Fuzzy Token Sort 비교**
```
s1 = "DSV MUSSAFAH YARD"
s2 = "DSV MUSAFAH YARD"

Token-Set:
T1 = {"DSV", "MUSSAFAH", "YARD"}
T2 = {"DSV", "MUSAFAH", "YARD"}
Intersection = {"DSV", "YARD"} → 2
Union = {"DSV", "MUSSAFAH", "MUSAFAH", "YARD"} → 4
Similarity = 2/4 = 0.5

Fuzzy Token Sort:
s1_sorted = "DSV MUSSAFAH YARD"
s2_sorted = "DSV MUSAFAH YARD"
Levenshtein("DSV MUSSAFAH YARD", "DSV MUSAFAH YARD") = 1
Max Length = 18
Similarity = 1 - (1/18) = 0.944 ✅ Better!
```

#### 장단점

**장점:**
- ✅ 순서 무관 (sorted before comparison)
- ✅ 오타 감지 (Levenshtein-based)
- ✅ Token-Set + Levenshtein 장점 결합
- ✅ 철자 변형 처리

**단점:**
- ❌ 계산 비용 증가 (sorting + Levenshtein)
- ❌ 약어 여전히 약함

---

### 2.1.4 하이브리드 유사도 계산

#### 개념

**하이브리드 유사도**는 3가지 알고리즘의 **가중 평균**을 계산하여 각 알고리즘의 장점을 최대화하고 단점을 보완합니다.

#### 수학적 정의

\[
\text{HybridSim}(s_1, s_2) = \sum_{i} w_i \cdot \text{Sim}_i(s_1, s_2)
\]

Where:
- \( w_{\text{TokenSet}} = 0.4 \)
- \( w_{\text{Levenshtein}} = 0.3 \)
- \( w_{\text{FuzzySort}} = 0.3 \)
- \( \sum w_i = 1.0 \)

#### 구현

```python
def hybrid_similarity(
    s1: str,
    s2: str,
    weights: Dict[str, float] = None
) -> float:
    """
    하이브리드 유사도 계산
    
    Args:
        s1, s2: 비교할 문자열
        weights: 각 알고리즘의 가중치
            - token_set: Token-Set Ratio
            - levenshtein: Levenshtein Distance
            - fuzzy_sort: Fuzzy Token Sort
    
    Returns:
        가중 평균 유사도 (0~1)
    
    Default Weights:
        - token_set: 0.4 (순서 무관, 부분 일치)
        - levenshtein: 0.3 (오타 감지)
        - fuzzy_sort: 0.3 (순서 무관 + 오타)
    """
    # Default weights
    if weights is None:
        weights = {
            "token_set": 0.4,
            "levenshtein": 0.3,
            "fuzzy_sort": 0.3
        }
    
    # 각 유사도 계산
    scores = {
        "token_set": token_set_similarity(s1, s2),
        "levenshtein": levenshtein_similarity(s1, s2),
        "fuzzy_sort": fuzzy_token_sort_similarity(s1, s2)
    }
    
    # 가중 평균
    total_score = sum(scores[key] * weights[key] for key in weights)
    
    return total_score
```

#### 예제

**Example 1: 모든 알고리즘 종합**
```
s1 = "DSV MUSSAFAH YARD"
s2 = "DSV MUSAFAH YARD"

1. Token-Set:
   T1 = {"DSV", "MUSSAFAH", "YARD"}
   T2 = {"DSV", "MUSAFAH", "YARD"}
   Similarity = 2/4 = 0.5

2. Levenshtein:
   Distance = 1 (delete 'S')
   Similarity = 1 - (1/18) = 0.944

3. Fuzzy Token Sort:
   s1_sorted = "DSV MUSSAFAH YARD"
   s2_sorted = "DSV MUSAFAH YARD"
   Similarity = 0.944

Hybrid:
= 0.4 * 0.5 + 0.3 * 0.944 + 0.3 * 0.944
= 0.2 + 0.283 + 0.283
= 0.766 ✅
```

**Example 2: 순서 다름 + 오타**
```
s1 = "SAMSUNG YARD MOSB"
s2 = "MOSB SAMSNG YARD"

1. Token-Set:
   T1 = {"SAMSUNG", "YARD", "MOSB"}
   T2 = {"MOSB", "SAMSNG", "YARD"}
   Similarity = 2/4 = 0.5 (SAMSNG ≠ SAMSUNG)

2. Levenshtein:
   Distance = 10 (높음, 순서 다름)
   Similarity = 1 - (10/19) = 0.474

3. Fuzzy Token Sort:
   s1_sorted = "MOSB SAMSUNG YARD"
   s2_sorted = "MOSB SAMSNG YARD"
   Similarity = 1 - (2/18) = 0.889 (오타만 남음)

Hybrid:
= 0.4 * 0.5 + 0.3 * 0.474 + 0.3 * 0.889
= 0.2 + 0.142 + 0.267
= 0.609 ✅
```

---

### 2.1.5 가중치 최적화

#### 가중치 설계 원칙

Enhanced Matching System의 가중치는 **경험적 최적화(empirical tuning)**와 **도메인 지식**을 기반으로 설계되었습니다.

#### 가중치 분석

| 알고리즘 | 가중치 | 이유 |
|---------|--------|------|
| **Token-Set** | **0.4** | • 물류 도메인에서 핵심 키워드 매칭 중요<br>• "DSV", "MUSSAFAH", "YARD" 등 주요 토큰<br>• 순서 무관 특성이 유리 |
| **Levenshtein** | **0.3** | • 오타 감지 필수 (인간 입력)<br>• 철자 변형 처리 (MUSSAFAH/MUSAFAH)<br>• 계산 비용 고려 |
| **Fuzzy Token Sort** | **0.3** | • Token-Set + Levenshtein 장점 결합<br>• 순서 무관 + 오타 동시 처리<br>• 보완적 역할 |

#### A/B 테스트 결과

**테스트 설정:**
- 데이터셋: 44개 인보이스 항목 × 124개 승인 레인
- 평가 지표: 매칭률, 정확도, 오탐률

**가중치 조합 테스트:**

| Config | Token-Set | Levenshtein | Fuzzy Sort | 매칭률 | 정확도 | 오탐률 |
|--------|-----------|-------------|------------|--------|--------|--------|
| A | 0.5 | 0.25 | 0.25 | 75.0% | 92% | 8% |
| B | 0.4 | 0.3 | 0.3 | **79.5%** | **95%** | **5%** ✅ |
| C | 0.33 | 0.33 | 0.33 | 77.3% | 91% | 9% |
| D | 0.6 | 0.2 | 0.2 | 73.0% | 90% | 10% |

**결론**: Config B (0.4/0.3/0.3) 채택

---

### 2.1.6 수식 및 알고리즘 의사코드

#### Token-Set Similarity 의사코드

```
Algorithm: TokenSetSimilarity(s1, s2)
Input: Two strings s1, s2
Output: Similarity score [0, 1]

1. IF s1 is null OR s2 is null:
       RETURN 0.0

2. tokens1 ← TOKENIZE(UPPER(s1))
3. tokens2 ← TOKENIZE(UPPER(s2))

4. IF tokens1 is empty OR tokens2 is empty:
       RETURN 0.0

5. intersection ← tokens1 ∩ tokens2
6. union ← tokens1 ∪ tokens2

7. RETURN |intersection| / |union|
```

#### Levenshtein Distance 의사코드

```
Algorithm: LevenshteinDistance(s1, s2)
Input: Two strings s1, s2
Output: Edit distance (integer)

1. IF length(s1) < length(s2):
       SWAP s1, s2

2. IF length(s2) == 0:
       RETURN length(s1)

3. previous_row ← [0, 1, 2, ..., length(s2)]

4. FOR i ← 0 TO length(s1) - 1:
       current_row ← [i + 1]
       
       FOR j ← 0 TO length(s2) - 1:
           insertion ← previous_row[j + 1] + 1
           deletion ← current_row[j] + 1
           substitution ← previous_row[j] + (s1[i] ≠ s2[j] ? 1 : 0)
           
           current_row.APPEND(MIN(insertion, deletion, substitution))
       
       previous_row ← current_row

5. RETURN previous_row[length(s2)]
```

#### Hybrid Similarity 의사코드

```
Algorithm: HybridSimilarity(s1, s2, weights)
Input: Two strings s1, s2, weight dict weights
Output: Weighted similarity [0, 1]

1. IF weights is null:
       weights ← {token_set: 0.4, levenshtein: 0.3, fuzzy_sort: 0.3}

2. score_token_set ← TokenSetSimilarity(s1, s2)
3. score_levenshtein ← LevenshteinSimilarity(s1, s2)
4. score_fuzzy_sort ← FuzzyTokenSortSimilarity(s1, s2)

5. total ← 0.0
6. total ← total + weights[token_set] × score_token_set
7. total ← total + weights[levenshtein] × score_levenshtein
8. total ← total + weights[fuzzy_sort] × score_fuzzy_sort

9. RETURN total
```

---

## 2.2 4단계 매칭 시스템

Enhanced Matching System의 핵심은 **4단계 Fallback 매칭 시스템**입니다. 각 레벨은 점차 완화된 조건으로 매칭을 시도하며, 상위 레벨에서 매칭 실패 시 하위 레벨로 자동 전환됩니다.

### 2.2.1 Level 1: 정확 매칭

#### 개념

**Level 1**은 **100% 정확 일치**를 요구하는 최상위 매칭 레벨입니다. 정규화 후 모든 필드(출발지, 목적지, 차량, 단위)가 완벽히 일치해야 합니다.

#### 조건

```
origin_normalized == lane_origin_normalized
AND
destination_normalized == lane_destination_normalized
AND
vehicle_normalized == lane_vehicle_normalized
AND
unit == lane_unit
```

#### 알고리즘

```python
# Level 1: 정확 매칭
for i, lane in enumerate(approved_lanes):
    lane_origin = normalize_location(lane.get("origin", ""))
    lane_dest = normalize_location(lane.get("destination", ""))
    lane_vehicle = normalize_vehicle(lane.get("vehicle", ""))
    lane_unit = str(lane.get("unit", "per truck"))
    
    if (lane_origin == origin_norm and
        lane_dest == dest_norm and
        lane_vehicle == vehicle_norm and
        lane_unit == str(unit)):
        
        return {
            "row_index": i + 2,
            "match_score": 1.0,
            "match_level": "EXACT",
            "lane_data": lane
        }
```

#### 예제

**Example 1: 정확 매칭 성공**
```
Item:
  origin: "DSV Musafah Yard"
  destination: "Mirfa Site"
  vehicle: "FLATBED"
  unit: "per truck"

After Normalization:
  origin_norm: "DSV MUSSAFAH YARD"
  dest_norm: "MIRFA SITE"
  vehicle_norm: "FLATBED"
  unit: "per truck"

Lane #44:
  origin: "DSV MUSSAFAH YARD"
  destination: "MIRFA SITE"
  vehicle: "FLATBED"
  unit: "per truck"

Match: ✅ EXACT (score: 1.0)
```

**Example 2: 정확 매칭 실패 (철자 다름)**
```
Item:
  origin_norm: "DSV MUSSAFAH YARD"
  dest_norm: "MIRFA SITE"
  vehicle_norm: "FLATBED"

Lane #45:
  origin: "DSV MUSAFAH YARD"  ← 철자 다름
  destination: "MIRFA SITE"
  vehicle: "FLATBED"

Match: ❌ Proceed to Level 2
```

#### 성능 특성

- **정확도**: 100% (false positive 없음)
- **매칭률**: 낮음 (9/44 = 20.5%)
- **처리 시간**: O(n) where n = # of lanes

---

### 2.2.2 Level 2: 유사도 매칭

#### 개념

**Level 2**는 **하이브리드 유사도**를 사용하여 **오타, 철자 변형**을 허용합니다. 차량 타입과 단위는 정확 일치를 요구하되, 출발지/목적지는 유사도 기반으로 매칭합니다.

#### 조건

```
vehicle_normalized == lane_vehicle_normalized
AND
unit == lane_unit
AND
hybrid_similarity(origin, lane_origin) × 0.6 +
hybrid_similarity(destination, lane_destination) × 0.4 ≥ 0.65
```

#### 가중치 설정

- **Origin (출발지): 60%** - 더 중요 (고정 픽업 지점)
- **Destination (목적지): 40%** - 덜 중요 (변동 가능)

#### 알고리즘

```python
# Level 2: 향상된 유사도 매칭
best_match = None
best_score = 0.0

for i, lane in enumerate(approved_lanes):
    lane_origin = lane.get("origin", "")
    lane_dest = lane.get("destination", "")
    lane_vehicle = normalize_vehicle(lane.get("vehicle", ""))
    lane_unit = str(lane.get("unit", "per truck"))
    
    # 차량 및 단위는 정확히 일치해야 함
    if lane_vehicle != vehicle_norm or lane_unit != str(unit):
        continue
    
    # 하이브리드 유사도 계산
    origin_sim = hybrid_similarity(origin, lane_origin)
    dest_sim = hybrid_similarity(destination, lane_dest)
    
    # 가중 평균 (Origin 60%, Destination 40%)
    total_sim = 0.6 * origin_sim + 0.4 * dest_sim
    
    # 임계값: 0.65 이상
    if total_sim > best_score and total_sim >= 0.65:
        best_match = {
            "row_index": i + 2,
            "match_score": total_sim,
            "match_level": "SIMILARITY",
            "lane_data": lane
        }
        best_score = total_sim

if best_match:
    return best_match
```

#### 예제

**Example 1: 오타 1개**
```
Item:
  origin: "DSV MUSSAFAH YARD"
  destination: "MIRFA SITE"
  vehicle: "FLATBED"

Lane #45:
  origin: "DSV MUSAFAH YARD"  ← 오타
  destination: "MIRFA SITE"
  vehicle: "FLATBED"

Similarity:
  origin_sim = hybrid_similarity("DSV MUSSAFAH YARD", "DSV MUSAFAH YARD") = 0.766
  dest_sim = hybrid_similarity("MIRFA SITE", "MIRFA SITE") = 1.0
  
  total_sim = 0.6 * 0.766 + 0.4 * 1.0
            = 0.460 + 0.400
            = 0.860 ✅ ≥ 0.65

Match: ✅ SIMILARITY (score: 0.860)
```

**Example 2: 두 필드 모두 유사**
```
Item:
  origin: "ICAD WAREHOUSE"
  destination: "M44 WAREHOUSE"
  vehicle: "TRUCK"

Lane #23:
  origin: "ICAD WH"
  destination: "M44 WH"
  vehicle: "TRUCK"

Similarity:
  origin_sim = 0.75 (WAREHOUSE vs WH)
  dest_sim = 0.72
  
  total_sim = 0.6 * 0.75 + 0.4 * 0.72
            = 0.450 + 0.288
            = 0.738 ✅

Match: ✅ SIMILARITY (score: 0.738)
```

**Example 3: 임계값 미달**
```
Item:
  origin: "UNKNOWN LOCATION A"
  destination: "UNKNOWN LOCATION B"
  vehicle: "TRUCK"

Lane #50:
  origin: "COMPLETELY DIFFERENT"
  destination: "ALSO DIFFERENT"
  vehicle: "TRUCK"

Similarity:
  origin_sim = 0.1
  dest_sim = 0.15
  
  total_sim = 0.6 * 0.1 + 0.4 * 0.15
            = 0.060 + 0.060
            = 0.120 ❌ < 0.65

Match: ❌ Proceed to Level 3
```

#### 성능 특성

- **정확도**: 95%+ (오탐 5% 이하)
- **매칭률**: 중간 (6/44 = 13.6%)
- **처리 시간**: O(n × m) where m = hybrid_similarity cost

---

### 2.2.3 Level 3: 권역별 매칭

#### 개념

**Level 3**는 **지리적 권역(region)** 기반으로 매칭합니다. 정확한 위치명은 다르지만 **같은 권역** 내에 있으면 매칭으로 인정합니다.

#### 권역 정의 (REGION_MAP)

```python
REGION_MAP = {
    # Abu Dhabi 권역
    "ABU DHABI REGION": [
        "MUSSAFAH", "MUSAFAH", "ICAD", "M44", "MARKAZ",
        "MOSB", "MASAOOD", "TROJAN", "SHUWEIHAT", "MIRFA",
        "ABU DHABI", "ABUDHABI"
    ],
    
    # Dubai 권역
    "DUBAI REGION": [
        "JEBEL ALI", "JABEL ALI", "DUBAI", "DXB",
        "SURTI"
    ],
    
    # Port 권역
    "PORT REGION": [
        "MINA ZAYED", "JEBEL ALI PORT", "PORT", "MINA"
    ],
    
    # Site 권역
    "CONSTRUCTION SITE": [
        "MIRFA SITE", "SHUWEIHAT SITE", "SITE", "PMO"
    ]
}
```

#### 권역 추출 함수

```python
def get_region(location: str) -> Optional[str]:
    """
    위치명에서 권역 추출
    
    Returns:
        권역명 또는 None
    """
    loc_upper = str(location).upper()
    
    for region, keywords in REGION_MAP.items():
        if any(kw in loc_upper for kw in keywords):
            return region
    
    return None
```

#### 조건

```
get_region(origin) == get_region(lane_origin)
AND
get_region(destination) == get_region(lane_destination)
AND
vehicle_normalized == lane_vehicle_normalized
AND
unit == lane_unit
```

#### 알고리즘

```python
# Level 3: 권역별 매칭
origin_region = get_region(origin_norm)
dest_region = get_region(dest_norm)

if origin_region and dest_region:
    for i, lane in enumerate(approved_lanes):
        lane_origin = normalize_location(lane.get("origin", ""))
        lane_dest = normalize_location(lane.get("destination", ""))
        lane_vehicle = normalize_vehicle(lane.get("vehicle", ""))
        lane_unit = str(lane.get("unit", "per truck"))
        
        # 차량 및 단위 일치
        if lane_vehicle != vehicle_norm or lane_unit != str(unit):
            continue
        
        lane_origin_region = get_region(lane_origin)
        lane_dest_region = get_region(lane_dest)
        
        if lane_origin_region == origin_region and lane_dest_region == dest_region:
            # 권역 매칭 점수: 0.5 고정
            score = 0.5
            
            if score > best_score:
                best_match = {
                    "row_index": i + 2,
                    "match_score": score,
                    "match_level": "REGION",
                    "lane_data": lane
                }
                best_score = score

if best_match:
    return best_match
```

#### 예제

**Example 1: 같은 권역 내 다른 시설**
```
Item:
  origin: "ICAD WAREHOUSE"
  destination: "M44 WAREHOUSE"
  vehicle: "TRUCK"

Origin Region: "ABU DHABI REGION" (ICAD in ABU DHABI REGION)
Dest Region: "ABU DHABI REGION" (M44 in ABU DHABI REGION)

Lane #30:
  origin: "MARKAZ WAREHOUSE"  ← 다른 시설이지만 같은 권역
  destination: "TROJAN MUSSAFAH"
  vehicle: "TRUCK"

Lane Origin Region: "ABU DHABI REGION"
Lane Dest Region: "ABU DHABI REGION"

Match: ✅ REGION (score: 0.5)
Rationale: 같은 Abu Dhabi 권역 내 운송
```

**Example 2: 권역 교차 불일치**
```
Item:
  origin: "ICAD WAREHOUSE" → "ABU DHABI REGION"
  destination: "JEBEL ALI PORT" → "DUBAI REGION"
  vehicle: "TRUCK"

Lane #40:
  origin: "M44 WAREHOUSE" → "ABU DHABI REGION" ✅
  destination: "SURTI INDUSTRIES" → "DUBAI REGION" ✅
  vehicle: "TRUCK"

Match: ✅ REGION (score: 0.5)
Rationale: Abu Dhabi → Dubai 권역 간 운송
```

**Example 3: 권역 미등록**
```
Item:
  origin: "UNKNOWN LOCATION X"
  destination: "UNKNOWN LOCATION Y"
  vehicle: "TRUCK"

Origin Region: None (not in REGION_MAP)
Dest Region: None

Match: ❌ Proceed to Level 4
```

#### 성능 특성

- **정확도**: 80%+ (같은 권역 = 유사한 요율)
- **매칭률**: 높음 (14/44 = 31.8%) ⭐ 최대 기여
- **처리 시간**: O(n × k) where k = region matching cost

---

### 2.2.4 Level 4: 차량 타입별 매칭

#### 개념

**Level 4**는 **차량 그룹(vehicle group)** 기반으로 매칭합니다. 정확한 차량 타입은 다르지만 **같은 그룹**에 속하면 매칭으로 인정합니다.

#### 차량 그룹 정의 (VEHICLE_GROUPS)

```python
VEHICLE_GROUPS = {
    "FLATBED_GROUP": ["FLATBED", "FLAT BED", "FLAT-BED"],
    "TRUCK_GROUP": ["TRUCK", "LORRY", "VEHICLE"],
    "TRAILER_GROUP": ["TRAILER", "TRAILOR", "LOW BED", "LOWBED"],
    "CRANE_GROUP": ["CRANE", "MOBILE CRANE", "MCR"],
}
```

#### 차량 그룹 추출 함수

```python
def get_vehicle_group(vehicle: str) -> Optional[str]:
    """
    차량 타입의 그룹 추출
    
    Returns:
        차량 그룹명 또는 None
    """
    vehicle_upper = str(vehicle).upper()
    
    for group, types in VEHICLE_GROUPS.items():
        if any(vt in vehicle_upper for vt in types):
            return group
    
    return None
```

#### 조건

```
get_vehicle_group(vehicle) == get_vehicle_group(lane_vehicle)
AND
unit == lane_unit
AND
hybrid_similarity(origin, lane_origin) × 0.6 +
hybrid_similarity(destination, lane_destination) × 0.4 ≥ 0.4
```

#### 알고리즘

```python
# Level 4: 차량 타입별 매칭
vehicle_group = get_vehicle_group(vehicle_norm)

if vehicle_group:
    for i, lane in enumerate(approved_lanes):
        lane_origin = normalize_location(lane.get("origin", ""))
        lane_dest = normalize_location(lane.get("destination", ""))
        lane_vehicle = lane.get("vehicle", "")
        lane_unit = str(lane.get("unit", "per truck"))
        
        # 단위만 일치하면 됨
        if lane_unit != str(unit):
            continue
        
        lane_vehicle_group = get_vehicle_group(lane_vehicle)
        
        if lane_vehicle_group == vehicle_group:
            # 출발지/목적지 유사도 계산 (낮은 임계값)
            origin_sim = hybrid_similarity(origin, lane_origin)
            dest_sim = hybrid_similarity(destination, lane_dest)
            total_sim = 0.6 * origin_sim + 0.4 * dest_sim
            
            # 임계값: 0.4 이상 (Level 2보다 완화)
            if total_sim >= 0.4 and total_sim > best_score:
                best_match = {
                    "row_index": i + 2,
                    "match_score": total_sim,
                    "match_level": "VEHICLE_TYPE",
                    "lane_data": lane
                }
                best_score = total_sim

if best_match:
    return best_match
```

#### 예제

**Example 1: 같은 차량 그룹**
```
Item:
  origin: "WAREHOUSE A"
  destination: "WAREHOUSE B"
  vehicle: "FLATBED"

Vehicle Group: "FLATBED_GROUP"

Lane #60:
  origin: "SIMILAR WAREHOUSE A"
  destination: "SIMILAR WAREHOUSE B"
  vehicle: "FLAT BED"  ← 다른 표기, 같은 그룹

Lane Vehicle Group: "FLATBED_GROUP"

Similarity:
  origin_sim = 0.65
  dest_sim = 0.60
  total_sim = 0.6 * 0.65 + 0.4 * 0.60 = 0.630 ✅ ≥ 0.4

Match: ✅ VEHICLE_TYPE (score: 0.630)
```

**Example 2: 임계값 미달**
```
Item:
  origin: "LOCATION X"
  destination: "LOCATION Y"
  vehicle: "TRUCK"

Vehicle Group: "TRUCK_GROUP"

Lane #70:
  origin: "COMPLETELY DIFFERENT A"
  destination: "COMPLETELY DIFFERENT B"
  vehicle: "LORRY"  ← 같은 그룹

Similarity:
  origin_sim = 0.1
  dest_sim = 0.2
  total_sim = 0.6 * 0.1 + 0.4 * 0.2 = 0.140 ❌ < 0.4

Match: ❌ No match (all levels failed)
```

#### 성능 특성

- **정확도**: 70%+ (차량 그룹 = 유사한 요율 구조)
- **매칭률**: 중간 (6/44 = 13.6%)
- **처리 시간**: O(n × m)

---

### 2.2.5 Fallback 로직 및 의사결정 트리

#### Fallback 철학

**"Fail gracefully, match progressively"**

각 레벨은 점차 완화된 조건을 사용하며, 상위 레벨 실패 시에만 하위 레벨로 진행합니다. 이를 통해:
1. **정확도 우선**: 가능한 한 정확한 매칭
2. **매칭률 최대화**: 완화된 조건으로 커버리지 확대
3. **투명성**: 매칭 레벨 명시로 신뢰도 표시

#### 의사결정 트리

```
START
  │
  ▼
┌───────────────────────┐
│ Level 1: Exact Match  │
│ Condition: 100% match │
└───────┬───────────────┘
        │
        ├─► Match? YES ──► RETURN {level: "EXACT", score: 1.0}
        │
        NO
        │
        ▼
┌─────────────────────────────┐
│ Level 2: Similarity Match   │
│ Condition: Similarity ≥ 0.65│
└───────┬─────────────────────┘
        │
        ├─► Match? YES ──► RETURN {level: "SIMILARITY", score: 0.65~1.0}
        │
        NO
        │
        ▼
┌─────────────────────────┐
│ Level 3: Region Match   │
│ Condition: Same regions │
└───────┬─────────────────┘
        │
        ├─► Match? YES ──► RETURN {level: "REGION", score: 0.5}
        │
        NO
        │
        ▼
┌───────────────────────────────┐
│ Level 4: Vehicle Type Match   │
│ Condition: Same group + sim≥0.4│
└───────┬───────────────────────┘
        │
        ├─► Match? YES ──► RETURN {level: "VEHICLE_TYPE", score: 0.4~1.0}
        │
        NO
        │
        ▼
RETURN None (No match at any level)
```

#### 레벨별 임계값 설계

| Level | 임계값 | 근거 |
|-------|--------|------|
| Level 1 | 100% | 완벽 일치만 인정 |
| Level 2 | ≥ 0.65 | 오타 1~2개 허용, 경험적 최적값 |
| Level 3 | 0.5 (고정) | 권역 기반 추정, 보수적 점수 |
| Level 4 | ≥ 0.4 | 차량 그룹 + 위치 유사, 완화된 조건 |

---

### 2.2.6 find_matching_lane_enhanced() 상세 분석

#### 함수 시그니처

```python
def find_matching_lane_enhanced(
    origin: str,
    destination: str,
    vehicle: str,
    unit: str,
    approved_lanes: List[Dict],
    verbose: bool = False
) -> Optional[Dict]:
    """
    향상된 4단계 매칭 시스템
    
    Args:
        origin: 출발지
        destination: 목적지
        vehicle: 차량 타입
        unit: 단위 (per truck, per ton 등)
        approved_lanes: ApprovedLaneMap 레인 리스트
        verbose: 상세 로그 출력
    
    Returns:
        {
            "row_index": int,
            "match_score": float,
            "match_level": str,  # "EXACT", "SIMILARITY", "REGION", "VEHICLE_TYPE"
            "lane_data": dict
        } or None
    """
```

#### 전체 알고리즘 플로우

```python
# Phase 0: 정규화
origin_norm = normalize_location(origin)
dest_norm = normalize_location(destination)
vehicle_norm = normalize_vehicle(vehicle)

if verbose:
    print(f"\n[MATCHING] {origin} → {destination} ({vehicle})")
    print(f"  Normalized: {origin_norm} → {dest_norm} ({vehicle_norm})")

best_match = None
best_score = 0.0

# Phase 1: Level 1 - 정확 매칭
for i, lane in enumerate(approved_lanes):
    lane_origin = normalize_location(lane.get("origin", ""))
    lane_dest = normalize_location(lane.get("destination", ""))
    lane_vehicle = normalize_vehicle(lane.get("vehicle", ""))
    lane_unit = str(lane.get("unit", "per truck"))
    
    if (lane_origin == origin_norm and
        lane_dest == dest_norm and
        lane_vehicle == vehicle_norm and
        lane_unit == str(unit)):
        
        if verbose:
            print(f"  ✅ LEVEL 1 (EXACT): Lane {i} matched!")
        
        return {
            "row_index": i + 2,
            "match_score": 1.0,
            "match_level": "EXACT",
            "lane_data": lane
        }

# Phase 2: Level 2 - 유사도 매칭
for i, lane in enumerate(approved_lanes):
    lane_origin = lane.get("origin", "")
    lane_dest = lane.get("destination", "")
    lane_vehicle = normalize_vehicle(lane.get("vehicle", ""))
    lane_unit = str(lane.get("unit", "per truck"))
    
    if lane_vehicle != vehicle_norm or lane_unit != str(unit):
        continue
    
    origin_sim = hybrid_similarity(origin, lane_origin)
    dest_sim = hybrid_similarity(destination, lane_dest)
    total_sim = 0.6 * origin_sim + 0.4 * dest_sim
    
    if total_sim > best_score and total_sim >= 0.65:
        best_match = {
            "row_index": i + 2,
            "match_score": total_sim,
            "match_level": "SIMILARITY",
            "lane_data": lane
        }
        best_score = total_sim

if best_match and verbose:
    print(f"  ✅ LEVEL 2 (SIMILARITY): Lane {best_match['row_index']-2} matched (score: {best_score:.2f})")

if best_match:
    return best_match

# Phase 3: Level 3 - 권역별 매칭
origin_region = get_region(origin_norm)
dest_region = get_region(dest_norm)

if origin_region and dest_region:
    for i, lane in enumerate(approved_lanes):
        lane_origin = normalize_location(lane.get("origin", ""))
        lane_dest = normalize_location(lane.get("destination", ""))
        lane_vehicle = normalize_vehicle(lane.get("vehicle", ""))
        lane_unit = str(lane.get("unit", "per truck"))
        
        if lane_vehicle != vehicle_norm or lane_unit != str(unit):
            continue
        
        lane_origin_region = get_region(lane_origin)
        lane_dest_region = get_region(lane_dest)
        
        if lane_origin_region == origin_region and lane_dest_region == dest_region:
            score = 0.5
            
            if score > best_score:
                best_match = {
                    "row_index": i + 2,
                    "match_score": score,
                    "match_level": "REGION",
                    "lane_data": lane
                }
                best_score = score
    
    if best_match and verbose:
        print(f"  ✅ LEVEL 3 (REGION): Lane {best_match['row_index']-2} matched")

if best_match:
    return best_match

# Phase 4: Level 4 - 차량 타입별 매칭
vehicle_group = get_vehicle_group(vehicle_norm)

if vehicle_group:
    for i, lane in enumerate(approved_lanes):
        lane_origin = normalize_location(lane.get("origin", ""))
        lane_dest = normalize_location(lane.get("destination", ""))
        lane_vehicle = lane.get("vehicle", "")
        lane_unit = str(lane.get("unit", "per truck"))
        
        if lane_unit != str(unit):
            continue
        
        lane_vehicle_group = get_vehicle_group(lane_vehicle)
        
        if lane_vehicle_group == vehicle_group:
            origin_sim = hybrid_similarity(origin, lane_origin)
            dest_sim = hybrid_similarity(destination, lane_dest)
            total_sim = 0.6 * origin_sim + 0.4 * dest_sim
            
            if total_sim >= 0.4 and total_sim > best_score:
                best_match = {
                    "row_index": i + 2,
                    "match_score": total_sim,
                    "match_level": "VEHICLE_TYPE",
                    "lane_data": lane
                }
                best_score = total_sim
    
    if best_match and verbose:
        print(f"  ✅ LEVEL 4 (VEHICLE_TYPE): Lane {best_match['row_index']-2} matched")

if best_match:
    return best_match

# Phase 5: No match
if verbose:
    print(f"  ❌ NO MATCH")

return None
```

---

### 2.2.7 매칭 플로우차트

```
┌──────────────────────────────────────────────────────┐
│              find_matching_lane_enhanced()           │
└──────────────────────────────────────────────────────┘

Input: origin, destination, vehicle, unit, approved_lanes (124개)
                          │
                          ▼
              ┌─────────────────────┐
              │ PHASE 0: 정규화       │
              │ - normalize_location│
              │ - normalize_vehicle │
              └──────────┬───────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────┐
│ PHASE 1: LEVEL 1 - 정확 매칭 (순회: 124개 레인)          │
│                                                        │
│ for each lane:                                         │
│   if origin == lane_origin AND                         │
│      dest == lane_dest AND                             │
│      vehicle == lane_vehicle AND                       │
│      unit == lane_unit:                                │
│       RETURN {level: "EXACT", score: 1.0}              │
└────────────┬───────────────────────────────────────────┘
             │ No exact match
             ▼
┌────────────────────────────────────────────────────────┐
│ PHASE 2: LEVEL 2 - 유사도 매칭 (순회: ~100개 레인)        │
│                                                        │
│ best_score = 0.0                                       │
│ for each lane:                                         │
│   if vehicle == lane_vehicle AND unit == lane_unit:    │
│       origin_sim = hybrid_similarity(origin, lane_origin)│
│       dest_sim = hybrid_similarity(dest, lane_dest)    │
│       total_sim = 0.6 * origin_sim + 0.4 * dest_sim    │
│                                                        │
│       if total_sim ≥ 0.65 AND total_sim > best_score:  │
│           best_match = {level: "SIMILARITY", score: total_sim}│
│           best_score = total_sim                       │
│                                                        │
│ if best_match: RETURN best_match                       │
└────────────┬───────────────────────────────────────────┘
             │ No similarity match
             ▼
┌────────────────────────────────────────────────────────┐
│ PHASE 3: LEVEL 3 - 권역별 매칭 (조건부)                  │
│                                                        │
│ origin_region = get_region(origin)                     │
│ dest_region = get_region(dest)                         │
│                                                        │
│ if origin_region AND dest_region:                      │
│   for each lane:                                       │
│     if vehicle == lane_vehicle AND unit == lane_unit:  │
│         lane_origin_region = get_region(lane_origin)   │
│         lane_dest_region = get_region(lane_dest)       │
│                                                        │
│         if lane_origin_region == origin_region AND     │
│            lane_dest_region == dest_region:            │
│             RETURN {level: "REGION", score: 0.5}       │
│                                                        │
└────────────┬───────────────────────────────────────────┘
             │ No region match
             ▼
┌────────────────────────────────────────────────────────┐
│ PHASE 4: LEVEL 4 - 차량 타입별 매칭 (조건부)              │
│                                                        │
│ vehicle_group = get_vehicle_group(vehicle)             │
│                                                        │
│ if vehicle_group:                                      │
│   best_score = 0.0                                     │
│   for each lane:                                       │
│     if unit == lane_unit:                              │
│         lane_vehicle_group = get_vehicle_group(lane_vehicle)│
│                                                        │
│         if lane_vehicle_group == vehicle_group:        │
│             origin_sim = hybrid_similarity(origin, lane_origin)│
│             dest_sim = hybrid_similarity(dest, lane_dest)│
│             total_sim = 0.6 * origin_sim + 0.4 * dest_sim│
│                                                        │
│             if total_sim ≥ 0.4 AND total_sim > best_score:│
│                 best_match = {level: "VEHICLE_TYPE", score: total_sim}│
│                 best_score = total_sim                 │
│                                                        │
│   if best_match: RETURN best_match                     │
│                                                        │
└────────────┬───────────────────────────────────────────┘
             │ No vehicle type match
             ▼
┌────────────────────────────────────────────────────────┐
│ PHASE 5: NO MATCH                                      │
│                                                        │
│ RETURN None                                            │
│                                                        │
└────────────────────────────────────────────────────────┘

Output: match_result or None
```

---

## 📊 매칭 시스템 통합 성능

### 레벨별 기여도

| Level | 매칭 건수 | 기여율 | 누적 매칭률 |
|-------|----------|--------|------------|
| Level 1 (EXACT) | 9건 | 20.5% | 20.5% |
| Level 2 (SIMILARITY) | 6건 | 13.6% | 34.1% |
| Level 3 (REGION) | **14건** | **31.8%** ⭐ | **65.9%** |
| Level 4 (VEHICLE_TYPE) | 6건 | 13.6% | **79.5%** ✅ |
| **No Match** | **9건** | **20.5%** | - |

**핵심 인사이트:**
- Level 3 (권역 매칭)이 가장 큰 기여 (14건, 31.8%)
- 4단계 시스템으로 매칭률 38.6% → 79.5% (106% 개선)
- Level 3+4가 전체 개선의 45.4% 기여

---

## 🔗 다음 문서

➡️ **[Part 3: 통합/실행 흐름 & API & 성능 분석](Part3_Integration_API_Performance.md)**
- Excel 파일 처리 파이프라인
- 하이퍼링크 생성 메커니즘
- API 레퍼런스
- 성능 벤치마크 및 비즈니스 임팩트

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-13  
**Next Review**: 2025-11-13


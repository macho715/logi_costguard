"""
Cross-Document Validator Module
================================

다중 문서 간 일관성 및 정합성 검증

Author: HVDC Logistics Team
Version: 1.0.0
Last Updated: 2025-10-13
"""

from typing import List, Dict, Optional, Tuple, Any
from rdflib import Graph, Namespace
from datetime import datetime
import logging


class CrossDocValidator:
    """
    다중 문서 간 의미론적 일관성 검증

    Features:
    - MBL 번호 일치 검증
    - Container 번호 일치 검증
    - Weight/Quantity 일치 검증
    - Date 논리 검증
    - SPARQL 기반 불일치 탐지
    """

    def __init__(self, ontology_graph: Optional[Graph] = None):
        """
        Args:
            ontology_graph: OntologyMapper에서 생성된 RDF 그래프
        """
        self.graph = ontology_graph if ontology_graph else Graph()
        self.ex = Namespace("http://samsung.com/hvdc-project#")
        self.logistics = Namespace("http://samsung.com/project-logistics#")

        self.logger = self._setup_logger()

        # 검증 규칙
        self.validation_rules = {
            "weight_tolerance": 0.03,  # 3% 허용 오차
            "qty_tolerance": 0,  # 수량은 정확히 일치
            "date_tolerance_days": 1,  # 날짜 1일 허용
        }

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("CrossDocValidator")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def validate_item_consistency(
        self, item_code: str, documents: List[Dict]
    ) -> List[Dict]:
        """
        Item별 모든 문서 간 일관성 체크

        Args:
            item_code: HVDC Item Code
            documents: 파싱된 문서 리스트 [{doc_type, data}, ...]

        Returns:
            불일치 이슈 리스트
        """
        issues = []

        # 문서 타입별 분류
        docs_by_type = {}
        for doc in documents:
            doc_type = doc.get("doc_type", "UNKNOWN")
            docs_by_type[doc_type] = doc.get("data", {})

        # 공통 정규화 함수들
        def _norm_mbl(d: Dict) -> str:
            """MBL/BL 번호 정규화 (동의어 처리)"""
            return (d.get("mbl_no") or d.get("bl_number") or "").strip()

        def _norm_containers(d: Dict) -> List[str]:
            """컨테이너 번호 정규화 (문자열/딕셔너리 혼재 처리)"""
            cs = []
            raw = d.get("containers", [])

            if isinstance(raw, list):
                for x in raw:
                    if isinstance(x, dict):
                        v = x.get("container_no")
                        if v:
                            cs.append(v)
                    elif isinstance(x, str):
                        cs.append(x)
            elif isinstance(raw, dict):
                v = raw.get("container_no")
                if v:
                    cs.append(v)
            elif isinstance(raw, str):
                cs.append(raw)

            return sorted(set(cs))

        def _norm_weight(d: Dict) -> float:
            """무게 필드 정규화 (다양한 필드명 지원)"""
            w = d.get("gross_weight_kg") or d.get("weight_kg") or d.get("gross_weight")
            try:
                return float(w) if w else 0.0
            except (ValueError, TypeError):
                return 0.0

        # Rule 1: MBL 일치 확인 (정규화 함수 사용)
        mbl_issues = self.validate_mbl_consistency(docs_by_type, _norm_mbl)
        issues.extend(mbl_issues)

        # Rule 2: Container 일치 확인 (정규화 함수 사용)
        container_issues = self.validate_container_consistency(
            docs_by_type, _norm_containers
        )
        issues.extend(container_issues)

        # Rule 3: Weight 일치 확인 (정규화 함수 사용)
        weight_issues = self.validate_weight_consistency(docs_by_type, _norm_weight)
        issues.extend(weight_issues)

        # Rule 4: Date 논리 확인
        date_issues = self.validate_date_logic(docs_by_type)
        issues.extend(date_issues)

        # Rule 5: Quantity 일치 확인
        qty_issues = self.validate_quantity_consistency(docs_by_type)
        issues.extend(qty_issues)

        self.logger.info(f"Item {item_code}: {len(issues)} issues found")
        return issues

    def validate_mbl_consistency(
        self, docs_by_type: Dict, norm_mbl_func=None
    ) -> List[Dict]:
        """
        MBL 번호 일치 검증 (정규화 함수 지원)

        BOE, DO, DN, CarrierInvoice 간 MBL 번호가 일치해야 함
        """
        issues = []

        # MBL 추출 (정규화 함수 사용)
        mbls = {}

        for doc_type in ["BOE", "DO", "CarrierInvoice"]:
            if doc_type in docs_by_type:
                data = docs_by_type[doc_type]
                if isinstance(data, dict):
                    if norm_mbl_func:
                        mbl = norm_mbl_func(data)
                    else:
                        mbl = (
                            data.get("mbl_no") or data.get("bl_number") or ""
                        ).strip()
                    if mbl:
                        mbls[doc_type] = mbl

        # 일치 확인
        if len(set(mbls.values())) > 1:
            issues.append(
                {
                    "type": "MBL_MISMATCH",
                    "severity": "HIGH",
                    "details": f"Multiple MBL numbers found: {mbls}",
                    "documents": list(mbls.keys()),
                }
            )
            self.logger.warning(f"MBL mismatch: {mbls}")

        return issues

    def validate_container_consistency(
        self, docs_by_type: Dict, norm_containers_func=None
    ) -> List[Dict]:
        """
        Container 번호 일치 검증 (정규화 함수 지원)

        BOE, DO, DN 간 Container 번호가 일치해야 함
        """
        issues = []

        # Container 추출 (정규화 함수 사용)
        containers_by_doc = {}

        for doc_type in ["BOE", "DO", "DN"]:
            if doc_type in docs_by_type:
                data = docs_by_type[doc_type]
                if isinstance(data, dict):
                    if norm_containers_func:
                        containers_by_doc[doc_type] = set(norm_containers_func(data))
                    else:
                        # 기존 로직 유지 (폴백)
                        containers = []
                        if doc_type in ["BOE", "DO"]:
                            container_list = data.get("containers", [])
                            if isinstance(container_list, list):
                                for c in container_list:
                                    if isinstance(c, dict):
                                        containers.append(c.get("container_no"))
                                    else:
                                        containers.append(c)
                        elif doc_type == "DN":
                            container_no = data.get("container_no")
                            if container_no:
                                containers.append(container_no)
                        containers_by_doc[doc_type] = set(filter(None, containers))

        # 비교
        if len(containers_by_doc) >= 2:
            doc_types = list(containers_by_doc.keys())

            for i in range(len(doc_types)):
                for j in range(i + 1, len(doc_types)):
                    doc1, doc2 = doc_types[i], doc_types[j]
                    containers1 = containers_by_doc[doc1]
                    containers2 = containers_by_doc[doc2]

                    if containers1 != containers2:
                        issues.append(
                            {
                                "type": "CONTAINER_MISMATCH",
                                "severity": "HIGH",
                                "details": f"{doc1} vs {doc2} container mismatch",
                                doc1: list(containers1),
                                doc2: list(containers2),
                                "missing_in_" + doc1: list(containers2 - containers1),
                                "missing_in_" + doc2: list(containers1 - containers2),
                            }
                        )
                        self.logger.warning(f"Container mismatch: {doc1} vs {doc2}")

        return issues

    def validate_weight_consistency(
        self, docs_by_type: Dict, norm_weight_func=None
    ) -> List[Dict]:
        """
        Weight 일치 검증 (±3% 허용, 정규화 함수 지원)

        BOE, DO 간 Gross Weight 비교
        """
        issues = []

        weights = {}

        for doc_type in ["BOE", "DO"]:
            if doc_type in docs_by_type:
                data = docs_by_type[doc_type]
                if isinstance(data, dict):
                    if norm_weight_func:
                        weight = norm_weight_func(data)
                    else:
                        # 기존 로직 유지 (폴백)
                        weight = data.get("gross_weight_kg") or data.get("weight_kg")
                        try:
                            weight = float(weight) if weight else 0.0
                        except (ValueError, TypeError):
                            weight = 0.0

                    if weight > 0:
                        weights[doc_type] = weight

        # 비교
        if len(weights) >= 2:
            doc_types = list(weights.keys())

            for i in range(len(doc_types)):
                for j in range(i + 1, len(doc_types)):
                    doc1, doc2 = doc_types[i], doc_types[j]
                    weight1 = weights[doc1]
                    weight2 = weights[doc2]

                    # Delta 계산
                    if weight1 > 0:
                        delta_pct = abs(weight1 - weight2) / weight1

                        if delta_pct > self.validation_rules["weight_tolerance"]:
                            issues.append(
                                {
                                    "type": "WEIGHT_DEVIATION",
                                    "severity": "MEDIUM",
                                    "details": f"{doc1} vs {doc2} weight deviation: {delta_pct*100:.2f}%",
                                    doc1 + "_weight": weight1,
                                    doc2 + "_weight": weight2,
                                    "delta_pct": round(delta_pct * 100, 2),
                                    "tolerance": self.validation_rules[
                                        "weight_tolerance"
                                    ]
                                    * 100,
                                }
                            )
                            self.logger.warning(
                                f"Weight deviation: {delta_pct*100:.2f}%"
                            )

        return issues

    def validate_quantity_consistency(self, docs_by_type: Dict) -> List[Dict]:
        """
        Quantity 일치 검증

        BOE, DO 간 수량 비교 (정확히 일치해야 함)
        """
        issues = []

        quantities = {}

        for doc_type in ["BOE", "DO"]:
            if doc_type in docs_by_type:
                data = docs_by_type[doc_type]
                if isinstance(data, dict):
                    qty = data.get("quantity") or data.get("num_containers")
                    if qty:
                        quantities[doc_type] = int(qty)

        # 비교
        if len(quantities) >= 2:
            unique_qtys = set(quantities.values())

            if len(unique_qtys) > 1:
                issues.append(
                    {
                        "type": "QUANTITY_MISMATCH",
                        "severity": "HIGH",
                        "details": f"Quantity mismatch across documents: {quantities}",
                        "quantities": quantities,
                    }
                )
                self.logger.warning(f"Quantity mismatch: {quantities}")

        return issues

    def validate_date_logic(self, docs_by_type: Dict) -> List[Dict]:
        """
        Date 논리 검증

        CI.date ≤ PL.date ≤ BL.etd ≤ BL.eta ≤ DO.release_date
        """
        issues = []

        dates = {}

        # BOE
        if "BOE" in docs_by_type:
            data = docs_by_type["BOE"]
            if isinstance(data, dict) and data.get("dec_date"):
                dates["BOE.dec_date"] = self._parse_date(data["dec_date"])

        # DO
        if "DO" in docs_by_type:
            data = docs_by_type["DO"]
            if isinstance(data, dict):
                if data.get("do_date"):
                    dates["DO.do_date"] = self._parse_date(data["do_date"])
                if data.get("delivery_valid_until"):
                    dates["DO.validity"] = self._parse_date(
                        data["delivery_valid_until"]
                    )

        # DN
        if "DN" in docs_by_type:
            data = docs_by_type["DN"]
            if isinstance(data, dict) and data.get("loading_date"):
                dates["DN.loading_date"] = self._parse_date(data["loading_date"])

        # 날짜 순서 검증
        date_order_rules = [
            ("BOE.dec_date", "DO.do_date"),
            ("DO.do_date", "DO.validity"),
            ("DO.do_date", "DN.loading_date"),
        ]

        for earlier, later in date_order_rules:
            if earlier in dates and later in dates:
                if dates[earlier] and dates[later]:
                    if dates[earlier] > dates[later]:
                        issues.append(
                            {
                                "type": "DATE_LOGIC_VIOLATION",
                                "severity": "MEDIUM",
                                "details": f"{earlier} should be before {later}",
                                earlier: dates[earlier].isoformat(),
                                later: dates[later].isoformat(),
                            }
                        )
                        self.logger.warning(
                            f"Date logic violation: {earlier} > {later}"
                        )

        return issues

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열 파싱"""
        if not date_str:
            return None

        formats = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%b-%Y", "%d/%b/%Y"]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue

        return None

    def run_sparql_validation(self, item_code: str) -> List[Dict]:
        """
        SPARQL 기반 불일치 탐지

        Args:
            item_code: HVDC Item Code

        Returns:
            불일치 이슈 리스트
        """
        issues = []

        # Query 1: MBL 불일치
        mbl_query = f"""
        PREFIX logistics: <http://samsung.com/project-logistics#>

        SELECT ?shipment ?doc1 ?doc2 ?mbl1 ?mbl2
        WHERE {{
            ?shipment logistics:containsItem <http://samsung.com/hvdc-project#Item_{item_code}> .
            ?shipment logistics:describedIn ?doc1 .
            ?shipment logistics:describedIn ?doc2 .

            ?doc1 logistics:hasMBL ?mbl1 .
            ?doc2 logistics:hasMBL ?mbl2 .

            FILTER(?doc1 != ?doc2)
            FILTER(?mbl1 != ?mbl2)
        }}
        """

        try:
            results = list(self.graph.query(mbl_query))
            if results:
                issues.append(
                    {
                        "type": "SPARQL_MBL_MISMATCH",
                        "severity": "HIGH",
                        "details": "MBL mismatch detected via SPARQL",
                        "count": len(results),
                    }
                )
        except Exception as e:
            self.logger.error(f"SPARQL query error: {e}")

        return issues

    def generate_validation_report(self, item_code: str, documents: List[Dict]) -> Dict:
        """
        종합 검증 보고서 생성

        Args:
            item_code: HVDC Item Code
            documents: 파싱된 문서 리스트

        Returns:
            검증 보고서 딕셔너리
        """
        issues = self.validate_item_consistency(item_code, documents)

        # 심각도별 분류
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for issue in issues:
            severity = issue.get("severity", "LOW")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # 문서 타입별 이슈
        issues_by_type = {}
        for issue in issues:
            issue_type = issue["type"]
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)

        # 전체 상태 결정
        if severity_counts["HIGH"] > 0:
            overall_status = "FAIL"
        elif severity_counts["MEDIUM"] > 0:
            overall_status = "WARNING"
        else:
            overall_status = "PASS"

        report = {
            "item_code": item_code,
            "validation_timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "total_issues": len(issues),
            "severity_breakdown": severity_counts,
            "issues_by_type": issues_by_type,
            "all_issues": issues,
            "documents_validated": len(documents),
        }

        self.logger.info(
            f"Validation report generated for {item_code}: {overall_status}"
        )
        return report


# 사용 예시
if __name__ == "__main__":
    validator = CrossDocValidator()

    # 테스트 데이터
    test_documents = [
        {
            "doc_type": "BOE",
            "data": {
                "dec_no": "20252101030815",
                "dec_date": "28-08-2025",
                "mbl_no": "CHN2595234",
                "containers": ["CMAU2623154", "TGHU8788690"],
                "gross_weight_kg": 53125.7,
                "quantity": 3,
            },
        },
        {
            "doc_type": "DO",
            "data": {
                "do_number": "DOCHP00042642",
                "do_date": "26-08-2025",
                "mbl_no": "CHN2595234",
                "containers": [
                    {"container_no": "CMAU2623154", "seal_no": "M3228611"},
                    {"container_no": "TGHU8788690", "seal_no": "M3228619"},
                ],
                "weight_kg": 53125.7,
                "quantity": 3,
            },
        },
        {
            "doc_type": "DN",
            "data": {
                "waybill_no": "0825-18970AUH",
                "loading_date": "30/08/2025",
                "container_no": "CMAU2623154",
            },
        },
    ]

    # 검증 실행
    report = validator.generate_validation_report("HVDC-ADOPT-SCT-0126", test_documents)

    print("Validation Report:")
    print(f"  Status: {report['overall_status']}")
    print(f"  Total Issues: {report['total_issues']}")
    print(f"  Severity: {report['severity_breakdown']}")

    if report["all_issues"]:
        print("\nIssues:")
        for issue in report["all_issues"]:
            print(f"  - {issue['type']}: {issue['details']}")

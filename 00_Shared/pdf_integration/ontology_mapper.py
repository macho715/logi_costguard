"""
Ontology Mapper Module
======================

RDF 트리플 생성 및 SPARQL 검증을 통한 온톨로지 통합

Author: HVDC Logistics Team
Version: 1.0.0
Last Updated: 2025-10-13
"""

from typing import List, Dict, Optional, Tuple, Any
from rdflib import Graph, Namespace, Literal, URIRef, RDF, RDFS, XSD
from datetime import datetime
import logging
import re

try:
    # 새 파서: dict 형태 반환
    from parsers import dsv_pdf_parser as Parser

    PARSER_OK = True
except Exception:
    PARSER_OK = False
    logging.warning("parsers not available; PDF mapping will rely on dict inputs")


class OntologyMapper:
    """
    파싱된 PDF 데이터를 RDF 온톨로지로 매핑

    Features:
    - RDF Triple 생성
    - SPARQL 검증 쿼리
    - 규제 요건 자동 추론 (HS Code 기반)
    - Cross-document 연결
    """

    def __init__(self, base_uri: str = "http://samsung.com/hvdc-project#"):
        self.graph = Graph()
        self.base_uri = base_uri
        self.ex = Namespace(base_uri)
        self.logistics = Namespace("http://samsung.com/project-logistics#")

        # 네임스페이스 바인딩
        self.graph.bind("ex", self.ex)
        self.graph.bind("logistics", self.logistics)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)

        self.logger = self._setup_logger()

        # 규제 요건 규칙
        self.certification_rules = self._init_certification_rules()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("OntologyMapper")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _init_certification_rules(self) -> Dict[str, Dict]:
        """규제 요건 규칙 초기화"""
        return {
            "FANR": {
                "hs_codes": ["2844"],  # Nuclear materials
                "keywords": ["radioactive", "nuclear", "isotope"],
                "description": "FANR Import Permit",
                "lead_time_days": 30,
            },
            "MOIAT": {
                "hs_codes": ["84", "85"],  # Electrical/Mechanical
                "keywords": [],
                "description": "MOIAT Certificate of Conformity",
                "lead_time_days": 14,
            },
            "DCD": {
                "hs_codes": [],
                "keywords": ["hazmat", "dangerous", "un_no"],
                "description": "Dubai Civil Defense Approval",
                "lead_time_days": 21,
            },
        }

    def _sanitize_uri(self, text: str) -> str:
        """URI용 텍스트 정제"""
        # 특수문자 제거, 공백을 언더스코어로
        sanitized = re.sub(r"[^\w\s-]", "", text)
        sanitized = re.sub(r"\s+", "_", sanitized)
        return sanitized[:100]  # 최대 100자

    def map_boe_to_ontology(
        self, boe_data: Any, item_code: Optional[str] = None
    ) -> URIRef:
        """
        BOE (Bill of Entry) 데이터를 온톨로지로 매핑 (dict 또는 dataclass 유사 객체)

        Args:
            boe_data: BOEData 객체 또는 딕셔너리
            item_code: HVDC Item Code

        Returns:
            Shipment URI
        """
        # 데이터 추출 - dict 또는 객체 속성 지원
        data = boe_data.__dict__ if hasattr(boe_data, "__dict__") else boe_data

        # Shipment 객체 생성
        mbl_no = data.get("mbl_no", "UNKNOWN")
        shipment_uri = URIRef(self.ex[f"Shipment_{self._sanitize_uri(mbl_no)}"])

        self.graph.add((shipment_uri, RDF.type, self.logistics.DSVShipment))
        self.graph.add((shipment_uri, self.logistics.hasMBL, Literal(mbl_no)))

        if data.get("vessel"):
            self.graph.add(
                (shipment_uri, self.logistics.hasVessel, Literal(data["vessel"]))
            )

        if data.get("voyage_no"):
            self.graph.add(
                (shipment_uri, self.logistics.hasVoyage, Literal(data["voyage_no"]))
            )

        # CustomsDeclaration 객체 생성
        dec_no = data.get("dec_no", "UNKNOWN")
        customs_uri = URIRef(self.ex[f"BOE_{dec_no}"])

        self.graph.add((customs_uri, RDF.type, self.logistics.CustomsDeclaration))
        self.graph.add((customs_uri, self.logistics.hasDECNo, Literal(dec_no)))

        if data.get("dec_date"):
            self.graph.add(
                (customs_uri, self.logistics.hasDecDate, Literal(data["dec_date"]))
            )

        if data.get("hs_code"):
            self.graph.add(
                (customs_uri, self.logistics.hasHSCode, Literal(data["hs_code"]))
            )

        if data.get("duty_aed"):
            self.graph.add(
                (
                    customs_uri,
                    self.logistics.hasDutyPaid,
                    Literal(data["duty_aed"], datatype=XSD.decimal),
                )
            )

        if data.get("vat_aed"):
            self.graph.add(
                (
                    customs_uri,
                    self.logistics.hasVATPaid,
                    Literal(data["vat_aed"], datatype=XSD.decimal),
                )
            )

        # Shipment → CustomsDeclaration 링크
        self.graph.add((shipment_uri, self.logistics.describedIn, customs_uri))

        # Container 객체들 생성
        containers = data.get("containers", [])
        if containers:
            for container_no in containers:
                container_uri = URIRef(self.ex[f"Container_{container_no}"])
                self.graph.add((container_uri, RDF.type, self.logistics.Container))
                self.graph.add(
                    (
                        container_uri,
                        self.logistics.hasContainerNo,
                        Literal(container_no),
                    )
                )
                self.graph.add(
                    (shipment_uri, self.logistics.hasContainer, container_uri)
                )

        # Item 연결
        if item_code:
            item_uri = URIRef(self.ex[f"Item_{self._sanitize_uri(item_code)}"])
            self.graph.add((item_uri, RDF.type, self.logistics.Item))
            self.graph.add((item_uri, self.logistics.hasItemCode, Literal(item_code)))
            self.graph.add((shipment_uri, self.logistics.containsItem, item_uri))

            # 규제 요건 추론
            if data.get("hs_code") or data.get("description"):
                cert_requirements = self.infer_certification_requirements(
                    data.get("hs_code"), data.get("description", "")
                )

                for cert in cert_requirements:
                    cert_uri = self._create_certification_requirement(item_uri, cert)

        self.logger.info(f"BOE mapped: {dec_no} → Shipment {mbl_no}")
        return shipment_uri

    def map_do_to_ontology(
        self, do_data: Any, item_code: Optional[str] = None
    ) -> URIRef:
        """
        DO (Delivery Order) 데이터를 온톨로지로 매핑

        Args:
            do_data: DOData 객체 또는 딕셔너리
            item_code: HVDC Item Code

        Returns:
            Shipment URI
        """
        if hasattr(do_data, "__dict__"):
            data = do_data.__dict__
        else:
            data = do_data

        # Shipment 객체 생성
        mbl_no = data.get("mbl_no", "UNKNOWN")
        shipment_uri = URIRef(self.ex[f"Shipment_{self._sanitize_uri(mbl_no)}"])

        self.graph.add((shipment_uri, RDF.type, self.logistics.DSVShipment))
        self.graph.add((shipment_uri, self.logistics.hasMBL, Literal(mbl_no)))

        # DeliveryOrder 객체 생성
        do_number = data.get("do_number", "UNKNOWN")
        do_uri = URIRef(self.ex[f"DO_{do_number}"])

        self.graph.add((do_uri, RDF.type, self.logistics.DeliveryOrder))
        self.graph.add((do_uri, self.logistics.hasDONumber, Literal(do_number)))

        if data.get("do_date"):
            self.graph.add(
                (do_uri, self.logistics.hasIssueDate, Literal(data["do_date"]))
            )

        if data.get("delivery_valid_until"):
            self.graph.add(
                (
                    do_uri,
                    self.logistics.hasExpiryDate,
                    Literal(data["delivery_valid_until"]),
                )
            )

        # Shipment → DO 링크
        self.graph.add((shipment_uri, self.logistics.hasDeliveryOrder, do_uri))

        # Container 객체들
        containers = data.get("containers", [])
        if containers:
            for container_info in containers:
                if isinstance(container_info, dict):
                    container_no = container_info.get("container_no")
                    seal_no = container_info.get("seal_no")
                else:
                    container_no = container_info
                    seal_no = None

                if container_no:
                    container_uri = URIRef(self.ex[f"Container_{container_no}"])
                    self.graph.add((container_uri, RDF.type, self.logistics.Container))
                    self.graph.add(
                        (
                            container_uri,
                            self.logistics.hasContainerNo,
                            Literal(container_no),
                        )
                    )

                    if seal_no:
                        self.graph.add(
                            (container_uri, self.logistics.hasSealNo, Literal(seal_no))
                        )

                    self.graph.add(
                        (shipment_uri, self.logistics.hasContainer, container_uri)
                    )

        # Item 연결
        if item_code:
            item_uri = URIRef(self.ex[f"Item_{self._sanitize_uri(item_code)}"])
            self.graph.add((shipment_uri, self.logistics.containsItem, item_uri))

        self.logger.info(f"DO mapped: {do_number} → Shipment {mbl_no}")
        return shipment_uri

    def map_dn_to_ontology(
        self, dn_data: Any, item_code: Optional[str] = None
    ) -> URIRef:
        """
        DN (Delivery Note) 데이터를 온톨로지로 매핑

        Args:
            dn_data: DNData 객체 또는 딕셔너리
            item_code: HVDC Item Code

        Returns:
            TransportLeg URI
        """
        if hasattr(dn_data, "__dict__"):
            data = dn_data.__dict__
        else:
            data = dn_data

        # TransportLeg 객체 생성
        waybill_no = data.get("waybill_no", "UNKNOWN")
        transport_uri = URIRef(self.ex[f"Transport_{self._sanitize_uri(waybill_no)}"])

        self.graph.add((transport_uri, RDF.type, self.logistics.TransportLeg))
        self.graph.add(
            (transport_uri, self.logistics.hasWaybillNo, Literal(waybill_no))
        )

        if data.get("trip_no"):
            self.graph.add(
                (transport_uri, self.logistics.hasTripNo, Literal(data["trip_no"]))
            )

        if data.get("driver_name"):
            self.graph.add(
                (transport_uri, self.logistics.hasDriver, Literal(data["driver_name"]))
            )

        if data.get("head_plate") or data.get("trailer_plate"):
            vehicle_id = f"{data.get('head_plate', '')}_{data.get('trailer_plate', '')}"
            self.graph.add(
                (transport_uri, self.logistics.hasVehicleID, Literal(vehicle_id))
            )

        # Origin/Destination
        if data.get("loading_point"):
            self.graph.add(
                (
                    transport_uri,
                    self.logistics.hasOrigin,
                    Literal(data["loading_point"]),
                )
            )

        if data.get("destination"):
            self.graph.add(
                (
                    transport_uri,
                    self.logistics.hasDestination,
                    Literal(data["destination"]),
                )
            )

        # Timing
        if data.get("loading_date"):
            self.graph.add(
                (
                    transport_uri,
                    self.logistics.hasLoadingDate,
                    Literal(data["loading_date"]),
                )
            )

        if data.get("arrival_loading_time"):
            self.graph.add(
                (
                    transport_uri,
                    self.logistics.hasArrivalTime,
                    Literal(data["arrival_loading_time"]),
                )
            )

        # Container 연결
        if data.get("container_no"):
            container_uri = URIRef(self.ex[f"Container_{data['container_no']}"])
            self.graph.add(
                (transport_uri, self.logistics.transportsContainer, container_uri)
            )

        # Item 연결
        if item_code:
            item_uri = URIRef(self.ex[f"Item_{self._sanitize_uri(item_code)}"])
            self.graph.add((transport_uri, self.logistics.transportsItem, item_uri))

        self.logger.info(f"DN mapped: {waybill_no}")
        return transport_uri

    def map_carrier_invoice_to_ontology(self, invoice_data: Any) -> URIRef:
        """
        Carrier Invoice 데이터를 온톨로지로 매핑

        Args:
            invoice_data: CarrierInvoiceData 객체 또는 딕셔너리

        Returns:
            Invoice URI
        """
        if hasattr(invoice_data, "__dict__"):
            data = invoice_data.__dict__
        else:
            data = invoice_data

        # Invoice 객체 생성
        invoice_no = data.get("invoice_number", "UNKNOWN")
        invoice_uri = URIRef(self.ex[f"Invoice_{invoice_no}"])

        self.graph.add((invoice_uri, RDF.type, self.logistics.CarrierInvoice))
        self.graph.add((invoice_uri, self.logistics.hasInvoiceNo, Literal(invoice_no)))

        if data.get("invoice_date"):
            self.graph.add(
                (
                    invoice_uri,
                    self.logistics.hasIssueDate,
                    Literal(data["invoice_date"]),
                )
            )

        if data.get("total_incl_tax"):
            self.graph.add(
                (
                    invoice_uri,
                    self.logistics.hasTotalAmount,
                    Literal(data["total_incl_tax"], datatype=XSD.decimal),
                )
            )

        if data.get("currency"):
            self.graph.add(
                (invoice_uri, self.logistics.hasCurrency, Literal(data["currency"]))
            )

        # BL 연결
        if data.get("bl_number"):
            shipment_uri = URIRef(
                self.ex[f"Shipment_{self._sanitize_uri(data['bl_number'])}"]
            )
            self.graph.add((invoice_uri, self.logistics.billedFor, shipment_uri))

        self.logger.info(f"Carrier Invoice mapped: {invoice_no}")
        return invoice_uri

    def infer_certification_requirements(
        self, hs_code: Optional[str], description: str
    ) -> List[Dict]:
        """
        HS Code와 Description 기반 규제 요건 추론

        Args:
            hs_code: HS Code
            description: 상품 설명

        Returns:
            규제 요건 리스트
        """
        requirements = []
        desc_lower = description.lower()

        for cert_type, rules in self.certification_rules.items():
            matched = False

            # HS Code 매칭
            if hs_code:
                for hs_prefix in rules["hs_codes"]:
                    if hs_code.startswith(hs_prefix):
                        matched = True
                        break

            # Keyword 매칭
            for keyword in rules["keywords"]:
                if keyword in desc_lower:
                    matched = True
                    break

            if matched:
                requirements.append(
                    {
                        "type": cert_type,
                        "description": rules["description"],
                        "lead_time_days": rules["lead_time_days"],
                        "status": "PENDING",
                    }
                )

        return requirements

    def _create_certification_requirement(
        self, item_uri: URIRef, cert_info: Dict
    ) -> URIRef:
        """CertificationRequirement 객체 생성"""
        cert_type = cert_info["type"]
        cert_uri = URIRef(self.ex[f"Cert_{cert_type}_{item_uri.split('_')[-1]}"])

        self.graph.add((cert_uri, RDF.type, self.logistics.CertificationRequirement))
        self.graph.add((cert_uri, self.logistics.certType, Literal(cert_type)))
        self.graph.add(
            (
                cert_uri,
                self.logistics.certDescription,
                Literal(cert_info["description"]),
            )
        )
        self.graph.add((cert_uri, self.logistics.status, Literal(cert_info["status"])))
        self.graph.add(
            (
                cert_uri,
                self.logistics.leadTimeDays,
                Literal(cert_info["lead_time_days"], datatype=XSD.integer),
            )
        )

        # Item → Certification 링크
        self.graph.add((item_uri, self.logistics.requiresCertification, cert_uri))

        return cert_uri

    def run_sparql_query(self, query: str) -> List[Dict]:
        """
        SPARQL 쿼리 실행

        Args:
            query: SPARQL 쿼리 문자열

        Returns:
            쿼리 결과 리스트
        """
        results = []

        try:
            qres = self.graph.query(query)

            for row in qres:
                result_dict = {}
                for var in qres.vars:
                    result_dict[str(var)] = str(row[var]) if row[var] else None
                results.append(result_dict)

        except Exception as e:
            self.logger.error(f"SPARQL query error: {e}")

        return results

    def validate_missing_certifications(self) -> List[Dict]:
        """누락된 인증서 검색"""
        query = """
        PREFIX logistics: <http://samsung.com/project-logistics#>

        SELECT ?item ?hs_code ?required_cert ?status
        WHERE {
            ?item a logistics:Item ;
                  logistics:requiresCertification ?cert .

            OPTIONAL { ?item logistics:hasHSCode ?hs_code }

            ?cert logistics:certType ?required_cert ;
                  logistics:status ?status .

            FILTER(?status = "PENDING")

            FILTER NOT EXISTS {
                ?cert logistics:attachedDocument ?cert_doc
            }
        }
        """

        return self.run_sparql_query(query)

    def export_to_turtle(self, output_path: str):
        """RDF 그래프를 Turtle 형식으로 내보내기"""
        try:
            self.graph.serialize(destination=output_path, format="turtle")
            self.logger.info(f"Ontology exported to {output_path}")
        except Exception as e:
            self.logger.error(f"Export error: {e}")

    def get_graph_stats(self) -> Dict:
        """그래프 통계 반환"""
        return {
            "total_triples": len(self.graph),
            "shipments": len(
                list(self.graph.subjects(RDF.type, self.logistics.DSVShipment))
            ),
            "items": len(list(self.graph.subjects(RDF.type, self.logistics.Item))),
            "containers": len(
                list(self.graph.subjects(RDF.type, self.logistics.Container))
            ),
            "certifications": len(
                list(
                    self.graph.subjects(
                        RDF.type, self.logistics.CertificationRequirement
                    )
                )
            ),
        }


# 사용 예시
if __name__ == "__main__":
    mapper = OntologyMapper()

    # 테스트 데이터
    test_boe = {
        "dec_no": "20252101030815",
        "dec_date": "28-08-2025",
        "mbl_no": "CHN2595234",
        "vessel": "CMA CGM PEGASUS",
        "voyage_no": "0MDEIE1MA",
        "containers": ["CMAU2623154", "TGHU8788690"],
        "hs_code": "9405500000",
        "description": "Nonelectrical luminaires",
        "duty_aed": 24657.00,
        "vat_aed": 6664.00,
    }

    shipment_uri = mapper.map_boe_to_ontology(test_boe, "HVDC-ADOPT-SCT-0126")

    print("Ontology Stats:", mapper.get_graph_stats())
    print("\nMissing Certifications:", mapper.validate_missing_certifications())

    # Turtle 내보내기
    mapper.export_to_turtle("output/hvdc_ontology.ttl")

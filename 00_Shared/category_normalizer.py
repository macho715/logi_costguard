#!/usr/bin/env python3
"""
Category Normalizer for HVDC Invoice Audit System
Category 정규화 (Synonym + 수량 제거 + 약어 확장)

Version: 1.0.0
Created: 2025-10-14
Author: MACHO-GPT v3.4-mini HVDC Project Enhancement
"""

import re
import json
from pathlib import Path
from typing import Dict, Optional
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CategoryNormalizer:
    """
    Category 정규화 클래스

    주요 기능:
    1. 수량 패턴 제거: "(1 X 20DC)", "(CW: 2136 KG)" 등
    2. Synonym 매핑: CHARGES → FEE, TRUCKING → TRANSPORTATION
    3. 연속 공백 제거
    4. 대문자 통일
    """

    def __init__(self, synonyms_config_path: Optional[str] = None):
        """
        초기화

        Args:
            synonyms_config_path: Synonym Dictionary JSON 파일 경로
        """
        if synonyms_config_path is None:
            # 기본 경로: Rate/config_synonyms.json
            synonyms_config_path = (
                Path(__file__).parent.parent / "Rate" / "config_synonyms.json"
            )
        else:
            synonyms_config_path = Path(synonyms_config_path)

        self.synonyms = self._load_synonyms(synonyms_config_path)
        self.synonym_map = self._flatten_synonyms()

        logger.info(
            f"CategoryNormalizer initialized with {len(self.synonym_map)} synonyms"
        )

    def _load_synonyms(self, config_path: Path) -> Dict:
        """Synonym Dictionary 로드"""
        if not config_path.exists():
            logger.warning(f"Synonym config not found: {config_path}")
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"Loaded synonyms from: {config_path.name}")
            return config
        except Exception as e:
            logger.error(f"Error loading synonyms: {e}")
            return {}

    def _flatten_synonyms(self) -> Dict[str, str]:
        """
        중첩된 Synonym Dictionary를 평면화

        Example:
            {"charge_types": {"CHARGES": "FEE", "CHARGE": "FEE"}}
            → {"CHARGES": "FEE", "CHARGE": "FEE"}
        """
        flat_map = {}

        for category, mappings in self.synonyms.items():
            if category == "metadata":
                continue

            if isinstance(mappings, dict):
                flat_map.update(mappings)

        return flat_map

    def normalize(self, category: str) -> str:
        """
        Category 정규화 수행

        Args:
            category: 원본 카테고리 (예: "TERMINAL HANDLING CHARGES (1 X 20DC)")

        Returns:
            정규화된 카테고리 (예: "TERMINAL HANDLING FEE")
        """
        if not category or not isinstance(category, str):
            return ""

        normalized = category.strip().upper()

        # Step 1: 괄호 안 내용 제거 (수량, 무게 등)
        # 예: "(1 X 20DC)", "(CW: 2136 KG)", "(PER 20 FT)"
        normalized = re.sub(r"\([^)]*\)", "", normalized)

        # Step 2: Synonym 매핑
        for old_term, new_term in self.synonym_map.items():
            # 단어 경계를 고려한 치환 (부분 매칭 방지)
            normalized = re.sub(
                rf"\b{re.escape(old_term)}\b", new_term, normalized, flags=re.IGNORECASE
            )

        # Step 3: 연속 공백 제거
        normalized = re.sub(r"\s+", " ", normalized)

        # Step 4: 양끝 공백 제거
        normalized = normalized.strip()

        if normalized != category.strip().upper():
            logger.debug(f"[NORMALIZE] '{category}' → '{normalized}'")

        return normalized

    def normalize_batch(self, categories: list) -> list:
        """
        여러 Category를 일괄 정규화

        Args:
            categories: 원본 카테고리 리스트

        Returns:
            정규화된 카테고리 리스트
        """
        return [self.normalize(cat) for cat in categories]

    def get_synonym_map(self) -> Dict[str, str]:
        """현재 Synonym Map 반환"""
        return self.synonym_map.copy()

    def add_synonym(self, old_term: str, new_term: str):
        """
        동적으로 Synonym 추가

        Args:
            old_term: 치환할 용어
            new_term: 표준 용어
        """
        self.synonym_map[old_term.upper()] = new_term.upper()
        logger.info(f"Added synonym: {old_term} → {new_term}")


# 테스트 실행
if __name__ == "__main__":
    normalizer = CategoryNormalizer()

    print("\n" + "=" * 80)
    print("Category Normalizer 테스트")
    print("=" * 80)

    # 테스트 케이스
    test_cases = [
        "TERMINAL HANDLING CHARGES (1 X 20DC)",
        "INLAND TRUCKING FROM AIRPORT TO MOSB",
        "CUSTOMS CLEARANCE FEE",
        "DELIVERY ORDER CHARGE (PER SHIPMENT)",
        "TRANSPORT CHARGES (CW: 2136 KG)",
        "THC FEE (40FT CONTAINER)",
        "HAND FEE",
        "DOC PROCESSING CHARGES",
    ]

    print("\n정규화 결과:")
    print("-" * 80)
    for original in test_cases:
        normalized = normalizer.normalize(original)
        print(f"  {original:<50} → {normalized}")

    print("\n" + "=" * 80)
    print(f"총 Synonym 수: {len(normalizer.get_synonym_map())}개")
    print("=" * 80)

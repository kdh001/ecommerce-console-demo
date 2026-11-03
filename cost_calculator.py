"""원가 계산에 사용되는 단계별 비용 모델.

합성 입력값만 사용하는 교육용 데모.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import math
from typing import Any


DISCLAIMER = (
    "본 계산은 참고용 추정입니다. 과세표준·관세·부가세는 품목 HS·CIF·특례 등에 따라 달라지며, "
    "실제 납부액은 관세사·관세청(UNI-PASS) 확인이 필요합니다. "
    "부가세는 사업자 여건에 따라 환급·공제 가능하나 자동 보장되지 않습니다."
)


@dataclass
class CostInput:
    """노란 입력 + 회색 설정."""

    unit_cny: float = 12.0
    qty: float = 50.0
    category: str = "기타/직접입력"
    tariff_override: float | None = 5.0
    box_l: float = 0.5
    box_w: float = 0.4
    box_h: float = 0.3
    box_count: float = 20.0
    sale_price: float | None = None
    target_margin: float | None = None
    # 설정
    cbm_price: float = 80_000.0
    fx: float = 200.0
    fee_mode: str = "%"  # "%" | "fixed"
    fee_pct: float = 10.0
    fee_fixed: float = 0.0
    domestic_override: float | None = None
    doc: float = 20_000.0
    # 카테고리 표에서 조회된 관세% (TBD면 None)
    category_tariff_pct: float | None = None


@dataclass
class CostResult:
    """초록 결과 + 단계별 스택."""

    unit_krw: float
    product_total: float
    box_cbm: float
    total_cbm: float
    intl: float
    fee: float
    tax_base: float
    tariff_pct_applied: float
    tariff: float
    vat: float
    domestic: float
    doc: float
    cash_total: float
    effective_total: float
    unit_cash: float
    unit_effective: float
    unit_vat: float
    margin_pct: float | None = None
    recommended_price: float | None = None
    disclaimer: str = DISCLAIMER
    steps: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _resolve_tariff_pct(inp: CostInput) -> float:
    """수동 덮어쓰기 우선, 없으면 카테고리 조회, 없으면 0."""
    if inp.tariff_override is not None:
        return float(inp.tariff_override)
    if inp.category_tariff_pct is not None:
        return float(inp.category_tariff_pct)
    return 0.0


def _auto_domestic(total_cbm: float) -> float:
    """합성 예시용 CBM 구간 국내화물. 5 초과는 0."""
    if total_cbm <= 3:
        return 60_000.0
    if total_cbm <= 5:
        return 90_000.0
    return 0.0


def calculate(inp: CostInput) -> CostResult:
    """8단계 비용을 계산하고 수량으로 나눈다."""
    required = ("unit_cny", "qty", "box_l", "box_w", "box_h", "box_count", "cbm_price", "fx", "fee_pct", "fee_fixed", "doc")  # 항상 필요한 숫자 필드다.
    optional = ("tariff_override", "category_tariff_pct", "sale_price", "target_margin", "domestic_override")  # 생략할 수 있는 숫자 필드다.
    for name in required + optional:  # 모든 입력을 계산 전에 검증한다.
        value = getattr(inp, name)  # 필드 값을 읽는다.
        if name in optional and value is None:  # 선택 필드의 생략은 허용한다.
            continue
        try:  # 너무 큰 정수는 유한성 검사 중 오류가 날 수 있다.
            valid = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)  # 숫자 문자열과 무한대·NaN을 거부한다.
        except OverflowError:  # 부동소수점으로 표현할 수 없는 정수다.
            valid = False
        if not valid or value < 0:  # 음수와 잘못된 숫자를 명확히 거부한다.
            raise ValueError(f"{name}은 유한한 0 이상의 숫자여야 합니다")
    if inp.qty <= 0:  # 개당 계산의 분모는 양수여야 한다.
        raise ValueError("qty는 0보다 커야 합니다")
    if inp.sale_price is not None and inp.sale_price <= 0:  # 마진의 분모도 양수여야 한다.
        raise ValueError("sale_price는 0보다 커야 합니다")
    if inp.target_margin is not None and inp.target_margin >= 100:  # 권장가의 분모가 0 이하가 되지 않도록 한다.
        raise ValueError("target_margin은 100 미만이어야 합니다")
    if inp.fee_mode not in ("%", "fixed"):  # 알 수 없는 모드를 고정 수수료로 오인하지 않는다.
        raise ValueError("fee_mode는 '%' 또는 'fixed'여야 합니다")
    inp = replace(inp, **{name: float(getattr(inp, name)) for name in required + optional if getattr(inp, name) is not None})  # 계산은 유한성 검사가 가능한 부동소수점으로 통일한다.
    unit_krw = inp.unit_cny * inp.fx
    product_total = unit_krw * inp.qty
    box_cbm = inp.box_l * inp.box_w * inp.box_h
    total_cbm = box_cbm * inp.box_count
    intl = total_cbm * inp.cbm_price
    if inp.fee_mode == "%":
        fee = product_total * inp.fee_pct / 100.0
    else:
        fee = float(inp.fee_fixed)
    tax_base = product_total + intl
    tariff_pct = _resolve_tariff_pct(inp)
    tariff = tax_base * tariff_pct / 100.0
    vat = (tax_base + tariff) * 0.10
    if inp.domestic_override is not None:
        domestic = float(inp.domestic_override)
    else:
        domestic = _auto_domestic(total_cbm)
    doc = float(inp.doc)
    cash = product_total + intl + fee + tariff + vat + domestic + doc
    effective = cash - vat
    qty = inp.qty
    unit_cash = cash / qty
    unit_effective = effective / qty
    unit_vat = vat / qty

    margin_pct: float | None = None
    recommended: float | None = None
    if inp.sale_price is not None and inp.sale_price > 0:
        margin_pct = (inp.sale_price - unit_effective) / inp.sale_price * 100.0
    if inp.target_margin is not None and inp.target_margin < 100:
        # 권장가 = 실질개당 / (1 - 목표마진%)
        denom = 1.0 - inp.target_margin / 100.0
        if denom > 0:
            recommended = unit_effective / denom

    calculated = (unit_krw, product_total, box_cbm, total_cbm, intl, fee, tax_base, tariff_pct, tariff, vat, domestic, doc, cash, effective, unit_cash, unit_effective, unit_vat, margin_pct, recommended)  # 오버플로를 검사할 결과다.
    if any(value is not None and not math.isfinite(value) for value in calculated):  # 유한한 입력끼리의 연산도 무한대가 될 수 있다.
        raise ValueError("계산 결과가 표현 가능한 범위를 벗어났습니다")

    steps = [
        {"step": 1, "name": "개당원화", "amount": unit_krw},
        {"step": 2, "name": "제품합계", "amount": product_total},
        {"step": 3, "name": "국제물류", "amount": intl},
        {"step": 4, "name": "수수료", "amount": fee},
        {"step": 5, "name": "관세", "amount": tariff},
        {"step": 6, "name": "부가세", "amount": vat},
        {"step": 7, "name": "국내화물", "amount": domestic},
        {"step": 8, "name": "서류비", "amount": doc},
    ]

    return CostResult(
        unit_krw=unit_krw,
        product_total=product_total,
        box_cbm=box_cbm,
        total_cbm=total_cbm,
        intl=intl,
        fee=fee,
        tax_base=tax_base,
        tariff_pct_applied=tariff_pct,
        tariff=tariff,
        vat=vat,
        domestic=domestic,
        doc=doc,
        cash_total=cash,
        effective_total=effective,
        unit_cash=unit_cash,
        unit_effective=unit_effective,
        unit_vat=unit_vat,
        margin_pct=margin_pct,
        recommended_price=recommended,
        steps=steps,
    )



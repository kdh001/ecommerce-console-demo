"""합성 입력과 계산 관계를 이용한 독립 실행 테스트."""

import unittest  # Python 표준 테스트 도구를 사용한다.

from cost_calculator import CostInput, calculate  # 공개 사본의 계산기를 검사한다.


class CostTests(unittest.TestCase):  # 원가 계산의 주요 관계를 확인한다.
    def test_synthetic_example(self):  # 합성 숫자의 주요 결과를 독립 계산과 비교한다.
        result = calculate(CostInput())  # 기본 합성 값을 사용한다.
        self.assertAlmostEqual(result.product_total, 120000)  # 12 × 200 × 50이다.
        self.assertAlmostEqual(result.intl, 96000)  # 부피 1.2 × 물류비 80000이다.
        self.assertAlmostEqual(result.tariff, 10800)  # 과세표준 216000의 가상 관세 5%다.
        self.assertAlmostEqual(result.vat, 22680)  # 과세표준과 관세의 10%다.
        self.assertAlmostEqual(result.cash_total - result.effective_total, result.vat)  # 부가세 차이를 확인한다.
        self.assertAlmostEqual(result.unit_effective, result.effective_total / 50)  # 50개에 배분한다.

    def test_manual_cost_and_margin(self):  # 고정 수수료와 목표 마진을 확인한다.
        result = calculate(CostInput(fee_mode="fixed", fee_fixed=5000, domestic_override=0, target_margin=20))  # 가상 값을 직접 지정한다.
        self.assertEqual(result.fee, 5000)  # 지정한 고정 수수료가 적용된다.
        self.assertEqual(result.domestic, 0)  # 지정한 국내 운송비가 적용된다.
        self.assertAlmostEqual(result.recommended_price, result.unit_effective / 0.8)  # 목표 마진 20%를 반영한다.

    def test_zero_quantity_rejected(self):  # 수량 0을 허용하지 않는다.
        with self.assertRaises(ValueError):  # 잘못된 입력은 오류여야 한다.
            calculate(CostInput(qty=0))  # 0개 입력을 전달한다.

    def test_invalid_numbers_and_modes(self):  # 잘못된 값이 조용히 계산되지 않는지 확인한다.
        cases = ({"qty": -1}, {"qty": float("nan")}, {"unit_cny": float("inf")}, {"unit_cny": "12"}, {"qty": True}, {"tariff_override": "bad"}, {"tariff_override": -1}, {"domestic_override": -1}, {"fee_mode": "unknown"}, {"sale_price": 0}, {"target_margin": -1}, {"target_margin": 100}, {"unit_cny": 10**400})  # 숫자·분모·모드 경계를 준비한다.
        for fields in cases:  # 각 입력을 따로 검증한다.
            with self.subTest(fields=fields), self.assertRaises(ValueError):  # 모든 잘못된 입력이 실패해야 한다.
                calculate(CostInput(**fields))  # 입력을 계산기에 전달한다.

    def test_overflow_rejected(self):  # 유한한 숫자끼리 곱해 무한대가 되는 경우다.
        with self.assertRaises(ValueError):  # 무한 결과를 반환하지 않아야 한다.
            calculate(CostInput(unit_cny=1e308, fx=1e308))  # 부동소수점 범위를 초과한다.

    def test_valid_boundary_values(self):  # 유효한 경계 입력도 확인한다.
        result = calculate(CostInput(unit_cny=0, tariff_override=0, domestic_override=0, target_margin=0, sale_price=1))  # 금액 0과 0%는 유효하다.
        self.assertEqual(result.tariff, 0)  # 관세 입력 0이 반영된다.
        self.assertAlmostEqual(result.recommended_price, result.unit_effective)  # 목표 마진 0%는 원가와 같다.


if __name__ == "__main__":  # 직접 실행 시 테스트를 수행한다.
    unittest.main()  # 모든 테스트를 실행한다.

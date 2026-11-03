"""합성 숫자로 수입 원가 계산 결과를 출력하는 예제."""

import json  # 결과를 읽기 쉬운 JSON으로 출력한다.

from cost_calculator import CostInput, calculate  # 사본 안의 계산기를 불러온다.


if __name__ == "__main__":  # 이 파일을 직접 실행했을 때만 예제를 출력한다.
    example = CostInput()  # 모든 기본 입력은 실제 거래와 무관한 합성 값이다.
    result = calculate(example)  # 단계별 비용과 개당 비용을 계산한다.
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))  # 한글을 유지해 출력한다.

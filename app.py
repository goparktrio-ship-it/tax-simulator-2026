import pandas as pd
import streamlit as st


def format_korean_currency(n: int) -> str:
    """숫자를 한글 금액 단위(만, 억, 조 등)로 변환하는 헬퍼 함수"""
    if n == 0:
        return "0원"
    units = ["", "만", "억", "조", "경"]
    res = []
    idx = 0
    while n > 0:
        chunk = n % 10000
        if chunk > 0:
            res.append(f"{chunk}{units[idx]}")
        n //= 10000
        idx += 1
    return " ".join(res[::-1]) + " 원"


# =========================================================
# 1. 정밀 재산세 및 종부세 통합 시뮬레이션 엔진
# =========================================================
class ComprehensiveTaxEngine:
  """1세대 1주택 및 다주택 종부세·정밀 재산세 통합 시뮬레이션 엔진"""

  @classmethod
  def get_tax_brackets(cls, year_label: str, property_type: str):
    is_multi = property_type in ["LOCAL_MULTI_HOME", "HEAVY_MULTI_HOME"]

    if year_label == "2026년":
      if property_type == "HEAVY_MULTI_HOME":
        return [
            (300_000_000, 0.005, 0),
            (600_000_000, 0.007, 600_000),
            (1_200_000_000, 0.010, 2_400_000),
            (2_500_000_000, 0.020, 14_400_000),
            (5_000_000_000, 0.030, 39_400_000),
            (9_400_000_000, 0.040, 89_400_000),
            (float("inf"), 0.050, 183_400_000),
        ]
      else:
        return [
            (300_000_000, 0.005, 0),
            (600_000_000, 0.007, 600_000),
            (1_200_000_000, 0.010, 2_400_000),
            (2_500_000_000, 0.013, 6_000_000),
            (5_000_000_000, 0.015, 11_000_000),
            (9_400_000_000, 0.020, 36_000_000),
            (float("inf"), 0.027, 101_800_000),
        ]
    elif year_label == "2027년":
      if is_multi:
        return [
            (300_000_000, 0.005, 0),
            (600_000_000, 0.007, 600_000),
            (1_200_000_000, 0.013, 4_200_000), 
            (2_500_000_000, 0.020, 12_600_000), 
            (5_000_000_000, 0.030, 37_600_000),
            (9_400_000_000, 0.040, 87_600_000),
            (float("inf"), 0.050, 181_600_000),
        ]
      else:
        return [
            (300_000_000, 0.005, 0),
            (600_000_000, 0.007, 600_000),
            (1_200_000_000, 0.013, 4_200_000), 
            (2_500_000_000, 0.015, 6_600_000), 
            (5_000_000_000, 0.020, 19_100_000),
            (9_400_000_000, 0.027, 54_100_000),
            (float("inf"), 0.035, 129_300_000),
        ]
    else:
      return [
          (300_000_000, 0.005, 0),
          (600_000_000, 0.007, 600_000),
          (1_200_000_000, 0.013, 4_200_000),
          (2_500_000_000, 0.020, 12_600_000),
          (5_000_000_000, 0.030, 37_600_000),
          (9_400_000_000, 0.040, 87_600_000),
          (float("inf"), 0.050, 181_600_000),
      ]

  @classmethod
  def get_basic_deduction(cls, property_type: str, year_label: str, is_joint_default: bool, price_res: int, total_price: int) -> int:
    is_residing = price_res > 0
    ratio = price_res / total_price if total_price > 0 else 0

    if year_label == "2026년":
      if property_type == "RESIDENT_1HOME":
        return 1_800_000_000 if is_joint_default else 1_200_000_000
      return 900_000_000
    else:
      if property_type == "RESIDENT_1HOME":
        if is_joint_default:
          return 1_800_000_000 if is_residing else 800_000_000
        else:
          return 1_400_000_000 if is_residing else 900_000_000
      else:
        return 400_000_000 + int(500_000_000 * ratio)

  @classmethod
  def get_fmvr(cls, property_type: str, year_label: str, is_joint_default: bool = False) -> float:
    if property_type == "HEAVY_MULTI_HOME" or (property_type == "RESIDENT_1HOME" and is_joint_default):
      if year_label == "2026년":
        return 60.0
      elif year_label == "2027년":
        return 70.0
      else:
        return 80.0
    elif property_type in ["RESIDENT_1HOME", "LOCAL_MULTI_HOME"]:
      if year_label == "2026년":
        return 60.0
      else:
        return 70.0
    return 60.0

  @classmethod
  def get_pt_fmvr(cls, property_type: str, year_label: str) -> float:
    if property_type == "RESIDENT_1HOME":
      return 0.45
    return 0.60

  @classmethod
  def calc_tax_base(cls, total_price: int, deduction: int, fmvr: float) -> int:
    return int(max(0, total_price - deduction) * (fmvr / 100.0))

  @classmethod
  def calc_gross_tax(cls, tax_base: int, property_type: str, year_label: str) -> tuple:
    if tax_base <= 0:
      return 0, 0.0
    brackets = cls.get_tax_brackets(year_label, property_type)
    for limit, rate, deduction in brackets:
      if tax_base <= limit:
        tax = int(tax_base * rate - deduction)
        return max(0, tax), rate
    return 0, 0.0

  @classmethod
  def calc_property_tax_deduction(cls, tax_base: int, pt_fmvr: float) -> int:
    if tax_base <= 0:
      return 0
    return int(tax_base * pt_fmvr * 0.004)

  @classmethod
  def calc_property_tax(cls, total_price: int, pt_fmvr: float) -> int:
    prop_tax_base = total_price * pt_fmvr

    if prop_tax_base <= 60_000_000:
      base_tax = prop_tax_base * 0.001
    elif prop_tax_base <= 150_000_000:
      base_tax = 60_000 + (prop_tax_base - 60_000_000) * 0.0015
    elif prop_tax_base <= 300_000_000:
      base_tax = 195_000 + (prop_tax_base - 150_000_000) * 0.0025
    else:
      base_tax = 570_000 + (prop_tax_base - 300_000_000) * 0.004

    urban_tax = prop_tax_base * 0.0014
    edu_tax = base_tax * 0.20

    return int(base_tax + urban_tax + edu_tax)

  @classmethod
  def calc_tax_credits(
      cls, year_label: str, age: int, holding_years: int, residence_years: int, is_eligible: bool
  ) -> tuple:
    if not is_eligible:
      return 0.0, 0.0, 0.0, "세액공제 대상 아님"

    age_rate = 0.0
    if age >= 70:
      age_rate = 0.40
    elif age >= 65:
      age_rate = 0.30
    elif age >= 60:
      age_rate = 0.20

    period_rate = 0.0
    desc_str = ""
    
    if year_label == "2026년":
      if holding_years >= 15:
        period_rate = 0.50
        desc_str = "보유15년"
      elif holding_years >= 10:
        period_rate = 0.40
        desc_str = "보유10년"
      elif holding_years >= 5:
        period_rate = 0.20
        desc_str = "보유5년"
      else:
        desc_str = "보유미달"
    elif year_label == "2027년":
      if holding_years >= 15 and residence_years >= 10:
        period_rate = 0.50
        desc_str = "거주요건만족"
      elif holding_years >= 10 and residence_years >= 5:
        period_rate = 0.40
        desc_str = "거주요건만족"
      elif holding_years >= 5:
        period_rate = 0.20
        desc_str = "보유기본적용(거주미달)"
      else:
        desc_str = "보유5년미만"
    else:
      if residence_years >= 15:
        period_rate = 0.50
        desc_str = "거주15년"
      elif residence_years >= 10:
        period_rate = 0.40
        desc_str = "거주10년"
      elif residence_years >= 5:
        period_rate = 0.20
        desc_str = "거주5년"
      else:
        period_rate = 0.0
        desc_str = "거주5년미만(기간공제0%)"

    total_rate = min(0.80, age_rate + period_rate)
    final_desc = f"{desc_str}"
    
    return total_rate, age_rate, period_rate, final_desc

  @classmethod
  def run_single_year(
      cls,
      year_label: str,
      total_price: int,
      price_res: int,
      property_type: str,
      age: int,
      holding_years: int,
      residence_years: int,
      prev_year_tax: int,
      prev_year_prop_tax: int,
      is_joint_default: bool,
      apply_tax_cap: bool,
  ) -> dict:
    
    deduction = cls.get_basic_deduction(property_type, year_label, is_joint_default, price_res, total_price)
    fmvr = cls.get_fmvr(property_type, year_label, is_joint_default)
    pt_fmvr = cls.get_pt_fmvr(property_type, year_label)

    # 1. 재산세 산출 및 세부담 상한(105% ~ 130%) 로직 적용
    calculated_prop_tax = cls.calc_property_tax(total_price, pt_fmvr)
    
    if total_price <= 300_000_000:
        pt_cap_rate = 1.05
    elif total_price <= 600_000_000:
        pt_cap_rate = 1.10
    else:
        pt_cap_rate = 1.30

    if apply_tax_cap and prev_year_prop_tax > 0:
        prop_tax_cap_limit = int(prev_year_prop_tax * pt_cap_rate)
    else:
        prop_tax_cap_limit = float("inf")

    final_property_tax = min(calculated_prop_tax, prop_tax_cap_limit)
    prop_cap_applied = calculated_prop_tax > prop_tax_cap_limit
    
    # 상한 적용으로 재산세가 줄어든 비율만큼, 종부세에서 공제되는 '재산세액'도 비례 축소
    pt_cap_ratio = final_property_tax / calculated_prop_tax if calculated_prop_tax > 0 else 1.0

    # 2. 종부세 산출 로직
    if is_joint_default and property_type == "RESIDENT_1HOME":
        person_price = total_price / 2
        person_deduct = deduction / 2
        person_tb = int(max(0, person_price - person_deduct) * (fmvr / 100.0))
        
        p_gross, applied_tax_rate = cls.calc_gross_tax(person_tb, property_type, year_label)
        p_prop_ded_raw = cls.calc_property_tax_deduction(person_tb, pt_fmvr)
        p_prop_ded_adj = int(p_prop_ded_raw * pt_cap_ratio) # 상한 비율 적용
        
        p_after = max(0, p_gross - p_prop_ded_adj)
        
        tax_base = person_tb * 2
        gross_tax = p_gross * 2
        prop_tax_ded = p_prop_ded_adj * 2
        tax_after_prop = p_after * 2
    else:
        tax_base = cls.calc_tax_base(total_price, deduction, fmvr)
        gross_tax, applied_tax_rate = cls.calc_gross_tax(tax_base, property_type, year_label)
        prop_tax_ded_raw = cls.calc_property_tax_deduction(tax_base, pt_fmvr)
        prop_tax_ded = int(prop_tax_ded_raw * pt_cap_ratio) # 상한 비율 적용
        
        tax_after_prop = max(0, gross_tax - prop_tax_ded)

    is_eligible = (property_type == "RESIDENT_1HOME") and (not is_joint_default)
    total_rate, age_rate, period_rate, period_desc = cls.calc_tax_credits(
        year_label, age, holding_years, residence_years, is_eligible
    )

    calc_credit_amount = int(tax_after_prop * total_rate)

    if year_label == "2026년":
      credit_limit_str = "한도 없음"
      final_credit_amount = calc_credit_amount
      credit_cap_applied = False
    elif year_label == "2027년":
      credit_limit_str = "8,000,000 원"
      final_credit_amount = min(calc_credit_amount, 8_000_000)
      credit_cap_applied = calc_credit_amount > 8_000_000
    else:
      credit_limit_str = "6,000,000 원"
      final_credit_amount = min(calc_credit_amount, 6_000_000)
      credit_cap_applied = calc_credit_amount > 6_000_000

    tax_after_credit = max(0, tax_after_prop - final_credit_amount)

    if apply_tax_cap and year_label != "2026년":
      tax_cap_limit = int(prev_year_tax * 2.0) if prev_year_tax > 0 else float("inf")
    else:
      tax_cap_limit = float("inf") 
      
    final_tax = min(tax_after_credit, tax_cap_limit)
    cap_applied = tax_after_credit > tax_cap_limit

    rural_tax = int(final_tax * 0.20)
    jongbu_total_payment = final_tax + rural_tax
    total_holding_tax = final_property_tax + jongbu_total_payment

    return {
        "year": year_label,
        "is_eligible": is_eligible,
        "deduction": deduction,
        "fmvr": fmvr,
        "tax_base": tax_base,
        "applied_tax_rate_pct": applied_tax_rate * 100,
        "gross_tax": gross_tax,
        "prop_tax_ded": prop_tax_ded,
        "tax_after_prop": tax_after_prop,
        "total_rate_pct": int(total_rate * 100),
        "age_rate_pct": int(age_rate * 100),
        "period_rate_pct": int(period_rate * 100),
        "period_desc": period_desc,
        "calc_credit_amount": calc_credit_amount,
        "credit_limit_str": credit_limit_str,
        "final_credit_amount": final_credit_amount,
        "credit_cap_applied": credit_cap_applied,
        "tax_after_credit": tax_after_credit,
        "prev_year_tax": prev_year_tax,
        "tax_cap_limit": tax_cap_limit,
        "final_tax": final_tax,
        "cap_applied": cap_applied,
        "rural_tax": rural_tax,
        "jongbu_total_payment": jongbu_total_payment,
        "property_tax": final_property_tax,
        "prop_cap_applied": prop_cap_applied,
        "prop_tax_cap_limit": prop_tax_cap_limit,
        "total_holding_tax": total_holding_tax,
    }

  @classmethod
  def run_simulation(
      cls,
      total_price: int,
      price_res: int,
      property_type: str,
      base_age: int,
      base_holding_years: int,
      base_residence_years: int,
      tax_2025: int,
      prop_tax_2025: int,
      is_joint_default: bool = False,
      apply_tax_cap: bool = False, 
  ) -> list:
    years_config = [("2026년", 0), ("2027년", 1), ("2028년 이후", 2)]
    results = []
    prev_tax = tax_2025
    prev_prop_tax = prop_tax_2025

    for label, offset in years_config:
      res = cls.run_single_year(
          year_label=label,
          total_price=total_price,
          price_res=price_res,
          property_type=property_type,
          age=base_age + offset,
          holding_years=base_holding_years + offset,
          residence_years=base_residence_years + offset,
          prev_year_tax=prev_tax,
          prev_year_prop_tax=prev_prop_tax,
          is_joint_default=is_joint_default,
          apply_tax_cap=apply_tax_cap,
      )
      results.append(res)
      prev_tax = res["final_tax"]
      prev_prop_tax = res["property_tax"]

    return results


# =========================================================
# 2. Streamlit 웹 인터페이스 (메인 실행부)
# =========================================================
def main():
  st.set_page_config(page_title="2026 종부세 시뮬레이터", page_icon="🏠", layout="wide")

  st.title("🏠 2026 종부세 시뮬레이터")
  st.markdown("---")

  with st.expander("⚙️ 시뮬레이션 설정 (여기를 눌러 입력값을 변경하세요)", expanded=True):
    
    property_choice = st.selectbox(
        "과세 유형 선택",
        [
            ("RESIDENT_1HOME", "1세대 1주택자 (특례 신청 포함)"),
            ("LOCAL_MULTI_HOME", "지방 1주택 + 지방 2주택자"),
            ("HEAVY_MULTI_HOME", "조정지역 주택 보유 다주택자 + 3주택 이상"),
        ],
        format_func=lambda x: x[1],
    )[0] 
    
    is_multi = property_choice in ["LOCAL_MULTI_HOME", "HEAVY_MULTI_HOME"]
    
    realization_rate = st.slider("공시가격 현실화율 (%)", min_value=50.0, max_value=100.0, value=69.0, step=1.0)
    st.divider()

    if is_multi:
        st.subheader("🏘️ 다주택 시가 입력")
        
        market_price_res_man = st.number_input("거주 주택 시가 합계 (만원)", min_value=0, value=150000, step=1000, format="%d")
        st.markdown(f"<div style='color: #4CAF50; font-weight: bold; margin-top: -10px; margin-bottom: 10px;'>{format_korean_currency(market_price_res_man * 10000)}</div>", unsafe_allow_html=True)
        
        market_price_non_res_man = st.number_input("비거주 주택 시가 합계 (만원)", min_value=0, value=300000, step=1000, format="%d")
        st.markdown(f"<div style='color: #4CAF50; font-weight: bold; margin-top: -10px; margin-bottom: 10px;'>{format_korean_currency(market_price_non_res_man * 10000)}</div>", unsafe_allow_html=True)
        
        market_price_res = market_price_res_man * 10000
        market_price_non_res = market_price_non_res_man * 10000
        market_total = market_price_res + market_price_non_res
        
        total_price = int(market_total * (realization_rate / 100.0))
        price_res = int(market_price_res * (realization_rate / 100.0))
        
        st.info(f"📌 **과세 기준 공시가 총액: `{total_price:,.0f}` 원**\n└ 거주: {price_res:,.0f} / 비거주: {total_price - price_res:,.0f}")
        
        is_joint_default = False
        base_age = 0
        base_holding_years = 0
        base_residence_years = 0
    else:
        st.subheader("🏠 1주택 시가 입력")
        market_total_man = st.number_input("주택 시가 (만원)", min_value=0, value=450000, step=1000, format="%d")
        st.markdown(f"<div style='color: #4CAF50; font-weight: bold; margin-top: -10px; margin-bottom: 10px;'>{format_korean_currency(market_total_man * 10000)}</div>", unsafe_allow_html=True)
        market_total = market_total_man * 10000
        
        total_price = int(market_total * (realization_rate / 100.0))
        st.info(f"📌 **과세 기준 공시가: `{total_price:,.0f}` 원**")

        st.divider()
        st.subheader("📝 명의 및 거주 정보")
        
        ownership_type = st.radio(
            "소유 형태 및 과세 방식",
            ["단독 명의 (또는 공동명의 1주택 특례)", "부부 공동 명의 (기본과세)"]
        )
        is_joint_default = (ownership_type == "부부 공동 명의 (기본과세)")

        is_residing_str = st.radio("해당 주택에 거주 중이신가요?", ["거주 중", "비거주"])
        market_price_res = market_total if is_residing_str == "거주 중" else 0
        price_res = int(market_price_res * (realization_rate / 100.0))

        st.divider()
        st.subheader("🧑 연령 및 기간 정보")
        base_age = st.number_input("2026년 기준 연령 (세)", min_value=20, max_value=110, value=70)
        base_holding_years = st.number_input("2026년 기준 보유기간 (년)", min_value=1, max_value=50, value=10)
        base_residence_years = st.number_input("2026년 기준 거주기간 (년)", min_value=0, max_value=50, value=10)

    st.divider()
    apply_tax_cap = st.checkbox("전년 대비 세부담 상한(종부세 200%, 재산세 105~130%) 적용", value=False)
    
    if apply_tax_cap:
        col_cap1, col_cap2 = st.columns(2)
        with col_cap1:
            tax_2025 = st.number_input("2025년도 납부 종부세액 (원)", min_value=0, value=5_000_000, step=100_000, format="%d")
        with col_cap2:
            prop_tax_2025 = st.number_input("2025년도 납부 재산세액 (원)", min_value=0, value=1_500_000, step=100_000, format="%d")
    else:
        tax_2025 = 0
        prop_tax_2025 = 0

  # 결과 계산
  results = ComprehensiveTaxEngine.run_simulation(
      total_price=total_price,
      price_res=price_res,
      property_type=property_choice,
      base_age=base_age,
      base_holding_years=base_holding_years,
      base_residence_years=base_residence_years,
      tax_2025=tax_2025,
      prop_tax_2025=prop_tax_2025,
      is_joint_default=is_joint_default,
      apply_tax_cap=apply_tax_cap,
  )

  st.markdown("### 📊 산출 결과")
  
  cols = st.columns(3)
  for idx, res in enumerate(results):
    with cols[idx]:
      st.subheader(f"📅 {res['year']}")
      
      with st.container(border=True):
          st.markdown(
              f"""
              <div style="background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                  <div style="margin-bottom: 10px;">
                      <span style="font-size: 16px; font-weight: bold; color: #333;">💰 총 보유세 합계</span><br>
                      <span style="font-size: 24px; font-weight: 900; color: #d62728;">{res['total_holding_tax']:,.0f} 원</span>
                  </div>
                  <div style="margin-bottom: 5px;">
                      <span style="font-size: 14px; font-weight: bold; color: #555;">└ 🔥 최종 종부세</span><br>
                      <span style="font-size: 24px; font-weight: 900; color: #d62728;">{res['jongbu_total_payment']:,.0f} 원</span>
                  </div>
                  <div>
                      <span style="font-size: 14px; color: #555;">└ 🏠 주택분 재산세</span><br>
                      <span style="font-size: 16px; color: #333;">{res['property_tax']:,.0f} 원</span>
                  </div>
              </div>
              """, 
              unsafe_allow_html=True
          )
          
          if is_multi and res['year'] != "2026년":
              ratio = price_res / total_price if total_price > 0 else 0
              st.markdown(f"**💡 기본공제액**: {res['deduction']:,.0f} 원")
              st.caption(f"└ 다주택 산식: 기본 4억 + (5억×거주비중 {ratio*100:.1f}%)")
          elif is_joint_default:
              st.markdown(f"**💡 기본공제액**: {res['deduction']:,.0f} 원 *(부부 합산, 인당 {res['deduction']//2:,.0f}원)*")
          else:
              st.markdown(f"**💡 기본공제액**: {res['deduction']:,.0f} 원")
              
          st.markdown(f"**📊 과세표준**: {res['tax_base']:,.0f} 원 *(FMVR {res['fmvr']:.0f}%)*")
          st.markdown(f"**📄 종부세 산출세액**: {res['gross_tax']:,.0f} 원")
          st.markdown(f"**➖ 재산세 중복 차감**: ▲ {res['prop_tax_ded']:,.0f} 원")
          st.divider()
          
          if res['tax_base'] <= 0:
              st.success("✅ **기본공제액 미달 (과세표준 0원)**")
              st.markdown("└ 종부세 납부 대상이 아닙니다.")
          elif not res['is_eligible']:
              if is_multi:
                  st.markdown("**✅ 세액공제율**: 0% *(다주택자는 세액공제 대상이 아님)*")
              else:
                  st.markdown("**✅ 세액공제율**: 0% *(공동명의 기본과세 적용으로 배제)*")
              st.markdown("**🎯 최종 세액공제액**: 0 원")
          else:
              st.markdown(f"**✅ 세액공제율**: {res['total_rate_pct']}% (연령{res['age_rate_pct']}%+기간{res['period_rate_pct']}%)")
              st.caption(f"└ 적용상세: {res['period_desc']}")
              st.markdown(f"**💰 산출 세액공제액**: {res['calc_credit_amount']:,.0f} 원")
              
              limit_mark = "🚨초과" if res['credit_cap_applied'] else ""
              st.markdown(f"**🛑 공제 한도**: {res['credit_limit_str']} {limit_mark}")
              st.markdown(f"**🎯 최종 세액공제액**: ▲ {res['final_credit_amount']:,.0f} 원")
          
          if res['cap_applied'] or res['prop_cap_applied']:
              st.divider()
              if res['prop_cap_applied']:
                  st.warning(f"※ 재산세 세부담 상한 발동 (상한액: {res['prop_tax_cap_limit']:,.0f}원)")
              if res['cap_applied']:
                  st.error(f"※ 종부세 200% 세부담 상한 발동 (상한액: {res['tax_cap_limit']:,.0f}원)")

  st.markdown("---")
  st.markdown("#### 📊 연도별 상세 보유세 산출 구조표")

  table_data = []
  for res in results:
    table_data.append({
        "과세 연도": res["year"],
        "기본공제액": f"{res['deduction']:,.0f} 원",
        "과세표준(FMVR적용)": f"{res['tax_base']:,.0f} 원 ({res['fmvr']:.0f}%)",
        "주택분 재산세": f"{res['property_tax']:,.0f} 원",
        "종부세 산출세액": f"{res['gross_tax']:,.0f} 원",
        "재산세 중복분 차감": f"▲ {res['prop_tax_ded']:,.0f} 원",
        "산출 세액공제액 (한도 전)": f"{res['calc_credit_amount']:,.0f} 원 ({res['total_rate_pct']}%)",
        "최종 세액공제액 (한도 후)": f"▲ {res['final_credit_amount']:,.0f} 원",
        "종부세 본세": f"{res['final_tax']:,.0f} 원",
        "농어촌특별세 (20%)": f"{res['rural_tax']:,.0f} 원",
        "최종 종부세 합계": f"{res['jongbu_total_payment']:,.0f} 원",
        "총 보유세 합계": f"{res['total_holding_tax']:,.0f} 원",
    })

  df = pd.DataFrame(table_data)
  st.dataframe(df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
  main()

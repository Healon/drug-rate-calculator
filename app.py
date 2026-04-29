import os
import streamlit as st
import streamlit.components.v1 as components
from decimal import Decimal, ROUND_HALF_UP

# =========================
# Page config
# =========================
st.set_page_config(
    page_title="急重症藥物速率換算",
    layout="centered",
)

# =========================
# Custom Component (雙向 wheel picker)
# =========================
_DIR = os.path.dirname(os.path.abspath(__file__))
_wheel_picker = components.declare_component(
    "wheel_picker",
    path=os.path.join(_DIR, "wheel_picker"),
)


def wheel_picker(weight_init: float, dose_init: float, version: int, key: str = "wheel"):
    return _wheel_picker(
        weight_init=float(weight_init),
        dose_init=float(dose_init),
        version=int(version),
        default={"weight": float(weight_init), "dose": float(dose_init), "v": int(version)},
        key=key,
    )


# =========================
# Session State
# =========================
ss = st.session_state
ss.setdefault("weight_init", 60.0)
ss.setdefault("dose_init", 5.0)
ss.setdefault("current_weight", 60.0)
ss.setdefault("current_dose", 5.0)
ss.setdefault("wheel_version", 0)


# =========================
# Utility
# =========================
def round_half_up(value: float, digits: int = 1) -> float:
    pattern = "0." + "0" * digits
    return float(Decimal(str(value)).quantize(Decimal(pattern), rounding=ROUND_HALF_UP))


def calculate_dopamine_rate(weight_kg: float, dose_mcg_kg_min: float) -> float:
    return (dose_mcg_kg_min * weight_kg * 60) / 1600


def set_quick_dose(value: float):
    """快速劑量按鈕：保留目前體重，重新定位劑量滾輪。"""
    ss.weight_init = ss.current_weight  # 以目前實際體重為新初始值
    ss.dose_init = float(value)
    ss.current_dose = float(value)
    ss.wheel_version += 1


# =========================
# Header
# =========================
st.title("急重症藥物速率換算")
st.caption("Adult Only｜成人臨床輔助計算工具")

st.warning("本工具僅供輔助計算。給藥前請依醫囑、院內規範與高警訊藥物雙人覆核流程執行。")

st.header("Dopamine / Easydopa")

st.info(
    """
    **藥品規格：** Easydopa 800 mg / 500 ml
    **泡製方式：** 不須稀釋
    **濃度：** 1.6 mg/ml = 1600 mcg/ml
    **建議劑量範圍：** 起始 5.0，最大 50.0 mcg/kg/min
    """
)

if not st.checkbox("我已確認藥品規格與目前使用品項相符"):
    st.stop()

st.divider()

# =========================
# Wheel picker
# =========================
st.subheader("參數設定")
st.caption("整數滾輪以 1 為單位、小數滾輪每格 0.1。請依院內規範確認使用實際體重 ABW 或理想體重 IBW。")

picker_value = wheel_picker(
    weight_init=ss.weight_init,
    dose_init=ss.dose_init,
    version=ss.wheel_version,
    key="wheel_picker_main",
)

if isinstance(picker_value, dict):
    if "weight" in picker_value:
        ss.current_weight = round_half_up(float(picker_value["weight"]), 1)
    if "dose" in picker_value:
        ss.current_dose = round_half_up(float(picker_value["dose"]), 1)

weight = ss.current_weight
dose = ss.current_dose

# =========================
# Quick dose buttons
# =========================
st.markdown("#### 快速劑量")

quick_cols = st.columns(6)
for col, dose_value in zip(quick_cols, [5.0, 10.0, 15.0, 20.0, 30.0, 50.0]):
    with col:
        st.button(
            f"{dose_value:g}",
            on_click=set_quick_dose,
            args=(dose_value,),
            use_container_width=True,
            key=f"qd_{dose_value}",
        )

st.caption("單位：mcg/kg/min")

# =========================
# Dose warning
# =========================
if dose < 5.0:
    st.warning("目前劑量低於表格建議起始劑量 5.0 mcg/kg/min，請確認醫囑。")

st.divider()

# =========================
# Calculation
# =========================
calc_ml_hr = calculate_dopamine_rate(weight, dose)
display_ml_hr = round_half_up(calc_ml_hr, 1)

st.markdown(
    f"""
    <div style="
        text-align: center;
        background-color: #102A1D;
        padding: 22px;
        border-radius: 14px;
        border: 3px solid #22C55E;
    ">
        <p style="font-size: 18px; color: #BBF7D0; margin-bottom: 4px;">
            建議幫浦設定流速
        </p>
        <h1 style="font-size: 52px; color: #22C55E; margin: 0;">
            {display_ml_hr:.1f}
            <span style="font-size: 26px;">ml/hr</span>
        </h1>
        <p style="font-size: 22px; color: #FFFFFF; margin-top: 12px; margin-bottom: 0;">
            目前劑量：<b>{dose:.1f} mcg/kg/min</b>
        </p>
        <p style="font-size: 18px; color: #D1D5DB; margin-top: 8px;">
            目前體重：{weight:.1f} kg
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(f"原始精確計算值：{calc_ml_hr:.2f} ml/hr")
st.caption(f"計算式：{dose:.1f} × {weight:.1f} × 60 ÷ 1600 = {calc_ml_hr:.2f} ml/hr")

st.error("高警訊藥物提醒：給藥前請完成雙人覆核流程。")

st.divider()

st.caption("資料版本：急重症藥物泡製流速表 1110701")
st.caption("目前版本：MVP v0.4｜Dopamine 單藥物測試版")

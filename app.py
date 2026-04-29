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

# 全域 CSS：手機上強制 columns 保持橫向、快速劑量按鈕緊湊
st.markdown(
    """
    <style>
      [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 6px !important;
      }
      [data-testid="stColumn"] {
        min-width: 0 !important;
      }
      .quick-dose [data-testid="stButton"] button {
        padding: 0.35rem 0.2rem !important;
        min-height: 38px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# Custom Component (雙向 wheel picker)
# =========================
_DIR = os.path.dirname(os.path.abspath(__file__))
_wheel_picker = components.declare_component(
    "wheel_picker",
    path=os.path.join(_DIR, "wheel_picker"),
)
_rate_input = components.declare_component(
    "rate_input",
    path=os.path.join(_DIR, "rate_input"),
)


def wheel_picker(weight_init: float, dose_init: float, version: int,
                 mode: str = "both", key: str = "wheel"):
    return _wheel_picker(
        weight_init=float(weight_init),
        dose_init=float(dose_init),
        version=int(version),
        mode=mode,
        default={"weight": float(weight_init), "dose": float(dose_init), "v": int(version)},
        key=key,
    )


def rate_input(initial: float, version: int, key: str = "rate"):
    return _rate_input(
        initial=float(initial),
        version=int(version),
        default={"rate": float(initial)},
        key=key,
    )


# =========================
# Session State
# =========================
ss = st.session_state
ss.setdefault("step", 1)
ss.setdefault("spec_confirmed", False)
ss.setdefault("weight_init", 60.0)
ss.setdefault("dose_init", 5.0)
ss.setdefault("current_weight", 60.0)
ss.setdefault("current_dose", 5.0)
ss.setdefault("current_rate", 11.3)  # 60 kg × 5 mcg/kg/min 對應流速
ss.setdefault("rate_init", 11.3)
ss.setdefault("rate_version", 0)
ss.setdefault("wheel_version", 0)


# =========================
# Utility
# =========================
def round_half_up(value: float, digits: int = 1) -> float:
    pattern = "0." + "0" * digits
    return float(Decimal(str(value)).quantize(Decimal(pattern), rounding=ROUND_HALF_UP))


def calculate_dopamine_rate(weight_kg: float, dose_mcg_kg_min: float) -> float:
    return (dose_mcg_kg_min * weight_kg * 60) / 1600


def calculate_dose_from_rate(weight_kg: float, rate_ml_hr: float) -> float:
    """反向計算：由流速 ml/hr 反推劑量 mcg/kg/min。"""
    if weight_kg <= 0:
        return 0.0
    return rate_ml_hr * 1600 / (weight_kg * 60)


# =========================
# Navigation
# =========================
def goto(step: int):
    new_step = max(1, min(4, step))
    if new_step != ss.step:
        # 切換步驟時，把所有 picker 的初始值同步成目前實際值並 bump 版本，
        # 避免新 step 的 picker 用舊 init 重建後反向覆蓋已設定值。
        ss.weight_init = ss.current_weight
        ss.dose_init = ss.current_dose
        ss.rate_init = ss.current_rate
        ss.wheel_version += 1
        ss.rate_version += 1
    ss.step = new_step


def next_step():
    goto(ss.step + 1)


def prev_step():
    goto(ss.step - 1)


def restart():
    ss.step = 1
    ss.spec_confirmed = False


def set_quick_dose(value: float):
    """快速劑量按鈕：保留目前體重，重新定位劑量滾輪。"""
    ss.weight_init = ss.current_weight
    ss.dose_init = float(value)
    ss.current_dose = float(value)
    ss.wheel_version += 1


def sync_picker(picker_value):
    if isinstance(picker_value, dict):
        if "weight" in picker_value:
            ss.current_weight = round_half_up(float(picker_value["weight"]), 1)
        if "dose" in picker_value:
            ss.current_dose = round_half_up(float(picker_value["dose"]), 1)


# =========================
# Breadcrumb
# =========================
def breadcrumb(current: int):
    labels = ["藥物", "體重", "流速", "劑量"]
    parts = []
    for i, label in enumerate(labels, start=1):
        if i < current:
            color, weight, bg = "#22C55E", "600", "#102A1D"
        elif i == current:
            color, weight, bg = "#60A5FA", "700", "#0B1E36"
        else:
            color, weight, bg = "#6B7280", "500", "#1F2937"
        parts.append(
            f"<span style='display:inline-flex;align-items:center;gap:6px;"
            f"padding:6px 12px;border-radius:999px;background:{bg};"
            f"color:{color};font-weight:{weight};font-size:13px;'>"
            f"<b>{i}</b> {label}</span>"
        )
    sep = "<span style='color:#374151;margin:0 4px;'>›</span>"
    st.markdown(
        "<div style='display:flex;flex-wrap:wrap;align-items:center;"
        "justify-content:center;margin:8px 0 16px;'>"
        + sep.join(parts) + "</div>",
        unsafe_allow_html=True,
    )


# =========================
# Common header
# =========================
def render_header(big: bool = False, show_warning: bool = False):
    if big:
        st.title("急重症藥物速率換算")
        st.caption("Adult Only｜成人臨床輔助計算工具")
    else:
        st.markdown(
            "<div style='font-size:18px;font-weight:700;'>急重症藥物速率換算"
            "<span style='font-size:12px;color:#9CA3AF;font-weight:500;margin-left:8px;'>"
            "Adult Only</span></div>",
            unsafe_allow_html=True,
        )
    if show_warning:
        st.warning(
            "本工具僅供輔助計算。給藥前請依醫囑、院內規範與高警訊藥物雙人覆核流程執行。"
        )


# =========================
# Step 1 — 藥物選擇
# =========================
def step1_drug_selection():
    render_header(big=True, show_warning=True)
    breadcrumb(1)

    st.header("Dopamine / Easydopa")
    st.info(
        """
        **藥品規格：** Easydopa 800 mg / 500 ml
        **建議劑量範圍：** 起始 5.0，最大 50.0 mcg/kg/min
        """
    )

    st.checkbox(
        "我已確認藥品規格與目前使用品項相符",
        key="spec_confirmed",
    )

    st.divider()
    cols = st.columns([1, 1])
    with cols[1]:
        st.button(
            "下一步 →",
            type="primary",
            use_container_width=True,
            disabled=not ss.spec_confirmed,
            on_click=next_step,
            key="s1_next",
        )


# =========================
# Step 2 — 體重
# =========================
def step2_weight():
    render_header()
    breadcrumb(2)

    st.subheader("設定體重")
    st.caption("整數滾輪以 1 為單位、小數滾輪每格 0.1。請依院內規範確認使用實際體重 ABW 或理想體重 IBW。")

    picker_value = wheel_picker(
        weight_init=ss.weight_init,
        dose_init=ss.dose_init,
        version=ss.wheel_version,
        mode="weight_only",
        key="picker_step2",
    )
    sync_picker(picker_value)

    st.markdown(
        f"<div style='text-align:center;font-size:18px;color:#D1D5DB;margin:8px 0 16px;'>"
        f"目前體重：<b style='font-size:26px;color:#FFFFFF;'>{ss.current_weight:.1f}</b> kg</div>",
        unsafe_allow_html=True,
    )

    st.divider()
    cols = st.columns(2)
    with cols[0]:
        st.button("← 上一步", use_container_width=True, on_click=prev_step, key="s2_prev")
    with cols[1]:
        st.button("下一步 →", type="primary", use_container_width=True,
                  on_click=next_step, key="s2_next")


# =========================
# Step 3 — 流速
# =========================
def step3_rate():
    render_header()
    breadcrumb(3)

    st.subheader("輸入幫浦流速")
    st.caption("輸入 IV pump 顯示的流速 ml/hr，將反推目前劑量。")

    rv = rate_input(
        initial=ss.rate_init,
        version=ss.rate_version,
        key="rate_input_step3",
    )
    if isinstance(rv, dict) and "rate" in rv:
        ss.current_rate = round_half_up(float(rv["rate"]), 1)

    st.markdown(
        f"<div style='text-align:center;font-size:18px;color:#D1D5DB;margin:8px 0 4px;'>"
        f"目前流速：<b style='font-size:26px;color:#FFFFFF;'>{ss.current_rate:.1f}</b> ml/hr"
        f"<br><span style='font-size:14px;color:#9CA3AF;'>體重 {ss.current_weight:.1f} kg</span></div>",
        unsafe_allow_html=True,
    )

    st.divider()
    cols = st.columns(2)
    with cols[0]:
        st.button("← 上一步", use_container_width=True, on_click=prev_step, key="s3_prev")
    with cols[1]:
        st.button("下一步 →", type="primary", use_container_width=True,
                  on_click=next_step, key="s3_next")


# =========================
# Step 4 — 劑量結果（反向計算）
# =========================
def step4_result():
    render_header()
    breadcrumb(4)

    weight = ss.current_weight
    rate = ss.current_rate
    calc_dose = calculate_dose_from_rate(weight, rate)
    display_dose = round_half_up(calc_dose, 1)

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
                目前實際劑量
            </p>
            <h1 style="font-size: 52px; color: #22C55E; margin: 0;">
                {display_dose:.1f}
                <span style="font-size: 26px;">mcg/kg/min</span>
            </h1>
            <p style="font-size: 22px; color: #FFFFFF; margin-top: 12px; margin-bottom: 0;">
                目前流速：<b>{rate:.1f} ml/hr</b>
            </p>
            <p style="font-size: 18px; color: #D1D5DB; margin-top: 8px;">
                目前體重：{weight:.1f} kg
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(f"原始精確計算值：{calc_dose:.2f} mcg/kg/min")
    st.caption(
        f"計算式：{rate:.1f} × 1600 ÷ ({weight:.1f} × 60) = {calc_dose:.2f} mcg/kg/min"
    )

    if calc_dose > 50.0:
        st.error(
            f"⚠ 計算劑量 {display_dose:.1f} mcg/kg/min 超過建議最大 50.0，"
            "請覆核流速與體重輸入是否正確。"
        )
    elif calc_dose < 5.0:
        st.warning(
            f"目前計算劑量 {display_dose:.1f} mcg/kg/min 低於建議起始 5.0，請確認醫囑。"
        )

    st.error("高警訊藥物提醒：給藥前請完成雙人覆核流程。")

    st.divider()

    cols = st.columns(3)
    with cols[0]:
        st.button("修改體重", use_container_width=True,
                  on_click=goto, args=(2,), key="s4_edit_w")
    with cols[1]:
        st.button("修改流速", use_container_width=True,
                  on_click=goto, args=(3,), key="s4_edit_r")
    with cols[2]:
        st.button("重新開始", use_container_width=True,
                  on_click=restart, key="s4_restart")

    st.caption("資料版本：急重症藥物泡製流速表 1110701")
    st.caption("目前版本：MVP v0.5-rate｜Dopamine 反向計算（流速 → 劑量）")


# =========================
# Main
# =========================
if ss.step == 1:
    step1_drug_selection()
elif ss.step == 2:
    step2_weight()
elif ss.step == 3:
    step3_rate()
else:
    step4_result()

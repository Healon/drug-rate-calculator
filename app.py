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

# 全域 CSS
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
      .drug-card [data-testid="stButton"] button {
        background: #1E2530 !important;
        border: 1px solid #2A3342 !important;
        color: #FAFAFA !important;
        padding: 14px 12px !important;
        text-align: left !important;
        font-size: 16px !important;
        white-space: pre-line !important;
        min-height: 84px !important;
      }
      .drug-card.selected [data-testid="stButton"] button {
        border-color: #22C55E !important;
        background: #102A1D !important;
        box-shadow: 0 0 0 2px rgba(34,197,94,0.35) !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# Drug catalog
# =========================
DRUGS = {
    "dopamine": {
        "key": "dopamine",
        "display_name": "Dopamine / Easydopa",
        "category": "升壓 / 強心",
        "needs_weight": True,
        "dose_unit": "mcg/kg/min",
        "concentrations": [
            {"label": "Easydopa 800 mg / 500 ml", "mcg_per_ml": 1600, "note": "不須稀釋"},
        ],
        "dose_default": 5.0,
        "dose_min": 0,        # 整數滾輪下限
        "dose_max": 50,       # 整數滾輪上限
        "dose_warn_low": 5.0,
        "dose_warn_high": 50.0,
        "quick_doses": [5.0, 10.0, 15.0, 20.0, 30.0, 50.0],
        "rate_max": 300.0,
    },
    "norepinephrine": {
        "key": "norepinephrine",
        "display_name": "Norepinephrine",
        "category": "升壓",
        "needs_weight": False,
        "dose_unit": "mcg/min",
        "concentrations": [
            {"label": "低濃度 8 mg / 500 ml D5W", "mcg_per_ml": 16,
             "note": "Levophed 4 mg/amp × 2 加入 500 ml D5W"},
            {"label": "高濃度 8 mg / 100 ml D5W", "mcg_per_ml": 80,
             "note": "Levophed 4 mg/amp × 2 加入 100 ml D5W"},
        ],
        "dose_default": 2.0,
        "dose_min": 0,
        "dose_max": 30,
        "dose_warn_low": 1.0,
        "dose_warn_high": 30.0,
        "quick_doses": [1.0, 2.0, 5.0, 10.0, 20.0, 30.0],
        "rate_max": 200.0,
    },
}
DRUG_ORDER = ["dopamine", "norepinephrine"]

# =========================
# Custom Component (雙向 wheel picker)
# =========================
_DIR = os.path.dirname(os.path.abspath(__file__))
_wheel_picker = components.declare_component(
    "wheel_picker",
    path=os.path.join(_DIR, "wheel_picker"),
)


def wheel_picker(weight_init: float, dose_init: float, version: int,
                 mode: str = "both", w_min: int = 10, w_max: int = 200,
                 d_min: int = 0, d_max: int = 50, key: str = "wheel"):
    return _wheel_picker(
        weight_init=float(weight_init),
        dose_init=float(dose_init),
        version=int(version),
        mode=mode,
        w_min=int(w_min), w_max=int(w_max),
        d_min=int(d_min), d_max=int(d_max),
        default={"weight": float(weight_init), "dose": float(dose_init), "v": int(version)},
        key=key,
    )


# =========================
# Session State
# =========================
ss = st.session_state
ss.setdefault("step", 1)
ss.setdefault("drug_key", None)
ss.setdefault("concentration_index", 0)
ss.setdefault("spec_confirmed", False)
ss.setdefault("weight_init", 60.0)
ss.setdefault("dose_init", 5.0)
ss.setdefault("current_weight", 60.0)
ss.setdefault("current_dose", 5.0)
ss.setdefault("wheel_version", 0)


# =========================
# Helpers
# =========================
def round_half_up(value: float, digits: int = 1) -> float:
    pattern = "0." + "0" * digits
    return float(Decimal(str(value)).quantize(Decimal(pattern), rounding=ROUND_HALF_UP))


def current_drug():
    if ss.drug_key is None:
        return None
    return DRUGS.get(ss.drug_key)


def current_concentration():
    drug = current_drug()
    if drug is None:
        return None
    idx = max(0, min(ss.concentration_index, len(drug["concentrations"]) - 1))
    return drug["concentrations"][idx]


def calculate_rate(drug, weight: float, dose: float) -> float:
    """正向：dose → ml/hr。"""
    conc = current_concentration()["mcg_per_ml"]
    if drug["needs_weight"]:
        return dose * weight * 60 / conc
    return dose * 60 / conc


def step_keys():
    """根據目前藥物決定 step 流程。"""
    drug = current_drug()
    if drug is None:
        return ["drug", "weight", "dose", "result"]  # 預設給 breadcrumb 用
    if drug["needs_weight"]:
        return ["drug", "weight", "dose", "result"]
    return ["drug", "dose", "result"]


def step_label(key: str) -> str:
    return {"drug": "藥物", "weight": "體重", "dose": "劑量", "result": "結果"}[key]


def total_steps() -> int:
    return len(step_keys())


# =========================
# Navigation
# =========================
def goto(step: int):
    new_step = max(1, min(total_steps(), step))
    if new_step != ss.step:
        ss.weight_init = ss.current_weight
        ss.dose_init = ss.current_dose
        ss.wheel_version += 1
    ss.step = new_step


def goto_key(key: str):
    keys = step_keys()
    if key in keys:
        goto(keys.index(key) + 1)


def next_step():
    goto(ss.step + 1)


def prev_step():
    goto(ss.step - 1)


def restart():
    ss.step = 1
    ss.spec_confirmed = False


def select_drug(drug_key: str):
    """切換藥物：重設規格確認、濃度與劑量初值。"""
    if ss.drug_key != drug_key:
        ss.drug_key = drug_key
        ss.concentration_index = 0
        ss.spec_confirmed = False
        drug = DRUGS[drug_key]
        ss.dose_init = drug["dose_default"]
        ss.current_dose = drug["dose_default"]
        ss.wheel_version += 1


def set_quick_dose(value: float):
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
def breadcrumb(current_idx: int):
    keys = step_keys()
    parts = []
    for i, key in enumerate(keys, start=1):
        label = step_label(key)
        if i < current_idx:
            color, weight, bg = "#22C55E", "600", "#102A1D"
        elif i == current_idx:
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
# Header
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

    st.subheader("選擇藥物")

    cols = st.columns(len(DRUG_ORDER))
    for col, drug_key in zip(cols, DRUG_ORDER):
        drug = DRUGS[drug_key]
        is_selected = (ss.drug_key == drug_key)
        with col:
            st.markdown(
                f"<div class='drug-card{' selected' if is_selected else ''}'>",
                unsafe_allow_html=True,
            )
            st.button(
                f"{drug['display_name']}\n{drug['category']}",
                on_click=select_drug,
                args=(drug_key,),
                use_container_width=True,
                key=f"drug_{drug_key}",
            )
            st.markdown("</div>", unsafe_allow_html=True)

    if ss.drug_key is None:
        st.info("請先點選一項藥物。")
        return

    drug = current_drug()

    st.divider()
    st.markdown(f"### {drug['display_name']}")

    if len(drug["concentrations"]) > 1:
        st.markdown("**選擇泡製濃度**")
        labels = [c["label"] for c in drug["concentrations"]]
        ss.concentration_index = st.radio(
            "濃度",
            options=list(range(len(labels))),
            format_func=lambda i: labels[i],
            index=ss.concentration_index,
            label_visibility="collapsed",
            key="conc_radio",
        )

    conc = current_concentration()
    spec_lines = [
        f"**藥品規格：** {conc['label']}",
        f"**濃度：** {conc['mcg_per_ml']} mcg/ml",
        f"**建議劑量範圍：** 起始 {drug['dose_warn_low']:g}，最大 {drug['dose_warn_high']:g} {drug['dose_unit']}",
    ]
    if conc.get("note"):
        spec_lines.insert(1, f"**泡製方式：** {conc['note']}")
    if not drug["needs_weight"]:
        spec_lines.append("**注意：** 此藥物劑量計算 **不需體重**。")
    st.info("\n\n".join(spec_lines))

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
# Step weight — 體重
# =========================
def step_weight():
    render_header()
    breadcrumb(2)

    st.subheader("設定體重")
    st.caption("整數滾輪以 1 為單位、小數滾輪每格 0.1。請依院內規範確認使用實際體重 ABW 或理想體重 IBW。")

    picker_value = wheel_picker(
        weight_init=ss.weight_init,
        dose_init=ss.dose_init,
        version=ss.wheel_version,
        mode="weight_only",
        key="picker_weight",
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
        st.button("← 上一步", use_container_width=True, on_click=prev_step, key="sw_prev")
    with cols[1]:
        st.button("下一步 →", type="primary", use_container_width=True,
                  on_click=next_step, key="sw_next")


# =========================
# Step dose — 劑量
# =========================
def step_dose():
    drug = current_drug()
    render_header()
    breadcrumb(step_keys().index("dose") + 1)

    st.subheader("設定劑量")
    st.caption(
        f"整數滾輪以 1 為單位、小數滾輪每格 0.1。建議劑量範圍 "
        f"{drug['dose_warn_low']:g}–{drug['dose_warn_high']:g} {drug['dose_unit']}。"
    )

    picker_value = wheel_picker(
        weight_init=ss.weight_init,
        dose_init=ss.dose_init,
        version=ss.wheel_version,
        mode="dose_only",
        d_min=drug["dose_min"], d_max=drug["dose_max"],
        key="picker_dose",
    )
    sync_picker(picker_value)

    st.markdown(
        f"##### 快速劑量 <span style='font-size:12px;color:#9CA3AF;font-weight:400;'>{drug['dose_unit']}</span>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='quick-dose'>", unsafe_allow_html=True)
    quick_cols = st.columns(len(drug["quick_doses"]))
    for col, dose_value in zip(quick_cols, drug["quick_doses"]):
        with col:
            st.button(
                f"{dose_value:g}",
                on_click=set_quick_dose,
                args=(dose_value,),
                use_container_width=True,
                key=f"qd_{dose_value}",
            )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f"<div style='text-align:center;font-size:18px;color:#D1D5DB;margin:8px 0 4px;'>"
        f"目前劑量：<b style='font-size:26px;color:#FFFFFF;'>{ss.current_dose:.1f}</b> {drug['dose_unit']}</div>",
        unsafe_allow_html=True,
    )

    if ss.current_dose < drug["dose_warn_low"]:
        st.warning(
            f"目前劑量低於建議起始劑量 {drug['dose_warn_low']:g} {drug['dose_unit']}，請確認醫囑。"
        )

    st.divider()
    cols = st.columns(2)
    with cols[0]:
        st.button("← 上一步", use_container_width=True, on_click=prev_step, key="sd_prev")
    with cols[1]:
        st.button("下一步 →", type="primary", use_container_width=True,
                  on_click=next_step, key="sd_next")


# =========================
# Step result — 結果
# =========================
def step_result():
    drug = current_drug()
    conc = current_concentration()
    render_header()
    breadcrumb(total_steps())

    weight = ss.current_weight
    dose = ss.current_dose
    calc_ml_hr = calculate_rate(drug, weight, dose)
    display_ml_hr = round_half_up(calc_ml_hr, 1)

    weight_line = (
        f"<p style='font-size:18px;color:#D1D5DB;margin-top:8px;'>目前體重：{weight:.1f} kg</p>"
        if drug["needs_weight"] else
        f"<p style='font-size:14px;color:#9CA3AF;margin-top:8px;'>{drug['display_name']}（無需體重）</p>"
    )

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
                目前劑量：<b>{dose:.1f} {drug['dose_unit']}</b>
            </p>
            {weight_line}
            <p style='font-size:13px;color:#9CA3AF;margin-top:8px;'>
                濃度：{conc['mcg_per_ml']} mcg/ml ｜ {conc['label']}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(f"原始精確計算值：{calc_ml_hr:.2f} ml/hr")
    if drug["needs_weight"]:
        st.caption(
            f"計算式：{dose:.1f} × {weight:.1f} × 60 ÷ {conc['mcg_per_ml']} = {calc_ml_hr:.2f} ml/hr"
        )
    else:
        st.caption(
            f"計算式：{dose:.1f} × 60 ÷ {conc['mcg_per_ml']} = {calc_ml_hr:.2f} ml/hr"
        )

    st.error("高警訊藥物提醒：給藥前請完成雙人覆核流程。")

    st.divider()

    btns = []
    if drug["needs_weight"]:
        btns.append(("修改體重", lambda: goto_key("weight"), "edit_w"))
    btns.append(("修改劑量", lambda: goto_key("dose"), "edit_d"))
    btns.append(("重新開始", restart, "restart"))

    cols = st.columns(len(btns))
    for col, (label, fn, k) in zip(cols, btns):
        with col:
            st.button(label, use_container_width=True, on_click=fn, key=f"sr_{k}")

    st.caption("資料版本：急重症藥物泡製流速表 1110701")
    st.caption("目前版本：MVP v0.6｜支援 Dopamine、Norepinephrine")


# =========================
# Main dispatch
# =========================
keys = step_keys()
key = keys[ss.step - 1] if ss.step <= len(keys) else "drug"

if key == "drug":
    step1_drug_selection()
elif key == "weight":
    step_weight()
elif key == "dose":
    step_dose()
else:
    step_result()

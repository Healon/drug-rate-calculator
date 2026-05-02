import os
from typing import Optional
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
      /* Pitressin 適應症對比配色 */
      .drug-card-teal [data-testid="stButton"] button {
        background: #0E2C24 !important;
        border-color: #14B8A6 !important;
      }
      .drug-card-teal.selected [data-testid="stButton"] button {
        background: #134E48 !important;
        box-shadow: 0 0 0 2px rgba(20,184,166,0.55) !important;
      }
      .drug-card-rose [data-testid="stButton"] button {
        background: #3B0F1F !important;
        border-color: #E11D48 !important;
      }
      .drug-card-rose.selected [data-testid="stButton"] button {
        background: #581832 !important;
        box-shadow: 0 0 0 2px rgba(225,29,72,0.55) !important;
      }
      /* 純按鈕劑量模式 */
      .dose-buttons [data-testid="stButton"] button {
        min-height: 56px !important;
        font-size: 22px !important;
        font-weight: 700 !important;
      }
      .dose-buttons.selected-mark [data-testid="stButton"] button {
        border-color: #22C55E !important;
        box-shadow: 0 0 0 2px rgba(34,197,94,0.45) !important;
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
        "secondary_warning": {
            "threshold": 15.0,
            "message": "劑量超過 15 mcg/min，請考慮合併 vasopressin 使用。",
        },
    },
    "pitressin_shock": {
        "key": "pitressin_shock",
        "display_name": "Pitressin｜休克使用",
        "card_color": "teal",
        "needs_weight": False,
        "dose_unit": "U/min",
        "concentrations": [
            {"label": "20 U / 20 ml NS", "mcg_per_ml": 1.0,
             "note": "Pitressin 20 U 加入 NS 至 20 ml（1 U/ml）"},
        ],
        "dose_default": 0.03,
        "dose_warn_low": 0.01,
        "dose_warn_high": 0.04,
        "quick_doses": [0.01, 0.02, 0.03, 0.04],
        "input_mode": "buttons",
        "rate_max": 5.0,
        "header_notice": {
            "level": "warning",
            "text": (
                "Vasopressin 為休克輔助升壓藥，通常於 norepinephrine 後使用。\n"
                "本頁僅限休克用途，劑量限制為 0.01–0.04 U/min。\n"
                "請勿與腸胃道出血劑量混用。"
            ),
        },
    },
    "pitressin_gi": {
        "key": "pitressin_gi",
        "display_name": "Pitressin｜腸胃道出血",
        "card_color": "rose",
        "needs_weight": False,
        "dose_unit": "U/min",
        "concentrations": [
            {"label": "100 U / 100 ml NS", "mcg_per_ml": 1.0,
             "note": "Pitressin 100 U 加入 NS 至 100 ml（1 U/ml）"},
        ],
        "dose_default": 0.2,
        "dose_warn_low": 0.2,
        "dose_warn_high": 0.4,
        "quick_doses": [0.2, 0.3, 0.4],
        "input_mode": "buttons",
        "rate_max": 30.0,
        "header_notice": {
            "level": "error",
            "text": (
                "高警訊：腸胃道出血／靜脈曲張出血使用。\n"
                "確認適應症，留意心肌、腸胃道、皮膚與周邊組織缺血徵候。"
            ),
        },
    },
    "epinephrine_shock": {
        "key": "epinephrine_shock",
        "display_name": "Epinephrine｜休克使用",
        "needs_weight": True,
        "dose_unit": "mcg/kg/min",
        "concentrations": [
            {"label": "2 mg / 20 ml D/W", "mcg_per_ml": 100,
             "note": "Epinephrine 2 mg 加入 D/W 至 20 ml（0.1 mg/ml = 100 mcg/ml）"},
        ],
        "dose_default": 0.05,
        "dose_warn_low": 0.05,
        "dose_warn_high": 2.00,
        "dose_decimals": 2,
        "quick_doses": [0.05, 0.10, 0.20, 0.30, 0.50, 1.00],
        "input_mode": "decimal_picker",
        "rate_max": 200.0,
        "header_notice": {
            "level": "warning",
            "text": "Norepinephrine + Vasopressin 後 MAP 仍不足，可依醫囑加用 Epinephrine。",
        },
        "monitoring_notice": (
            "請監測心搏過速、心律不整、心肌缺血、高血壓、外滲組織壞死、尿量下降與 lactate 變化。\n"
            "Epinephrine 可能使 lactate 上升，判讀 lactate 時需合併臨床灌流狀態。"
        ),
    },
}
DRUG_ORDER = ["dopamine", "norepinephrine", "pitressin_shock", "pitressin_gi", "epinephrine_shock"]

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
                 d_min: int = 0, d_max: int = 50, d_decimals: int = 1,
                 d_min_real: Optional[float] = None, d_max_real: Optional[float] = None,
                 key: str = "wheel"):
    return _wheel_picker(
        weight_init=float(weight_init),
        dose_init=float(dose_init),
        version=int(version),
        mode=mode,
        w_min=int(w_min), w_max=int(w_max),
        d_min=int(d_min), d_max=int(d_max),
        d_decimals=int(d_decimals),
        d_min_real=float(d_min_real if d_min_real is not None else d_min),
        d_max_real=float(d_max_real if d_max_real is not None else d_max),
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
            drug = current_drug()
            decimals = 1
            if drug:
                decimals = drug.get("dose_decimals",
                                    2 if drug["dose_warn_high"] < 1 else 1)
            ss.current_dose = round_half_up(float(picker_value["dose"]), decimals)


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

    # 2 × 2 網格
    for i in range(0, len(DRUG_ORDER), 2):
        row_keys = DRUG_ORDER[i:i + 2]
        cols = st.columns(2)
        for col, drug_key in zip(cols, row_keys):
            drug = DRUGS[drug_key]
            is_selected = (ss.drug_key == drug_key)
            color_cls = f" drug-card-{drug.get('card_color')}" if drug.get("card_color") else ""
            with col:
                st.markdown(
                    f"<div class='drug-card{color_cls}{' selected' if is_selected else ''}'>",
                    unsafe_allow_html=True,
                )
                subtitle = drug.get("card_subtitle", "")
                detail = drug.get("card_detail", "")
                label_lines = [drug["display_name"]]
                if subtitle:
                    label_lines.append(subtitle)
                if detail:
                    label_lines.append(detail)
                st.button(
                    "\n".join(label_lines),
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
    conc_unit = "U/ml" if drug["dose_unit"].startswith("U") else "mcg/ml"
    spec_lines = [
        f"**藥品規格：** {conc['label']}",
        f"**濃度：** {conc['mcg_per_ml']:g} {conc_unit}",
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
def render_header_notice(drug):
    notice = drug.get("header_notice")
    if not notice:
        return
    fn = {"warning": st.warning, "error": st.error, "info": st.info}.get(
        notice["level"], st.warning
    )
    fn(notice["text"])


def render_dose_buttons(drug):
    """純按鈕劑量輸入（input_mode='buttons'）：跳過 wheel，硬性 hard stop。"""
    st.markdown("<div class='dose-buttons'>", unsafe_allow_html=True)
    cols = st.columns(len(drug["quick_doses"]))
    for col, dose_value in zip(cols, drug["quick_doses"]):
        is_current = abs(ss.current_dose - dose_value) < 1e-9
        with col:
            if is_current:
                st.markdown("<div class='selected-mark'>", unsafe_allow_html=True)
            st.button(
                f"{dose_value:g}",
                on_click=set_quick_dose,
                args=(dose_value,),
                use_container_width=True,
                key=f"qd_{drug['key']}_{dose_value}",
                type="primary" if is_current else "secondary",
            )
            if is_current:
                st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def step_dose():
    drug = current_drug()
    render_header()
    breadcrumb(step_keys().index("dose") + 1)
    render_header_notice(drug)

    st.subheader("設定劑量")

    fmt = "%.2f" if drug.get("input_mode") == "buttons" and drug["dose_warn_high"] < 1 else "%.1f"

    if drug.get("input_mode") == "buttons":
        st.caption(
            f"請點選下方劑量按鈕（{drug['dose_warn_low']:g}–{drug['dose_warn_high']:g} {drug['dose_unit']}）。"
        )
        st.markdown(
            f"##### 劑量選擇 <span style='font-size:12px;color:#9CA3AF;font-weight:400;'>{drug['dose_unit']}</span>",
            unsafe_allow_html=True,
        )
        render_dose_buttons(drug)
    elif drug.get("input_mode") == "decimal_picker":
        st.caption(
            f"三輪滾輪：整數 + 小數第 1 位 + 小數第 2 位。建議劑量範圍 "
            f"{drug['dose_warn_low']:.2f}–{drug['dose_warn_high']:.2f} {drug['dose_unit']}，step 0.01。"
        )
        picker_value = wheel_picker(
            weight_init=ss.weight_init,
            dose_init=ss.dose_init,
            version=ss.wheel_version,
            mode="dose_only",
            d_min=int(drug["dose_warn_low"]),
            d_max=int(drug["dose_warn_high"]),
            d_decimals=2,
            d_min_real=float(drug["dose_warn_low"]),
            d_max_real=float(drug["dose_warn_high"]),
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
                    f"{dose_value:.2f}",
                    on_click=set_quick_dose,
                    args=(dose_value,),
                    use_container_width=True,
                    key=f"qd_{dose_value}",
                )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
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

    dose_decimals = drug.get("dose_decimals", 2 if drug["dose_warn_high"] < 1 else 1)
    dose_fmt = f"{{:.{dose_decimals}f}}"
    st.markdown(
        f"<div style='text-align:center;font-size:18px;color:#D1D5DB;margin:8px 0 4px;'>"
        f"目前劑量：<b style='font-size:26px;color:#FFFFFF;'>"
        f"{dose_fmt.format(ss.current_dose)}</b> {drug['dose_unit']}</div>",
        unsafe_allow_html=True,
    )

    if ss.current_dose < drug["dose_warn_low"]:
        st.warning(
            f"目前劑量低於建議起始劑量 {drug['dose_warn_low']:g} {drug['dose_unit']}，請確認醫囑。"
        )

    sw = drug.get("secondary_warning")
    if sw and ss.current_dose > sw["threshold"]:
        st.warning(sw["message"])

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
    render_header_notice(drug)

    weight = ss.current_weight
    dose = ss.current_dose
    calc_ml_hr = calculate_rate(drug, weight, dose)
    display_ml_hr = round_half_up(calc_ml_hr, 1)

    weight_line = (
        f"<p style='font-size:18px;color:#D1D5DB;margin-top:8px;'>目前體重：{weight:.1f} kg</p>"
        if drug["needs_weight"] else
        f"<p style='font-size:14px;color:#9CA3AF;margin-top:8px;'>{drug['display_name']}（無需體重）</p>"
    )

    conc_unit = "U/ml" if drug["dose_unit"].startswith("U") else "mcg/ml"
    dose_decimals = drug.get("dose_decimals", 2 if drug["dose_warn_high"] < 1 else 1)
    dose_fmt = f"{{:.{dose_decimals}f}}"

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
                目前劑量：<b>{dose_fmt.format(dose)} {drug['dose_unit']}</b>
            </p>
            {weight_line}
            <p style='font-size:13px;color:#9CA3AF;margin-top:8px;'>
                濃度：{conc['mcg_per_ml']:g} {conc_unit} ｜ {conc['label']}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(f"原始精確計算值：{calc_ml_hr:.2f} ml/hr")
    if drug["needs_weight"]:
        st.caption(
            f"計算式：{dose_fmt.format(dose)} × {weight:.1f} × 60 ÷ {conc['mcg_per_ml']:g} = {calc_ml_hr:.2f} ml/hr"
        )
    else:
        st.caption(
            f"計算式：{dose_fmt.format(dose)} × 60 ÷ {conc['mcg_per_ml']:g} = {calc_ml_hr:.2f} ml/hr"
        )

    sw = drug.get("secondary_warning")
    if sw and dose > sw["threshold"]:
        st.warning(sw["message"])

    st.error("高警訊藥物提醒：給藥前請完成雙人覆核流程。")

    if drug.get("monitoring_notice"):
        st.warning(drug["monitoring_notice"])

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
    st.caption("目前版本：MVP v0.8｜支援 Dopamine、Norepinephrine、Epinephrine、Pitressin（休克 / GI 出血）")


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

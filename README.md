# 急重症藥物速率換算工具 v0.8

## 專案說明

本專案是一個以 Streamlit 建立的急重症藥物速率換算工具，
針對行動裝置（手機）操作優化，採用步驟引導 + 自製滾輪輸入。

定位：

- 成人 Adult Only
- 即時換算 ml/hr
- 不輸入、不儲存、不傳送任何病人個資
- 不設使用者鎖定 / 登入機制

## 目前支援藥物

| 分類 | 藥物 | 適應症 / 備註 | 劑量單位 |
|---|---|---|---|
| 升壓 / 強心 | Dopamine / Easydopa | — | mcg/kg/min |
| 升壓 | Norepinephrine | 低濃度 16 mcg/ml、高濃度 80 mcg/ml 兩種泡法 | mcg/min |
| 升壓 | Epinephrine（休克） | 成人 septic shock 輔助升壓，NE+Vasopressin 後使用 | mcg/kg/min |
| 升壓 | Pitressin（休克） | 休克輔助升壓，常於 norepinephrine 後加上 | U/min |
| 出血 | Pitressin（腸胃道出血） | 高警訊：腸胃道 / 靜脈曲張出血專用 | U/min |

> Pitressin 兩個適應症在工具內是**獨立卡片**，避免混用。

## 各藥物速覽

### Dopamine / Easydopa

| 項目 | 內容 |
|---|---|
| 規格 / 泡製 | Easydopa 800 mg / 500 ml，不須稀釋 |
| 濃度 | 1.6 mg/ml（1600 mcg/ml） |
| 起始 / 最大劑量 | 5 / 50 mcg/kg/min |
| 60 kg 參考流速 | 11.25–112.5 ml/hr |

### Norepinephrine

| 項目 | 內容 |
|---|---|
| 低濃度泡製 | Levophed 4 mg × 2 amp + 500 ml D5W → 16 mcg/ml |
| 高濃度泡製 | Levophed 4 mg × 2 amp + 100 ml D5W → 80 mcg/ml |
| 劑量範圍 | 1–30 mcg/min |
| 警示 | 劑量 > 15 mcg/min 時，提醒考慮合併 vasopressin |

### Epinephrine（休克）

| 項目 | 內容 |
|---|---|
| 泡製 | Epinephrine 2 mg + D/W 至 20 ml → 0.1 mg/ml（100 mcg/ml） |
| 劑量範圍 | 0.05–2.00 mcg/kg/min（step 0.01） |
| 60 kg 參考流速 | 1.8–72 ml/hr |
| 劑量輸入 | 三輪小數滾輪（整數 + 小數第 1 位 + 小數第 2 位），含上下限 hard stop |
| 警示 | 監測心搏過速、心律不整、心肌缺血、外滲組織壞死、lactate 變化 |

### Pitressin（休克）

| 項目 | 內容 |
|---|---|
| 泡製 | Pitressin 20 U + NS 至 20 ml → 1 U/ml |
| 劑量範圍 | 0.01–0.04 U/min |

### Pitressin（腸胃道出血）

| 項目 | 內容 |
|---|---|
| 泡製 | Pitressin 100 U + NS 至 100 ml → 1 U/ml |
| 劑量範圍 | 0.2–0.4 U/min |
| 高警訊 | 確認適應症，留意心肌、腸胃道、皮膚與周邊組織缺血徵候 |

## 使用流程（Wizard）

採步驟引導式介面，根據藥物自動決定步驟數：

- **需要體重**（Dopamine、Epinephrine）：藥物 → 體重 → 劑量 → 結果（4 步）
- **不需體重**（NE、Pitressin 兩種）：藥物 → 劑量 → 結果（3 步）

第一步藥物選擇為 2x2 卡片排列（5 種藥物時最後一格獨佔一列），
Pitressin 兩個適應症採用不同配色避免混用。
劑量輸入使用自製 `wheel_picker/` 滾輪元件（行動裝置慣性滾動體驗）：

- 一般藥物用 2 輪（整數 + 小數第 1 位）
- Epinephrine 用 3 輪（整數 + 小數第 1 位 + 小數第 2 位，step 0.01）
- 跨度較小的藥物（Pitressin）改用快速劑量按鈕

## 計算公式

需要體重的藥物（以 mcg/kg/min 為單位）：

```text
流速 ml/hr = 劑量 mcg/kg/min × 體重 kg × 60 ÷ 藥物濃度 mcg/ml
```

不需體重的藥物（以 mcg/min 或 U/min 為單位）：

```text
流速 ml/hr = 劑量 × 60 ÷ 藥物濃度（每 ml）
```

## 執行方式

安裝套件：

```bash
pip install -r requirements.txt
```

啟動：

```bash
streamlit run app.py
```

瀏覽器開啟：

```text
http://localhost:8501
```

## 安全聲明

本工具僅供輔助計算。

給藥前請依：

- 醫囑
- 院內規範
- 高警訊藥物雙人覆核流程

執行確認。

## 個資聲明

本工具不輸入、不儲存、不傳送以下資料：

- 病人姓名
- 病歷號
- 身分證字號
- 床號
- 診斷
- 任何可識別病人資料

## 版本資訊

- 資料版本：急重症藥物泡製流速表 1110701
- 工具版本：v0.8
- 目前支援藥物：Dopamine / Easydopa、Norepinephrine、Epinephrine（休克）、Pitressin（休克 / 腸胃道出血）

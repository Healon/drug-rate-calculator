# 急重症藥物速率換算工具 MVP v0.4

## 專案說明

本專案是一個以 Streamlit 建立的急重症藥物速率換算工具。

第一版僅支援：

- Dopamine / Easydopa
- 成人 Adult Only
- 即時換算 ml/hr
- 不輸入病人個資
- 不設鎖定機制

## Dopamine 資料

| 項目 | 內容 |
|---|---|
| 藥品名稱 | Dopamine / Easydopa |
| 規格 | 800 mg / 500 ml |
| 泡製方式 | 不須稀釋 |
| 濃度 | 1.6 mg/ml = 1600 mcg/ml |
| 起始劑量 | 5.0 mcg/kg/min |
| 最大劑量 | 50.0 mcg/kg/min |
| 60 kg 參考流速 | 11.25–112.5 ml/hr |

## 計算公式

```text
流速 ml/hr = 劑量 mcg/kg/min × 體重 kg × 60 ÷ 藥物濃度 mcg/ml
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
- 工具版本：MVP v0.4
- 目前支援藥物：Dopamine / Easydopa

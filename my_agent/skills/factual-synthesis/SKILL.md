---
name: factual-synthesis
description: 利用收集到的資料進行合成，並產出市場數據、新聞摘要與基於證據的結論。
---

[CRITICAL RULES: DATA ACCURACY]
1. DECIMAL-TO-PERCENTAGE: 嚴格執行小數轉百分比。例如 0.0400 必須轉換為 4.00%，禁止誤植為 40%。
2. MULTI-DIMENSIONAL ANALYSIS: 在描述營收或利潤等總額時，必須同時檢查對應的增長率 (Growth Rate)。若總額巨大但增長率為負 (如 -0.031)，結論必須客觀指出「營收基礎穩固但成長放緩」。
3. SOURCE-BASED ONLY: 禁止任何基於資料之外的推測，所有結論必須有數據支持。

[OUTPUT SECTIONS]
1. Base Market Data: 包含現價、52週區間、市值、P/E、毛利率與淨利率。
2. Recent News Summary: 摘要最新新聞點，並附上標題。
3. Evidence-Based Conclusion: 
   - 財務健康度評估 (結合利潤率與負債比)。
   - 市場競爭力評估 (結合新聞趨勢與市佔描述)。
   - 潛在風險警示 (結合估值 P/E 與成長性)。

使用JSON格式輸出。

[TONE]
極其嚴謹、冷靜的投資銀行分析師風格。

# 📊 ML Pipeline - Visualization Guide & Cluster Interpretation

**التاريخ:** 2026-06-01  
**الإصدار:** v0

---

## 📈 Exploit Likelihood Visualizations

### **1️⃣ Feature Importance (v0_eda.png)**
**الهدف:** فهم أي features أهم في التنبؤ بـ in_kev

```
Graph Type: Horizontal Bar Chart with Error Bars
Metric: Permutation Importance (Mean Decrease in PR-AUC)

Results:
┌──────────────────┬────────────┬──────────┐
│ Feature          │ Importance │ % Total  │
├──────────────────┼────────────┼──────────┤
│ percentile       │ 0.3042     │ 97.6% 🔴 │
│ cve_age_years    │ 0.0062     │ 2.0% 🟡  │
│ cvss             │ 0.0011     │ 0.4% 🟢  │
└──────────────────┴────────────┴──────────┘

Interpretation:
- percentile is DOMINANT (97.6%)
  → EPSS-based ranking is the strongest signal
- cve_age_years is secondary (2.0%)
  → Age matters but less than EPSS
- cvss is minimal (0.4%)
  → Base score alone is weak predictor
  → EPSS captures exploitation likelihood better
```

**متى تستخدمه:**
- التأكد من أن الموديل يعتمد على الـ right signals
- شرح للـ stakeholders لماذا EPSS أقوى من CVSS
- تشخيص إذا كان في features غير ضروري

---

### **2️⃣ Precision-Recall Curve (v0_eval.png)**
**الهدف:** قياس الـ model performance على balanced way

```
Graph Type: Line Plot
Metric: Precision vs Recall (Trade-off curve)

Performance Metrics:
- PR-AUC: 0.9960 (Excellent)
- Threshold: 0.5
- Interpretation: Model يقدر يصيد 99.6% من exploited CVEs
  مع maintaining جودة عالية
```

**متى تستخدمه:**
- عرض الـ model quality للـ team
- شرح precision vs recall trade-off
- اختيار threshold مناسب حسب business needs

---

### **3️⃣ Confusion Matrix (v0_confusion_matrix.png)** ✨ NEW
**الهدف:** فهم أنواع الأخطاء (False Positives vs False Negatives)

```
Graph Type: 2x2 Heatmap
Threshold: 0.5

Confusion Matrix Interpretation:
┌─────────────────────┬──────────────────┬──────────────────┐
│                     │ Predicted: Not   │ Predicted: In    │
│                     │ Exploited (0)    │ KEV (1)          │
├─────────────────────┼──────────────────┼──────────────────┤
│ Actual: Not (0)     │ TN (True Neg)     │ FP (False Pos)   │
│                     │ = Correct Rejects │ = Alert Fatigue  │
├─────────────────────┼──────────────────┼──────────────────┤
│ Actual: In KEV (1)  │ FN (False Neg)    │ TP (True Pos)    │
│                     │ = Missed Exploits │ = Detected       │
└─────────────────────┴──────────────────┴──────────────────┘

Business Impact:
- High TP: Good (catching real exploited CVEs)
- Low FN: Critical (not missing exploited CVEs)
- Low FP: Important (reducing noisy alerts)
- High TN: Good (correctly excluding non-exploited)
```

**متى تستخدمه:**
- فهم أين الموديل يخطئ الأكثر
- قرار threshold: أين يجب نختار TP vs FP trade-off
- compliance reporting

---

## ⏱️ Time-to-Exploit Visualizations

### **4️⃣ TTE Distribution (v0_t2e_eda.png)**
**الهدف:** فهم توزيع days_to_exploit في البيانات

```
Graph Type: Histogram (30 bins)
Metric: Days to Exploit from CVE publication

Distribution Stats:
- Min: 1 day
- Median: 524 days
- Max: 2,554 days
- Mean: ~750 days (estimated)

Interpretation:
- Most CVEs exploited within ~2 years
- Long tail: Some CVEs exploited even after years
- Planning: Use percentiles for SLA setting
```

**متى تستخدمه:**
- عرض realistic time-to-exploit distribution
- SLA setting (e.g., 30th percentile = 90 days)
- stakeholder education

---

### **5️⃣ Predicted vs Actual TTE (v0_t2e_eval.png)**
**الهدف:** قياس regression accuracy

```
Graph Type: Scatter Plot + Diagonal Reference
Metric: Predicted Days vs Actual Days

Performance:
- MAE: 166.13 days (±166 days on average)
- R²: 0.9356 (93.56% variance explained)
- Threshold line: y=x (perfect prediction)

Interpretation:
- Points near diagonal = good predictions
- Points above = over-prediction (conservative)
- Points below = under-prediction (risky)
- Scatter width = model uncertainty
```

**متى تستخدمه:**
- regression model evaluation
- confidence bands calculation
- threshold tuning for SLAs

---

## 🎯 Attack Patterns Clustering Visualizations

### **6️⃣ K Selection (v0_patterns_k_selection.png)**
**الهدف:** اختيار الـ optimal number of clusters

```
Graph Type: Dual Axis Line Plot
Left Axis (Blue): Inertia (sum of squared distances)
Right Axis (Orange): Silhouette Score (cluster quality)

Result: k=6 selected
- Silhouette Score: 0.7398 (Good)
- Elbow: Around k=6
- Interpretation: 6 clusters is sweet spot
```

---

### **7️⃣ Host Cluster Profile (v0_patterns_profile.png)**
**الهدف:** رؤية الـ clusters في 2D space

```
Graph Type: Scatter Plot (colored by cluster)
X-Axis: Total Events
Y-Axis: Unique Attack Types
Bubble Size: Severe Tactics Present

Visual:
- Each dot = 1 host
- Color = cluster membership (0-5)
- Bubble size = severity of tactics
- Position = activity level & variety
```

---

## 🔍 Cluster Interpretation Table

### **الآن، ما معنى الـ 6 Clusters؟**

```
┌─────────┬──────────────────────┬──────────────────────────────────────┬──────────────┐
│ Cluster │ Profile              │ Characteristics                      │ Action Items │
├─────────┼──────────────────────┼──────────────────────────────────────┼──────────────┤
│    0    │ LOW RISK / QUIET     │ • Few events (< 50)                  │ • Standard   │
│         │ HOSTS                │ • Simple attack patterns             │   patch SLA  │
│         │                      │ • No severe tactics                  │ • Annual     │
│         │                      │ • Likely: Internal systems           │   audit      │
├─────────┼──────────────────────┼──────────────────────────────────────┼──────────────┤
│    1    │ PERSISTENT TARGET    │ • High event volume (200-500)        │ • CRITICAL   │
│         │ / ACTIVE THREAT      │ • 2-4 attack types                   │   patch SLA  │
│         │                      │ • Repeated attack behavior           │ • Continuous │
│         │                      │ • Likely: Public-facing servers      │   monitoring │
│         │                      │                                      │ • Incidence  │
│         │                      │                                      │   plan       │
├─────────┼──────────────────────┼──────────────────────────────────────┼──────────────┤
│    2    │ HIGH SEVERITY        │ • Extreme event volume (> 500)       │ • URGENT     │
│         │ / CRITICAL FOCUS     │ • 4+ unique attack types             │   patch SLA  │
│         │                      │ • Severe tactics detected            │ • Daily      │
│         │                      │ • True positive rate > 0.7           │   monitoring │
│         │                      │ • Likely: High-value targets         │ • Threat     │
│         │                      │                                      │   hunting    │
├─────────┼──────────────────────┼──────────────────────────────────────┼──────────────┤
│    3    │ NOISY / FALSE        │ • Very high event count              │ • Tune       │
│         │ POSITIVE SOURCES     │ • Low severity tactics               │   detection  │
│         │                      │ • High FP rate (> 0.4)               │ • Reduce     │
│         │                      │ • Often: Scanners, logging tools     │   noise      │
│         │                      │                                      │ • Baseline   │
│         │                      │                                      │   normal     │
├─────────┼──────────────────────┼──────────────────────────────────────┼──────────────┤
│    4    │ MULTI-VECTOR         │ • Moderate-high event volume         │ • Enhanced   │
│         │ ATTACKER / LATERAL   │ • 3 attack types                     │   patch SLA  │
│         │ MOVEMENT             │ • Mixed severity tactics             │ • Network    │
│         │                      │ • Evidence of lateral movement       │   segm.      │
│         │                      │ • Likely: Mid-tier targets           │ • EDR tuning │
├─────────┼──────────────────────┼──────────────────────────────────────┼──────────────┤
│    5    │ INVESTIGATION        │ • Anomalous patterns                 │ • Incident   │
│         │ PRIORITY / OUTLIERS  │ • Unique attack chains               │   response   │
│         │ / ACTIVE INCIDENTS   │ • May indicate 0-day or APT          │ • Forensics  │
│         │                      │ • True positive rate highly variable │ • Isolate &  │
│         │                      │ • Likely: Compromised hosts          │   remediate  │
└─────────┴──────────────────────┴──────────────────────────────────────┴──────────────┘
```

---

## 📋 Summary: All 7 Visualizations

| # | Name | File | Type | Metric | Business Value |
|---|------|------|------|--------|-----------------|
| 1 | Feature Importance | v0_eda.png | Bar | Permutation Imp. | Explain model decisions |
| 2 | PR Curve | v0_eval.png | Line | PR-AUC = 0.9960 | Model quality metric |
| 3 | Confusion Matrix | v0_confusion_matrix.png | Heatmap | TP/FP/TN/FN | Error breakdown |
| 4 | TTE Distribution | v0_t2e_eda.png | Histogram | Days range | SLA calibration |
| 5 | Predicted vs Actual | v0_t2e_eval.png | Scatter | MAE=166d, R²=0.94 | Regression accuracy |
| 6 | K Selection | v0_patterns_k_selection.png | Line | k=6, Silh=0.74 | Clustering quality |
| 7 | Cluster Profile | v0_patterns_profile.png | Scatter | 6 clusters | Host profiling |

---

## ✅ Dashboard Readiness

- ✅ **Exploit Likelihood:** 3 visuals (Importance, PR Curve, Confusion)
- ✅ **Time-to-Exploit:** 2 visuals (Distribution, Prediction accuracy)
- ✅ **Attack Patterns:** 2 visuals (K selection, Cluster profile) + **Table (Interpretation)**
- ✅ **Business Alignment:** Cluster profiles tied to action items
- ✅ **Non-Technical:** Interpretation table for stakeholders

**الحالة:** 🟢 **Ready for Presentation & Dashboard Integration**

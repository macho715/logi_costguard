# 📌 청구서·요율 검증 지침 v2.1

# Inland Trucking Charge Rate Table

Use this table as the **reference rate source** during invoice validation. Match on **Category + Port + Destination + Unit**.  
`Flag` column: `ok` (within ±30 %), `outlier` (deviation > 30 %), `missing` (rate not provided).

| Category   | Port              | Destination                 | Charge_Description                      | Unit      |   Rate_USD | Flag    |
|:-----------|:------------------|:----------------------------|:----------------------------------------|:----------|-----------:|:--------|
| Air        | Abu Dhabi Airport | MIRFA SITE                  | Inland Trucking (Upto 1ton)             | per truck |      150   | outlier |
| Air        | Abu Dhabi Airport | MIRFA SITE                  | Inland Trucking (Above 1ton, Upto 3ton) | per truck |      150   | outlier |
| Air        | Abu Dhabi Airport | MIRFA SITE                  | Inland Trucking (Above 3ton, Upto 5ton) | per truck |      180   | ok      |
| Air        | Abu Dhabi Airport | SHUWEIHAT Site              | Inland Trucking (Upto 1ton)             | per truck |      210   | ok      |
| Air        | Abu Dhabi Airport | SHUWEIHAT Site              | Inland Trucking (Above 1ton, Upto 3ton) | per truck |      210   | ok      |
| Air        | Abu Dhabi Airport | SHUWEIHAT Site              | Inland Trucking (Above 3ton, Upto 5ton) | per truck |      250   | ok      |
| Air        | Abu Dhabi Airport | Storage Yard                | Inland Trucking (Upto 1ton)             | per truck |      100   | outlier |
| Air        | Abu Dhabi Airport | Storage Yard                | Inland Trucking (Above 1ton, Upto 3ton) | per truck |      100   | outlier |
| Air        | Abu Dhabi Airport | Storage Yard                | Inland Trucking (Above 3ton, Upto 5ton) | per truck |      120   | outlier |
| Air        | Dubai Airport     | Hamariya free zone, Sharjah | Inland Trucking (Upto 1ton)             | per truck |      250   | ok      |
| Air        | Dubai Airport     | Hamariya free zone, Sharjah | Inland Trucking (Above 1ton, Upto 3ton) | per truck |      250   | ok      |
| Air        | Dubai Airport     | Hamariya free zone, Sharjah | Inland Trucking (Above 3ton, Upto 5ton) | per truck |      300   | ok      |
| Air        | Dubai Airport     | MIRFA SITE                  | Inland Trucking (Upto 1ton)             | per truck |      290   | ok      |
| Air        | Dubai Airport     | MIRFA SITE                  | Inland Trucking (Above 1ton, Upto 3ton) | per truck |      290   | ok      |
| Air        | Dubai Airport     | MIRFA SITE                  | Inland Trucking (Above 3ton, Upto 5ton) | per truck |      370   | outlier |
| Air        | Dubai Airport     | SHUWEIHAT Site              | Inland Trucking (Upto 1ton)             | per truck |      410   | outlier |
| Air        | Dubai Airport     | SHUWEIHAT Site              | Inland Trucking (Above 1ton, Upto 3ton) | per truck |      410   | outlier |
| Air        | Dubai Airport     | SHUWEIHAT Site              | Inland Trucking (Above 3ton, Upto 5ton) | per truck |      460   | outlier |
| Air        | Dubai Airport     | Storage Yard                | Inland Trucking (Upto 1ton)             | per truck |      200   | ok      |
| Air        | Dubai Airport     | Storage Yard                | Inland Trucking (Above 1ton, Upto 3ton) | per truck |      200   | ok      |
| Air        | Dubai Airport     | Storage Yard                | Inland Trucking (Above 3ton, Upto 5ton) | per truck |      250   | ok      |
| Bulk       | Jebel Ali Port    | Hamariya free zone, Sharjah | Inland Trucking                         | per RT    |       14   | ok      |
| Bulk       | Jebel Ali Port    | Hamariya free zone, Sharjah | Inland Trucking                         | per RT    |       19   | ok      |
| Bulk       | Jebel Ali Port    | MIRFA SITE                  | Inland Trucking                         | per RT    |       34.5 | outlier |
| Bulk       | Jebel Ali Port    | MIRFA SITE                  | Inland Trucking                         | per RT    |       20   | ok      |
| Bulk       | Jebel Ali Port    | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       44.5 | outlier |
| Bulk       | Jebel Ali Port    | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       25   | outlier |
| Bulk       | Jebel Ali Port    | Storage Yard                | Inland Trucking                         | per RT    |       15   | ok      |
| Bulk       | Jebel Ali Port    | Storage Yard                | Inland Trucking                         | per RT    |       19   | ok      |
| Bulk       | Khalifa Port      | MIRFA SITE                  | Inland Trucking                         | per RT    |       24.2 | outlier |
| Bulk       | Khalifa Port      | MIRFA SITE                  | Inland Trucking                         | per RT    |       13.4 | ok      |
| Bulk       | Khalifa Port      | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       29.2 | outlier |
| Bulk       | Khalifa Port      | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       15.2 | ok      |
| Bulk       | Khalifa Port      | Storage Yard                | Inland Trucking                         | per RT    |       10.5 | outlier |
| Bulk       | Khalifa Port      | Storage Yard                | Inland Trucking                         | per RT    |       12.4 | outlier |
| Bulk       | Mina Zayed Port   | MIRFA SITE                  | Inland Trucking                         | per RT    |       21   | ok      |
| Bulk       | Mina Zayed Port   | MIRFA SITE                  | Inland Trucking                         | per RT    |       11.6 | outlier |
| Bulk       | Mina Zayed Port   | MIRFA SITE                  | Inland Trucking                         | per RT    |       28.2 | outlier |
| Bulk       | Mina Zayed Port   | MIRFA SITE                  | Inland Trucking                         | per RT    |      nan   | missing |
| Bulk       | Mina Zayed Port   | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       25   | outlier |
| Bulk       | Mina Zayed Port   | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       13.1 | ok      |
| Bulk       | Mina Zayed Port   | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       34.7 | outlier |
| Bulk       | Mina Zayed Port   | SHUWEIHAT Site              | Inland Trucking                         | per RT    |      nan   | missing |
| Bulk       | Mina Zayed Port   | Storage Yard                | Inland Trucking                         | per RT    |        8.4 | outlier |
| Bulk       | Mina Zayed Port   | Storage Yard                | Inland Trucking                         | per RT    |       10.5 | outlier |
| Bulk       | Mina Zayed Port   | Storage Yard                | Inland Trucking                         | per RT    |       23.8 | ok      |
| Bulk       | Mina Zayed Port   | Storage Yard                | Inland Trucking                         | per RT    |      nan   | missing |
| Bulk       | Musaffah Port     | MIRFA SITE                  | Inland Trucking                         | per RT    |       18.4 | ok      |
| Bulk       | Musaffah Port     | MIRFA SITE                  | Inland Trucking                         | per RT    |       10.5 | outlier |
| Bulk       | Musaffah Port     | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       22.2 | ok      |
| Bulk       | Musaffah Port     | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       11.9 | outlier |
| Bulk       | Musaffah Port     | Storage Yard                | Inland Trucking                         | per RT    |        5.2 | outlier |
| Bulk       | Musaffah Port     | Storage Yard                | Inland Trucking                         | per RT    |        6.3 | outlier |
| Container  | Jebel Ali Port    | Hamariya free zone, Sharjah | Inland Trucking                         | per RT    |       55   | outlier |
| Container  | Jebel Ali Port    | Hamariya free zone, Sharjah | Inland Trucking                         | per truck |      400   | ok      |
| Container  | Jebel Ali Port    | Hamariya free zone, Sharjah | Inland Trucking                         | per truck |      400   | ok      |
| Container  | Jebel Ali Port    | MIRFA SITE                  | Inland Trucking                         | per RT    |       68   | outlier |
| Container  | Jebel Ali Port    | MIRFA SITE                  | Inland Trucking                         | per truck |      770   | outlier |
| Container  | Jebel Ali Port    | MIRFA SITE                  | Inland Trucking                         | per truck |      770   | outlier |
| Container  | Jebel Ali Port    | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       85   | outlier |
| Container  | Jebel Ali Port    | SHUWEIHAT Site              | Inland Trucking                         | per truck |      980   | outlier |
| Container  | Jebel Ali Port    | SHUWEIHAT Site              | Inland Trucking                         | per truck |      980   | outlier |
| Container  | Jebel Ali Port    | Storage Yard                | Inland Trucking                         | per RT    |       55   | outlier |
| Container  | Jebel Ali Port    | Storage Yard                | Inland Trucking                         | per truck |      400   | ok      |
| Container  | Jebel Ali Port    | Storage Yard                | Inland Trucking                         | per truck |      400   | ok      |
| Container  | Khalifa Port      | MIRFA SITE                  | Inland Trucking                         | per RT    |       35   | outlier |
| Container  | Khalifa Port      | MIRFA SITE                  | Inland Trucking                         | per truck |      496   | ok      |
| Container  | Khalifa Port      | MIRFA SITE                  | Inland Trucking                         | per truck |      496   | ok      |
| Container  | Khalifa Port      | Mina Zayed Port             | Inland Trucking                         | per RT    |       35   | outlier |
| Container  | Khalifa Port      | Mina Zayed Port             | Inland Trucking                         | per truck |      400   | ok      |
| Container  | Khalifa Port      | Mina Zayed Port             | Inland Trucking                         | per truck |      400   | ok      |
| Container  | Khalifa Port      | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       45   | outlier |
| Container  | Khalifa Port      | SHUWEIHAT Site              | Inland Trucking                         | per truck |      679   | outlier |
| Container  | Khalifa Port      | SHUWEIHAT Site              | Inland Trucking                         | per truck |      679   | outlier |
| Container  | Khalifa Port      | Storage Yard                | Inland Trucking                         | per RT    |       29   | outlier |
| Container  | Khalifa Port      | Storage Yard                | Inland Trucking                         | per truck |      252   | outlier |
| Container  | Khalifa Port      | Storage Yard                | Inland Trucking                         | per truck |      252   | outlier |


---

# 📊 Domestic Rate Additional Analysis

# ğŸ“Š Domestic Rate - ì¶”ê°€ ë¶„ì„ ë³´ê³ ì„œ (PerKM, Vehicle, Fixed Cost)

## 1ï¸âƒ£ Per Kilometer ìš”ìœ¨ í†µê³„ (PerKM_Stats)
ìš´í–‰ êµ¬ê°„ë³„ ê±°ë¦¬ ëŒ€ë¹„ ìš”ìœ¨(USD/km) í‰ê· ê°’ ë° í¸ì°¨ í†µê³„ì…ë‹ˆë‹¤.

| Unnamed: 0   |       Value |
|:-------------|------------:|
| count        |  130        |
| mean         |   39.3012   |
| std          |  145.486    |
| min          |    0.833333 |
| 25%          |    2.4      |
| 50%          |    3.75     |
| 75%          |   20        |
| max          | 1500        |

## 2ï¸âƒ£ ì°¨ëŸ‰ë³„ ìš”ì•½ (Vehicle_Summary)
ì°¨ì¢…ë³„ í‰ê·  ìš”ìœ¨, ì´ ìš´í–‰ ê±°ë¦¬, ì´ íŠ¸ë¦½ ìˆ˜ ë“±ì˜ í†µê³„ ìš”ì•½ì…ë‹ˆë‹¤.

| Vehicle Type          |   count |      mean |       min |        max |
|:----------------------|--------:|----------:|----------:|-----------:|
| 3 TON PU              |      14 |   5.33902 |  1        |   24       |
| Flatbed               |     100 |  26.0588  |  0.833333 |  529.081   |
| Flatbed - CICPA       |       1 |   4.61538 |  4.61538  |    4.61538 |
| Flatbed HAZMAT        |       1 |  47.651   | 47.651    |   47.651   |
| Flatbed(Side Grilled) |       2 |   2.4     |  2.4      |    2.4     |
| Lowbed                |       9 | 236.77    |  6.78857  | 1500       |
| Lowbed(1 X 14m)       |       1 |  57.5     | 57.5      |   57.5     |
| Lowbed(2 X 23m)       |       1 |  80       | 80        |   80       |

## 3ï¸âƒ£ ë¹„ì •ìƒ ê³ ì •ìš”ìœ¨ íƒì§€ (FixedCost_Suspect)
ê³ ì • ìš”ìœ¨(Fixed Rate)ì´ ë¹„ì •ìƒì ìœ¼ë¡œ ë†’ì€ í•­ëª©ì„ íƒì§€í•˜ì—¬ ì •ë¦¬í•œ í…Œì´ë¸”ì…ë‹ˆë‹¤.

|   No. | date                | Shipment Reference                   | Place of Loading   | Place of Delivery   | Vehicle Type   |   Distance(km) |   Rate (USD) |   per kilometer / usd | Flag                 |
|------:|:--------------------|:-------------------------------------|:-------------------|:--------------------|:---------------|---------------:|-------------:|----------------------:|:---------------------|
|     2 | 2024-10-01 00:00:00 | HVDC-ADOPT-SIM-0005                  | DSV MUSSAFAH YARD  | ESNAAD (MOSB)       | Flatbed        |             10 |       200    |                20     | Suspected Fixed Cost |
|    10 | 2024-10-01 00:00:00 | HVDC-DSV-MOSB-JETTY                  | ESNAAD (MOSB)      | JETTY               | Lowbed         |              5 |      1500    |               300     | Suspected Fixed Cost |
|    12 | 2024-10-01 00:00:00 | HVDC-DSV-MOSB-050                    | ESNAAD (MOSB)      | ESNAAD (MOSB)       | Flatbed        |              1 |       200    |               200     | Suspected Fixed Cost |
|    13 | 2024-10-01 00:00:00 | HVDC-DSV-MOSB-050                    | ESNAAD (MOSB)      | DSV MUSSAFAH YARD   | Flatbed        |              5 |       200    |                40     | Suspected Fixed Cost |
|    14 | 2024-10-01 00:00:00 | HVDC-DSV-MOSB-050                    | DSV MUSSAFAH YARD  | ESNAAD (MOSB)       | Flatbed        |             10 |       200    |                20     | Suspected Fixed Cost |
|    22 | 2024-11-01 00:00:00 | HVDC-DSV-MOSB-052                    | MOSB               | DSV MUSSAFAH AYRD   | Flatbed        |              5 |       200    |                40     | Suspected Fixed Cost |
|    23 | 2024-11-01 00:00:00 | HVDC-DSV-MOSB-052                    | DSV MUSSAFAH AYRD  | MOSB                | Flatbed        |              5 |       200    |                40     | Suspected Fixed Cost |
|    24 | 2024-11-01 00:00:00 | HVDC-DSV-MOSB-057                    | DSV MUSSAFAH AYRD  | MOSB                | Flatbed        |              5 |       200    |                40     | Suspected Fixed Cost |
|    26 | 2024-11-01 00:00:00 | HVDC-ADOPT-SIM-0005-2-MOSB           | DSV MUSAFFAH YARD  | MOSB                | Flatbed        |             10 |       200    |                20     | Suspected Fixed Cost |
|    27 | 2024-11-01 00:00:00 | Shifting of Basket                   | MOSB               | MOSB                | Flatbed        |              1 |       200    |               200     | Suspected Fixed Cost |
|    28 | 2024-11-01 00:00:00 | HVDC-DSV-DAS-SHIFTING                | DSV Musaffah Yard  | DSV MUSAFFAH YARD   | Flatbed        |              2 |       200    |               100     | Suspected Fixed Cost |
|    29 | 2024-11-01 00:00:00 | HVDC-DSV-SOC-CNT                     | MOSB               | MOSB                | Flatbed        |              1 |       200    |               200     | Suspected Fixed Cost |
|    37 | 2024-11-01 00:00:00 | HVDC-DSV-MIR-0031                    | DSV Musaffah Yard  | MOSB                | Flatbed        |             10 |       420    |                42     | Suspected Fixed Cost |
|    50 | 2024-11-01 00:00:00 | HVDC-DSV-MOSB-059                    | MOSB               | MOSB                | Lowbed         |              1 |      1500    |              1500     | Suspected Fixed Cost |
|    56 | 2024-11-01 00:00:00 | HVDC-SCT-RE-0001                     | Sharjah            | Jubail              | Flatbed        |             10 |      5290.81 |               529.081 | Suspected Fixed Cost |
|    57 | 2024-12-01 00:00:00 | HVDC-ADOPT-SIM-0005-2-MOSB           | DSV MUSAFFAH YARD  | MOSB                | Flatbed        |             10 |       200    |                20     | Suspected Fixed Cost |
|    58 | 2024-12-01 00:00:00 | Shifting of Basket                   | MOSB               | MOSB                | Flatbed        |              1 |       200    |               200     | Suspected Fixed Cost |
|    66 | 2024-12-01 00:00:00 | HVDC-DSV-DAS-SHIFTING                | DSV Musaffah Yard  | DSV MUSAFFAH YARD   | Flatbed        |              2 |       200    |               100     | Suspected Fixed Cost |
|    67 | 2024-12-01 00:00:00 | HVDC-DSV-SOC-CNT                     | MOSB               | MOSB                | Flatbed        |              1 |       200    |               200     | Suspected Fixed Cost |
|    70 | 2024-12-01 00:00:00 | HVDC-DSV-MIR-0031                    | DSV Musaffah Yard  | MOSB                | Flatbed        |             10 |       420    |                42     | Suspected Fixed Cost |
|    80 | 2025-02-01 00:00:00 | HVDC-ADOPT-SIM-0006-AAA              | AAA WAREHOUSE      | MOSB                | Flatbed HAZMAT |             10 |       476.51 |                47.651 | Suspected Fixed Cost |
|    82 | 2025-02-01 00:00:00 | HVDC-DAS-DSV-086                     | MINA FREEPORT      | MINA FREEPORT       | Flatbed        |              5 |       171    |                34.2   | Suspected Fixed Cost |
|    83 | 2025-02-01 00:00:00 | HVDC-ADOPT-SCT-0029-MOSB             | DSV MUSSAFAH YARD  | MOSB                | Flatbed        |              5 |       200    |                40     | Suspected Fixed Cost |
|    87 | 2025-02-01 00:00:00 | HVDC-ADOPT-SCT-0037-MOSB             | DSV MUSSAFAH YARD  | MOSB                | Flatbed        |              5 |       200    |                40     | Suspected Fixed Cost |
|    90 | 2025-02-01 00:00:00 | HVDC-DAS-NIE-MOSB-004                | DSV MUSSAFAH YARD  | MOSB                | Flatbed        |              5 |       200    |                40     | Suspected Fixed Cost |
|   107 | 2025-02-01 00:00:00 | HVDC-DSV-FP-093                      | MINA FREEPORT      | MINA FREEPORT       | Lowbed         |              5 |       980.26 |               196.052 | Suspected Fixed Cost |
|   113 | 2025-03-01 00:00:00 | HVDC-ADOPT-SCT-0043, 0045, 0047-MOSB | DSV MUSSAFAH YARD  | MOSB                | Flatbed        |              5 |       200    |                40     | Suspected Fixed Cost |
|   114 | 2025-03-01 00:00:00 | HVDC-ADOPT-SCT-0038,0039-MOSB        | DSV MUSSAFAH YARD  | MOSB                | Flatbed        |              5 |       200    |                40     | Suspected Fixed Cost |
|   118 | 2025-03-01 00:00:00 | HVDC-DSV-MOSB-SHU-097                | MOSB               | DSV MUSSAFAH YARD   | 3 TON PU       |              5 |       120    |                24     | Suspected Fixed Cost |
|   130 | 2025-03-01 00:00:00 | Mina Zayed Transformer               | MINA ZAYED         | MINA ZAYED          | nan            |              5 |       515.18 |               103.036 | Suspected Fixed Cost |

---

# 📋 2025년 4월 국내 운송 요율 최종 검증 보고서

# ğŸ“‘ 2025ë…„ 4ì›” êµ­ë‚´ ìš´ì†¡ ìš”ìœ¨ ìµœì¢… ê²€ì¦ ë³´ê³ ì„œ

### 1ï¸âƒ£ Executive Summary (2025-06-12 10:19)
- **ì´ 92 ê±´** ìš´ì†¡ ë‚´ì—­ ì¤‘ **Verified 76 ê±´**, **Pending Review 16 ê±´**.
- ê²€ì¦ ê¸°ì¤€: Domestic Rate Reference Summary Â±3% ì¼ì¹˜ ì—¬ë¶€.
- í†µí™” ê¸°ì¤€: USD ê³ ì •, í†µí™” ë³€í™˜ ì—†ìŒ.

---
### 2ï¸âƒ£ ìƒì„¸ ê²€ì¦ í…Œì´ë¸”

|   Ref No. |   S/N | Shipment Reference                                                                                                                          | Place of Loading          | Place of Delivery                          | Vehicle Type    |   Rate (USD) |   Amount (USD) | Verification Result   | Verification Logic                   |
|----------:|------:|:--------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------|:-------------------------------------------|:----------------|-------------:|---------------:|:----------------------|:-------------------------------------|
|         1 |     1 | HVDC-ADOPT-SIM-0050                                                                                                                         | DSV Mussafah Yard         | MOSB                                       | Lowbed          |       617    |         617    | Verified              | Contract Â±3% match                   |
|         2 |     2 | HVDC-ADOPT-SCT-0066,HVDC-ADOPT-SIM-0072                                                                                                     | DSV Mussafah Yard         | MIRFA                                      | Flatbed         |       420    |         420    | Verified              | Contract Â±3% match                   |
|         3 |     2 | HVDC-ADOPT-SCT-0066,HVDC-ADOPT-SIM-0072                                                                                                     | DSV Mussafah Yard         | MOSB                                       | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|         4 |     2 | HVDC-ADOPT-SCT-0066,HVDC-ADOPT-SIM-0072                                                                                                     | MOSB                      | Shuweihat                                  | Flatbed         |       600    |         600    | Verified              | Contract Â±3% match                   |
|         5 |     3 | HVDC-ADOPT-SCT-0066                                                                                                                         | DSV Mussafah Yard         | Shuweihat                                  | 3 Ton Pickup    |       250    |         250    | Pending Review        | Rate not found in reference list Â±3% |
|         6 |     4 | HVDC-ADOPT-SIM-0058                                                                                                                         | M44 Warehouse             | MOSB                                       | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|         7 |     4 | HVDC-ADOPT-SIM-0058                                                                                                                         | MOSB                      | DSV Mussafah Yard                          | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|         8 |     5 | HVDC-DSV-F3-SHU-103                                                                                                                         | F3 Fujairah               | Shuweihat                                  | Flatbed         |      1420    |        1420    | Pending Review        | Rate not found in reference list Â±3% |
|         9 |     6 | HVDC-HE-DAS-DSV-ALMASAOOD                                                                                                                   | DSV WH Mussafah Yard      | Al Masaood                                 | Flatbed         |       200    |         800    | Verified              | Contract Â±3% match                   |
|        10 |     6 | HVDC-HE-DAS-DSV-ALMASAOOD                                                                                                                   | DSV Mussafah Yard         | Al Masaood                                 | Lowbed          |       580    |        4060    | Pending Review        | Rate not found in reference list Â±3% |
|        11 |     6 | HVDC-HE-DAS-DSV-ALMASAOOD                                                                                                                   | AL Masaood                | DSV Mussafah Yard                          | Lowbed          |       580    |         580    | Pending Review        | Rate not found in reference list Â±3% |
|        12 |     6 | HVDC-HE-DAS-DSV-ALMASAOOD                                                                                                                   | MOSB                      | DSV Mussafah Yard                          | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|        13 |     7 | HVDC-ADOPT-SCT-0053                                                                                                                         | DSV Mussafah Yard         | MIRFA                                      | Flatbed         |       420    |         420    | Verified              | Contract Â±3% match                   |
|        14 |     7 | HVDC-ADOPT-SCT-0053                                                                                                                         | DSV Mussafah Yard         | Shuweihat                                  | Flatbed         |       600    |         600    | Verified              | Contract Â±3% match                   |
|        15 |     7 | HVDC-ADOPT-SCT-0053                                                                                                                         | DSV Mussafah Yard         | MOSB                                       | Flatbed         |       200    |         400    | Verified              | Contract Â±3% match                   |
|        16 |     8 | HVDC-DSV-PRE-MIR-109                                                                                                                        | Prestige Mussafah         | MIRFA                                      | Flatbed         |       420    |         420    | Verified              | Contract Â±3% match                   |
|        17 |     8 | HVDC-DSV-PRE-MIR-109                                                                                                                        | Prestige Mussafah         | Shuweihat                                  | Flatbed         |       600    |         600    | Verified              | Contract Â±3% match                   |
|        18 |     9 | HVDC-DSV-MOSB-MIR-100                                                                                                                       | MOSB                      | MIRFA                                      | Flatbed         |       420    |         420    | Verified              | Contract Â±3% match                   |
|        19 |    10 | HVDC-DSV-SIM/KEC-MOSB-098                                                                                                                   | KEC DIP DUBAI             | Shuweihat                                  | Flatbed         |       980    |         980    | Verified              | Contract Â±3% match                   |
|        20 |    11 | HVDC-DSV-MOSB-DSV-112                                                                                                                       | MOSB                      | DSV Mussafah Yard                          | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|        21 |    11 | HVDC-DSV-MOSB-DSV-112                                                                                                                       | M44 Warehouse             | DSV Mussafah Yard                          | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|        22 |    11 | HVDC-DSV-MOSB-DSV-112                                                                                                                       | DSV Mussafah Yard         | MOSB                                       | Flatbed         |       200    |         400    | Verified              | Contract Â±3% match                   |
|        23 |    12 | HVDC-SCT,DSV-ALM-MOSB-DSV-110                                                                                                               | Al Masaood                | MOSB                                       | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|           |       |  HVDC-DSV-ALM-MOSB-111                                                                                                                      |                           |                                            |                 |              |                |                       |                                      |
|        24 |    12 | HVDC-SCT,DSV-ALM-MOSB-DSV-110                                                                                                               | MOSB                      | DSV Mussafah Yard                          | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|           |       |  HVDC-DSV-ALM-MOSB-111                                                                                                                      |                           |                                            |                 |              |                |                       |                                      |
|        25 |    12 | HVDC-SCT,DSV-ALM-MOSB-DSV-110                                                                                                               | M44 Warehouse             | DSV Mussafah Yard                          | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|           |       |  HVDC-DSV-ALM-MOSB-111                                                                                                                      |                           |                                            |                 |              |                |                       |                                      |
|        26 |    12 | HVDC-SCT,DSV-ALM-MOSB-DSV-110                                                                                                               | DSV Mussafah Yard         | MOSB                                       | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|           |       |  HVDC-DSV-ALM-MOSB-111                                                                                                                      |                           |                                            |                 |              |                |                       |                                      |
|        27 |    12 | HVDC-SCT,DSV-ALM-MOSB-DSV-110                                                                                                               | Al Masaood                | MOSB                                       | Flatbed         |       200    |         400    | Verified              | Contract Â±3% match                   |
|           |       |  HVDC-DSV-ALM-MOSB-111                                                                                                                      |                           |                                            |                 |              |                |                       |                                      |
|        28 |    12 | HVDC-SCT,DSV-ALM-MOSB-DSV-110                                                                                                               | MOSB                      | Al Masaood                                 | Flatbed         |       200    |         400    | Verified              | Contract Â±3% match                   |
|           |       |  HVDC-DSV-ALM-MOSB-111                                                                                                                      |                           |                                            |                 |              |                |                       |                                      |
|        29 |    13 | HVDC-ADOPT-SIM-0074_Local,HVDC-DSV-PRE-MOSB-106                                                                                             | Prestige Mussafah         | MOSB                                       | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|        30 |    14 | HVDC-DSV-F3-MIR-096,HVDC-DSV-F3-MOSB-113                                                                                                    | F3 Fujairah               | Mirfa                                      | Flatbed         |      1217.7  |        4870.8  | Pending Review        | Rate not found in reference list Â±3% |
|        31 |    14 | HVDC-DSV-F3-MIR-096,HVDC-DSV-F3-MOSB-113                                                                                                    | F3 Fujairah               | Mirfa                                      | Lowbed          |      2500    |        2500    | Pending Review        | Rate not found in reference list Â±3% |
|        32 |    14 | HVDC-DSV-F3-MIR-096,HVDC-DSV-F3-MOSB-113                                                                                                    | F3 Fujairah               | MOSB                                       | Flatbed         |       836    |         836    | Verified              | Contract Â±3% match                   |
|        33 |    15 | HVDC-ADOPT-SCT-0050,HVDC-ADOPT-SCT-0051,HVDC-ADOPT-SCT-0052,HVDC-ADOPT-SCT-0054,HVDC-ADOPT-SCT-0055,HVDC-ADOPT-SCT-0065                     | DSV Mussafah Yard         | MIRFA                                      | Flatbed         |       420    |        2100    | Verified              | Contract Â±3% match                   |
|        34 |    16 | HVDC-DSV-HE-SHU-114                                                                                                                         | DSV Markaz                | Shuweihat                                  | Flatbed         |       600    |        2400    | Verified              | Contract Â±3% match                   |
|        35 |    17 | HVDC-DSV-MOSB-104                                                                                                                           | DSV Mussafah Yard         | MOSB                                       | Flatbed         |       200    |        1600    | Verified              | Contract Â±3% match                   |
|        36 |    18 | HVDC-ADOPT-SCT-0069                                                                                                                         | DSV Mussafah Yard         | Shuweihat                                  | 3 Ton Pickup    |       250    |         250    | Pending Review        | Rate not found in reference list Â±3% |
|        37 |    19 | HVDC-ADOPT-SCT-0050,HVDC-ADOPT-SCT-0051,HVDC-ADOPT-SCT-0052,HVDC-ADOPT-SCT-0054,HVDC-ADOPT-SCT-0055,HVDC-ADOPT-SCT-0065,HVDC-ADOPT-SCT-0069 | DSV Mussafah Yard         | Shuweihat                                  | Flatbed         |       600    |        3600    | Verified              | Contract Â±3% match                   |
|        38 |    20 | HVDC-DSV-MOSB-MIR-116                                                                                                                       | MOSB                      | MIRFA                                      | Flatbed         |       420    |         420    | Verified              | Contract Â±3% match                   |
|        39 |    21 | HVDC-DAS-ALS-257                                                                                                                            | DSV Mussafah Yard         | Al Masaood                                 | Flatbed         |       200    |        1200    | Verified              | Contract Â±3% match                   |
|        40 |    21 | HVDC-DAS-ALS-257                                                                                                                            | DSV Mussafah Yard         | Al Masaood                                 | Lowbed          |       580    |        3480    | Pending Review        | Rate not found in reference list Â±3% |
|        41 |    22 | HVDC-ADOPT-SIM-0056                                                                                                                         | DSV Mussafah Yard         | Shuweihat                                  | Flatbed         |       600    |        4200    | Verified              | Contract Â±3% match                   |
|        42 |    23 | HVDC-DSV-GEO-MOSB-102                                                                                                                       | Prime Geotextile Mussafah | MOSB                                       | 3 Ton Pickup    |       120    |         120    | Pending Review        | Rate not found in reference list Â±3% |
|        43 |    23 | HVDC-DSV-GEO-MOSB-102                                                                                                                       | Prime Geotextile Mussafah | MOSB                                       | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|        44 |    24 | HVDC-DSV-MOSB-SHU-101                                                                                                                       | MOSB                      | Shuweihat                                  | 3 Ton Pickup    |       250    |         250    | Pending Review        | Rate not found in reference list Â±3% |
|        45 |    25 | HVDC-DSV-MOSB-ALM-117                                                                                                                       | MOSB                      | Al Masaood                                 | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|           |       |  HVDC-DSV-MOSB-SHU-MOSB-116                                                                                                                 |                           |                                            |                 |              |                |                       |                                      |
|        46 |    25 | HVDC-DSV-MOSB-ALM-117                                                                                                                       | Shuweihat                 | MOSB                                       | Flatbed         |       600    |         600    | Verified              | Contract Â±3% match                   |
|           |       |  HVDC-DSV-MOSB-SHU-MOSB-116                                                                                                                 |                           |                                            |                 |              |                |                       |                                      |
|        47 |    26 | HVDC-DSV-MIR-MMT-107                                                                                                                        | Mirfa                     | Mammoet Jebel Ali                          | Flatbed         |       770    |         770    | Pending Review        | Rate not found in reference list Â±3% |
|        48 |    27 | HVDC-ADOPT-HE-0195                                                                                                                          | M44 Warehouse             | Shuweihat                                  | Flatbed         |       600    |         600    | Verified              | Contract Â±3% match                   |
|        49 |    28 | HVDC-JPTW,71                                                                                                                                | Mina Freeport             | Mina Freeport                              | Lowbed          |       980.26 |         980.26 | Verified              | Contract Â±3% match                   |
|        50 |    28 | HVDC-JPTW,71                                                                                                                                | Mina Freeport             | Mina Freeport                              | Flatbed         |       171    |         171    | Verified              | Contract Â±3% match                   |
|        51 |    29 | HVDC-DSV-MMT-MIR-105                                                                                                                        | Mirfa                     | Mammoet Jebel Ali                          | Flatbed         |       770    |         770    | Pending Review        | Rate not found in reference list Â±3% |
|        52 |    30 | HVDC-ADOPT-HE-0012, 0013                                                                                                                    | MOSB                      | Al Masaood                                 | Lowbed          |       953.03 |         953.03 | Verified              | Contract Â±3% match                   |
|        53 |    31 | HVDC-ADOPT-HE-0311-1,HVDC-ADOPT-HE-0311-2                                                                                                   | DSV Markaz                | Shuweihat                                  | Flatbed         |       600    |        2400    | Verified              | Contract Â±3% match                   |
|        54 |    32 | HVDC-ADOPT-HE-0005, 0200, 0192, 0187                                                                                                        | DSV Mussafah Yard         | MOSB                                       | Flatbed         |       200    |         400    | Verified              | Contract Â±3% match                   |
|        55 |    33 | HVDC-DSV-KEC-MIR-SHU-132                                                                                                                    | KEC Towers LLC Office     | MIRFA PMO SAMSUNG, Shuweihat Power Station | Flatbed         |      1750    |        1750    | Pending Review        | Rate not found in reference list Â±3% |
|        56 |    34 | HVDC-DSV-HE-MOSB-130, HVDC-DSV-HE-MOSB-131                                                                                                  | DSV Mussafah Yard         | MOSB                                       | Lowbed          |       953.03 |         953.03 | Verified              | Contract Â±3% match                   |
|        57 |    34 | HVDC-DSV-HE-MOSB-130, HVDC-DSV-HE-MOSB-131                                                                                                  | DSV Mussafah Yard         | MOSB                                       | Flatbed         |       200    |         600    | Verified              | Contract Â±3% match                   |
|        58 |    34 | HVDC-DSV-HE-MOSB-130, HVDC-DSV-HE-MOSB-131                                                                                                  | M44 Warehouse             | DSV Mussafah Yard                          | Flatbed         |       200    |         400    | Verified              | Contract Â±3% match                   |
|        59 |    34 | HVDC-DSV-HE-MOSB-130, HVDC-DSV-HE-MOSB-131                                                                                                  | MOSB                      | DSV Mussafah Yard                          | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|        60 |    35 | HVDC-DSV-HE-MOSB-134                                                                                                                        | M44 Warehouse             | MOSB                                       | Flatbed         |       200    |         400    | Verified              | Contract Â±3% match                   |
|        61 |    36 | HVDC-DSV-PRE-MIR-SHU-127                                                                                                                    | Prestige Mussafah         | Mirfa, Shuweihat                           | Flatbed         |       810    |         810    | Pending Review        | Rate not found in reference list Â±3% |
|        62 |    36 | HVDC-DSV-PRE-MIR-SHU-127                                                                                                                    | Prestige Mussafah         | Shuweihat                                  | Flatbed         |       600    |         600    | Verified              | Contract Â±3% match                   |
|        63 |    36 | HVDC-DSV-PRE-MIR-SHU-127                                                                                                                    | Prestige Mussafah         | Mirfa                                      | Flatbed         |       420    |         420    | Verified              | Contract Â±3% match                   |
|        64 |    37 | HVDC-ADOPT-SCT-0062                                                                                                                         | DSV Mussafah Yard         | Mirfa                                      | Flatbed (CICPA) |       420    |         420    | Verified              | Contract Â±3% match                   |
|        65 |    37 | HVDC-ADOPT-SCT-0062                                                                                                                         | DSV Mussafah Yard         | MOSB                                       | Flatbed         |       200    |         400    | Verified              | Contract Â±3% match                   |
|        66 |    37 | HVDC-ADOPT-SCT-0062                                                                                                                         | DSV Mussafah Yard         | Shuweihat                                  | Flatbed         |       600    |         600    | Verified              | Contract Â±3% match                   |
|        67 |    38 | HVDC-DSV-HE-MOSB-130                                                                                                                        | Prestige Mussafah         | MIRFA PMO SAMSUNG, Shuweihat Power Station | Flatbed         |       810    |         810    | Pending Review        | Rate not found in reference list Â±3% |
|        68 |    39 | HVDC-DSV-MOSB-ALM-130                                                                                                                       | MOSB                      | Al Masaood                                 | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|        69 |    40 | HVDC-ADOPT-SCT-0076 / HVDC-ADOPT-SCT-0081                                                                                                   | DSV Mussafah Yard         | Mirfa                                      | Flatbed         |       420    |         420    | Verified              | Contract Â±3% match                   |
|        70 |    40 | HVDC-ADOPT-SCT-0076 / HVDC-ADOPT-SCT-0081                                                                                                   | DSV Mussafah Yard         | Shuweihat                                  | Flatbed         |       600    |         600    | Verified              | Contract Â±3% match                   |
|        71 |    40 | HVDC-ADOPT-SCT-0076 / HVDC-ADOPT-SCT-0081                                                                                                   | DSV Mussafah Yard         | MOSB                                       | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|        72 |    40 | HVDC-ADOPT-SCT-0076 / HVDC-ADOPT-SCT-0081                                                                                                   | MOSB                      | DSV Mussafah Yard                          | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|        73 |    41 | HVDC-ADOPT-SIM-0061                                                                                                                         | DSV Mussafah Yard         | Mirfa                                      | Lowbed          |       953.03 |         953.03 | Verified              | Contract Â±3% match                   |
|        74 |    41 | HVDC-ADOPT-SIM-0061                                                                                                                         | DSV Mussafah Yard         | Mirfa                                      | Flatbed         |       420    |        2520    | Verified              | Contract Â±3% match                   |
|        75 |    42 | HVDC-DSV-HE-MOSB-126                                                                                                                        | M44 Warehouse             | DSV Mussafah Yard                          | Flatbed         |       200    |         400    | Verified              | Contract Â±3% match                   |
|        76 |    42 | HVDC-DSV-HE-MOSB-126                                                                                                                        | DSV Mussafah Yard         | MOSB                                       | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|        77 |    43 | HVDC-DAS-ALS-272                                                                                                                            | DSV Mussafah Yard         | Al Masaood                                 | Flatbed         |       200    |        2800    | Verified              | Contract Â±3% match                   |
|        78 |    44 | HVDC-DSV-HE-MOSB-129                                                                                                                        | MOSB                      | DSV Mussafah Yard                          | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|        79 |    45 | HVDC-DAS-ALS-278                                                                                                                            | DSV Mussafah Yard         | Al Masaood                                 | Lowbed          |       953.03 |         953.03 | Verified              | Contract Â±3% match                   |
|        80 |    45 | HVDC-DAS-ALS-278                                                                                                                            | DSV Mussafah Yard         | Al Masaood                                 | Lowbed (23m)    |       408.44 |         816.88 | Verified              | Contract Â±3% match                   |
|        81 |    45 | HVDC-DAS-ALS-278                                                                                                                            | DSV Mussafah Yard         | Al Masaood                                 | Flatbed         |       200    |        1000    | Verified              | Contract Â±3% match                   |
|        82 |    46 | HVDC-DSV-SHU-MOSB-128                                                                                                                       | Shuweihat                 | MOSB                                       | Flatbed         |       600    |         600    | Verified              | Contract Â±3% match                   |
|        83 |    47 | HVDC-DSV-HE-MOSB-121                                                                                                                        | DSV Mussafah Yard         | MOSB                                       | Flatbed         |       200    |         800    | Verified              | Contract Â±3% match                   |
|        84 |    48 | HVDC-ADOPT-SIM-0081_Local                                                                                                                   | Siemens Masdar            | Shuweihat                                  | 3 Ton Pickup    |       250    |         250    | Pending Review        | Rate not found in reference list Â±3% |
|        85 |    49 | HVDC-ADOPT-SIM-0077                                                                                                                         | Power Max Jebel Ali       | MOSB                                       | 3 Ton Pickup    |       400    |         400    | Verified              | Contract Â±3% match                   |
|        86 |    50 | HVDC-DSV-UPC-FP-MOSB-122                                                                                                                    | Mina Freeport             | MOSB                                       | Flatbed         |       171    |         171    | Verified              | Contract Â±3% match                   |
|        87 |    51 | HVDC-DSV-MOSB-ALM-120                                                                                                                       | MOSB                      | Al Masaood                                 | Flatbed         |       200    |         200    | Verified              | Contract Â±3% match                   |
|        88 |    52 | HVDC-DAS-ALS-270                                                                                                                            | DSV Mussafah Yard         | Al Masaood                                 | Flatbed         |       200    |        2800    | Verified              | Contract Â±3% match                   |
|        89 |    53 | HVDC-SHU-MIRFA-PRESTIGE, HVDC-ADOPT-SIM-0065                                                                                                | Prestige Mussafah         | Mirfa                                      | Flatbed         |       420    |         420    | Verified              | Contract Â±3% match                   |
|        90 |    53 | HVDC-SHU-MIRFA-PRESTIGE, HVDC-ADOPT-SIM-0065                                                                                                | Prestige Mussafah         | Shuweihat                                  | Flatbed         |       600    |         600    | Verified              | Contract Â±3% match                   |
|        91 |    53 | HVDC-SHU-MIRFA-PRESTIGE, HVDC-ADOPT-SIM-0065                                                                                                | DSV Mussafah Yard         | Mirfa                                      | Flatbed         |       420    |         420    | Verified              | Contract Â±3% match                   |
|        92 |    54 | HVDC-AGI-NOVATECH (PJC-PO-014_NOVA/RFQ/JJ/24)                                                                                               | DSV Mussafah Yard         | MOSB                                       | Flatbed         |       200    |         600    | Verified              | Contract Â±3% match                   |

---
### 3ï¸âƒ£ ì°¸ê³  ë¬¸ì„œ
- Domestic_Rate_Reference_Summary.md
- Domestic_Rate_Additional_Analysis.md


---

# 🚛 Inland Trucking Charge Rate Table

# Inland Trucking Charge Rate Table

Use this table as the **reference rate source** during invoice validation. Match on **Category + Port + Destination + Unit**.  
`Flag` column: `ok` (within ±30 %), `outlier` (deviation > 30 %), `missing` (rate not provided).

| Category   | Port              | Destination                 | Charge_Description                      | Unit      |   Rate_USD | Flag    |
|:-----------|:------------------|:----------------------------|:----------------------------------------|:----------|-----------:|:--------|
| Air        | Abu Dhabi Airport | MIRFA SITE                  | Inland Trucking (Upto 1ton)             | per truck |      150   | outlier |
| Air        | Abu Dhabi Airport | MIRFA SITE                  | Inland Trucking (Above 1ton, Upto 3ton) | per truck |      150   | outlier |
| Air        | Abu Dhabi Airport | MIRFA SITE                  | Inland Trucking (Above 3ton, Upto 5ton) | per truck |      180   | ok      |
| Air        | Abu Dhabi Airport | SHUWEIHAT Site              | Inland Trucking (Upto 1ton)             | per truck |      210   | ok      |
| Air        | Abu Dhabi Airport | SHUWEIHAT Site              | Inland Trucking (Above 1ton, Upto 3ton) | per truck |      210   | ok      |
| Air        | Abu Dhabi Airport | SHUWEIHAT Site              | Inland Trucking (Above 3ton, Upto 5ton) | per truck |      250   | ok      |
| Air        | Abu Dhabi Airport | Storage Yard                | Inland Trucking (Upto 1ton)             | per truck |      100   | outlier |
| Air        | Abu Dhabi Airport | Storage Yard                | Inland Trucking (Above 1ton, Upto 3ton) | per truck |      100   | outlier |
| Air        | Abu Dhabi Airport | Storage Yard                | Inland Trucking (Above 3ton, Upto 5ton) | per truck |      120   | outlier |
| Air        | Dubai Airport     | Hamariya free zone, Sharjah | Inland Trucking (Upto 1ton)             | per truck |      250   | ok      |
| Air        | Dubai Airport     | Hamariya free zone, Sharjah | Inland Trucking (Above 1ton, Upto 3ton) | per truck |      250   | ok      |
| Air        | Dubai Airport     | Hamariya free zone, Sharjah | Inland Trucking (Above 3ton, Upto 5ton) | per truck |      300   | ok      |
| Air        | Dubai Airport     | MIRFA SITE                  | Inland Trucking (Upto 1ton)             | per truck |      290   | ok      |
| Air        | Dubai Airport     | MIRFA SITE                  | Inland Trucking (Above 1ton, Upto 3ton) | per truck |      290   | ok      |
| Air        | Dubai Airport     | MIRFA SITE                  | Inland Trucking (Above 3ton, Upto 5ton) | per truck |      370   | outlier |
| Air        | Dubai Airport     | SHUWEIHAT Site              | Inland Trucking (Upto 1ton)             | per truck |      410   | outlier |
| Air        | Dubai Airport     | SHUWEIHAT Site              | Inland Trucking (Above 1ton, Upto 3ton) | per truck |      410   | outlier |
| Air        | Dubai Airport     | SHUWEIHAT Site              | Inland Trucking (Above 3ton, Upto 5ton) | per truck |      460   | outlier |
| Air        | Dubai Airport     | Storage Yard                | Inland Trucking (Upto 1ton)             | per truck |      200   | ok      |
| Air        | Dubai Airport     | Storage Yard                | Inland Trucking (Above 1ton, Upto 3ton) | per truck |      200   | ok      |
| Air        | Dubai Airport     | Storage Yard                | Inland Trucking (Above 3ton, Upto 5ton) | per truck |      250   | ok      |
| Bulk       | Jebel Ali Port    | Hamariya free zone, Sharjah | Inland Trucking                         | per RT    |       14   | ok      |
| Bulk       | Jebel Ali Port    | Hamariya free zone, Sharjah | Inland Trucking                         | per RT    |       19   | ok      |
| Bulk       | Jebel Ali Port    | MIRFA SITE                  | Inland Trucking                         | per RT    |       34.5 | outlier |
| Bulk       | Jebel Ali Port    | MIRFA SITE                  | Inland Trucking                         | per RT    |       20   | ok      |
| Bulk       | Jebel Ali Port    | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       44.5 | outlier |
| Bulk       | Jebel Ali Port    | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       25   | outlier |
| Bulk       | Jebel Ali Port    | Storage Yard                | Inland Trucking                         | per RT    |       15   | ok      |
| Bulk       | Jebel Ali Port    | Storage Yard                | Inland Trucking                         | per RT    |       19   | ok      |
| Bulk       | Khalifa Port      | MIRFA SITE                  | Inland Trucking                         | per RT    |       24.2 | outlier |
| Bulk       | Khalifa Port      | MIRFA SITE                  | Inland Trucking                         | per RT    |       13.4 | ok      |
| Bulk       | Khalifa Port      | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       29.2 | outlier |
| Bulk       | Khalifa Port      | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       15.2 | ok      |
| Bulk       | Khalifa Port      | Storage Yard                | Inland Trucking                         | per RT    |       10.5 | outlier |
| Bulk       | Khalifa Port      | Storage Yard                | Inland Trucking                         | per RT    |       12.4 | outlier |
| Bulk       | Mina Zayed Port   | MIRFA SITE                  | Inland Trucking                         | per RT    |       21   | ok      |
| Bulk       | Mina Zayed Port   | MIRFA SITE                  | Inland Trucking                         | per RT    |       11.6 | outlier |
| Bulk       | Mina Zayed Port   | MIRFA SITE                  | Inland Trucking                         | per RT    |       28.2 | outlier |
| Bulk       | Mina Zayed Port   | MIRFA SITE                  | Inland Trucking                         | per RT    |      nan   | missing |
| Bulk       | Mina Zayed Port   | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       25   | outlier |
| Bulk       | Mina Zayed Port   | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       13.1 | ok      |
| Bulk       | Mina Zayed Port   | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       34.7 | outlier |
| Bulk       | Mina Zayed Port   | SHUWEIHAT Site              | Inland Trucking                         | per RT    |      nan   | missing |
| Bulk       | Mina Zayed Port   | Storage Yard                | Inland Trucking                         | per RT    |        8.4 | outlier |
| Bulk       | Mina Zayed Port   | Storage Yard                | Inland Trucking                         | per RT    |       10.5 | outlier |
| Bulk       | Mina Zayed Port   | Storage Yard                | Inland Trucking                         | per RT    |       23.8 | ok      |
| Bulk       | Mina Zayed Port   | Storage Yard                | Inland Trucking                         | per RT    |      nan   | missing |
| Bulk       | Musaffah Port     | MIRFA SITE                  | Inland Trucking                         | per RT    |       18.4 | ok      |
| Bulk       | Musaffah Port     | MIRFA SITE                  | Inland Trucking                         | per RT    |       10.5 | outlier |
| Bulk       | Musaffah Port     | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       22.2 | ok      |
| Bulk       | Musaffah Port     | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       11.9 | outlier |
| Bulk       | Musaffah Port     | Storage Yard                | Inland Trucking                         | per RT    |        5.2 | outlier |
| Bulk       | Musaffah Port     | Storage Yard                | Inland Trucking                         | per RT    |        6.3 | outlier |
| Container  | Jebel Ali Port    | Hamariya free zone, Sharjah | Inland Trucking                         | per RT    |       55   | outlier |
| Container  | Jebel Ali Port    | Hamariya free zone, Sharjah | Inland Trucking                         | per truck |      400   | ok      |
| Container  | Jebel Ali Port    | Hamariya free zone, Sharjah | Inland Trucking                         | per truck |      400   | ok      |
| Container  | Jebel Ali Port    | MIRFA SITE                  | Inland Trucking                         | per RT    |       68   | outlier |
| Container  | Jebel Ali Port    | MIRFA SITE                  | Inland Trucking                         | per truck |      770   | outlier |
| Container  | Jebel Ali Port    | MIRFA SITE                  | Inland Trucking                         | per truck |      770   | outlier |
| Container  | Jebel Ali Port    | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       85   | outlier |
| Container  | Jebel Ali Port    | SHUWEIHAT Site              | Inland Trucking                         | per truck |      980   | outlier |
| Container  | Jebel Ali Port    | SHUWEIHAT Site              | Inland Trucking                         | per truck |      980   | outlier |
| Container  | Jebel Ali Port    | Storage Yard                | Inland Trucking                         | per RT    |       55   | outlier |
| Container  | Jebel Ali Port    | Storage Yard                | Inland Trucking                         | per truck |      400   | ok      |
| Container  | Jebel Ali Port    | Storage Yard                | Inland Trucking                         | per truck |      400   | ok      |
| Container  | Khalifa Port      | MIRFA SITE                  | Inland Trucking                         | per RT    |       35   | outlier |
| Container  | Khalifa Port      | MIRFA SITE                  | Inland Trucking                         | per truck |      496   | ok      |
| Container  | Khalifa Port      | MIRFA SITE                  | Inland Trucking                         | per truck |      496   | ok      |
| Container  | Khalifa Port      | Mina Zayed Port             | Inland Trucking                         | per RT    |       35   | outlier |
| Container  | Khalifa Port      | Mina Zayed Port             | Inland Trucking                         | per truck |      400   | ok      |
| Container  | Khalifa Port      | Mina Zayed Port             | Inland Trucking                         | per truck |      400   | ok      |
| Container  | Khalifa Port      | SHUWEIHAT Site              | Inland Trucking                         | per RT    |       45   | outlier |
| Container  | Khalifa Port      | SHUWEIHAT Site              | Inland Trucking                         | per truck |      679   | outlier |
| Container  | Khalifa Port      | SHUWEIHAT Site              | Inland Trucking                         | per truck |      679   | outlier |
| Container  | Khalifa Port      | Storage Yard                | Inland Trucking                         | per RT    |       29   | outlier |
| Container  | Khalifa Port      | Storage Yard                | Inland Trucking                         | per truck |      252   | outlier |
| Container  | Khalifa Port      | Storage Yard                | Inland Trucking                         | per truck |      252   | outlier |


---

# 📑 HVDC Inland Trucking 계약 요율표 (v1.1)

# HVDC PROJECT - INLAND TRUCKING CHARGE RATES CONTRACT
**Document Version:** v1.1  
**Effective Date:** 2025-01-01  
**Contract ID:** HVDC-ITC-2025-001  
**Project:** Samsung C&T Ã— ADNOCÂ·DSV Partnership  
**System:** MACHO-GPT v3.4-mini Logistics Operations  

---

## ğŸ“‹ EXECUTIVE SUMMARY

This contract establishes the standardized inland trucking charge rates for High Voltage Direct Current (HVDC) project cargo transportation within the UAE. The rates apply to all Samsung C&T and ADNOCÂ·DSV partnership operations, ensuring cost transparency and operational efficiency.

**Key Metrics:**
- **Coverage:** 6 Major Ports Ã— 4 Destination Sites
- **Rate Categories:** Air Cargo, Bulk Cargo, Container Cargo
- **Compliance:** FANR & MOIAT Certified
- **Validation:** Multi-source verification (â‰¥90% confidence)

---

## ğŸ¢ CONTRACTING PARTIES

### **Principal Contractor**
- **Samsung C&T Corporation** (Logistics Division)
- **ADNOC Logistics & Services**
- **DSV Solutions UAE**

### **Service Providers**
- Approved UAE Inland Trucking Operators
- FANR-Licensed Heavy Transport Providers
- MOIAT-Certified Cargo Handlers

---

## ğŸ“Š RATE STRUCTURE & CATEGORIES

### **1. AIR CARGO TRUCKING RATES**

#### **From Abu Dhabi Airport**
| Destination | Weight Category | Rate (USD/truck) | Status | Approval |
|:------------|:----------------|:-----------------|:-------|:---------|
| MIRFA SITE | Up to 1 ton | 150 | Outlier | Pending Review |
| MIRFA SITE | 1-3 tons | 150 | Outlier | Pending Review |
| MIRFA SITE | 3-5 tons | 180 | âœ… Approved | Active |
| SHUWEIHAT Site | Up to 1 ton | 210 | âœ… Approved | Active |
| SHUWEIHAT Site | 1-3 tons | 210 | âœ… Approved | Active |
| SHUWEIHAT Site | 3-5 tons | 250 | âœ… Approved | Active |
| Storage Yard | Up to 1 ton | 100 | Outlier | Pending Review |
| Storage Yard | 1-3 tons | 100 | Outlier | Pending Review |
| Storage Yard | 3-5 tons | 120 | Outlier | Pending Review |

#### **From Dubai Airport**
| Destination | Weight Category | Rate (USD/truck) | Status | Approval |
|:------------|:----------------|:-----------------|:-------|:---------|
| Hamariya FZ, Sharjah | Up to 1 ton | 250 | âœ… Approved | Active |
| Hamariya FZ, Sharjah | 1-3 tons | 250 | âœ… Approved | Active |
| Hamariya FZ, Sharjah | 3-5 tons | 300 | âœ… Approved | Active |
| MIRFA SITE | Up to 1 ton | 290 | âœ… Approved | Active |
| MIRFA SITE | 1-3 tons | 290 | âœ… Approved | Active |
| MIRFA SITE | 3-5 tons | 370 | Outlier | Pending Review |
| SHUWEIHAT Site | Up to 1 ton | 410 | Outlier | Pending Review |
| SHUWEIHAT Site | 1-3 tons | 410 | Outlier | Pending Review |
| SHUWEIHAT Site | 3-5 tons | 460 | Outlier | Pending Review |
| Storage Yard | Up to 1 ton | 200 | âœ… Approved | Active |
| Storage Yard | 1-3 tons | 200 | âœ… Approved | Active |
| Storage Yard | 3-5 tons | 250 | âœ… Approved | Active |

### **2. BULK CARGO TRUCKING RATES**

#### **From Jebel Ali Port**
| Destination | Rate (USD/RT) | Status | Approval |
|:------------|:-------------|:-------|:---------|
| Hamariya FZ, Sharjah | 14.00 | âœ… Approved | Active |
| Hamariya FZ, Sharjah | 19.00 | âœ… Approved | Active |
| MIRFA SITE | 20.00 | âœ… Approved | Active |
| MIRFA SITE | 34.50 | Outlier | Pending Review |
| SHUWEIHAT Site | 25.00 | Outlier | Pending Review |
| SHUWEIHAT Site | 44.50 | Outlier | Pending Review |
| Storage Yard | 15.00 | âœ… Approved | Active |
| Storage Yard | 19.00 | âœ… Approved | Active |

#### **From Khalifa Port**
| Destination | Rate (USD/RT) | Status | Approval |
|:------------|:-------------|:-------|:---------|
| MIRFA SITE | 13.40 | âœ… Approved | Active |
| MIRFA SITE | 24.20 | Outlier | Pending Review |
| SHUWEIHAT Site | 15.20 | âœ… Approved | Active |
| SHUWEIHAT Site | 29.20 | Outlier | Pending Review |
| Storage Yard | 10.50 | Outlier | Pending Review |
| Storage Yard | 12.40 | Outlier | Pending Review |

#### **From Mina Zayed Port**
| Destination | Rate (USD/RT) | Status | Approval |
|:------------|:-------------|:-------|:---------|
| MIRFA SITE | 11.60 | Outlier | Pending Review |
| MIRFA SITE | 21.00 | âœ… Approved | Active |
| MIRFA SITE | 28.20 | Outlier | Pending Review |
| SHUWEIHAT Site | 13.10 | âœ… Approved | Active |
| SHUWEIHAT Site | 25.00 | Outlier | Pending Review |
| SHUWEIHAT Site | 34.70 | Outlier | Pending Review |
| Storage Yard | 8.40 | Outlier | Pending Review |
| Storage Yard | 10.50 | Outlier | Pending Review |
| Storage Yard | 23.80 | âœ… Approved | Active |

#### **From Musaffah Port**
| Destination | Rate (USD/RT) | Status | Approval |
|:------------|:-------------|:-------|:---------|
| MIRFA SITE | 10.50 | Outlier | Pending Review |
| MIRFA SITE | 18.40 | âœ… Approved | Active |
| SHUWEIHAT Site | 11.90 | Outlier | Pending Review |
| SHUWEIHAT Site | 22.20 | âœ… Approved | Active |
| Storage Yard | 5.20 | Outlier | Pending Review |
| Storage Yard | 6.30 | Outlier | Pending Review |

### **3. CONTAINER CARGO TRUCKING RATES**

#### **From Jebel Ali Port**
| Destination | Unit | Rate (USD) | Status | Approval |
|:------------|:-----|:-----------|:-------|:---------|
| Hamariya FZ, Sharjah | per RT | 55.00 | Outlier | Pending Review |
| Hamariya FZ, Sharjah | per truck | 400.00 | âœ… Approved | Active |
| MIRFA SITE | per RT | 68.00 | Outlier | Pending Review |
| MIRFA SITE | per truck | 770.00 | Outlier | Pending Review |
| SHUWEIHAT Site | per RT | 85.00 | Outlier | Pending Review |
| SHUWEIHAT Site | per truck | 980.00 | Outlier | Pending Review |
| Storage Yard | per RT | 55.00 | Outlier | Pending Review |
| Storage Yard | per truck | 400.00 | âœ… Approved | Active |

#### **From Khalifa Port**
| Destination | Unit | Rate (USD) | Status | Approval |
|:------------|:-----|:-----------|:-------|:---------|
| MIRFA SITE | per RT | 35.00 | Outlier | Pending Review |
| MIRFA SITE | per truck | 496.00 | âœ… Approved | Active |
| Mina Zayed Port | per RT | 35.00 | Outlier | Pending Review |
| Mina Zayed Port | per truck | 400.00 | âœ… Approved | Active |
| SHUWEIHAT Site | per RT | 45.00 | Outlier | Pending Review |
| SHUWEIHAT Site | per truck | 679.00 | Outlier | Pending Review |
| Storage Yard | per RT | 29.00 | Outlier | Pending Review |
| Storage Yard | per truck | 252.00 | Outlier | Pending Review |

---

## ğŸ“‹ TERMS & CONDITIONS

### **1. RATE VALIDATION METHODOLOGY**
- **Confidence Threshold:** â‰¥90% (MACHO-GPT v3.4-mini standard)
- **Validation Criteria:** Within Â±30% of market benchmark
- **Status Categories:**
  - `âœ… Approved`: Rates within acceptable range
  - `Outlier`: Deviation >30%, requires review
  - `Missing`: Rate not provided, requires quotation

### **2. PAYMENT TERMS**
- **Payment Method:** Net 30 days from invoice date
- **Currency:** USD (United States Dollar)
- **Exchange Rate:** Dubai Interbank Offered Rate (DIBOR) + 2%
- **Late Payment:** 1.5% monthly penalty

### **3. SERVICE LEVEL AGREEMENTS**
- **Pickup Time:** Within 24 hours of booking
- **Transit Time:** 
  - Local (within emirate): 4-8 hours
  - Inter-emirate: 8-24 hours
- **Delivery Confirmation:** Real-time GPS tracking + electronic proof of delivery

### **4. INSURANCE & LIABILITY**
- **Cargo Insurance:** Minimum USD 1,000,000 per incident
- **Liability Coverage:** USD 5,000,000 general liability
- **Force Majeure:** Weather delays >24 hours exempt from SLA

### **5. REGULATORY COMPLIANCE**
- **FANR Requirements:** All radioactive materials transport
- **MOIAT Certification:** Oversized/overweight cargo permits
- **UAE Customs:** Real-time customs clearance integration
- **HSE Standards:** Zero-incident safety record mandatory

---

## ğŸ” INVOICE VALIDATION RULES

### **Automated Validation Logic**
```python
def validate_trucking_invoice(invoice_data):
    """
    MACHO-GPT Invoice Validation for Trucking Charges
    Confidence Threshold: â‰¥90%
    """
    
    validation_rules = {
        'rate_match': match_rate_table(invoice_data),
        'route_validation': validate_route(invoice_data),
        'weight_verification': verify_weight_category(invoice_data),
        'compliance_check': check_regulatory_compliance(invoice_data)
    }
    
    confidence_score = calculate_confidence(validation_rules)
    
    if confidence_score >= 0.90:
        return {'status': 'APPROVED', 'confidence': confidence_score}
    else:
        return {'status': 'REVIEW_REQUIRED', 'confidence': confidence_score}
```

### **Matching Criteria**
1. **Category + Port + Destination + Unit** must match exactly
2. **Rate deviation â‰¤30%** from contracted rate
3. **Weight category** must align with actual cargo weight
4. **Regulatory permits** must be valid and current

---

## ğŸ“ˆ PERFORMANCE METRICS & KPIs

### **Operational KPIs**
- **On-Time Delivery:** â‰¥95%
- **Damage Rate:** <0.1%
- **Cost Variance:** Â±5% from contracted rates
- **Compliance Score:** 100% (FANR/MOIAT)

### **Financial KPIs**
- **Invoice Accuracy:** â‰¥95%
- **Payment Processing:** â‰¤3 days average
- **Dispute Resolution:** â‰¤7 days
- **Cost Savings:** 10-15% vs. market rates

---

## ğŸš¨ ESCALATION PROCEDURES

### **Level 1: Operational Issues**
- **Contact:** Operations Manager
- **Response Time:** 2 hours
- **Resolution:** 24 hours

### **Level 2: Commercial Disputes**
- **Contact:** Commercial Director
- **Response Time:** 4 hours
- **Resolution:** 48 hours

### **Level 3: Legal/Regulatory**
- **Contact:** Legal Counsel
- **Response Time:** 8 hours
- **Resolution:** 72 hours

---

## ğŸ”„ CONTRACT AMENDMENTS

### **Rate Review Cycle**
- **Quarterly Review:** Market rate benchmarking
- **Annual Adjustment:** CPI-linked rate updates
- **Emergency Adjustment:** Force majeure events

### **Amendment Process**
1. **Notification:** 30 days advance notice
2. **Negotiation:** 15 days discussion period
3. **Approval:** Joint committee approval required
4. **Implementation:** 7 days after approval

---

## ğŸ“‹ APPENDICES

### **Appendix A: Contact Information**
- **Samsung C&T:** operations@samsung-ct.ae
- **ADNOC Logistics:** logistics@adnoc.ae
- **DSV Solutions:** uae@dsv.com
- **Emergency Hotline:** +971-2-HVDC-911

### **Appendix B: Regulatory References**
- **FANR Regulation:** FANR-REG-06 (Radioactive Material Transport)
- **MOIAT Guidelines:** MOIAT-TL-2024 (Heavy Transport Permits)
- **UAE Customs:** Federal Law No. 3 of 2006

### **Appendix C: Route Maps**
- Interactive route optimization maps
- Real-time traffic integration
- Weather impact assessments

---

## ğŸ“ DOCUMENT CONTROL

| Field | Value |
|:------|:------|
| **Document ID** | HVDC-ITC-2025-001 |
| **Version** | v1.1 |
| **Created By** | MACHO-GPT v3.4-mini |
| **Approved By** | Samsung C&T Ã— ADNOCÂ·DSV Joint Committee |
| **Effective Date** | 2025-01-01 |
| **Review Date** | 2025-04-01 |
| **Next Update** | 2025-07-01 |
| **Classification** | Commercial Confidential |

---

## ğŸ” DIGITAL SIGNATURES

**Samsung C&T Corporation**  
*Authorized Signatory*  
Date: ___________  

**ADNOC Logistics & Services**  
*Authorized Signatory*  
Date: ___________  

**DSV Solutions UAE**  
*Authorized Signatory*  
Date: ___________  

---

*This document is generated and maintained by MACHO-GPT v3.4-mini Logistics Operations System. All rates and terms are subject to automated validation and real-time market benchmarking.*

ğŸ”§ **ì¶”ì²œ ëª…ë ¹ì–´:**
/invoice_audit [OCR-based invoice validation with FANR/MOIAT compliance]
/rate_benchmark [Real-time market rate comparison and validation]
/route_optimize [Dynamic route optimization with weather and traffic data] 

---

# 🛢 Bulk Cargo Rates (원본 Excel 변환)


---

|   No. | CARGO TYPE   | PORT            | DESTINATION                 | DETAIL CARGO TYPE           |   Min Metric Ton  |   Max Metric Ton  |   Length(meter) |   Width(meter) |   Height(Meter) | Description                             | Unit            | Rates(USD)              | Remark                                                                                                                                                                                                                                          |
|------:|:-------------|:----------------|:----------------------------|:----------------------------|------------------:|------------------:|----------------:|---------------:|----------------:|:----------------------------------------|:----------------|:------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|     1 | Bulk         | Jebel Ali Port  | nan                         | General                     |               nan |               nan |             nan |          nan   |           nan   | Custom Clearance                        | per B/L         | 350                     | * Indicate Charge per B/L (Min 350 USD)                                                                                                                                                                                                         |
|     2 | Bulk         | Jebel Ali Port  | nan                         | General                     |               nan |               nan |             nan |          nan   |           nan   | DO Fee                                  | per B/L         | 150                     | nan                                                                                                                                                                                                                                             |
|     3 | Bulk         | Jebel Ali Port  | nan                         | General                     |               nan |               nan |             nan |          nan   |           nan   | Port Handling Charge                    | per RT          | 8.5                     | Port Handling Charge only. Other charge will be back charged.                                                                                                                                                                                   |
|     4 | Bulk         | Jebel Ali Port  | MIRFA SITE                  | General                     |                 1 |                25 |              12 |            2.5 |             2.5 | Inland Trucking                         | per RT          | 34.5                    | inland-tranporation for Bulk shipment shall be charged by the cargo category defined in the contract regardless of the trailer type. Rate shall be applicable upto 25ton / 12m x 2.5m x 2.5m(LWH) only                                          |
|     5 | Bulk         | Jebel Ali Port  | SHUWEIHAT Site              | General                     |                 1 |                25 |              12 |            2.5 |             2.5 | Inland Trucking                         | per RT          | 44.5                    | inland-tranporation for Bulk shipment shall be charged by the cargo category defined in the contract regardless of the trailer type. Rate shall be applicable upto 25ton / 12m x 2.5m x 2.5m(LWH) only                                          |
|     6 | Bulk         | Jebel Ali Port  | Storage Yard                | General                     |                 1 |                25 |              12 |            2.5 |             2.5 | Inland Trucking                         | per RT          | 15                      | inland-tranporation for Bulk shipment shall be charged by the cargo category defined in the contract regardless of the trailer type. Rate shall be applicable upto 25ton / 12m x 2.5m x 2.5m(LWH) only                                          |
|     7 | Bulk         | Jebel Ali Port  | Hamariya free zone, Sharjah | General                     |                 1 |                25 |              12 |            2.5 |             2.5 | Inland Trucking                         | per RT          | 14                      | inland-tranporation for Bulk shipment shall be charged by the cargo category defined in the contract regardless of the trailer type. Rate shall be applicable upto 25ton / 12m x 2.5m x 2.5m(LWH) only                                          |
|     8 | Bulk         | Jebel Ali Port  | nan                         | General                     |               nan |               nan |             nan |          nan   |           nan   | Inspection Fee                          | per RT          | 125                     | nan                                                                                                                                                                                                                                             |
|     9 | Bulk         | Jebel Ali Port  | nan                         | General                     |                 1 |                25 |              12 |            2.5 |             2.5 | Truck Detention                         | Per Truck, Hour | 52                      | 3hours at POL+ 3 hours at POD non-reversable                                                                                                                                                                                                    |
|    10 | Bulk         | Jebel Ali Port  | nan                         | Overweight & Oversized Heav |               nan |               nan |             nan |          nan   |           nan   | Custom Clearance                        | per B/L         | 350                     | * Indicate Charge per B/L (Min 350 USD)                                                                                                                                                                                                         |
|    11 | Bulk         | Jebel Ali Port  | nan                         | Overweight & Oversized Heav |               nan |               nan |             nan |          nan   |           nan   | DO Fee                                  | per B/L         | 150                     | nan                                                                                                                                                                                                                                             |
|    12 | Bulk         | Jebel Ali Port  | nan                         | Overweight & Oversized Heav |               nan |               nan |             nan |          nan   |           nan   | Port Handling Charge                    | per RT          | 8.5                     | Port Handling Charge only. Other charge will be back charged.                                                                                                                                                                                   |
|    13 | Bulk         | Jebel Ali Port  | MIRFA SITE                  | Overweight & Oversized Heav |                26 |                45 |              14 |            3.5 |             3.5 | Inland Trucking                         | per RT          | 20                      | inland-tranporation for Bulk shipment shall be charged by the cargo category defined in the contract regardless of the trailer type. DSV : Rate shall be applicable from 25ton / 12m x 2.5m x 2.5m(LWH) upto 45ton/14m x 3.5m x 3.5m(LWH) only. |
|    14 | Bulk         | Jebel Ali Port  | SHUWEIHAT Site              | Overweight & Oversized Heav |                26 |                45 |              14 |            3.5 |             3.5 | Inland Trucking                         | per RT          | 25                      | inland-tranporation for Bulk shipment shall be charged by the cargo category defined in the contract regardless of the trailer type. DSV : Rate shall be applicable from 25ton / 12m x 2.5m x 2.5m(LWH) upto 45ton/14m x 3.5m x 3.5m(LWH) only. |
|    15 | Bulk         | Jebel Ali Port  | Storage Yard                | Overweight & Oversized Heav |                26 |                45 |              14 |            3.5 |             3.5 | Inland Trucking                         | per RT          | 19                      | inland-tranporation for Bulk shipment shall be charged by the cargo category defined in the contract regardless of the trailer type. DSV : Rate shall be applicable from 25ton / 12m x 2.5m x 2.5m(LWH) upto 45ton/14m x 3.5m x 3.5m(LWH) only. |
|    16 | Bulk         | Jebel Ali Port  | Hamariya free zone, Sharjah | Overweight & Oversized Heav |                26 |                45 |              14 |            3.5 |             3.5 | Inland Trucking                         | per RT          | 19                      | inland-tranporation for Bulk shipment shall be charged by the cargo category defined in the contract regardless of the trailer type. DSV : Rate shall be applicable from 25ton / 12m x 2.5m x 2.5m(LWH) upto 45ton/14m x 3.5m x 3.5m(LWH) only. |
|    17 | Bulk         | Jebel Ali Port  | nan                         | Overweight & Oversized Heav |               nan |               nan |             nan |          nan   |           nan   | Inspection Fee                          | per RT          | 125                     | nan                                                                                                                                                                                                                                             |
|    18 | Bulk         | Jebel Ali Port  | nan                         | Overweight & Oversized Heav |                26 |                45 |              14 |            3.5 |             3.5 | Truck Detention                         | Per Truck, Hour | 104.5                   | 3hours at POL+ 3 hours at POD non-reversable                                                                                                                                                                                                    |
|    19 | Bulk         | Jebel Ali Port  | nan                         | nan                         |               nan |               nan |             nan |          nan   |           nan   | Port Storage Charge at Discharging Port | nan             | At cost                 | * Indicate days of free time                                                                                                                                                                                                                    |
|    20 | Bulk         | Mina Zayed Port | nan                         | 20FT(Including OT/FR)       |               nan |               nan |             nan |          nan   |           nan   | Custom Clearance                        | per B/L         | 150                     | * Indicate Charge per B/L (Min 125 USD)                                                                                                                                                                                                         |
|    21 | Bulk         | Mina Zayed Port | nan                         | 20FT(Including OT/FR)       |               nan |               nan |             nan |          nan   |           nan   | DO Fee                                  | per B/L         | 150                     | nan                                                                                                                                                                                                                                             |
|    22 | Bulk         | Mina Zayed Port | nan                         | 40FT(In Gauge)              |               nan |               nan |             nan |          nan   |           nan   | Port Handling Charge                    | per RT          | 7.1                     | Incl. all other surcharges related port handling                                                                                                                                                                                                |
|    23 | Bulk         | Mina Zayed Port | MIRFA SITE                  | 40FT(In Gauge)              |                 1 |                25 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 21                      | inland-tranporation for Bulk shipment shall be charged by the cargo category defined in the contract regardless of the trailer type.                                                                                                            |
|    24 | Bulk         | Mina Zayed Port | SHUWEIHAT Site              | 40FT(In Gauge)              |                 1 |                25 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 25                      | nan                                                                                                                                                                                                                                             |
|    25 | Bulk         | Mina Zayed Port | Storage Yard                | 40FT(In Gauge)              |                 1 |                25 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 8.4                     | nan                                                                                                                                                                                                                                             |
|    26 | Bulk         | Mina Zayed Port | nan                         | 40FT(In Gauge)              |               nan |               nan |             nan |          nan   |           nan   | Inspection Fee                          | per RT          | 125                     | nan                                                                                                                                                                                                                                             |
|    27 | Bulk         | Mina Zayed Port | nan                         | 40FT(In Gauge)              |                 1 |                25 |              12 |            3   |             3   | Truck Detention                         | Per Truck, Hour | 52                      | 6 hours Free-time at job site after arrival                                                                                                                                                                                                     |
|    28 | Bulk         | Mina Zayed Port | nan                         | 40FT(In Gauge)              |               nan |               nan |             nan |          nan   |           nan   | Custom Clearance                        | per B/L         | 150                     | * Indicate Charge per B/L (Min 125 USD)                                                                                                                                                                                                         |
|    29 | Bulk         | Mina Zayed Port | nan                         | 40FT(In Gauge)              |               nan |               nan |             nan |          nan   |           nan   | DO Fee                                  | per B/L         | 150                     | nan                                                                                                                                                                                                                                             |
|    30 | Bulk         | Mina Zayed Port | nan                         | 40FT(In Gauge)              |               nan |               nan |             nan |          nan   |           nan   | Port Handling Charge                    | per RT          | 7.8                     | Incl. all other surcharges related port handling                                                                                                                                                                                                |
|    31 | Bulk         | Mina Zayed Port | MIRFA SITE                  | 40FT(In Gauge)              |                26 |                60 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 11.6                    | inland-tranporation for Bulk shipment shall be charged by the cargo category defined in the contract regardless of the trailer type.                                                                                                            |
|    32 | Bulk         | Mina Zayed Port | SHUWEIHAT Site              | 40FT(In Gauge)              |                26 |                60 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 13.1                    | nan                                                                                                                                                                                                                                             |
|    33 | Bulk         | Mina Zayed Port | Storage Yard                | 40FT(In Gauge)              |                26 |                60 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 10.5                    | nan                                                                                                                                                                                                                                             |
|    34 | Bulk         | Mina Zayed Port | nan                         | 40FT(In Gauge)              |               nan |               nan |             nan |          nan   |           nan   | Inspection Fee                          | per RT          | 125                     | nan                                                                                                                                                                                                                                             |
|    35 | Bulk         | Mina Zayed Port | nan                         | 40FT(In Gauge)              |                26 |                60 |              12 |            3   |             3   | Truck Detention                         | Per Truck, Hour | 104.5                   | 6 hours Free-time at job site after arrival                                                                                                                                                                                                     |
|    36 | Bulk         | Mina Zayed Port | nan                         | Light Heavy                 |               nan |               nan |             nan |          nan   |           nan   | Custom Clearance                        | per B/L         | 150                     | * Indicate Charge per B/L (Min 125 USD)                                                                                                                                                                                                         |
|    37 | Bulk         | Mina Zayed Port | nan                         | Light Heavy                 |               nan |               nan |             nan |          nan   |           nan   | DO Fee                                  | per B/L         | 150                     | nan                                                                                                                                                                                                                                             |
|    38 | Bulk         | Mina Zayed Port | nan                         | Light Heavy                 |               nan |               nan |             nan |          nan   |           nan   | Port Handling Charge                    | per RT          | 7.8                     | Incl. all other surcharges related port handling                                                                                                                                                                                                |
|    39 | Bulk         | Mina Zayed Port | MIRFA SITE                  | Light Heavy                 |                61 |               150 |             nan |          nan   |           nan   | Inland Trucking                         | per RT          | 28.2                    | nan                                                                                                                                                                                                                                             |
|    40 | Bulk         | Mina Zayed Port | SHUWEIHAT Site              | Light Heavy                 |                61 |               150 |             nan |          nan   |           nan   | Inland Trucking                         | per RT          | 34.7                    | nan                                                                                                                                                                                                                                             |
|    41 | Bulk         | Mina Zayed Port | Storage Yard                | Light Heavy                 |                61 |               150 |             nan |          nan   |           nan   | Inland Trucking                         | per RT          | 23.8                    | nan                                                                                                                                                                                                                                             |
|    42 | Bulk         | Mina Zayed Port | nan                         | Light Heavy                 |               nan |               nan |             nan |          nan   |           nan   | Inspection Fee (If required)            | per RT          | At Cost                 | nan                                                                                                                                                                                                                                             |
|    43 | Bulk         | Mina Zayed Port | nan                         | Light Heavy                 |                61 |               150 |             nan |          nan   |           nan   | Truck Detention                         | Per Axle, Hour  | 104.5                   | 6 hours Free-time at job site after arrival                                                                                                                                                                                                     |
|    44 | Bulk         | Mina Zayed Port | nan                         | Heavy                       |               nan |               nan |             nan |          nan   |           nan   | Custom Clearance                        | per B/L         | 150                     | * Indicate Charge per B/L (Min 125 USD)                                                                                                                                                                                                         |
|    45 | Bulk         | Mina Zayed Port | nan                         | Heavy                       |               nan |               nan |             nan |          nan   |           nan   | DO Fee                                  | per B/L         | 150                     | nan                                                                                                                                                                                                                                             |
|    46 | Bulk         | Mina Zayed Port | nan                         | Heavy                       |               nan |               nan |             nan |          nan   |           nan   | Port Handling Charge                    | per RT          | 12                      | Incl. all other surcharges related port handling                                                                                                                                                                                                |
|    47 | Bulk         | Mina Zayed Port | MIRFA SITE                  | Heavy                       |               151 |               300 |             nan |          nan   |           nan   | Inland Trucking                         | per RT          | Case by Case            | nan                                                                                                                                                                                                                                             |
|    48 | Bulk         | Mina Zayed Port | SHUWEIHAT Site              | Heavy                       |               151 |               300 |             nan |          nan   |           nan   | Inland Trucking                         | per RT          | Case by Case            | nan                                                                                                                                                                                                                                             |
|    49 | Bulk         | Mina Zayed Port | Storage Yard                | Heavy                       |               151 |               300 |             nan |          nan   |           nan   | Inland Trucking                         | per RT          | Case by Case            | nan                                                                                                                                                                                                                                             |
|    50 | Bulk         | Mina Zayed Port | nan                         | Heavy                       |               nan |               nan |             nan |          nan   |           nan   | Inspection Fee (If required)            | per RT          | At Cost                 | nan                                                                                                                                                                                                                                             |
|    51 | Bulk         | Mina Zayed Port | nan                         | Heavy                       |               151 |               300 |             nan |          nan   |           nan   | Truck Detention                         | Per Axle, Hour  | 104.5                   | 6 hours Free-time at job site after arrival                                                                                                                                                                                                     |
|    52 | Bulk         | Mina Zayed Port | nan                         | nan                         |               nan |               nan |             nan |          nan   |           nan   | Port Storage Charge at Discharging Port | nan             | At Cost after free time | * Indicate days of free time                                                                                                                                                                                                                    |
|    53 | Bulk         | Musaffah Port   | nan                         | General                     |               nan |               nan |             nan |          nan   |           nan   | Custom Clearance                        | per B/L         | 150                     | * Indicate Charge per B/L (Min 125 USD)                                                                                                                                                                                                         |
|    54 | Bulk         | Musaffah Port   | nan                         | General                     |               nan |               nan |             nan |          nan   |           nan   | DO Fee                                  | per B/L         | 150                     | nan                                                                                                                                                                                                                                             |
|    55 | Bulk         | Musaffah Port   | nan                         | General                     |               nan |               nan |             nan |          nan   |           nan   | Port Handling Charge                    | per RT          | 7.1                     | Incl. all other surcharges related port handling                                                                                                                                                                                                |
|    56 | Bulk         | Musaffah Port   | MIRFA SITE                  | General                     |                 1 |                25 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 18.4                    | nan                                                                                                                                                                                                                                             |
|    57 | Bulk         | Musaffah Port   | SHUWEIHAT Site              | General                     |                 1 |                25 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 22.2                    | nan                                                                                                                                                                                                                                             |
|    58 | Bulk         | Musaffah Port   | Storage Yard                | General                     |                 1 |                25 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 5.2                     | nan                                                                                                                                                                                                                                             |
|    59 | Bulk         | Musaffah Port   | nan                         | General                     |               nan |               nan |             nan |          nan   |           nan   | Inspection Fee (If required)            | per RT          | At Cost                 | nan                                                                                                                                                                                                                                             |
|    60 | Bulk         | Musaffah Port   | nan                         | General                     |                 1 |                25 |              12 |            3   |             3   | Truck Detention                         | Per Truck, Hour | 52.3                    | 6 hours Free-time at job site after arrival                                                                                                                                                                                                     |
|    61 | Bulk         | Musaffah Port   | nan                         | Overweight & Oversized Heav |               nan |               nan |             nan |          nan   |           nan   | Custom Clearance                        | per B/L         | 150                     | * Indicate Charge per B/L (Min 125 USD)                                                                                                                                                                                                         |
|    62 | Bulk         | Musaffah Port   | nan                         | Overweight & Oversized Heav |               nan |               nan |             nan |          nan   |           nan   | DO Fee                                  | per B/L         | 150                     | nan                                                                                                                                                                                                                                             |
|    63 | Bulk         | Musaffah Port   | nan                         | Overweight & Oversized Heav |               nan |               nan |             nan |          nan   |           nan   | Port Handling Charge                    | per RT          | 7.8                     | Incl. all other surcharges related port handling                                                                                                                                                                                                |
|    64 | Bulk         | Musaffah Port   | MIRFA SITE                  | Overweight & Oversized Heav |                26 |                60 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 10.5                    | nan                                                                                                                                                                                                                                             |
|    65 | Bulk         | Musaffah Port   | SHUWEIHAT Site              | Overweight & Oversized Heav |                26 |                60 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 11.9                    | nan                                                                                                                                                                                                                                             |
|    66 | Bulk         | Musaffah Port   | Storage Yard                | Overweight & Oversized Heav |                26 |                60 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 6.3                     | nan                                                                                                                                                                                                                                             |
|    67 | Bulk         | Musaffah Port   | nan                         | Overweight & Oversized Heav |               nan |               nan |             nan |          nan   |           nan   | Inspection Fee (If required)            | per RT          | At Cost                 | nan                                                                                                                                                                                                                                             |
|    68 | Bulk         | Musaffah Port   | nan                         | Overweight & Oversized Heav |                26 |                60 |              12 |            3   |             3   | Truck Detention                         | Per Truck, Hour | 110                     | 6 hours Free-time at job site after arrival                                                                                                                                                                                                     |
|    69 | Bulk         | Musaffah Port   | nan                         | nan                         |               nan |               nan |             nan |          nan   |           nan   | Port Storage Charge at Discharging Port | nan             | At Cost after free time | * Indicate days of free time                                                                                                                                                                                                                    |
|    70 | Bulk         | Khalifa Port    | nan                         | General                     |               nan |               nan |             nan |          nan   |           nan   | Custom Clearance                        | per B/L         | 150                     | * Indicate Charge per B/L (Min 125 USD)                                                                                                                                                                                                         |
|    71 | Bulk         | Khalifa Port    | nan                         | General                     |               nan |               nan |             nan |          nan   |           nan   | DO Fee                                  | per B/L         | 150                     | nan                                                                                                                                                                                                                                             |
|    72 | Bulk         | Khalifa Port    | nan                         | General                     |               nan |               nan |             nan |          nan   |           nan   | Port Handling Charge                    | per RT          | 7.1                     | Incl. all other surcharges related port handling                                                                                                                                                                                                |
|    73 | Bulk         | Khalifa Port    | MIRFA SITE                  | General                     |                 1 |                25 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 24.2                    | nan                                                                                                                                                                                                                                             |
|    74 | Bulk         | Khalifa Port    | SHUWEIHAT Site              | General                     |                 1 |                25 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 29.2                    | nan                                                                                                                                                                                                                                             |
|    75 | Bulk         | Khalifa Port    | Storage Yard                | General                     |                 1 |                25 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 10.5                    | nan                                                                                                                                                                                                                                             |
|    76 | Bulk         | Khalifa Port    | nan                         | General                     |               nan |               nan |             nan |          nan   |           nan   | Inspection Fee (If required)            | per RT          | At Cost                 | nan                                                                                                                                                                                                                                             |
|    77 | Bulk         | Khalifa Port    | nan                         | General                     |                 1 |                25 |              12 |            3   |             3   | Truck Detention                         | Per Truck, Hour | 52.3                    | 6 hours Free-time at job site after arrival                                                                                                                                                                                                     |
|    78 | Bulk         | Khalifa Port    | nan                         | Overweight & Oversized Heav |               nan |               nan |             nan |          nan   |           nan   | Custom Clearance                        | per B/L         | 150                     | * Indicate Charge per B/L (Min 125 USD)                                                                                                                                                                                                         |
|    79 | Bulk         | Khalifa Port    | nan                         | Overweight & Oversized Heav |               nan |               nan |             nan |          nan   |           nan   | DO Fee                                  | per B/L         | 150                     | nan                                                                                                                                                                                                                                             |
|    80 | Bulk         | Khalifa Port    | nan                         | Overweight & Oversized Heav |               nan |               nan |             nan |          nan   |           nan   | Port Handling Charge                    | per RT          | 7.8                     | Incl. all other surcharges related port handling                                                                                                                                                                                                |
|    81 | Bulk         | Khalifa Port    | MIRFA SITE                  | Overweight & Oversized Heav |                26 |                60 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 13.4                    | nan                                                                                                                                                                                                                                             |
|    82 | Bulk         | Khalifa Port    | SHUWEIHAT Site              | Overweight & Oversized Heav |                26 |                60 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 15.2                    | nan                                                                                                                                                                                                                                             |
|    83 | Bulk         | Khalifa Port    | Storage Yard                | Overweight & Oversized Heav |                26 |                60 |              12 |            3   |             3   | Inland Trucking                         | per RT          | 12.4                    | nan                                                                                                                                                                                                                                             |
|    84 | Bulk         | Khalifa Port    | nan                         | Overweight & Oversized Heav |               nan |               nan |             nan |          nan   |           nan   | Inspection Fee (If required)            | per RT          | At Cost                 | nan                                                                                                                                                                                                                                             |
|    85 | Bulk         | Khalifa Port    | nan                         | Overweight & Oversized Heav |                26 |                60 |              12 |            3   |             3   | Truck Detention                         | Per Truck, Hour | 104.5                   | 6 hours Free-time at job site after arrival                                                                                                                                                                                                     |
|    86 | Bulk         | Khalifa Port    | nan                         | nan                         |               nan |               nan |             nan |          nan   |           nan   | Port Storage Charge at Discharging Port | nan             | At Cost after free time | * Indicate days of free time                                                                                                                                                                                                                    |
# APEX GLOBAL MULTI-ASSET CREDIT & EQUITY FUND
## INVESTMENT POLICY STATEMENT & MANDATE (SEC FORM N-1A / STATEMENT OF ADDITIONAL INFORMATION EXCERPT)
**Document ID:** `IPS-APEX-2026-V4`  
**Effective Date:** `2026-01-01`  
**Governing Regulatory Framework:** Investment Company Act of 1940 (Rule 35d-1 & Rule 206(4)-7 Compliance Program)  
**Fund Base Currency:** `USD`  
**Current Audited Net Asset Value (NAV):** `$100,000,000.00`

---

### ARTICLE I — DEFINITIONS & INTERPRETIVE RULES

* **Section 1.01 ("Net Asset Value" or "NAV"):** Means the total net asset value of the Fund calculated as of the immediately preceding business day's close. All percentage limitations in this Mandate apply on a **Post-Trade Pro-Forma Basis** (`(Current Holding Market Value + Proposed Trade Market Value) / Total Fund NAV`).
* **Section 1.02 ("Investment Grade"):** Means a security rated at least `BBB-` by Standard & Poor's (S&P) or Fitch, or at least `Baa3` by Moody's Investors Service.
* **Section 1.03 ("High Yield" or "Below-Investment-Grade"):** Means any debt security rated below `BBB-` (S&P/Fitch) or below `Baa3` (Moody's), or unrated securities deemed equivalent by the Adviser.
* **Section 1.04 ("Single-Issuer Group" / Parent-Subsidiary Aggregation):** For all concentration limits under Article III, holdings issued by a parent corporation and all of its majority-owned subsidiaries or guaranteed affiliates (sharing the same `ultimate_parent_id` in the Fund's security master) **must be aggregated and treated as a single issuer**.
* **Section 1.05 ("Eligible OECD Sovereign"):** Means the central government or central bank of a country that is a full member of the Organisation for Economic Co-operation and Development (OECD) as of the trade date (including, without limitation, the United States, United Kingdom, Japan, Germany, France, and Canada).

---

### ARTICLE II — CREDIT QUALITY & SPLIT-RATING RULES

* **Section 2.01 (Aggregate High-Yield Ceiling):** The Fund may invest no more than **15.00% of its total NAV** in aggregate across all High Yield (Below-Investment-Grade) debt securities.
* **Section 2.02 (Split-Rated Securities Rule):**
  * **(a)** If a security is rated by both S&P and Moody's and both ratings fall within Investment Grade, it is classified as Investment Grade.
  * **(b)** If a security is **split-rated** between S&P and Moody's (where one agency assigns an Investment Grade rating of `BBB-`/`Baa3` or higher, and the other agency assigns a High Yield rating of `BB+`/`Ba1` or lower), **the higher of the two ratings shall govern** for purposes of determining whether the security counts as Investment Grade under Section 2.01 and Section 3.02.
  * **(c)** Notwithstanding Section 2.02(b), any security rated `CCC+` / `Caa1` or lower by *any* rating agency is strictly prohibited from purchase.

---

### ARTICLE III — CONCENTRATION & SECTOR LIMITS

* **Section 3.01 (Single-Issuer Concentration Limit):**
  * **(a) Standard Limit:** No proposed purchase may cause the Fund's total exposure to any single issuer to exceed **5.00% of total Fund NAV** on a post-trade basis.
  * **(b) Affiliated Group Limit:** Pursuant to Section 1.04, the **5.00% of total Fund NAV** limit applies to the combined market value of all securities sharing the same `ultimate_parent_id`.
* **Section 3.02 (Sector & High-Yield Sub-Limits):**
  * **(a) Broad Sector Limit:** No single GICS sector may exceed **25.00% of total Fund NAV**.
  * **(b) High-Yield Energy Sub-Cap:** Aggregate holdings in **High Yield (Below-Investment-Grade) issuers within the `Energy` sector** shall not exceed **5.00% of total Fund NAV** on a post-trade basis.
* **Section 3.03 (Passive Market-Drift Cure Provision vs. Active Additions):**
  * If a holding or Single-Issuer Group exceeds the `5.00%` limit solely due to passive market price appreciation or NAV fluctuations ("Passive Drift"), the Fund is **not** required to forcibly liquidate the existing position. However, **zero incremental active purchases (`BUY` orders of any dollar amount)** may be executed in that issuer or Single-Issuer Group while its post-trade exposure remains above `5.00%` of NAV.

---

### ARTICLE IV — CURRENCY & FOREIGN EXCHANGE RESTRICTIONS

* **Section 4.01 (Non-USD Currency Exposure):**
  * **(a) General Hedging Requirement:** All non-USD denominated corporate and municipal securities must be `100% currency-hedged` back to `USD` at the time of trade execution (`is_fx_hedged = true`). Unhedged non-USD corporate debt purchases are prohibited.
  * **(b) Eligible OECD Sovereign Carve-Out:** By way of exception to Section 4.01(a), the Fund may purchase **unhedged (`is_fx_hedged = false`) non-USD debt securities** provided that:
    1. The security is a direct sovereign obligation (`asset_class = "SOVEREIGN_BOND"`) of an **Eligible OECD Sovereign** (as defined in Section 1.05); AND
    2. Total unhedged non-USD sovereign exposure across the entire Fund does not exceed **10.00% of total Fund NAV** post-trade.

---

### ARTICLE V — ESG, SANCTIONS & RESTRICTED ACTIVITIES

* **Section 5.01 (Thermal Coal & Controversial Weapons Exclusions):**
  * **(a) Hard Revenue Threshold:** The Fund shall not purchase securities of any issuer that derives **more than 10.00% of its gross annual revenue** directly from thermal coal extraction (`thermal_coal_revenue_pct > 10.0`).
  * **(b) Qualitative Infrastructure Ambiguity Clause:** The Fund shall also avoid issuers that are *"substantially dependent on dedicated thermal coal transport or captive coal-fired logistics infrastructure,"* as determined by the Compliance Committee upon review of underlying freight revenue disclosures.
* **Section 5.02 (Sanctions & Look-Through Obligation):**
  * The Fund is strictly prohibited from acquiring direct or indirect economic exposure (including via Special Purpose Vehicles (`SPVs`), Credit-Linked Notes (`CLNs`), or total return swaps) to any entity subject to OFAC/EU sanctions. Where a security is issued by a pass-through SPV or orphan trust without transparent look-through reference data in the security master, automated systems **must abstain and escalate to Human Compliance Review** prior to execution.


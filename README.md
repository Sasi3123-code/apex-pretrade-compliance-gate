# 🛡️ Apex Pre-Trade Compliance Gate & Firm P&L Protection

**Tresata Take-Home Assignment — Prototype, 10-Case Evaluation Suite & 5-Page Written Brief**  
**Author:** Darla Venkata Sasi Kumar (IIT Madras, Engineering Physics | `EP23B026`)  
**Jurisdiction Covered:** United States — SEC Investment Company Act of 1940 (`Rule 206(4)-7` & `Rule 35d-1`, SEC Forms `N-1A` & `N-PORT`)  
**Headline Impact:** **+$375,500 Saved · $0 Out-of-Pocket Loss Paid by the Firm** (across $10.70M of screened orders)

---

## 1. Why This Problem Matters in Plain Dollars (`SEC Rule 206(4)-7`)

Before an institutional credit or multi-asset fund executes a proposed trade order, compliance must verify that the **post-trade portfolio** obeys every concentration cap, parent-company aggregation rule, split credit rating tie-breaker, foreign currency rule, and footnote restriction in the fund's rulebook (**Investment Policy Statement / SEC Form N-1A**).

> **Why It Matters:** If a bad trade slips through and gets executed, the fund breaks **SEC Rule 206(4)-7**. The fund is forced to undo (unwind) the trade in the open market, and **the investment firm has to pay for any resulting losses out of its own pocket** — typically **$30,000 to $500,000+ per trade error** in bid-ask slippage, swap termination penalties, and regulatory remediation fees.

### Why Neither SQL Rules Alone Nor Raw LLMs Work:
- **Why SQL / Database Rules Fail on Their Own:** Standard database checks sum numeric columns well, but they cannot read a 3-sentence deal footnote disclosing that a rail company gets `22%` of its revenue from mixed coal freight corridors (`TC-09`) or that an `A-` rated Cayman Islands trust is an orphan SPV backed by an undisclosed oil-and-gas swap basket (`TC-10`).
- **Why a Single-Call LLM Fails on Its Own:** Dumping `75,000+` holdings rows into an LLM prompt burns `~3.6M tokens`, exposes private custodian bank codes, misses parent-subsidiary corporate links (`ultimate_parent_id`, such as knowing NextEra Energy owns Florida Power & Light in `TC-03`), and fumbles basis-point math.

---

## 2. How Our 4-Step Hybrid Pipeline Works

Our architecture keeps **exact portfolio math** and **probabilistic footnote reading** strictly separate:

```text
[Proposed Trade Order + Deal Footnotes]        [Settled $100M Portfolio (N-PORT) + YAML Schema]
                   │                                                  │
                   ▼                                                  ▼
  ┌──────────────────────────────────────────┐      ┌──────────────────────────────────────────┐
  │ Step 1: Rulebook Search (src/retriever)  │      │ Step 2: Exact Limit Calculator (No AI)   │
  │ • Hybrid BM25 + TF-IDF keyword search    │      │ • Strips private account cols (99.993%   │
  │ • Auto-follows linked definitions        │      │   token reduction via fund_schema.yaml)  │
  │   (e.g., Sec 3.01 -> Sec 1.04)           │      │ • Exact Parent-Group, Split-Rating       │
  │ • Saves exact [char_start..char_end]     │      │   (Sec 2.02b) & FX carve-out math        │
  └────────────────────┬─────────────────────┘      └────────────────────┬─────────────────────┘
                       └───────────────────────┬─────────────────────────┘
                                               ▼
                     ┌──────────────────────────────────────────────────┐
                     │ Step 3: Deal Footnote Reader (OpenRouter LLM)    │
                     │ • Reads unstructured deal supplement notes       │
                     │ • Flags coal freight (5.01b) & SPV swaps (5.02)  │
                     │ • Never touches or overrides portfolio math      │
                     └─────────────────────────┬────────────────────────┘
                                               ▼
                     ┌──────────────────────────────────────────────────┐
                     │ Step 4: Final Safety Lock & Quote Verifier       │
                     │ • Verifies exact substring quote in rulebook     │
                     │ • AI can NEVER downgrade a Step 2 math BREACH    │
                     │ • Routes gray areas to Officer Sign-Off Queue    │
                     └────────────┬─────────────────────────┬───────────┘
                                  ▼                         ▼
                        [APPROVED / BLOCKED]      [HELD FOR OFFICER REVIEW]
```

---

## 3. The 4 Interactive Dashboards (`app.py` — Warm Electric Orange Edition)

Modeled on the **AEGIS** visual language and **Emil Kowalski's** design engineering principles, `app.py` presents 100% plain-English business insights across four dedicated dashboards:

1. **`01 · Pre-Trade Gate`:** Features the signature **"Needs You" Split-Card** with `30px` tabular numerals (*Before trade -> After trade*), a **2-segment overshoot bar** highlighting the exact red breach segment past the limit tick mark, a 4-step pulsing checkpoint stepper, a conic-gradient score ring, line-by-line rule verification, and a What-If simulator.
2. **`02 · Losses vs. Savings`:** Executive P&L protection dashboard comparing **Without Pre-Trade Gate (-$277,500 loss/cost)** vs. **With Our Gate ($0 loss paid · +$375,500 saved)**, breaking savings down across forced unwind slippage avoided (`+$167,000`), false alarms prevented (`+$166,500`), and SEC review fees saved (`+$42,000`).
3. **`03 · All Activity & Protection`:** Visual Bento grid across all 10 screened orders (`$10.70M` screened: `$3.90M` safely executed vs. `$6.80M` stopped/held), with an outcome donut ring, interactive decision filters, inline SVG icons, and per-trade P&L strips.
4. **`04 · Fund Portfolio ($100M)`:** Displays the `$100.0M` settled Form N-PORT portfolio (`$82.35M` invested across 12 positions + `$17.65M` cash) with parent-group concentration bars, `5.00%` limit markers, and passive market-drift tracking (`NVIDIA` at `5.15%`).

---

## 4. Quickstart & How to Run (Works Out-of-the-Box Without an API Key)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Launch the 4-Dashboard App Immediately (Zero API Key Required)
```bash
python -m streamlit run app.py
```
> **Note on API Keys:** You do **not** need an OpenRouter API key to run `app.py`, `evaluate_10_cases.py`, or the unit tests. When no `.env` file is present, the system automatically runs its full deterministic retrieval, parent-group math, and grounding verification pipeline offline (and includes recorded live OpenRouter benchmark runs in `data/evaluation_results_10.json`).  
> If you want to test live OpenRouter LLM calls, copy `.env.example` to `.env` and add a free key from [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys):
> ```env
> OPENROUTER_API_KEY=sk-or-v1-your-key-here
> OPENROUTER_MODEL=openrouter/free
> ```

### Step 3: Run Automated Unit Tests
```bash
python -m tests.test_compliance_engine
```

### Step 4: Run the 10-Case Evaluation Benchmark or Regenerate the 5-Page PDF
```bash
python evaluate_10_cases.py
python generate_brief_pdf.py
```

---

## 5. Repository Structure

```text
├── app.py                          # Interactive 4-Dashboard Streamlit App (AEGIS + Emil Kowalski Orange Edition)
├── evaluate_10_cases.py            # CLI benchmark runner across all 10 trades (works with or without API key)
├── generate_brief_pdf.py           # ReportLab script generating the humanized 5-Page Written Brief PDF
├── TRESATA_WRITTEN_BRIEF.pdf       # Final 5-Page Written Brief (Pages 1-4) + One-Page Appendix (Page 5)
├── TRESATA_WRITTEN_BRIEF.md        # Markdown version of the 5-Page Written Brief + Appendix
├── DESIGN_SYSTEM.md                # UI/UX Design System specification
├── requirements.txt                # Python dependencies
├── .env.example                    # Optional template for OpenRouter free-tier API key
├── data/
│   ├── fund_mandate_ips.md         # Governing Fund Mandate (IPS-APEX-2026-V4, Articles I-V)
│   ├── fund_schema.yaml            # Schema-pruning config (99.993% token reduction)
│   ├── holdings_nport.json         # Settled $100M NAV portfolio positions (SEC Form N-PORT schema)
│   ├── test_cases_10.json          # 10 realistic pre-trade test cases with ground-truth rationales
│   └── evaluation_results_10.json  # Recorded empirical results from live OpenRouter API execution
├── src/
│   ├── retriever.py                # Hybrid BM25 + TF-IDF Cosine + 1-Hop Cross-Reference Graph Retriever
│   ├── deterministic_engine.py     # Schema-Pruned Context Compiler & Deterministic Compliance Calculator
│   └── agent_graph.py              # 4-Node Stateful Orchestrator + OpenRouter Client + Safety Critic
└── tests/
    └── test_compliance_engine.py   # Automated unit tests (10/10 deterministic & retrieval verification)
```

---

## 6. Summary of the 10 Screened Trade Scenarios (`+$375,500` Saved)

| ID | Company & Proposed Order | Basic Check | Our Gate | Loss (No Gate) | Money Saved | Why It Matters |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`TC-01`** | **Microsoft Corp** — Buy `$1.20M` AAA Bond | `APPROVED` | **`APPROVED`** | `$0` | `$0` | Clean trade; exposure moves `3.10% -> 4.30%` (`<= 5.00%` cap). |
| **`TC-02`** | **Apple Inc** — Buy `$1.25M` AA+ Bond | `BLOCKED` | **`BLOCKED`** | `$0` | **`+$45,000`** | Direct company breach (`4.20% -> 5.45% > 5.00%`); saves unwind slippage & fees. |
| **`TC-03`** | **Florida Power & Light** — Buy `$1.30M` Bond | `APPROVED` *(Miss!)* | **`BLOCKED`** | **`-$68,000`** | **`+$68,000`** | `0%` direct holding, but parent **NextEra Energy** hits `5.40% > 5.00%`. |
| **`TC-04`** | **Ford Motor Credit** — Buy `$1.50M` Split-Rated Bond | `BLOCKED` *(False!)* | **`APPROVED`** | **`-$82,500`** | **`+$82,500`** | Split-rated `BBB- / Ba1`; higher rating (`BBB-`) wins under Sec 2.02(b), preventing a costly false alarm. |
| **`TC-05`** | **Permian Resources** — Buy `$700k` BB Energy Bond | `APPROVED` *(Miss!)* | **`BLOCKED`** | **`-$34,000`** | **`+$34,000`** | Total High-Yield is `14.90% <= 15%`, but **High-Yield Energy** hits `5.20% > 5.00%` sub-limit. |
| **`TC-06`** | **UK Treasury Gilt** — Buy `$1.20M` GBP Gov Bond | `APPROVED` | **`APPROVED`** | `$0` | `$0` | Qualifies for Sec 4.01(b) unhedged OECD government bond carve-out (`8.70% <= 10%`). |
| **`TC-07`** | **Siemens AG** — Buy `$1.00M` Unhedged EUR Bond | `BLOCKED` | **`BLOCKED`** | `$0` | **`+$38,000`** | OECD currency carve-out applies only to government bonds, not corporate bonds. |
| **`TC-08`** | **NVIDIA Corp** — Buy `$50k` Stock Above 5% Drift | `BLOCKED` | **`BLOCKED`** | `$0` | **`+$15,000`** | Holding `5.15%` passive stock appreciation is legal (Sec 3.03), but any active `BUY` is banned. |
| **`TC-09`** | **Heartland Rail** — Buy `$1.00M` Bond (Coal Footnote) | `APPROVED` *(Miss!)* | **`HELD (CCO)`** | **`-$41,000`** | **`+$41,000`** | Direct coal is `4.2% <= 10%`, but footnote discloses `22%` mixed coal rail freight (Sec 5.01b). |
| **`TC-10`** | **Cayman Emerald Trust** — Buy `$1.50M` SPV Note | `APPROVED` *(Miss!)* | **`HELD (CCO)`** | **`-$52,000`** | **`+$52,000`** | Footnote reveals orphan SPV backed by an undisclosed oil & gas total return swap basket (Sec 5.02). |

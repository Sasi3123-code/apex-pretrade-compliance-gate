# 🛡️ Apex Pre-Trade Compliance Gate — Investment Mandate Enforcement & Compliance Controls

**Tresata Take-Home Assignment — Prototype, 10-Case Evaluation Suite & 5-Page Written Brief**  
**Author:** Darla Venkata Sasi Kumar (IIT Madras, Engineering Physics | `EP23B026`)  
**Regulatory & Domain Context:** Institutional Fund Investment Policy Statements (`IPS`), SEC Rule `206(4)-7` (under the Investment Advisers Act of 1940), SEC Rule `38a-1` (under the Investment Company Act of 1940), and SEC Forms `N-1A` & `N-PORT`  
**Headline Impact:** **2 Unsafe Approvals Caught · 1 False Block Fixed · 2 Gray Areas Escalated** (`+$184,500` direct incremental loss/cost avoided over basic checks + `$93,000` ambiguous exposure held for CCO review + `$98,000` baseline breaches caught by both)

---

## 1. Why Pre-Trade Mandate Enforcement Matters

Before an institutional credit or multi-asset fund executes a proposed trade order, compliance must verify that the **post-trade portfolio** obeys every concentration cap, parent-company aggregation rule, split credit rating tie-breaker, foreign currency rule, and footnote restriction in the fund's **Investment Policy Statement (IPS)** and registration disclosures (**SEC Form N-1A**).

> **Regulatory & Financial Context:** If a trade violates the fund's investment mandate, it can create a mandate breach, trigger costly trade unwinding and remediation, and expose the adviser to compliance and fiduciary risks (including reimbursing the fund for resulting unwind losses). The firm's compliance program — including its written controls under **SEC Rule 206(4)-7** (under the Investment Advisers Act of 1940 for registered investment advisers) and **SEC Rule 38a-1** (under the Investment Company Act of 1940 for registered investment companies) — must be designed to prevent, detect, and address such mandate violations before execution.

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
  │ Step 1: Mandate Search (src/retriever)   │      │ Step 2: Exact Limit Calculator (No AI)   │
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
                     │ • Verifies exact substring quote in mandate      │
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
2. **`02 · Losses vs. Savings`:** Reconciled financial attribution dashboard separating **Incremental Value Added by Our Gate (`+$184,500` realized across `TC-03`, `TC-04`, `TC-05`)** from **Ambiguous Exposure Held for CCO Review (`$93,000` in `TC-09`, `TC-10`)** and **Baseline Protection (`$98,000` caught by both systems in `TC-02`, `TC-07`, `TC-08`)**.
3. **`03 · All Activity & Protection`:** Visual Bento grid across all 10 screened orders (`$10.70M` screened: 3 approved, 5 blocked, 2 held for CCO review), with an outcome donut ring, interactive decision filters, inline SVG icons, and per-trade incremental vs. baseline attribution.
4. **`04 · Fund Portfolio ($100M)`:** Displays the `$100.0M` settled Form N-PORT portfolio (`$82.35M` invested across 12 positions + `$17.65M` cash) with parent-group concentration bars, `5.00%` synthetic IPS limit markers, and passive market-drift tracking (`NVIDIA` at `5.15%`).

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

### Step 4: Run the 10-Case Evaluation Benchmark
```bash
python evaluate_10_cases.py
```

---

## 5. Repository Structure

```text
├── app.py                          # Interactive 4-Dashboard Streamlit App (AEGIS + Emil Kowalski Orange Edition)
├── evaluate_10_cases.py            # CLI benchmark runner across all 10 trades (works with or without API key)
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

## 6. Reconciled 10-Trade Benchmark & Incremental Attribution

To avoid over-claiming savings on trades that a basic single-ticket checker already catches, our evaluation explicitly separates:
- **1. Incremental Value Realized by Our Gate (`+$184,500`):** 2 unsafe approvals caught (`TC-03` `+$68,000` + `TC-05` `+$34,000` = **`+$102,000`** direct unwind losses avoided) + 1 false block corrected (`TC-04` Ford = **`+$82,500`** replacement spread cost avoided).
- **2. Ambiguous Exposure Held for CCO Review (`$93,000`):** 2 footnote-trap trades (`TC-09` `$41,000` + `TC-10` `$52,000`) paused for human Chief Compliance Officer sign-off (`$2.50M` notional).
- **3. Baseline Breaches Blocked by Both Systems (`$98,000`):** 3 direct breaches (`TC-02` `$45,000` + `TC-07` `$38,000` + `TC-08` `$15,000`) already caught by basic checks (`$0` incremental claimed).

| ID | Company & Proposed Order | Basic Check | Our Gate | Baseline / At-Risk | Incremental Value (Ours) | Why It Matters |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`TC-01`** | **Microsoft Corp** — Buy `$1.20M` AAA Bond | `APPROVED` | **`APPROVED`** | `$0` | `$0 (Both pass)` | Clean trade; exposure moves `3.10% -> 4.30%` (`<= 5.00%` IPS cap). |
| **`TC-02`** | **Apple Inc** — Buy `$1.25M` AA+ Bond | `BLOCKED` | **`BLOCKED`** | `$45,000 base` | `$0 (Both block)` | Direct company breach (`4.20% -> 5.45% > 5.00%`); caught by both systems. |
| **`TC-03`** | **Florida Power & Light** — Buy `$1.30M` Bond | `APPROVED` *(Miss!)* | **`BLOCKED`** | `-$68,000 loss` | **`+$68,000 Saved`** | `0%` direct holding, but parent **NextEra Energy** hits `5.40% > 5.00%`. |
| **`TC-04`** | **Ford Motor Credit** — Buy `$1.50M` Split-Rated Bond | `BLOCKED` *(False!)* | **`APPROVED`** | `-$82,500 cost` | **`+$82,500 Saved`** | Split-rated `BBB- / Ba1`; higher rating (`BBB-`) governs under Sec 2.02(b), preventing a costly false block. |
| **`TC-05`** | **Permian Resources** — Buy `$700k` BB Energy Bond | `APPROVED` *(Miss!)* | **`BLOCKED`** | `-$34,000 loss` | **`+$34,000 Saved`** | Total High-Yield is `14.90% <= 15%`, but **High-Yield Energy** hits `5.20% > 5.00%` sub-limit. |
| **`TC-06`** | **UK Treasury Gilt** — Buy `$1.20M` GBP Gov Bond | `APPROVED` | **`APPROVED`** | `$0` | `$0 (Both pass)` | Qualifies for Sec 4.01(b) unhedged OECD sovereign bond carve-out (`8.70% <= 10%`). |
| **`TC-07`** | **Siemens AG** — Buy `$1.00M` Unhedged EUR Bond | `BLOCKED` | **`BLOCKED`** | `$38,000 base` | `$0 (Both block)` | OECD currency carve-out applies only to sovereigns, not corporate bonds; caught by both. |
| **`TC-08`** | **NVIDIA Corp** — Buy `$50k` Stock Above 5% Drift | `BLOCKED` | **`BLOCKED`** | `$15,000 base` | `$0 (Both block)` | Holding `5.15%` passive stock appreciation is compliant (Sec 3.03), but active `BUY` is blocked by both. |
| **`TC-09`** | **Heartland Rail** — Buy `$1.00M` Bond (Coal Footnote) | `APPROVED` *(Miss!)* | **`HELD (CCO)`** | `$41,000 at-risk` | **`Escalated ($1.0M)`** | Direct coal is `4.2% <= 10%`, but footnote discloses `22%` mixed coal rail freight (Sec 5.01b). |
| **`TC-10`** | **Cayman Emerald Trust** — Buy `$1.50M` SPV Note | `APPROVED` *(Miss!)* | **`HELD (CCO)`** | `$52,000 at-risk` | **`Escalated ($1.5M)`** | Footnote reveals orphan SPV backed by an undisclosed oil & gas total return swap basket (Sec 5.02). |

---

## 7. Evaluation Methodology & Baseline Construction

### 7.1 Baseline Construction: Rule-Based Ticket-Only Baseline (Basic Single-Ticket Checker)
To avoid over-claiming savings against a strawman or misrepresenting handcrafted rules as a naive LLM, the benchmark in `evaluate_10_cases.py` compares our gate against an explicit programmatic **Rule-Based Ticket-Only Baseline (5/10, 50.0% accuracy)**. This baseline reflects the reality of legacy OMS pre-trade checking:
1. **Direct Issuer Match Only:** Sums holdings matching `trade['issuer_id']` directly. It has no access to the security master's corporate tree (`ultimate_parent_id`), so it misses parent-subsidiary aggregation (e.g., failing to catch Florida Power & Light under NextEra in `TC-03`).
2. **Conservative Rating Rule:** Evaluates ratings using single-agency conservative rules without cross-referenced legal tie-breakers. Because Moody's rates Ford `Ba1` (High-Yield), it falsely blocks Ford Motor Credit in `TC-04`, missing Section 2.02(b) which specifies that the higher rating (`BBB-`) governs.
3. **Broad Portfolio Caps Only:** Checks top-level portfolio limits (15.00% High-Yield), but lacks multi-dimensional sub-limit tracking, missing the 5.00% High-Yield Energy cap in `TC-05`.
4. **Structured Columns Only:** Reads only structured database values (e.g. `thermal_coal_revenue_pct = 4.2%`), completely blind to unstructured deal footnotes revealing 22% mixed coal rail corridors (`TC-09`) or orphan SPV swap baskets (`TC-10`).

### 7.2 Ground Truth Construction & Expected Verdicts
The 10 test cases in `data/test_cases_10.json` represent realistic institutional fixed-income, equity, and credit derivative orders screened against the governing fund mandate (`data/fund_mandate_ips.md`):
- **3 Compliant / Permitted Trades (`PASS`):** `TC-01` (Microsoft clean bond), `TC-04` (Ford split-rating tie-breaker), `TC-06` (UK Gilt OECD sovereign carve-out).
- **5 Hard Contractual Breaches (`BREACH`):** `TC-02` (Apple direct 5.45%), `TC-03` (NextEra parent group 5.40%), `TC-05` (HY Energy 5.20%), `TC-07` (Siemens unhedged corporate EUR), `TC-08` (NVIDIA active buy during market drift).
- **2 Qualitative Footnote Gray Areas (`ESCALATE_TO_HUMAN`):** `TC-09` (Heartland Rail mixed freight), `TC-10` (Cayman Emerald SPV oil/gas swap look-through).

### 7.3 Live API vs. Offline Deterministic Fallback
- **Live OpenRouter API:** When an `OPENROUTER_API_KEY` is present in `.env`, Step 3 calls instruction-tuned open-source LLMs (`nvidia/nemotron-3.5-super-vl:free`, `meta-llama/llama-3.3-70b-instruct:free`, etc.) to parse deal footnotes, while Step 4 strictly enforces quote substring grounding and the one-way safety state lock.
- **Offline Deterministic Fallback:** When cloned without an API key, the system runs 100% locally: BM25/TF-IDF retrieval, parent-group aggregation, split-rating resolution, and schema pruning execute in under 5ms, while pre-recorded live LLM benchmarks are loaded from `data/evaluation_results_10.json`.


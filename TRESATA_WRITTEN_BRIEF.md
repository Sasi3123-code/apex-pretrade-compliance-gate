# Apex Pre-Trade Compliance Gate -- Investment Mandate Enforcement & Compliance Controls
**Author:** Darla Venkata Sasi Kumar (IIT Madras `EP23B026`)  
**Domain:** Institutional Asset Management & Private Credit (Fund Investment Policy Statements (`IPS`), SEC Rule `206(4)-7` under the Investment Advisers Act of 1940, SEC Rule `38a-1` under the Investment Company Act of 1940, Forms `N-1A` & `N-PORT`)  
**Prototype:** `app.py` (4-Dashboard AEGIS + Emil Kowalski Warm Electric Orange Edition) & `evaluate_10_cases.py`  
**Headline Impact:** **2 Unsafe Approvals Caught | 1 False Block Fixed | 2 Gray Areas Escalated** (`+$184,500` direct incremental loss/cost avoided over basic checks + `$93,000` ambiguous exposure held for CCO review + `$98,000` baseline breaches caught by both)

---

## Page 1: The Area I Explored, What Surprised Me & Regulatory Compliance Context

### 1. The Area I Explored & Three Things That Surprised Me
When I interned as a Software Engineer at **Apollo Global Management**, I built data delivery pipelines and dashboards across **75,000+ holdings and 20,000+ trade records**, along with a natural-language query assistant for portfolio data. That experience got me interested in a deceptively simple question: *what actually happens in the 60 seconds between a portfolio manager clicking "Buy" and the order hitting the market?* When I explored institutional **Investment Policy Statements (IPS)**, SEC Form N-1A registration statements, and compliance-program controls for this project, three things genuinely surprised me:

1. **A rule on Page 12 is defined on Page 2:** In a fund's Investment Policy Statement, a limit looks straightforward at first glance -- for example, a synthetic fund mandate limit of *"No more than 5.00% of Fund NAV in any single issuer"* (Section 3.01a). But if you flip back to Section 1.04, "Single Issuer" is redefined to aggregate every majority-owned subsidiary sharing an ultimate parent company. And if S&P rates a bond `BBB-` (Investment Grade) while Moody's rates it `Ba1` (High-Yield), Section 2.02b specifies that the higher rating governs. Reading the limit paragraph without pulling the cross-referenced definition paragraph gives the wrong answer.
2. **Holding a stock above 5% is compliant, but buying \$1 more violates the mandate:** If NVIDIA rallies and grows to 5.15% of the fund on its own (passive market drift), standard Market Drift Cure Provisions (Section 3.03) allow the fund to keep holding it passively. However, executing even a \$50,000 active `BUY` order while NVIDIA sits above 5.00% is an immediate active-purchase breach.
3. **Why neither SQL rules nor raw LLMs can do this alone:** Traditional database checks are great at summing columns, but they cannot read a 3-sentence deal footnote warning that a rail company gets 22% of its revenue from mixed coal corridors, or that a Cayman Islands trust is backed by an undisclosed oil-and-gas swap basket. Conversely, pasting 75,000 holdings rows into an LLM burns ~3.6 million tokens, leaks private custodian account numbers, and routinely fumbles parent-company joins and basis-point math.

### 2. The Problem We Solve & Regulatory Compliance Context
> **Why Pre-Trade Mandate Enforcement Matters:** If a trade violates the fund's investment mandate, it can create a mandate breach, trigger costly trade unwinding and remediation, and expose the adviser to compliance and fiduciary risks (including reimbursing the fund for resulting unwind losses). The firm's compliance program -- including its written controls under **SEC Rule 206(4)-7** (under the Investment Advisers Act of 1940 for registered investment advisers) and **SEC Rule 38a-1** (under the Investment Company Act of 1940 for registered investment companies) -- must be designed to prevent, detect, and address such mandate violations before execution.

- **Who uses this & how often:** Pre-trade compliance officers and middle-office desks at multi-asset credit and equity funds (\$500M to \$50B AUM), screening **50 to 300+ proposed allocation tickets every trading day** against fund-specific IPS limits, prospectus disclosures (Form N-1A), and institutional client side letters.
- **What it costs today:** Checking a complex bond or swap across PDF rulebooks and side letters takes **15 to 30 minutes of manual lookup**. Missing a parent-group link or sub-cap forces an open-market trade unwind (costing 3% to 5% in bid-ask/illiquidity slippage plus external review fees), while misreading a split-rating rule causes false blocks on valid trades (costing ~55 bps in replacement spread).
- **Why now:** As private credit and bespoke Separately Managed Accounts (SMAs) grow, firms manage hundreds of custom client mandates. Hard-coding every new prose side letter into legacy SQL engines takes 3 to 6 weeks. Combining exact Python portfolio math with a constrained AI footnote reader cuts verification to seconds with zero math drift.

| What Is In Scope (Pre-Trade Mandate Gate) | What Is Explicitly Out of Scope |
| :--- | :--- |
| - Exact post-trade NAV % math across direct issuers and parent groups (Sec 1.04 / 3.01) under synthetic IPS thresholds.<br>- Split credit rating tie-breakers (Sec 2.02b), High-Yield Energy sub-limits (3.02b), and OECD sovereign FX carve-outs (4.01b).<br>- Screening deal footnotes for coal freight ambiguity (5.01b) and orphan SPV swaps (5.02), and auditing incremental loss avoidance. | - Broker order-book routing, execution slicing, and FIX protocol market connectivity.<br>- Post-trade T+1 custodian bank wire settlement and cash reconciliation.<br>- Predicting security returns or offering automated legal advice without CCO review. |

---

## Page 2: How the System Works, System Boundaries & The 4-Dashboard Prototype

### 2.1 How the System Works: Exact Math First, AI Reading Second
The core design principle of our system is simple: **never let a language model do portfolio arithmetic, and never expect a SQL query to read a legal footnote**. In `src/agent_graph.py`, every proposed trade passes through four distinct steps where exact calculation and AI reading are kept strictly separate:

1. **Step 1 -- Mandate Search (`src/retriever.py`):** Uses hybrid `BM25 + TF-IDF` keyword search plus a 1-hop cross-reference graph expander that automatically pulls linked definitions (e.g., `Section 3.01 -> Section 1.04`) and records exact `[char_start..char_end]` character offsets.
2. **Step 2 -- Exact Limit Calculator (`src/deterministic_engine.py`):** Uses `fund_schema.yaml` to strip private account numbers locally (cutting context by **99.993%**, from ~3.6M tokens to 240 tokens) and computes exact parent-group exposure (`ultimate_parent_id`), split credit ratings, High-Yield Energy sub-caps, and foreign currency carve-outs in Python.
3. **Step 3 -- Deal Note Reader (`src/agent_graph.py`):** An OpenRouter LLM reads only the retrieved IPS clauses and unstructured deal footnotes to flag qualitative gray areas (such as mixed coal rail corridors in `TC-09` or opaque Cayman SPVs in `TC-10`). It never touches portfolio math.
4. **Step 4 -- Final Safety Lock (`src/agent_graph.py`):** Verifies that the LLM's cited quote exists character-for-character in the mandate (`verify_verbatim_quote()`) and enforces a one-way safety lock: **the AI can never downgrade a Step 2 math breach into an approval**.

### 2.2 Where Knowledge Lives & How Rules Stay Up to Date

| System Step | Exact or AI? | Where Knowledge Lives | Why It Works & How We Verify It |
| :--- | :--- | :--- | :--- |
| **1. Mandate Search** (`src/retriever.py`) | **100% Exact** (BM25 + Graph) | Versioned mandate file (`fund_mandate_ips.md`) | Finds exact section numbers and automatically pulls linked definitions (e.g., Sec 3.01 -> Sec 1.04) with character offsets. |
| **2. Limit Calculator** (`deterministic_engine.py`) | **100% Exact** (Python Math) | `holdings_nport.json` + `fund_schema.yaml` | Strips private account numbers locally (99.993% token cut) and calculates exact parent-group, credit, and currency percentages. |
| **3. Footnote Reader** (`src/agent_graph.py`) | **Probabilistic** (OpenRouter LLM) | Retrieved IPS clauses + deal supplement notes | Reads unstructured deal prose to spot gray areas (mixed coal rail corridors in Sec 5.01b or opaque Cayman SPVs in Sec 5.02). |
| **4. Final Safety Gate** (`src/agent_graph.py`) | **100% Exact** (State Lock) | `verify_verbatim_quote()` + Asymmetric Lock | Checks that the cited quote exists character-for-character in the mandate. The AI can never turn a math breach into an approval. |

- **What happens when a fund mandate rule is amended or expires:** No rules or limits are baked into model weights. Every contractual threshold lives in `fund_schema.yaml` and `fund_mandate_ips.md` (tagged with Document ID `IPS-APEX-2026-V4`). When a fund board amends an IPS cap or adds a client side letter, updating the file immediately updates Step 1 and Step 2 with zero retraining. Past audit logs remain bound to the Mandate ID active at trade time (supporting annual compliance reviews under Advisers Act Rule 206(4)-7 and 1940 Act Rule 38a-1).
- **Adapting to another regulatory regime (e.g., EU UCITS or India SEBI):** Our testbed models a US institutional fund mandate alongside SEC Form N-1A/N-PORT schemas. Moving to European UCITS funds (which enforce statutory `5/10/40` issuer concentration rules) requires only swapping the mandate file and adding a 4-line summation check in Step 2.

### 2.3 The 4-Dashboard Prototype (Plain-English Orange Edition)
Compliance officers should not have to read raw JSON or backend code on screen. Modeled after the **AEGIS** visual system and **Emil Kowalski's** motion engineering principles, our Streamlit app (`app.py`) uses a **Warm Electric Orange (`#F04E14`)** theme and organizes the workflow into four plain-English dashboards:
- **`01 - Pre-Trade Gate`:** Features the signature "Needs You" Split-Card with 30px tabular numerals (*Before trade -> After trade*), a 2-segment overshoot bar showing the exact red breach segment past the limit tick mark, a 4-step pulsing checkpoint stepper, a conic-gradient score ring, and a What-If simulator.
- **`02 - Losses vs. Savings`:** Separates **Incremental Value Added by Our Gate (+\$184,500 realized across `TC-03`, `TC-04`, `TC-05`)** from **Ambiguous Exposure Held for CCO Review (\$93,000 in `TC-09`, `TC-10`)** and **Baseline Protection (\$98,000 caught by both systems in `TC-02`, `TC-07`, `TC-08`)**.
- **`03 - All Activity & Protection`:** A dedicated visual Bento dashboard across all 10 orders (\$10.70M screened: 3 approved, 5 blocked, 2 held for CCO review), complete with an outcome donut ring, interactive decision filters, inline SVG icons, and transparent per-trade attribution.
- **`04 - Fund Portfolio (\$100M)`:** Displays the \$100.0M settled Form N-PORT portfolio (\$82.35M across 12 holdings + \$17.65M cash) with parent-group concentration bars, 5.00% IPS limit markers, and passive market-drift indicators (e.g., NVIDIA at 5.15%).

---

## Page 3: Rejected Approaches, Weakest Point & Risk Governance

### 3.1 Four Approaches We Tested and Rejected

| Rejected Approach | Why It Fails on Real Institutional Trades |
| :--- | :--- |
| **1. One Big LLM Call Over All Holdings + Mandate** | Sending 75,000 holdings rows (~3.6M tokens) to an LLM costs \$10-\$30 per trade check, takes 30+ seconds, exposes private custodian bank codes to external APIs, and routinely miscalculates parent-company sums and 5.00% vs. 5.01% boundary math. |
| **2. Pure Vector Embedding Search (Dense RAG Only)** | Legal mandates rely on exact section numbers (`Section 3.01(b)`) and rating symbols (`Ba1`, `BBB-`). Dense embeddings blur negations and miss multi-hop definitions (pulling Section 3.01 without pulling Section 1.04). Our BM25 + TF-IDF + Cross-Reference Graph fixes both. |
| **3. 100% Hard-Coded SQL Rules (No AI Reader)** | Fails silently on **TC-09 and TC-10**: when database columns look clean (`coal_revenue = 4.2% <= 10%`, `rating = A-`), SQL auto-approves the trade and misses the footnote revealing 22% mixed coal rail freight or an undisclosed Cayman swap basket. |
| **4. Letting an LLM Write SQL Queries on the Fly** | If a Text-to-SQL agent forgets `GROUP BY ultimate_parent_id` on just one run out of a hundred, a \$1.3M subsidiary breach (like Florida Power & Light under NextEra Energy) slips through. Compliance math must be locked in tested code, not generated dynamically. |

### 3.2 The Weakest Point in Our Design (And What Would Break It)
> **Our Biggest Vulnerability -- Stale Parent-Company Links in the Security Master (`ultimate_parent_id`):**  
> Step 2 catches parent-subsidiary breaches (like knowing NextEra Energy owns Florida Power & Light) by grouping holdings on `ultimate_parent_id`. That math is 100% exact, but it trusts that the upstream corporate tree table is up to date.

- **How to break it (Scenario 1 -- Same-Day Spin-Off or New Financing Shell):** Suppose an existing portfolio company creates a brand-new Delaware financing subsidiary this morning to issue bonds, and our data vendor has not linked the new subsidiary's `ultimate_parent_id` yet. Step 2 will see 0% existing exposure and approve the trade unless the deal footnote explicitly names the parent company for Step 3 to catch.
- **How to break it (Scenario 2 -- Chained Side-Letter Waivers):** Our cross-reference expander follows 1-hop links (e.g., `Section 3.01 -> Section 1.04`). If an institutional client signs three sequential side-letter riders that modify each other conditionally (*"Rider 3 pauses Rider 1 during Q4 unless High-Yield exceeds 12%"*), a 1-hop lookup can miss the interaction between Rider 3 and Rider 1.

### 3.3 Managing Real-World Risks & Human-in-the-Loop Governance

| Risk Category | What Happens If Something Goes Wrong | How Our Architecture Protects the Firm |
| :--- | :--- | :--- |
| **1. Unequal Cost of Errors** (False Positive vs. False Negative) | Pausing a good trade costs 2 minutes of officer review. Approving a mandate breach triggers forced market unwinds, remediation, and adviser reimbursement risk. | **One-Way Safety Lock:** Step 4 is biased strictly toward safety. The AI can escalate a clean math check to `HELD FOR OFFICER`, but it can **never** override a Step 2 math breach. |
| **2. Outdated Mandates** (Stale IPS Thresholds) | Checking today's trade against a superseded IPS cap or an expired client side-letter carve-out. | Every trade decision stamps the active Mandate ID (`IPS-APEX-2026-V4`), effective date, and exact character span `[char_start..char_end]` into the audit record. |
| **3. Data Privacy Leakage** (Confidential Holdings) | Exposing full fund positions, prime-broker codes, or internal desk notes to external LLM providers. | **YAML Schema Pruning (`fund_schema.yaml`):** Strips private columns locally and sends only pre-summed numbers (**240 tokens instead of 3.6M tokens -- a 99.993% cut**). |
| **4. Fiduciary & CCO Governance** (Advisers Act 206(4)-7 / 1940 Act 38a-1) | Under SEC Rule 206(4)-7 (advisers) and Rule 38a-1 (registered funds), oversight responsibility rests on a designated human Chief Compliance Officer (CCO), never an AI. | **Mandatory Officer Sign-Off Queue:** Quantitative breaches are blocked automatically; qualitative gray areas (`TC-09`, `TC-10`) are held until a human officer records written sign-off. |

---

## Page 4: 10-Trade Benchmark, Transparent Financial Attribution & Honest AI Failures

### 4.1 10-Trade Benchmark & Transparent Financial Attribution
We evaluated our 4-step gate across **10 proposed trades (\$10.70M order flow)** against a \$100.0M settled portfolio. To avoid over-claiming savings on trades that a basic single-ticket checker already catches, the table below explicitly separates:
1. **Incremental Savings Realized by Our Gate (+\$184,500)** on the 2 unsafe approvals caught (`TC-03` +\$68,000, `TC-05` +\$34,000 = **+\$102,000** unwind losses avoided) and 1 false block fixed (`TC-04` Ford = **+\$82,500** replacement spread cost avoided);
2. **Ambiguous Exposure Held for CCO Review (\$93,000)** on the 2 escalated trades (`TC-09` \$41,000, `TC-10` \$52,000, which are paused for human decision, not claimed as auto-realized savings); and
3. **Baseline Protection (\$98,000)** on the 3 breaches blocked by both systems (`TC-02` \$45,000, `TC-07` \$38,000, `TC-08` \$15,000 -- `\$0` incremental claimed):

| ID | Proposed Order & Mandate Rule Tested | Basic Check | Our Gate | Baseline / At-Risk | Incremental Value (Ours) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TC-01` | **Microsoft Corp** (\$1.20M AAA Bond) -- Clean; 3.10% -> 4.30% (<= 5% IPS cap). | APPROVED | **APPROVED** | \$0 | \$0 (Both pass) |
| `TC-02` | **Apple Inc** (\$1.25M AA+ Bond) -- Direct company breach: 4.20% -> 5.45% (> 5%). | BLOCKED | **BLOCKED** | \$45,000 base | \$0 (Both block) |
| `TC-03` | **Florida Power & Light** (\$1.30M) -- 0% direct, but parent NextEra hits 5.40% (> 5%). | APPROVED (Miss!) | **BLOCKED** | -\$68,000 loss | **+\$68,000 Saved** |
| `TC-04` | **Ford Motor Credit** (\$1.50M BBB-/Ba1) -- Higher rating governs (Sec 2.02b); IG. | BLOCKED (False!) | **APPROVED** | -\$82,500 cost | **+\$82,500 Saved** |
| `TC-05` | **Permian Resources** (\$700k BB Energy) -- Total HY 14.9%, but HY Energy 5.20% (> 5%). | APPROVED (Miss!) | **BLOCKED** | -\$34,000 loss | **+\$34,000 Saved** |
| `TC-06` | **UK Treasury Gilt** (\$1.20M GBP Gov Bond) -- Valid OECD sovereign carve-out (8.70%). | APPROVED | **APPROVED** | \$0 | \$0 (Both pass) |
| `TC-07` | **Siemens AG** (\$1.00M Unhedged EUR Corp) -- OECD FX carve-out is for sovereigns only. | BLOCKED | **BLOCKED** | \$38,000 base | \$0 (Both block) |
| `TC-08` | **NVIDIA Corp** (\$50k Stock Buy) -- At 5.15% passive drift; active BUY is prohibited. | BLOCKED | **BLOCKED** | \$15,000 base | \$0 (Both block) |
| `TC-09` | **Heartland Rail** (\$1.00M Bond) -- 4.2% coal, but footnote shows 22% mixed coal rail. | APPROVED (Miss!) | **HELD (CCO)** | \$41,000 at-risk | **Escalated (\$1.0M)** |
| `TC-10` | **Cayman Emerald Trust** (\$1.50M SPV) -- Footnote shows undisclosed oil/gas swap basket. | APPROVED (Miss!) | **HELD (CCO)** | \$52,000 at-risk | **Escalated (\$1.5M)** |

#### Reconciliation of Pre-Trade Protection Across All 10 Test Cases:
- **1. Incremental Unwind Loss Avoided (`TC-03` \$68k + `TC-05` \$34k caught by our gate):** `+$102,000` (Realized Incremental)
- **2. Incremental False-Block Cost Avoided (`TC-04` Ford split-rating fixed by our gate):** `+$82,500` (Realized Incremental)
  - *Total Realized Incremental Value Over Basic Checker (`TC-03` + `TC-04` + `TC-05`):* **`+$184,500`**
- **3. Ambiguous Exposure Held for CCO Review (`TC-09` \$41k + `TC-10` \$52k escalated):** `$93,000` (Held for CCO Decision on \$2.50M Notional)
- **4. Baseline Breaches Blocked by Both Systems (`TC-02` \$45k + `TC-07` \$38k + `TC-08` \$15k):** `$98,000` (Baseline Protection -- `\$0` Incremental Claimed)
  - *(Grand total across all 4 transparent buckets = `$102,000 + $82,500 + $93,000 + $98,000 = $375,500`)*

### 4.2 Honest Report: Three Places Where the AI Struggled in Testing
1. **Free-tier reasoning models running out of tokens inside `<think>` tags:** On our first live OpenRouter test run, a reasoning model spent its entire 500-token budget thinking inside `<think>...</think>` tags and cut off before outputting JSON. We fixed this by stripping `<think>` blocks in `src/agent_graph.py` and routing to instruction-tuned models first.
2. **Minor quote paraphrasing on 4 out of 10 live runs:** Smaller free-tier models occasionally dropped a comma or paraphrased a word when copying the mandate quote. Our Step 4 verifier (`verify_verbatim_quote()`) caught all 4 instances and automatically anchored the citation to the exact character span `[char_start..char_end]`.
3. **Free-tier API latency swings (7.5s to 68.6s) & Two-Tier Fast Path:** While Steps 1, 2, and 4 finish locally in **under 5 milliseconds**, waiting on a free-tier LLM for every trade is too slow for a high-speed desk. In production, 90% of standard bond and stock orders have no special deal footnotes or SPV wrappers, so they clear Steps 1 & 2 in **`< 5 ms`**, calling Step 3 (AI) only when unstructured rider prose is attached.

---

## Page 5: One-Page Appendix -- What I Added Beyond the AI

### A.1 How I Used AI (And Three Prompts That Actually Helped)
I treated AI as a fast sparring partner for legal edge-case brainstorming and UI layout iteration, while keeping all architecture, retrieval math, and compliance state locks in my own hands. Three prompts that were genuinely useful:
1. **Finding real-world compliance traps:** *"Give me concrete examples of how institutional bond funds accidentally violate their Investment Policy Statement (IPS) or Form N-1A mandate even when basic SQL checks on single-issuer % pass."*
2. **Drafting realistic cross-referenced mandate clauses:** *"Draft an institutional Investment Policy Statement (IPS) where the 5% single-issuer cap in Article III depends on a parent-group definition in Article I, a split-rating tie-breaker in Article II, an OECD sovereign currency exception in Article IV, and qualitative coal/SPV rules in Article V."*
3. **Locking down the Step 3 footnote reader prompt:** *"You are a Senior Fund Compliance Auditor. Analyze the proposed trade using ONLY the retrieved IPS clauses, the exact numbers from the Deterministic Calculator, and the deal footnotes. NEVER invent math or override the Deterministic Calculator."*

### A.2 Three AI Suggestions I Rejected (And How I Knew Better)

| What the AI Suggested | Why I Rejected It & Where My Judgment Came From |
| :--- | :--- |
| **1. "Use a Text-to-SQL agent to query the holdings table dynamically on every trade."** | **How I knew:** At **Apollo Global Management**, I built a natural-language-to-DB assistant over 75K+ holdings and 20K+ trades. For ad-hoc analyst questions, a 98% query accuracy rate is great. For pre-trade compliance, if an LLM forgets `GROUP BY ultimate_parent_id` even once, the fund executes a mandate breach. I replaced dynamic query generation with fixed, tested aggregation code in Step 2. |
| **2. "Chunk the rulebook into 500-token slices and use vector embeddings."** | **How I knew:** From building my **Vector Space Retrieval Engine** (benchmarking BM25, TF-IDF, LSA, and WordNet expansion on the Cranfield corpus), I knew dense embeddings struggle with exact section codes (`Section 3.01(b)`) and sever cross-references when a limit in Article III relies on a definition in Article I. I built a hybrid BM25 + TF-IDF retriever with a 1-hop cross-reference graph expander instead. |
| **3. "Claim all blocked trades as incremental AI savings and label IPS caps as SEC statutory limits."** | **How I knew:** Basic SQL checks already block simple breaches (`TC-02`, `TC-07`, `TC-08`), and `TC-09`/`TC-10` are held for officer review rather than auto-blocked. I separated **+\$184,500 in incremental value** (`TC-03`, `TC-04`, `TC-05`) from **\$93,000 held for review** and **\$98,000 baseline**, and distinguished synthetic IPS caps from SEC Rule 206(4)-7 (Advisers Act) and Rule 38a-1 (1940 Act). |

### A.3 What Came Directly From Me
- **Auditable Incremental Attribution (+\$184,500 Incremental / \$93,000 Escalated / \$98,000 Baseline):** Instead of lumping all 10 test cases into a single un-reconciled total, I broke down every dollar by case and counterfactual baseline: 2 hidden breaches blocked (+\$102,000), 1 false block fixed (+\$82,500), 2 ambiguous trades escalated (\$2.50M notional / \$93,000 exposure paused for CCO sign-off), and 3 baseline breaches excluded from incremental claims (\$98,000).
- **Schema-pruned context budgeting (`data/fund_schema.yaml`):** Inspired by my work at Apollo optimizing token budgets across fund schemas, I designed `fund_schema.yaml` to strip sensitive custodian and broker fields locally and reduce LLM prompt context from ~3.6M tokens to 240 tokens (**99.993% reduction**).
- **Modeling the passive market-drift vs. active purchase lockout (`TC-08`):** Most prototypes check `weight <= 5%` statically. I explicitly modeled the transition where holding a drifted position (NVIDIA at 5.15%) is compliant under Section 3.03, but adding a \$50,000 active `BUY` order is blocked.

### A.4 What I Will Happily Defend Live on a Whiteboard Without AI
With zero AI or notes, I am ready to derive, code, and walk through the entire retrieval and compliance engine live:
1. **The Hybrid BM25 + Cross-Reference Graph Retriever (`src/retriever.py`):** Inverted index construction, Okapi BM25 scoring `IDF(q) * [tf * (k1 + 1)] / [tf + k1 * (1 - b + b * dl / avgdl)]`, TF-IDF cosine fusion, 1-hop regex graph expansion across legal sections, and character-offset substring verification.
2. **The Pro-Forma Compliance Calculator & Safety Gate (`src/deterministic_engine.py`):** Parent-group relational aggregation on `ultimate_parent_id`, split-rating ordinal rank resolution (`min(rank_SP, rank_Moodys) <= 10`), and the one-way safety state machine in Step 4.

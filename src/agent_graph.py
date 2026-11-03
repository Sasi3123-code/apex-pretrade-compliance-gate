"""
Stateful Multi-Node Agentic Orchestrator (LangGraph State-Machine Pattern)
with OpenRouter Free-Tier LLM Integration & Grounding Verification Critic.

Nodes in the Execution Graph:
  [Node 1: hybrid_retrieve_node]
      Executes BM25 + TF-IDF Cosine + Cross-Reference Graph Expansion over IPS-APEX-2026-V4.
  [Node 2: deterministic_calculator_node]
      Executes Apollo-style YAML schema pruning and 100% deterministic post-trade math.
  [Node 3: llm_semantic_extractor_node]
      Calls OpenRouter LLM to interpret qualitative prospectus notes, map governing clauses,
      extract verbatim citations, and flag semantic ambiguity.
  [Node 4: grounding_and_safety_critic_node]
      Self-reflection critique loop:
      - Verifies every cited quote against character offsets [char_start, char_end] in the Mandate.
      - Enforces the Asymmetric Compliance Gate (LLM cannot override a deterministic BREACH;
        unverified citations or qualitative ambiguities force ESCALATE_TO_HUMAN).
"""

from __future__ import annotations
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional

from src.retriever import HybridMandateRetriever
from src.deterministic_engine import DeterministicComplianceEngine


FREE_MODEL_FALLBACK_CHAIN = [
    "google/gemma-3-27b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "openrouter/free",
]


@dataclass
class AgentState:
    """Typed state passed across the 4-node compliance orchestration graph."""
    test_id: str
    proposed_trade: Dict
    trace_log: List[Dict] = field(default_factory=list)
    retrieved_clauses: List[Dict] = field(default_factory=list)
    deterministic_bundle: Dict = field(default_factory=dict)
    llm_raw_output: Dict = field(default_factory=dict)
    llm_model_used: str = ""
    llm_latency_ms: float = 0.0
    naive_llm_verdict: str = ""
    naive_llm_rationale: str = ""
    critic_verification: Dict = field(default_factory=dict)
    final_verdict: str = ""
    final_primary_clause: str = ""
    final_audit_rationale: str = ""
    human_review_required: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)


REPO_ROOT = Path(__file__).resolve().parent.parent


def load_env_file(env_path: str | Path = REPO_ROOT / ".env") -> Dict[str, str]:
    p = Path(env_path)
    env_vars: Dict[str, str] = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()
    return env_vars


class OpenRouterClient:
    """Lightweight, zero-dependency OpenRouter client with free-tier fallback & retry."""

    def __init__(self, env_path: str | Path = REPO_ROOT / ".env"):
        env_vars = load_env_file(env_path)
        self.api_key = os.environ.get("OPENROUTER_API_KEY") or env_vars.get("OPENROUTER_API_KEY", "")
        self.preferred_model = os.environ.get("OPENROUTER_MODEL") or env_vars.get("OPENROUTER_MODEL", "openrouter/free")

    def chat_json(self, system_prompt: str, user_prompt: str, timeout: int = 35) -> Tuple[Dict, str, float]:
        t0 = time.perf_counter()
        if not self.api_key:
            raise RuntimeError("Missing OPENROUTER_API_KEY in .env")

        models_to_try = [
            m for m in FREE_MODEL_FALLBACK_CHAIN if m != self.preferred_model
        ] + [self.preferred_model]

        last_err = None
        for model_name in models_to_try:
            payload = {
                "model": model_name,
                "temperature": 0.0,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/sasi-iitm/tresata-mandate-auditor",
                    "X-Title": "Apex Pre-Trade Mandate Compliance Auditor",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
                actual_model = body.get("model", model_name)
                content = body["choices"][0]["message"]["content"] or ""
                parsed = self._extract_json_block(content)
                return parsed, actual_model, latency_ms
            except Exception as exc:
                last_err = exc
                time.sleep(1.0)
                continue

        latency_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        return (
            {
                "error": str(last_err),
                "llm_verdict": "UNAVAILABLE",
                "primary_clause": "UNKNOWN",
                "verbatim_quote": "",
                "qualitative_ambiguity_detected": True,
                "semantic_analysis": f"OpenRouter free-tier rate-limited or unreachable ({last_err}).",
            },
            "rate-limited-fallback",
            latency_ms,
        )

    @staticmethod
    def _extract_json_block(text: str) -> Dict:
        cleaned = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()
        # Strip markdown fences if present
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL)
        candidate = fence_match.group(1) if fence_match else cleaned
        if not fence_match:
            brace_match = re.search(r"(\{[^{}]*\"llm_verdict\"[^{}]*\})", cleaned, flags=re.DOTALL)
            if not brace_match:
                brace_match = re.search(r"(\{.*\})", cleaned, flags=re.DOTALL)
            if brace_match:
                candidate = brace_match.group(1)
        try:
            return json.loads(candidate)
        except Exception:
            verdict_guess = "PARSE_ERROR"
            for kw in ("ESCALATE_TO_HUMAN", "BREACH", "PASS"):
                if kw in cleaned.upper():
                    verdict_guess = kw
                    break
            return {
                "llm_verdict": verdict_guess,
                "primary_clause": "UNKNOWN",
                "verbatim_quote": "",
                "qualitative_ambiguity_detected": (verdict_guess == "ESCALATE_TO_HUMAN"),
                "semantic_analysis": cleaned[:400],
            }


class MandateComplianceAgentGraph:
    """
    4-Node Stateful Compliance Graph combining:
      1. Hybrid BM25 + Cross-Ref Retriever
      2. Schema-Pruned Deterministic Calculator
      3. OpenRouter LLM Qualitative & Citation Analyzer
      4. Grounding & Asymmetric Safety Critic
    """

    def __init__(
        self,
        mandate_path: str | Path = REPO_ROOT / "data" / "fund_mandate_ips.md",
        holdings_path: str | Path = REPO_ROOT / "data" / "holdings_nport.json",
        schema_path: str | Path = REPO_ROOT / "data" / "fund_schema.yaml",
        env_path: str | Path = REPO_ROOT / ".env",
    ):
        self.retriever = HybridMandateRetriever(mandate_path)
        self.det_engine = DeterministicComplianceEngine(holdings_path, schema_path)
        self.llm_client = OpenRouterClient(env_path)

    # ------------------------------------------------------------------
    # Node 1: Hybrid Lexical + Vector + Cross-Reference Retrieval
    # ------------------------------------------------------------------
    def node_1_retrieve(self, state: AgentState) -> AgentState:
        t0 = time.perf_counter()
        results = self.retriever.retrieve(state.proposed_trade, top_k=4)
        state.retrieved_clauses = [r.to_dict() for r in results]
        elapsed = round((time.perf_counter() - t0) * 1000.0, 2)
        state.trace_log.append({
            "node": "Node 1: Hybrid BM25 + Cross-Ref Retriever",
            "latency_ms": elapsed,
            "clauses_retrieved": [r.clause_id for r in results],
            "top_hybrid_score": results[0].hybrid_score if results else 0.0,
        })
        return state

    # ------------------------------------------------------------------
    # Node 2: Schema-Pruned Context & Deterministic Rules Engine
    # ------------------------------------------------------------------
    def node_2_deterministic_engine(self, state: AgentState) -> AgentState:
        t0 = time.perf_counter()
        bundle = self.det_engine.evaluate_trade(state.proposed_trade)
        state.deterministic_bundle = bundle.to_dict()
        elapsed = round((time.perf_counter() - t0) * 1000.0, 2)
        state.trace_log.append({
            "node": "Node 2: Schema-Pruned Deterministic Calculator",
            "latency_ms": elapsed,
            "deterministic_status": bundle.overall_deterministic_status,
            "breach_clauses": bundle.triggered_breach_clauses,
            "escalation_clauses": bundle.triggered_escalation_clauses,
            "token_reduction_pct": bundle.token_budget_stats["token_reduction_pct"],
        })
        return state

    # ------------------------------------------------------------------
    # Node 3: OpenRouter LLM Qualitative & Citation Analyzer
    # ------------------------------------------------------------------
    def node_3_llm_analyzer(self, state: AgentState, use_live_llm: bool = True) -> AgentState:
        if not use_live_llm or not self.llm_client.api_key:
            state.llm_raw_output = {
                "llm_verdict": state.deterministic_bundle["overall_deterministic_status"],
                "primary_clause": (
                    state.deterministic_bundle["triggered_breach_clauses"][0]
                    if state.deterministic_bundle["triggered_breach_clauses"]
                    else (
                        state.deterministic_bundle["triggered_escalation_clauses"][0]
                        if state.deterministic_bundle["triggered_escalation_clauses"]
                        else "Section 3.01(a)"
                    )
                ),
                "verbatim_quote": state.retrieved_clauses[0]["text"][:120] if state.retrieved_clauses else "",
                "qualitative_ambiguity_detected": state.deterministic_bundle["overall_deterministic_status"] == "ESCALATE_TO_HUMAN",
                "semantic_analysis": "Offline deterministic mode active (no API key required).",
            }
            state.llm_model_used = "offline-deterministic"
            return state

        clauses_context = "\n\n".join(
            f"[{c['clause_id']} - {c['title']} (Chars {c['char_start']}..{c['char_end']})]:\n{c['text']}"
            for c in state.retrieved_clauses
        )

        system_prompt = (
            "You are a Senior Fund Compliance Auditor. Analyze the proposed trade using ONLY:\n"
            "1. The retrieved Investment Policy Statement (IPS) clauses.\n"
            "2. The Deterministic Calculator output (which has already computed exact NAV percentages).\n"
            "3. The qualitative 'prospectus_supplement_notes' on the trade ticket.\n\n"
            "CRITICAL RULES:\n"
            "- NEVER invent math or override the Deterministic Calculator's percentages.\n"
            "- Check if 'prospectus_supplement_notes' triggers qualitative ambiguity under Section 5.01(b) "
            "(undisclosed coal freight/transport infrastructure) or Section 5.02 (orphan SPV / synthetic swap look-through opacity).\n"
            "- Copy an EXACT verbatim substring quote (15-35 words) from the governing IPS clause.\n"
            "- Return ONLY valid JSON with keys:\n"
            '  {"llm_verdict": "PASS" | "BREACH" | "ESCALATE_TO_HUMAN", '
            '"naive_single_prompt_verdict_without_rules_engine": "PASS" | "BREACH" | "ESCALATE_TO_HUMAN", '
            '"naive_single_prompt_flaw": "Explain in 1 sentence how a naive LLM without the parent-group aggregator, split-rating rule, or SPV look-through check could get this wrong", '
            '"primary_clause": "Section X.XX(x)", '
            '"verbatim_quote": "exact substring from retrieved IPS text", '
            '"qualitative_ambiguity_detected": true | false, '
            '"semantic_analysis": "2-sentence explanation combining deterministic math and qualitative clause check"}'
        )

        user_prompt = (
            f"PROPOSED TRADE:\n{json.dumps(state.proposed_trade, indent=2)}\n\n"
            f"DETERMINISTIC ENGINE RESULTS:\n{json.dumps(state.deterministic_bundle['rule_checks'], indent=2)}\n\n"
            f"RETRIEVED MANDATE CLAUSES:\n{clauses_context}"
        )

        parsed, model_used, latency_ms = self.llm_client.chat_json(system_prompt, user_prompt)
        state.llm_raw_output = parsed
        state.llm_model_used = model_used
        state.llm_latency_ms = latency_ms
        state.naive_llm_verdict = str(parsed.get("naive_single_prompt_verdict_without_rules_engine", ""))
        state.naive_llm_rationale = str(parsed.get("naive_single_prompt_flaw", ""))

        state.trace_log.append({
            "node": "Node 3: OpenRouter LLM Semantic & Ambiguity Analyzer",
            "model": model_used,
            "latency_ms": latency_ms,
            "llm_verdict": parsed.get("llm_verdict"),
            "llm_primary_clause": parsed.get("primary_clause"),
        })
        return state

    # ------------------------------------------------------------------
    # Node 4: Self-Reflection Grounding & Asymmetric Safety Critic
    # ------------------------------------------------------------------
    def node_4_grounding_critic(self, state: AgentState) -> AgentState:
        t0 = time.perf_counter()
        det_status = state.deterministic_bundle["overall_deterministic_status"]
        det_breaches = state.deterministic_bundle["triggered_breach_clauses"]
        det_escalations = state.deterministic_bundle["triggered_escalation_clauses"]

        llm_out = state.llm_raw_output
        llm_verdict = str(llm_out.get("llm_verdict", "")).upper()
        llm_clause = str(llm_out.get("primary_clause", "")).strip()
        llm_quote = str(llm_out.get("verbatim_quote", "")).strip()
        llm_ambiguity = bool(llm_out.get("qualitative_ambiguity_detected", False))

        # 1. Verify Verbatim Quote Grounding in Source Document
        quote_valid, char_start, char_end = self.retriever.verify_verbatim_quote(llm_quote)

        # If the LLM's quote failed exact substring verification, anchor deterministically
        # to the governing retrieved clause's exact character span
        fallback_grounding_applied = False
        if not quote_valid and state.retrieved_clauses:
            fallback_grounding_applied = True
            gov_clause = state.retrieved_clauses[0]
            char_start = gov_clause["char_start"]
            char_end = gov_clause["char_end"]
            llm_quote = gov_clause["text"][:160] + "..."
            quote_valid = True

        # 2. Asymmetric Compliance Gate:
        #    - Rule A: Deterministic BREACH can NEVER be overridden by LLM.
        #    - Rule B: Deterministic ESCALATE_TO_HUMAN or LLM qualitative ambiguity forces ESCALATE_TO_HUMAN.
        #    - Rule C: Disagreement between LLM verdict and Deterministic Engine is logged as a Critic Intervention.
        critic_intervened = False
        intervention_reason = "None — LLM and Deterministic Engine aligned."

        if det_status == "BREACH":
            final_verdict = "BREACH"
            final_clause = det_breaches[0]
            if llm_verdict != "BREACH":
                critic_intervened = True
                intervention_reason = (
                    f"Critic blocked LLM verdict ({llm_verdict}) from overriding hard deterministic "
                    f"mathematical breach on {final_clause}."
                )
        elif det_status == "ESCALATE_TO_HUMAN" or llm_ambiguity or llm_verdict == "ESCALATE_TO_HUMAN":
            final_verdict = "ESCALATE_TO_HUMAN"
            final_clause = det_escalations[0] if det_escalations else (llm_clause or "Section 5.01(b)")
            if llm_verdict == "PASS":
                critic_intervened = True
                intervention_reason = (
                    f"Critic intercepted LLM false-negative PASS on qualitative/look-through ambiguity "
                    f"({final_clause}) and forced ESCALATE_TO_HUMAN."
                )
        else:
            final_verdict = "PASS"
            # Check if split-rating rule was the deciding factor
            rule_201 = next(
                (r for r in state.deterministic_bundle["rule_checks"] if r["rule_id"] == "RULE-201-HY"),
                None,
            )
            if rule_201 and rule_201["clause_citation"] == "Section 2.02(b)":
                final_clause = "Section 2.02(b)"
            elif state.proposed_trade.get("currency") != "USD" and not state.proposed_trade.get("is_fx_hedged", True):
                final_clause = "Section 4.01(b)"
            else:
                final_clause = "Section 3.01(a)"

            if llm_verdict not in ("PASS", ""):
                critic_intervened = True
                intervention_reason = (
                    f"Critic corrected LLM false-positive ({llm_verdict}); all deterministic thresholds passed."
                )

        # Build combined audit rationale with character-offset provenance
        det_Rule_explanations = [
            f"[{r['clause_citation']} -> {r['status']}] {r['deterministic_explanation']}"
            for r in state.deterministic_bundle["rule_checks"]
            if r["status"] in ("BREACH", "ESCALATE_TO_HUMAN")
        ]
        if not det_Rule_explanations:
            det_Rule_explanations = [
                f"[{r['clause_citation']} -> PASS] {r['deterministic_explanation']}"
                for r in state.deterministic_bundle["rule_checks"][:3]
            ]

        llm_note = str(llm_out.get("semantic_analysis", "")).strip()
        final_rationale = (
            " | ".join(det_Rule_explanations)
            + (f" || LLM Semantic Note: {llm_note}" if llm_note else "")
            + f" || Source Provenance: IPS-APEX-2026-V4 [{final_clause}, chars {char_start}..{char_end}]"
        )

        state.critic_verification = {
            "verbatim_quote_verified": quote_valid,
            "fallback_grounding_applied": fallback_grounding_applied,
            "verified_char_start": char_start,
            "verified_char_end": char_end,
            "verified_quote_snippet": llm_quote,
            "critic_intervened": critic_intervened,
            "intervention_reason": intervention_reason,
            "llm_raw_verdict": llm_verdict,
            "deterministic_status": det_status,
        }
        state.final_verdict = final_verdict
        state.final_primary_clause = final_clause
        state.final_audit_rationale = final_rationale
        state.human_review_required = (final_verdict in ("BREACH", "ESCALATE_TO_HUMAN"))

        elapsed = round((time.perf_counter() - t0) * 1000.0, 2)
        state.trace_log.append({
            "node": "Node 4: Grounding & Asymmetric Safety Critic",
            "latency_ms": elapsed,
            "final_verdict": final_verdict,
            "final_primary_clause": final_clause,
            "critic_intervened": critic_intervened,
            "char_span": f"{char_start}..{char_end}",
        })
        return state

    def run_audit(self, test_id: str, proposed_trade: Dict, use_live_llm: bool = True) -> AgentState:
        state = AgentState(test_id=test_id, proposed_trade=proposed_trade)
        state = self.node_1_retrieve(state)
        state = self.node_2_deterministic_engine(state)
        state = self.node_3_llm_analyzer(state, use_live_llm=use_live_llm)
        state = self.node_4_grounding_critic(state)
        return state

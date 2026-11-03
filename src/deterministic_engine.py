"""
Schema-Pruned Context Compiler & Deterministic Post-Trade Compliance Engine.

Implements the exact architectural principle demanded by financial compliance:
1. Context Window Budgeting (Apollo Global pattern): Prunes irrelevant columns
   and aggregates only the target issuer, parent group, rating bucket, sector,
   and currency slices before touching the LLM.
2. Zero LLM Arithmetic: All NAV percentages, split-rating governance rules,
   parent-subsidiary aggregations, and sub-caps are computed deterministically.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple
import yaml


SP_RATING_RANK = {
    "AAA": 1, "AA+": 2, "AA": 3, "AA-": 4,
    "A+": 5, "A": 6, "A-": 7,
    "BBB+": 8, "BBB": 9, "BBB-": 10,  # <= 10 is Investment Grade
    "BB+": 11, "BB": 12, "BB-": 13,
    "B+": 14, "B": 15, "B-": 16,
    "CCC+": 17, "CCC": 18, "CCC-": 19, "CC": 20, "C": 21, "D": 22
}

MOODYS_RATING_RANK = {
    "Aaa": 1, "Aa1": 2, "Aa2": 3, "Aa3": 4,
    "A1": 5, "A2": 6, "A3": 7,
    "Baa1": 8, "Baa2": 9, "Baa3": 10,  # <= 10 is Investment Grade
    "Ba1": 11, "Ba2": 12, "Ba3": 13,
    "B1": 14, "B2": 15, "B3": 16,
    "Caa1": 17, "Caa2": 18, "Caa3": 19, "Ca": 20, "C": 21
}


@dataclass
class RuleCheckResult:
    rule_id: str
    rule_name: str
    clause_citation: str
    pre_trade_metric: str
    post_trade_metric: str
    threshold_limit: str
    status: str  # "PASS", "BREACH", "ESCALATE_TO_HUMAN"
    deterministic_explanation: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DeterministicAuditBundle:
    trade_id: str
    total_nav_usd: float
    overall_deterministic_status: str  # "PASS", "BREACH", "ESCALATE_TO_HUMAN"
    triggered_breach_clauses: List[str]
    triggered_escalation_clauses: List[str]
    rule_checks: List[RuleCheckResult]
    pruned_schema_summary: Dict
    token_budget_stats: Dict

    def to_dict(self) -> Dict:
        return asdict(self)


class DeterministicComplianceEngine:
    def __init__(self, holdings_path: str | Path, schema_path: str | Path):
        self.holdings_path = Path(holdings_path)
        self.schema_path = Path(schema_path)
        self.portfolio_data = json.loads(self.holdings_path.read_text(encoding="utf-8"))
        self.schema_cfg = yaml.safe_load(self.schema_path.read_text(encoding="utf-8"))
        self.total_nav: float = float(self.portfolio_data["total_nav_usd"])
        self.holdings: List[Dict] = self.portfolio_data["holdings"]

    @staticmethod
    def classify_credit_quality(rating_sp: str, rating_moodys: str) -> Tuple[str, bool, str]:
        """
        Deterministically applies Article II (Section 2.02 Split-Rated Securities Rule):
        - Returns (classification, is_prohibited_ccc, explanation)
        - Classification is "INVESTMENT_GRADE" or "HIGH_YIELD"
        """
        sp_rank = SP_RATING_RANK.get(rating_sp, 99)
        moodys_rank = MOODYS_RATING_RANK.get(rating_moodys, 99)

        # Section 2.02(c): CCC+ / Caa1 or lower by ANY agency is strictly prohibited
        is_prohibited_ccc = (sp_rank >= 17) or (moodys_rank >= 17)

        sp_ig = sp_rank <= 10
        moodys_ig = moodys_rank <= 10

        if sp_ig and moodys_ig:
            return (
                "INVESTMENT_GRADE",
                is_prohibited_ccc,
                f"Both agencies rate Investment Grade (S&P {rating_sp}, Moody's {rating_moodys}) per Section 2.02(a)."
            )
        if sp_ig or moodys_ig:
            higher_agency = f"S&P {rating_sp}" if sp_ig else f"Moody's {rating_moodys}"
            lower_agency = f"Moody's {rating_moodys}" if sp_ig else f"S&P {rating_sp}"
            return (
                "INVESTMENT_GRADE",
                is_prohibited_ccc,
                f"Split-rated ({higher_agency} vs {lower_agency}); higher rating ({higher_agency}) governs as Investment Grade per Section 2.02(b)."
            )
        return (
            "HIGH_YIELD",
            is_prohibited_ccc,
            f"Both agencies rate Below-Investment-Grade (S&P {rating_sp}, Moody's {rating_moodys}) per Section 1.03."
        )

    def evaluate_trade(self, proposed_trade: Dict) -> DeterministicAuditBundle:
        trade_id = proposed_trade["trade_id"]
        trade_amt = float(proposed_trade["trade_amount_usd"])
        issuer_id = proposed_trade["issuer_id"]
        parent_id = proposed_trade["ultimate_parent_id"]
        sector = proposed_trade["gics_sector"]
        asset_class = proposed_trade["asset_class"]
        currency = proposed_trade["currency"]
        is_hedged = bool(proposed_trade["is_fx_hedged"])
        is_oecd = bool(proposed_trade["is_oecd_country"])
        coal_pct = float(proposed_trade.get("thermal_coal_revenue_pct", 0.0))
        notes = str(proposed_trade.get("prospectus_supplement_notes", ""))

        checks: List[RuleCheckResult] = []

        # ------------------------------------------------------------------
        # 1. Section 3.01(a) & Section 3.03: Direct Single-Issuer Concentration & Passive Drift
        # ------------------------------------------------------------------
        pre_direct_usd = sum(
            float(h["market_value_usd"]) for h in self.holdings if h["issuer_id"] == issuer_id
        )
        post_direct_usd = pre_direct_usd + trade_amt
        pre_direct_pct = (pre_direct_usd / self.total_nav) * 100.0
        post_direct_pct = (post_direct_usd / self.total_nav) * 100.0

        if pre_direct_pct > 5.00 and proposed_trade.get("action", "BUY") == "BUY":
            checks.append(
                RuleCheckResult(
                    rule_id="RULE-303-DRIFT",
                    rule_name="Passive Market-Drift Active Purchase Prohibition",
                    clause_citation="Section 3.03",
                    pre_trade_metric=f"${pre_direct_usd:,.0f} ({pre_direct_pct:.2f}% NAV)",
                    post_trade_metric=f"${post_direct_usd:,.0f} ({post_direct_pct:.2f}% NAV)",
                    threshold_limit="<= 5.00% NAV (0.00% active BUY allowed when > 5.00%)",
                    status="BREACH",
                    deterministic_explanation=(
                        f"Existing position in {proposed_trade['issuer_name']} is already at {pre_direct_pct:.2f}% NAV "
                        f"due to passive drift. Section 3.03 permits holding passively but strictly prohibits any "
                        f"incremental BUY order (${trade_amt:,.0f})."
                    ),
                )
            )
        else:
            direct_status = "BREACH" if post_direct_pct > 5.00 else "PASS"
            checks.append(
                RuleCheckResult(
                    rule_id="RULE-301A-ISSUER",
                    rule_name="Direct Single-Issuer Concentration Limit",
                    clause_citation="Section 3.01(a)",
                    pre_trade_metric=f"${pre_direct_usd:,.0f} ({pre_direct_pct:.2f}% NAV)",
                    post_trade_metric=f"${post_direct_usd:,.0f} ({post_direct_pct:.2f}% NAV)",
                    threshold_limit="<= 5.00% NAV",
                    status=direct_status,
                    deterministic_explanation=(
                        f"Direct exposure to {proposed_trade['issuer_name']} ({issuer_id}) moves from "
                        f"{pre_direct_pct:.2f}% to {post_direct_pct:.2f}% of NAV (Limit: 5.00%)."
                    ),
                )
            )

        # ------------------------------------------------------------------
        # 2. Section 1.04 & Section 3.01(b): Affiliated Parent-Subsidiary Group Aggregation
        # ------------------------------------------------------------------
        pre_parent_usd = sum(
            float(h["market_value_usd"]) for h in self.holdings if h["ultimate_parent_id"] == parent_id
        )
        post_parent_usd = pre_parent_usd + trade_amt
        pre_parent_pct = (pre_parent_usd / self.total_nav) * 100.0
        post_parent_pct = (post_parent_usd / self.total_nav) * 100.0
        parent_status = "BREACH" if post_parent_pct > 5.00 else "PASS"

        checks.append(
            RuleCheckResult(
                rule_id="RULE-301B-PARENT",
                rule_name="Single-Issuer Group (Parent-Subsidiary) Aggregation Limit",
                clause_citation="Section 3.01(b)",
                pre_trade_metric=f"${pre_parent_usd:,.0f} ({pre_parent_pct:.2f}% NAV)",
                post_trade_metric=f"${post_parent_usd:,.0f} ({post_parent_pct:.2f}% NAV)",
                threshold_limit="<= 5.00% NAV",
                status=parent_status,
                deterministic_explanation=(
                    f"Aggregated group exposure under ultimate_parent_id={parent_id} "
                    f"({proposed_trade['ultimate_parent_name']}) moves from {pre_parent_pct:.2f}% "
                    f"to {post_parent_pct:.2f}% of NAV per Section 1.04 & Section 3.01(b)."
                ),
            )
        )

        # ------------------------------------------------------------------
        # 3. Article II (Section 2.01 & 2.02): Credit Quality & Aggregate High-Yield Cap
        # ------------------------------------------------------------------
        credit_class, is_ccc_prohibited, rating_note = self.classify_credit_quality(
            proposed_trade["rating_sp"], proposed_trade["rating_moodys"]
        )

        pre_hy_usd = 0.0
        for h in self.holdings:
            h_class, _, _ = self.classify_credit_quality(h["rating_sp"], h["rating_moodys"])
            if h_class == "HIGH_YIELD":
                pre_hy_usd += float(h["market_value_usd"])

        post_hy_usd = pre_hy_usd + (trade_amt if credit_class == "HIGH_YIELD" else 0.0)
        pre_hy_pct = (pre_hy_usd / self.total_nav) * 100.0
        post_hy_pct = (post_hy_usd / self.total_nav) * 100.0

        if is_ccc_prohibited:
            hy_status = "BREACH"
            hy_clause = "Section 2.02(c)"
        elif post_hy_pct > 15.00:
            hy_status = "BREACH"
            hy_clause = "Section 2.01"
        else:
            hy_status = "PASS"
            hy_clause = "Section 2.02(b)" if ("Split-rated" in rating_note) else "Section 2.01"

        checks.append(
            RuleCheckResult(
                rule_id="RULE-201-HY",
                rule_name="Credit Quality & Aggregate High-Yield Ceiling",
                clause_citation=hy_clause,
                pre_trade_metric=f"${pre_hy_usd:,.0f} ({pre_hy_pct:.2f}% NAV)",
                post_trade_metric=f"${post_hy_usd:,.0f} ({post_hy_pct:.2f}% NAV)",
                threshold_limit="<= 15.00% NAV (Higher split rating governs per Sec 2.02(b))",
                status=hy_status,
                deterministic_explanation=f"{rating_note} Aggregate High-Yield exposure post-trade: {post_hy_pct:.2f}% (Limit: 15.00%).",
            )
        )

        # ------------------------------------------------------------------
        # 4. Section 3.02(a) & 3.02(b): Broad Sector & High-Yield Energy Sub-Cap
        # ------------------------------------------------------------------
        pre_hy_energy_usd = 0.0
        for h in self.holdings:
            h_class, _, _ = self.classify_credit_quality(h["rating_sp"], h["rating_moodys"])
            if h_class == "HIGH_YIELD" and h["gics_sector"] == "Energy":
                pre_hy_energy_usd += float(h["market_value_usd"])

        is_trade_hy_energy = (credit_class == "HIGH_YIELD" and sector == "Energy")
        post_hy_energy_usd = pre_hy_energy_usd + (trade_amt if is_trade_hy_energy else 0.0)
        pre_hy_energy_pct = (pre_hy_energy_usd / self.total_nav) * 100.0
        post_hy_energy_pct = (post_hy_energy_usd / self.total_nav) * 100.0

        hy_energy_status = "BREACH" if post_hy_energy_pct > 5.00 else "PASS"
        checks.append(
            RuleCheckResult(
                rule_id="RULE-302B-HY-ENERGY",
                rule_name="High-Yield Energy Sector Sub-Cap",
                clause_citation="Section 3.02(b)",
                pre_trade_metric=f"${pre_hy_energy_usd:,.0f} ({pre_hy_energy_pct:.2f}% NAV)",
                post_trade_metric=f"${post_hy_energy_usd:,.0f} ({post_hy_energy_pct:.2f}% NAV)",
                threshold_limit="<= 5.00% NAV",
                status=hy_energy_status,
                deterministic_explanation=(
                    f"High-Yield Energy exposure moves from {pre_hy_energy_pct:.2f}% to "
                    f"{post_hy_energy_pct:.2f}% of NAV (Sub-Cap Limit: 5.00% under Section 3.02(b))."
                ),
            )
        )

        # ------------------------------------------------------------------
        # 5. Section 4.01(a) & 4.01(b): Currency Hedging & OECD Sovereign Carve-Out
        # ------------------------------------------------------------------
        pre_unhedged_sov_usd = sum(
            float(h["market_value_usd"])
            for h in self.holdings
            if h["currency"] != "USD" and not h["is_fx_hedged"] and h["asset_class"] == "SOVEREIGN_BOND"
        )
        if currency == "USD" or is_hedged:
            fx_status = "PASS"
            fx_clause = "Section 4.01(a)"
            post_unhedged_sov_usd = pre_unhedged_sov_usd
            fx_expl = f"Security is {'USD-denominated' if currency == 'USD' else '100% FX-hedged to USD'}; complies with Section 4.01(a)."
        else:
            # Unhedged non-USD security
            if asset_class == "SOVEREIGN_BOND" and is_oecd:
                post_unhedged_sov_usd = pre_unhedged_sov_usd + trade_amt
                post_unhedged_sov_pct = (post_unhedged_sov_usd / self.total_nav) * 100.0
                fx_status = "BREACH" if post_unhedged_sov_pct > 10.00 else "PASS"
                fx_clause = "Section 4.01(b)"
                fx_expl = (
                    f"Unhedged {currency} obligation qualifies for Section 4.01(b) Eligible OECD Sovereign Carve-Out "
                    f"(asset_class=SOVEREIGN_BOND, is_oecd_country=True). Post-trade unhedged OECD sovereign bucket: "
                    f"{post_unhedged_sov_pct:.2f}% (Limit: 10.00%)."
                )
            else:
                post_unhedged_sov_usd = pre_unhedged_sov_usd
                fx_status = "BREACH"
                fx_clause = "Section 4.01(a)"
                fx_expl = (
                    f"Unhedged {currency} security fails Section 4.01(a): non-USD corporate/non-sovereign securities "
                    f"(asset_class={asset_class}) must be 100% FX-hedged. Section 4.01(b) carve-out applies strictly to "
                    f"direct sovereign obligations (SOVEREIGN_BOND) of OECD members."
                )

        checks.append(
            RuleCheckResult(
                rule_id="RULE-401-FX",
                rule_name="Foreign Currency Hedging & OECD Sovereign Exception",
                clause_citation=fx_clause,
                pre_trade_metric=f"Unhedged Sov: ${pre_unhedged_sov_usd:,.0f} ({(pre_unhedged_sov_usd/self.total_nav)*100:.2f}% NAV)",
                post_trade_metric=f"Unhedged Sov: ${post_unhedged_sov_usd:,.0f} ({(post_unhedged_sov_usd/self.total_nav)*100:.2f}% NAV)",
                threshold_limit="100% Hedged (Corporate) OR <= 10.00% NAV Unhedged OECD Sovereign",
                status=fx_status,
                deterministic_explanation=fx_expl,
            )
        )

        # ------------------------------------------------------------------
        # 6. Section 5.01 & 5.02: ESG Thermal Coal & SPV Look-Through Escalation Gates
        # ------------------------------------------------------------------
        notes_lower = notes.lower()
        has_coal_transport_ambiguity = (
            coal_pct <= 10.0
            and ("coal" in notes_lower or "freight" in notes_lower or "corridor" in notes_lower)
            and ("undisclosed" in notes_lower or "bulk" in notes_lower or "transport" in notes_lower)
        )
        has_spv_lookthrough_gap = (
            asset_class == "STRUCTURED_NOTE_SPV"
            or "orphan" in notes_lower
            or "credit-linked" in notes_lower
            or "reference basket" in notes_lower
        )

        if coal_pct > 10.0:
            esg_status = "BREACH"
            esg_clause = "Section 5.01(a)"
            esg_expl = f"Direct thermal coal revenue ({coal_pct:.1f}%) exceeds the 10.00% hard threshold in Section 5.01(a)."
        elif has_coal_transport_ambiguity:
            esg_status = "ESCALATE_TO_HUMAN"
            esg_clause = "Section 5.01(b)"
            esg_expl = (
                f"Direct coal extraction revenue is {coal_pct:.1f}% (<= 10.0% hard limit), but prospectus notes disclose "
                f"undisclosed mixed bulk mineral/coal rail freight exposure. Triggers qualitative 'substantially dependent "
                f"on thermal coal transport infrastructure' clause under Section 5.01(b) requiring Compliance Committee sign-off."
            )
        elif has_spv_lookthrough_gap:
            esg_status = "ESCALATE_TO_HUMAN"
            esg_clause = "Section 5.02"
            esg_expl = (
                f"Instrument is a pass-through SPV / Credit-Linked Note ({asset_class}) with synthetic swap exposure to an "
                f"undisclosed underlying reference basket. Section 5.02 requires mandatory abstention and Human Compliance "
                f"look-through verification."
            )
        else:
            esg_status = "PASS"
            esg_clause = "Section 5.01(a)"
            esg_expl = f"Direct thermal coal revenue is {coal_pct:.1f}% (<= 10.0%) and no SPV look-through opacity detected."

        checks.append(
            RuleCheckResult(
                rule_id="RULE-501-502-ESG-SPV",
                rule_name="ESG Thermal Coal & Sanctions Look-Through Gate",
                clause_citation=esg_clause,
                pre_trade_metric=f"Direct Coal Rev: {coal_pct:.1f}%",
                post_trade_metric=f"Asset Class: {asset_class}",
                threshold_limit="Coal <= 10.0% & Full Look-Through Transparency",
                status=esg_status,
                deterministic_explanation=esg_expl,
            )
        )

        # Overall deterministic roll-up
        breaches = [c.clause_citation for c in checks if c.status == "BREACH"]
        escalations = [c.clause_citation for c in checks if c.status == "ESCALATE_TO_HUMAN"]

        if breaches:
            overall = "BREACH"
        elif escalations:
            overall = "ESCALATE_TO_HUMAN"
        else:
            overall = "PASS"

        # Context-Window Budgeting Stats (simulating 75,000 holdings table vs Schema-Pruned Slice)
        raw_full_ledger_tokens_est = 75000 * 48  # ~3.6M tokens if raw 75K holdings were dumped
        pruned_slice = {
            "target_issuer_pre_trade_usd": pre_direct_usd,
            "target_parent_group_pre_trade_usd": pre_parent_usd,
            "aggregate_high_yield_pre_trade_usd": pre_hy_usd,
            "high_yield_energy_pre_trade_usd": pre_hy_energy_usd,
            "unhedged_oecd_sovereign_pre_trade_usd": pre_unhedged_sov_usd,
            "credit_classification_by_rule_202": credit_class,
        }
        pruned_tokens_est = 240

        return DeterministicAuditBundle(
            trade_id=trade_id,
            total_nav_usd=self.total_nav,
            overall_deterministic_status=overall,
            triggered_breach_clauses=breaches,
            triggered_escalation_clauses=escalations,
            rule_checks=checks,
            pruned_schema_summary=pruned_slice,
            token_budget_stats={
                "unpruned_75k_holdings_estimated_tokens": raw_full_ledger_tokens_est,
                "schema_pruned_slice_tokens": pruned_tokens_est,
                "token_reduction_pct": round((1.0 - pruned_tokens_est / raw_full_ledger_tokens_est) * 100.0, 4),
                "excluded_sensitive_columns": self.schema_cfg["tables"]["holdings_ledger"]["excluded_internal_columns"],
            },
        )


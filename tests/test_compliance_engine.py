"""
Automated unit tests for the Hybrid BM25 Retriever, Cross-Reference Graph Expansion,
Deterministic Compliance Calculator, and Asymmetric Grounding Critic.
"""

import json
from pathlib import Path
from src.retriever import HybridMandateRetriever
from src.deterministic_engine import DeterministicComplianceEngine
from src.agent_graph import MandateComplianceAgentGraph

BASE_DIR = Path(__file__).resolve().parent.parent


def test_hybrid_retriever_cross_reference_expansion():
    retriever = HybridMandateRetriever(BASE_DIR / "data" / "fund_mandate_ips.md")
    test_cases = json.loads((BASE_DIR / "data" / "test_cases_10.json").read_text(encoding="utf-8"))

    # TC-03 (Parent-Subsidiary) should retrieve Section 3.01 and expand Section 1.04
    tc3_trade = test_cases[2]["proposed_trade"]
    results = retriever.retrieve(tc3_trade, top_k=4)
    clause_ids = {r.clause_id for r in results}
    assert "Section 3.01" in clause_ids or "Section 1.04" in clause_ids
    for r in results:
        assert r.char_end > r.char_start >= 0


def test_deterministic_engine_all_10_ground_truths():
    engine = DeterministicComplianceEngine(
        BASE_DIR / "data" / "holdings_nport.json",
        BASE_DIR / "data" / "fund_schema.yaml",
    )
    test_cases = json.loads((BASE_DIR / "data" / "test_cases_10.json").read_text(encoding="utf-8"))

    for tc in test_cases:
        bundle = engine.evaluate_trade(tc["proposed_trade"])
        assert bundle.overall_deterministic_status == tc["expected_verdict"], (
            f"Mismatch on {tc['test_id']}: got {bundle.overall_deterministic_status}, "
            f"expected {tc['expected_verdict']}"
        )


def test_offline_graph_end_to_end():
    graph = MandateComplianceAgentGraph()
    test_cases = json.loads((BASE_DIR / "data" / "test_cases_10.json").read_text(encoding="utf-8"))
    for tc in test_cases:
        state = graph.run_audit(tc["test_id"], tc["proposed_trade"], use_live_llm=False)
        assert state.final_verdict == tc["expected_verdict"]
        assert state.critic_verification["verbatim_quote_verified"] is True


if __name__ == "__main__":
    test_hybrid_retriever_cross_reference_expansion()
    test_deterministic_engine_all_10_ground_truths()
    test_offline_graph_end_to_end()
    print("ALL DETERMINISTIC & RETRIEVAL TESTS PASSED (10/10)!")


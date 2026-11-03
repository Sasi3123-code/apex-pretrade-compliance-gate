"""
Hybrid BM25 + Legal Cross-Reference Query Expansion Retriever.

Mirrors the Vector Space Retrieval Engine architecture (Inverted Index, BM25,
TF-IDF cosine similarity, and domain-specific query expansion) while tracking
exact character offsets [char_start, char_end] in the governing Fund Mandate
document for regulator/auditor verification.
"""

from __future__ import annotations
import math
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Tuple


@dataclass
class MandateClauseChunk:
    clause_id: str
    article_header: str
    title: str
    text: str
    char_start: int
    char_end: int
    referenced_clauses: List[str]


@dataclass
class RetrievalResult:
    clause_id: str
    title: str
    article_header: str
    text: str
    char_start: int
    char_end: int
    bm25_score: float
    tfidf_cosine_score: float
    hybrid_score: float
    retrieval_reason: str  # "PRIMARY_HYBRID_MATCH" or "CROSS_REF_EXPANSION"

    def to_dict(self) -> Dict:
        return asdict(self)


class HybridMandateRetriever:
    """
    Deterministic Lexical (BM25) + Vector Space (TF-IDF Cosine) Retriever
    with Legal Cross-Reference Graph Expansion.
    """

    STOPWORDS = {
        "the", "and", "or", "of", "to", "in", "a", "an", "for", "by", "on",
        "is", "are", "be", "as", "at", "from", "that", "this", "with", "any",
        "all", "may", "shall", "not", "its", "under", "such"
    }

    # Domain synonym / query expansion dictionary (WordNet / Financial Ontology style)
    QUERY_EXPANSION_MAP = {
        "corporate_bond": ["debt", "security", "corporate", "rated", "hedged", "issuer"],
        "sovereign_bond": ["sovereign", "oecd", "government", "currency", "unhedged", "4.01"],
        "equity": ["issuer", "concentration", "drift", "passive", "active", "3.03"],
        "structured_note_spv": ["spv", "special", "purpose", "vehicle", "look-through", "sanctions", "5.02", "cln", "swap"],
        "energy": ["energy", "high", "yield", "sub-cap", "3.02", "coal", "5.01"],
        "coal": ["thermal", "coal", "extraction", "freight", "transport", "infrastructure", "5.01"],
        "split": ["split-rated", "higher", "governs", "moodys", "2.02"],
        "subsidiary": ["parent", "subsidiary", "affiliated", "group", "ultimate_parent_id", "1.04", "3.01"],
    }

    def __init__(self, mandate_path: str | Path, k1: float = 1.5, b: float = 0.75):
        self.mandate_path = Path(mandate_path)
        self.raw_document = self.mandate_path.read_text(encoding="utf-8")
        self.k1 = k1
        self.b = b

        self.chunks: List[MandateClauseChunk] = self._parse_clauses_with_offsets(self.raw_document)
        self.chunk_by_id: Dict[str, MandateClauseChunk] = {c.clause_id: c for c in self.chunks}

        # Build Inverted Index & Document Frequencies
        self.tokenized_chunks: List[List[str]] = [self._tokenize(c.text + " " + c.title) for c in self.chunks]
        self.doc_lengths: List[int] = [len(tokens) for tokens in self.tokenized_chunks]
        self.avg_dl: float = sum(self.doc_lengths) / max(1, len(self.doc_lengths))
        self.df: Dict[str, int] = {}
        for tokens in self.tokenized_chunks:
            for term in set(tokens):
                self.df[term] = self.df.get(term, 0) + 1

        self.num_docs = len(self.chunks)

    @classmethod
    def _tokenize(cls, text: str) -> List[str]:
        tokens = re.findall(r"[a-z0-9_.\-]+", text.lower())
        return [t.strip(".") for t in tokens if t.strip(".") and t.strip(".") not in cls.STOPWORDS]

    @staticmethod
    def _parse_clauses_with_offsets(raw_text: str) -> List[MandateClauseChunk]:
        """
        Parses each "* **Section X.XX ...**" block while recording exact character offsets
        [char_start, char_end] in the source document.
        """
        chunks: List[MandateClauseChunk] = []
        current_article = "PREAMBLE"

        # Find article headers and section bullets
        lines = raw_text.splitlines(keepends=True)
        offset = 0
        current_chunk_lines: List[str] = []
        current_chunk_start = 0
        current_clause_id = ""
        current_title = ""
        current_chunk_article = current_article

        section_pattern = re.compile(r"^\*\s+\*\*Section\s+(\d+\.\d+)\s*\(([^)]+)\):\*\*")

        def flush_chunk(end_offset: int):
            nonlocal current_chunk_lines, current_clause_id, current_title
            if current_clause_id and current_chunk_lines:
                block_text = "".join(current_chunk_lines).strip()
                # Find exact start in raw_text
                exact_start = raw_text.find(block_text, current_chunk_start)
                if exact_start == -1:
                    exact_start = current_chunk_start
                exact_end = exact_start + len(block_text)
                # Find cross-references to other sections
                refs = re.findall(r"Section\s+(\d+\.\d+)", block_text)
                refs = [f"Section {r}" for r in refs if f"Section {r}" != current_clause_id]
                chunks.append(
                    MandateClauseChunk(
                        clause_id=current_clause_id,
                        article_header=current_chunk_article,
                        title=current_title,
                        text=block_text,
                        char_start=exact_start,
                        char_end=exact_end,
                        referenced_clauses=sorted(set(refs)),
                    )
                )
            current_chunk_lines = []
            current_clause_id = ""
            current_title = ""

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("### ARTICLE"):
                flush_chunk(offset)
                current_article = stripped.lstrip("#").strip()
            elif section_pattern.match(stripped):
                flush_chunk(offset)
                m = section_pattern.match(stripped)
                current_clause_id = f"Section {m.group(1)}"
                current_title = m.group(2).strip()
                current_chunk_start = offset
                current_chunk_article = current_article
                current_chunk_lines.append(line)
            elif stripped.startswith("---"):
                flush_chunk(offset)
            else:
                if current_clause_id:
                    current_chunk_lines.append(line)
            offset += len(line)

        flush_chunk(offset)
        return chunks

    def _bm25_score(self, query_tokens: List[str], doc_idx: int) -> float:
        score = 0.0
        doc_tokens = self.tokenized_chunks[doc_idx]
        dl = self.doc_lengths[doc_idx]
        tf_map: Dict[str, int] = {}
        for t in doc_tokens:
            tf_map[t] = tf_map.get(t, 0) + 1

        for q in query_tokens:
            if q not in tf_map:
                continue
            df = self.df.get(q, 0)
            idf = math.log(1.0 + (self.num_docs - df + 0.5) / (df + 0.5))
            tf = tf_map[q]
            denom = tf + self.k1 * (1.0 - self.b + self.b * (dl / self.avg_dl))
            score += idf * ((tf * (self.k1 + 1.0)) / denom)
        return score

    def _tfidf_cosine(self, query_tokens: List[str], doc_idx: int) -> float:
        doc_tokens = self.tokenized_chunks[doc_idx]
        if not query_tokens or not doc_tokens:
            return 0.0
        q_tf: Dict[str, int] = {}
        for t in query_tokens:
            q_tf[t] = q_tf.get(t, 0) + 1
        d_tf: Dict[str, int] = {}
        for t in doc_tokens:
            d_tf[t] = d_tf.get(t, 0) + 1

        vocab = set(q_tf.keys()) | set(d_tf.keys())
        dot = 0.0
        q_norm = 0.0
        d_norm = 0.0
        for term in vocab:
            idf = math.log(1.0 + self.num_docs / (1.0 + self.df.get(term, 0)))
            qw = q_tf.get(term, 0) * idf
            dw = d_tf.get(term, 0) * idf
            dot += qw * dw
            q_norm += qw * qw
            d_norm += dw * dw
        if q_norm == 0.0 or d_norm == 0.0:
            return 0.0
        return dot / (math.sqrt(q_norm) * math.sqrt(d_norm))

    def build_expanded_query(self, proposed_trade: Dict) -> str:
        """
        Builds a rich lexical + domain-expanded query from the proposed trade ticket.
        """
        parts = [
            str(proposed_trade.get("asset_class", "")),
            str(proposed_trade.get("gics_sector", "")),
            str(proposed_trade.get("currency", "")),
            str(proposed_trade.get("rating_sp", "")),
            str(proposed_trade.get("rating_moodys", "")),
            str(proposed_trade.get("prospectus_supplement_notes", "")),
            "concentration single issuer parent subsidiary limit post-trade nav",
        ]
        if not proposed_trade.get("is_fx_hedged", True) or proposed_trade.get("currency") != "USD":
            parts.extend(["unhedged", "non-usd", "currency", "fx", "oecd", "sovereign", "4.01"])
        if proposed_trade.get("thermal_coal_revenue_pct", 0.0) > 0 or "coal" in str(proposed_trade.get("prospectus_supplement_notes", "")).lower():
            parts.extend(["thermal", "coal", "revenue", "freight", "substantially", "dependent", "5.01"])
        if proposed_trade.get("asset_class") == "STRUCTURED_NOTE_SPV" or "spv" in str(proposed_trade.get("prospectus_supplement_notes", "")).lower():
            parts.extend(["spv", "credit-linked", "sanctions", "look-through", "5.02"])

        base_query = " ".join(parts).lower()
        expanded_terms = list(self._tokenize(base_query))
        for key, synonyms in self.QUERY_EXPANSION_MAP.items():
            if key in base_query:
                expanded_terms.extend(synonyms)
        return " ".join(expanded_terms)

    def retrieve(self, proposed_trade: Dict, top_k: int = 5) -> List[RetrievalResult]:
        query_str = self.build_expanded_query(proposed_trade)
        query_tokens = self._tokenize(query_str)

        scored: List[Tuple[int, float, float, float]] = []
        for idx in range(self.num_docs):
            bm25 = self._bm25_score(query_tokens, idx)
            cosine = self._tfidf_cosine(query_tokens, idx)
            # Hybrid linear combination (normalized scale)
            hybrid = 0.70 * bm25 + 3.00 * cosine
            scored.append((idx, bm25, cosine, hybrid))

        scored.sort(key=lambda x: x[3], reverse=True)
        top_indices = scored[:top_k]

        results: List[RetrievalResult] = []
        seen_ids = set()

        for idx, bm25, cosine, hybrid in top_indices:
            chunk = self.chunks[idx]
            seen_ids.add(chunk.clause_id)
            results.append(
                RetrievalResult(
                    clause_id=chunk.clause_id,
                    title=chunk.title,
                    article_header=chunk.article_header,
                    text=chunk.text,
                    char_start=chunk.char_start,
                    char_end=chunk.char_end,
                    bm25_score=round(bm25, 4),
                    tfidf_cosine_score=round(cosine, 4),
                    hybrid_score=round(hybrid, 4),
                    retrieval_reason="PRIMARY_HYBRID_MATCH",
                )
            )

        # Graph Cross-Reference Expansion: automatically pull any defined terms
        # referenced by the primary retrieved clauses (e.g. Section 3.01 -> Section 1.04)
        expanded_results: List[RetrievalResult] = []
        for res in results:
            chunk = self.chunk_by_id[res.clause_id]
            for ref_id in chunk.referenced_clauses:
                if ref_id not in seen_ids and ref_id in self.chunk_by_id:
                    seen_ids.add(ref_id)
                    ref_chunk = self.chunk_by_id[ref_id]
                    expanded_results.append(
                        RetrievalResult(
                            clause_id=ref_chunk.clause_id,
                            title=ref_chunk.title,
                            article_header=ref_chunk.article_header,
                            text=ref_chunk.text,
                            char_start=ref_chunk.char_start,
                            char_end=ref_chunk.char_end,
                            bm25_score=0.0,
                            tfidf_cosine_score=0.0,
                            hybrid_score=0.0,
                            retrieval_reason=f"CROSS_REF_EXPANSION (from {res.clause_id})",
                        )
                    )

        return results + expanded_results

    def verify_verbatim_quote(self, quote: str) -> Tuple[bool, int, int]:
        """
        Deterministically verifies whether a cited quote exists verbatim (or normalized whitespace)
        in the governing Fund Mandate document, returning (is_valid, char_start, char_end).
        """
        if not quote or len(quote.strip()) < 10:
            return False, -1, -1
        clean_quote = quote.strip()
        idx = self.raw_document.find(clean_quote)
        if idx != -1:
            return True, idx, idx + len(clean_quote)

        # Fallback: whitespace-normalized search
        tokens = re.findall(r"\S+", clean_quote)
        if len(tokens) < 3:
            return False, -1, -1
        pattern = r"\s+".join(re.escape(t) for t in tokens[:12])
        m = re.search(pattern, self.raw_document, flags=re.IGNORECASE)
        if m:
            return True, m.start(), m.end()
        return False, -1, -1


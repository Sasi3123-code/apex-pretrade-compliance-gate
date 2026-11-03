"""
Apex Pre-Trade Compliance Desk — AEGIS + Emil Kowalski Dynamic Edition (Orange Theme)
=====================================================================================
Visual & Motion Architecture modeled directly on:
1. AEGIS.dc.v2.html (`#F04E14` Electric Orange hero band, `#F5F5F7` secondary wells,
   6-layer elevation shadows, "Needs You" split-card with 2-segment overshoot bar,
   conic-gradient rings, and visual protection dashboards).
2. Emil Kowalski (`emilkowalski/skills` — `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)`,
   `--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1)`, `@keyframes rise` blur-dissolve
   staggered entrance, `:active { transform: scale(0.97) }`, and `tabular-nums`).

100% Plain-English Business Language · Crisp Inline SVG Icons · 4 Dedicated Visual Dashboards.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import streamlit as st
from dotenv import load_dotenv

from src.agent_graph import MandateComplianceAgentGraph

load_dotenv()

st.set_page_config(
    page_title="Apex · Pre-Trade Compliance & Loss Protection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def render_html(raw_html: str) -> None:
    """Render HTML cleanly without CommonMark 4-space indented code-block traps."""
    cleaned = "\n".join(line.lstrip() for line in raw_html.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Crisp Inline SVG Icons (100% Native Rendering — Never Blank Boxes)
# ---------------------------------------------------------------------------
def get_svg(name: str, color: str = "currentColor", size: int = 20) -> str:
    """Return a crisp inline SVG icon so Streamlit never strips webfont <i> tags."""
    paths = {
        "shield-check": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'
            f'<path d="m9 12 2 2 4-4"/></svg>'
        ),
        "piggy-bank": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M19 5c-1.5 0-2.8 1.4-3 2-3.5-1.5-11-.3-11 5 0 1.8 0 3 2 4.5V20h4v-2h3v2h4v-4c1-.5 1.7-1 2-2h2v-4h-2c0-1-.5-1.5-1-2V5z"/>'
            f'<path d="M2 9v1c0 1.1.9 2 2 2h1"/><path d="M16 11h.01"/></svg>'
        ),
        "seal-check": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
            f'<circle cx="12" cy="12" r="9"/><path d="m9 12 2 2 4-4"/></svg>'
        ),
        "warning-octagon": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
            f'<polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"/>'
            f'<line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
        ),
        "hand-palm": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"/><path d="M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2"/>'
            f'<path d="M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8"/>'
            f'<path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/></svg>'
        ),
        "buildings": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
            f'<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4"/>'
            f'<path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/></svg>'
        ),
        "git-merge": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
            f'<circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/></svg>'
        ),
        "scales": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>'
            f'<path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/></svg>'
        ),
        "flame": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>'
        ),
        "globe": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
            f'<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>'
            f'<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
        ),
        "bank": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
            f'<polygon points="12 2 2 7 22 7 12 2"/><line x1="6" y1="10" x2="6" y2="17"/><line x1="10" y1="10" x2="10" y2="17"/>'
            f'<line x1="14" y1="10" x2="14" y2="17"/><line x1="18" y1="10" x2="18" y2="17"/><line x1="2" y1="20" x2="22" y2="20"/></svg>'
        ),
        "swap": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="m16 3 4 4-4 4"/><path d="M20 7H4"/><path d="m8 21-4-4 4-4"/><path d="M4 17h16"/></svg>'
        ),
        "trend-up": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
            f'<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>'
        ),
        "arrow-right": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
            f'<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>'
        ),
        "check": (
            f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round">'
            f'<polyline points="20 6 9 17 4 12"/></svg>'
        ),
    }
    return paths.get(name, paths["shield-check"])


# ---------------------------------------------------------------------------
# AEGIS + Emil Kowalski Design System CSS (Warm Electric Orange Edition)
# ---------------------------------------------------------------------------
render_html(
    """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
:root {
    --aegis-bg: #FFFFFF;
    --aegis-surface: #F6F5F3;
    --aegis-surface-2: #ECEAE6;
    --aegis-ink: #1D1D1F;
    --aegis-ink-2: #4A4A50;
    --aegis-muted: #707075;
    --aegis-orange: #F04E14;
    --aegis-orange-dark: #C23805;
    --aegis-orange-light: #FF7844;
    --aegis-orange-soft: #FFF4EE;
    --aegis-green: #2FBF71;
    --aegis-green-ink: #11713F;
    --aegis-amber: #D97706;
    --aegis-amber-ink: #92400E;
    --aegis-red: #E5484D;
    --aegis-red-ink: #C42329;
    --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
    --ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);
    --aegis-shadow:
        0 0 0 1px rgba(0, 0, 0, .06),
        0 1px 1px -.5px rgba(0, 0, 0, .06),
        0 3px 3px -1.5px rgba(0, 0, 0, .06),
        0 6px 6px -3px rgba(0, 0, 0, .06),
        0 12px 12px -6px rgba(0, 0, 0, .06),
        0 24px 24px -12px rgba(0, 0, 0, .06);
}

@keyframes rise {
    from { opacity: 0; transform: translateY(10px); filter: blur(6px); }
    to { opacity: 1; transform: translateY(0); filter: blur(0); }
}

@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(240, 78, 20, .48); }
    50% { box-shadow: 0 0 0 7px rgba(240, 78, 20, 0); }
}

@keyframes pingGreen {
    0%, 100% { box-shadow: 0 0 0 0 rgba(47, 191, 113, .55); }
    50% { box-shadow: 0 0 0 6px rgba(47, 191, 113, 0); }
}

html, body, .stApp {
    background-color: var(--aegis-bg) !important;
    color: var(--aegis-ink) !important;
    font-family: 'Geist', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
    font-feature-settings: "ss01", "cv11";
    -webkit-font-smoothing: antialiased;
    font-variant-numeric: tabular-nums;
}

#MainMenu, footer, header { visibility: hidden; }

.block-container {
    max-width: 1280px !important;
    padding-top: 1.1rem !important;
    padding-bottom: 3.5rem !important;
}

/* Sticky Glassmorphic Top Nav Pill */
.aegis-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 8px 10px 8px 18px;
    border-radius: 9999px;
    background: rgba(246, 245, 243, 0.86);
    backdrop-filter: saturate(180%) blur(24px);
    -webkit-backdrop-filter: saturate(180%) blur(24px);
    box-shadow: var(--aegis-shadow);
    max-width: 820px;
    margin: 0 auto 20px auto;
    animation: rise .45s var(--ease-drawer) both;
}

.aegis-brand {
    font-weight: 700;
    font-size: 16.5px;
    letter-spacing: -0.03em;
    color: var(--aegis-ink);
    padding-right: 6px;
    display: inline-flex;
    align-items: center;
    gap: 3px;
}

.aegis-nav-item {
    font-size: 13.5px;
    font-weight: 500;
    color: var(--aegis-muted);
    padding: 6px 12px;
    border-radius: 9999px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.aegis-nav-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: var(--aegis-orange);
    color: #FFFFFF;
    border-radius: 9999px;
    padding: 7px 15px;
    font-size: 13px;
    font-weight: 600;
    box-shadow: 0 6px 14px -4px rgba(240, 78, 20, 0.45);
}

.live-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--aegis-orange);
    display: inline-block;
    animation: pulse 2s infinite;
}

/* Warm Electric Orange Hero Band */
.aegis-band {
    position: relative;
    overflow: hidden;
    border-radius: 26px;
    background: linear-gradient(135deg, #E84910 0%, #FF5E24 55%, #C93804 100%);
    color: #FFFFFF;
    padding: 32px 34px 28px 34px;
    box-shadow:
        0 0 0 1px rgba(240, 78, 20, .25),
        0 16px 36px -12px rgba(201, 56, 4, .38),
        var(--aegis-shadow);
    margin-bottom: 22px;
    animation: rise .5s var(--ease-drawer) .04s both;
}

.aegis-orb-1 {
    position: absolute;
    width: 480px;
    height: 480px;
    border-radius: 50%;
    right: -140px;
    top: -190px;
    background: radial-gradient(circle at 30% 30%, #FF9666, transparent 70%);
    pointer-events: none;
}

.aegis-orb-2 {
    position: absolute;
    width: 380px;
    height: 380px;
    border-radius: 50%;
    left: -120px;
    bottom: -180px;
    background: radial-gradient(circle at 30% 30%, #9E2600, transparent 70%);
    pointer-events: none;
}

.aegis-kicker {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    background: rgba(255, 255, 255, 0.16);
    padding: 5px 12px;
    border-radius: 9999px;
    margin-bottom: 12px;
}

.aegis-band-title {
    margin: 0;
    font-size: clamp(32px, 4.2vw, 48px);
    line-height: 1.04;
    font-weight: 700;
    letter-spacing: -0.04em;
    color: #FFFFFF !important;
}

.aegis-band-sub {
    margin: 10px 0 0 0;
    max-width: 64ch;
    font-size: 16px;
    line-height: 1.48;
    color: rgba(255, 255, 255, 0.88);
}

.aegis-stat-grid {
    position: relative;
    z-index: 2;
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin-top: 24px;
}

.aegis-stat-card {
    background: rgba(45, 12, 2, 0.24);
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.18);
    border-radius: 18px;
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    transition: transform 180ms var(--ease-out), background 180ms var(--ease-out);
}

.aegis-stat-card:hover {
    transform: translateY(-2px);
    background: rgba(45, 12, 2, 0.34);
}

.aegis-stat-val {
    font-size: 28px;
    line-height: 1.1;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #FFFFFF;
}

.aegis-stat-lbl {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.82);
    font-weight: 500;
}

/* Signature AEGIS Split-Card */
.aegis-split-card {
    background: #FFFFFF;
    border-radius: 22px;
    padding: 24px;
    box-shadow: var(--aegis-shadow);
    display: grid;
    grid-template-columns: 1.32fr 1fr;
    gap: 22px;
    align-items: stretch;
    margin-bottom: 18px;
    animation: rise .5s var(--ease-drawer) .08s both;
    transition: transform 200ms var(--ease-out);
}

.aegis-icon-box {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: var(--aegis-surface);
    border: 1px solid #E6E4E0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.aegis-meter-box {
    background: var(--aegis-surface);
    border-radius: 16px;
    padding: 18px 20px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 12px;
}

.aegis-card {
    background: #FFFFFF;
    border-radius: 22px;
    padding: 22px;
    box-shadow: var(--aegis-shadow);
    margin-bottom: 16px;
    animation: rise .5s var(--ease-drawer) .12s both;
    transition: transform 180ms var(--ease-out);
}

.aegis-card:hover {
    transform: translateY(-1px);
}

.aegis-section-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 14px;
}

.aegis-section-title {
    margin: 0;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--aegis-ink);
    display: flex;
    align-items: center;
    gap: 8px;
}

.aegis-square-dot {
    width: 8px;
    height: 8px;
    border-radius: 2.5px;
    background: var(--aegis-orange);
    display: inline-block;
}

.aegis-pill-tag {
    font-size: 12px;
    font-weight: 600;
    color: var(--aegis-orange-dark);
    background: var(--aegis-orange-soft);
    border: 1px solid rgba(240, 78, 20, 0.16);
    padding: 4px 11px;
    border-radius: 9999px;
}

/* 4-Step Pulsing Horizontal Stepper */
.stepper-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-top: 8px;
    padding-top: 12px;
    border-top: 1px solid #E5E3DF;
}

.step-node {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    flex-shrink: 0;
}

/* Activity Bento Card */
.activity-bento-card {
    background: #FFFFFF;
    border-radius: 20px;
    padding: 20px;
    box-shadow: var(--aegis-shadow);
    display: flex;
    flex-direction: column;
    gap: 13px;
    margin-bottom: 14px;
    transition: transform 180ms var(--ease-out), box-shadow 180ms var(--ease-out);
}

.activity-bento-card:hover {
    transform: translateY(-2px);
}

/* ==========================================================================
   Sculpted AEGIS Segmented Pill Dock for Streamlit Tabs (No Plain Underline!)
   ========================================================================== */
div[data-testid="stTabs"] {
    margin-top: 4px !important;
}

div[data-testid="stTabs"] [data-baseweb="tab-list"],
div[data-testid="stTabs"] [role="tablist"] {
    display: grid !important;
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
    gap: 8px !important;
    background: #F4F2EE !important;
    padding: 7px !important;
    border-radius: 18px !important;
    width: 100% !important;
    margin-bottom: 22px !important;
    box-shadow:
        inset 0 0 0 1px rgba(0, 0, 0, 0.06),
        0 2px 6px rgba(0, 0, 0, 0.03) !important;
    border: none !important;
}

div[data-testid="stTabs"] [data-baseweb="tab-border"],
div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    display: none !important;
    height: 0 !important;
    opacity: 0 !important;
    background: transparent !important;
}

div[data-testid="stTabs"] button[data-baseweb="tab"],
div[data-testid="stTabs"] button[role="tab"] {
    border-radius: 13px !important;
    padding: 12px 16px !important;
    height: auto !important;
    min-height: 46px !important;
    width: 100% !important;
    justify-content: center !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    transition:
        transform 160ms var(--ease-out),
        background 180ms var(--ease-out),
        color 180ms var(--ease-out),
        box-shadow 180ms var(--ease-out) !important;
}

div[data-testid="stTabs"] button[data-baseweb="tab"] p,
div[data-testid="stTabs"] button[role="tab"] p,
div[data-testid="stTabs"] button[data-baseweb="tab"] span {
    font-family: 'Geist', system-ui, sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    letter-spacing: -0.015em !important;
    color: #5A5854 !important;
    margin: 0 !important;
    transition: color 180ms var(--ease-out) !important;
}

div[data-testid="stTabs"] button[data-baseweb="tab"]:hover:not([aria-selected="true"]) {
    background: rgba(255, 255, 255, 0.72) !important;
    transform: translateY(-1px) !important;
}

div[data-testid="stTabs"] button[data-baseweb="tab"]:hover:not([aria-selected="true"]) p {
    color: #1D1D1F !important;
}

div[data-testid="stTabs"] button[data-baseweb="tab"]:active {
    transform: scale(0.97) !important;
}

div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #F04E14 0%, #FF6428 100%) !important;
    box-shadow:
        0 8px 18px -6px rgba(240, 78, 20, 0.52),
        0 2px 4px rgba(0, 0, 0, 0.08),
        inset 0 1px 0 rgba(255, 255, 255, 0.25) !important;
}

div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p,
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p,
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] span {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}

/* Primary Buttons in Electric Orange */
.stButton > button {
    border-radius: 9999px !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    padding: 0.55rem 1.25rem !important;
    transition: transform 150ms var(--ease-out), box-shadow 150ms var(--ease-out), background 150ms var(--ease-out) !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #F04E14 0%, #FF6428 100%) !important;
    border: none !important;
    color: #FFFFFF !important;
    box-shadow: 0 8px 18px -6px rgba(240, 78, 20, 0.5) !important;
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #D9410B 0%, #F04E14 100%) !important;
    transform: translateY(-1px) !important;
}

.stButton > button:active {
    transform: scale(0.97) !important;
}

@media (max-width: 900px) {
    .aegis-stat-grid { grid-template-columns: repeat(2, 1fr); }
    .aegis-split-card { grid-template-columns: 1fr; }
    div[data-testid="stTabs"] [data-baseweb="tab-list"] { grid-template-columns: repeat(2, 1fr) !important; }
}
</style>
"""
)


# ---------------------------------------------------------------------------
# Business & Protection Metadata Across All 10 Screened Orders
# ---------------------------------------------------------------------------
TRADE_METADATA: Dict[str, Dict[str, Any]] = {
    "TC-01": {
        "menu_label": "Microsoft Corp — Buy $1,200,000 Corporate Bond (Approved)",
        "icon": "buildings",
        "order_notional": 1_200_000,
        "loss_paid_without": 0,
        "loss_paid_with": 0,
        "payment_saved": 0,
        "unwind_saved": 0,
        "false_alarm_saved": 0,
        "fee_saved": 0,
        "meter_title": "Parent Group Exposure vs. 5.00% Cap",
        "meter_before": "2.60%",
        "meter_after": "3.80%",
        "meter_before_pct": 2.60,
        "meter_after_pct": 3.80,
        "meter_cap_pct": 5.00,
        "meter_scale_max": 6.50,
        "short_driver": "1.20% safety buffer below 5.00% limit",
        "plain_reason": (
            "Buying $1.20M of Microsoft brings total Microsoft exposure to 3.80% of the $100M fund—"
            "safely below the 5.00% single-company limit. All 4 safety checks pass."
        ),
        "why_saved": "Clean AAA Microsoft bond trade. Safe to execute with zero loss exposure.",
    },
    "TC-02": {
        "menu_label": "Apple Inc — Buy $1,250,000 Corporate Bond (Blocked · Saved $45,000)",
        "icon": "hand-palm",
        "order_notional": 1_250_000,
        "loss_paid_without": 0,
        "loss_paid_with": 0,
        "payment_saved": 45_000,
        "unwind_saved": 33_000,
        "false_alarm_saved": 0,
        "fee_saved": 12_000,
        "meter_title": "Apple Total Exposure vs. 5.00% Cap",
        "meter_before": "4.20%",
        "meter_after": "5.45%",
        "meter_before_pct": 4.20,
        "meter_after_pct": 5.45,
        "meter_cap_pct": 5.00,
        "meter_scale_max": 6.50,
        "short_driver": "+0.45% ($450k) over the 5.00% limit",
        "plain_reason": (
            "The fund already holds $4.20M (4.20%) in Apple. Buying another $1.25M pushes Apple to "
            "5.45%, breaking the 5.00% ($5.00M) single-company cap by $450,000."
        ),
        "why_saved": (
            "Stopped $1.25M excess trade before execution, saving $33,000 in forced-sale slippage "
            "and $12,000 in compliance remediation costs."
        ),
    },
    "TC-03": {
        "menu_label": "Florida Power & Light — Buy $1,300,000 Bond (Blocked · Saved $68,000)",
        "icon": "git-merge",
        "order_notional": 1_300_000,
        "loss_paid_without": 68_000,
        "loss_paid_with": 0,
        "payment_saved": 68_000,
        "unwind_saved": 56_000,
        "false_alarm_saved": 0,
        "fee_saved": 12_000,
        "meter_title": "NextEra Parent Group vs. 5.00% Cap",
        "meter_before": "4.10%",
        "meter_after": "5.40%",
        "meter_before_pct": 4.10,
        "meter_after_pct": 5.40,
        "meter_cap_pct": 5.00,
        "meter_scale_max": 6.50,
        "short_driver": "+0.40% ($400k) over parent group limit",
        "plain_reason": (
            "On its own, Florida Power & Light looks like 0% of the fund. However, it is owned by "
            "NextEra Energy, where the fund already holds $4.10M across two affiliates. Combined "
            "exposure hits 5.40%, breaking the 5.00% parent-company limit."
        ),
        "why_saved": (
            "Standard checks miss that NextEra owns Florida Power & Light. Stopping this trade "
            "pre-execution saved $68,000 in forced unwind losses."
        ),
    },
    "TC-04": {
        "menu_label": "Ford Motor Credit — Buy $1,500,000 Split-Rated Bond (Approved · Saved $82,500)",
        "icon": "scales",
        "order_notional": 1_500_000,
        "loss_paid_without": 82_500,
        "loss_paid_with": 0,
        "payment_saved": 82_500,
        "unwind_saved": 0,
        "false_alarm_saved": 82_500,
        "fee_saved": 0,
        "meter_title": "High-Yield Bucket vs. 15.00% Cap",
        "meter_before": "14.10%",
        "meter_after": "14.10%",
        "meter_before_pct": 14.10,
        "meter_after_pct": 14.10,
        "meter_cap_pct": 15.00,
        "meter_scale_max": 18.00,
        "short_driver": "Split-rating rule keeps High-Yield at 14.10%",
        "plain_reason": (
            "Ford has a split rating: S&P rates it BBB- (Investment Grade), Moody's rates it Ba1 "
            "(High-Yield), and Fitch rates it BBB-. Under fund rules, when two agencies disagree, "
            "Fitch breaks the tie—so Ford is Investment Grade and does not breach the High-Yield cap."
        ),
        "why_saved": (
            "Prevented a false alarm on Ford's split rating, saving $82,500 in unnecessary trade "
            "cancellation and replacement spread costs."
        ),
    },
    "TC-05": {
        "menu_label": "Permian Resources — Buy $700,000 Energy Bond (Blocked · Saved $34,000)",
        "icon": "flame",
        "order_notional": 700_000,
        "loss_paid_without": 34_000,
        "loss_paid_with": 0,
        "payment_saved": 34_000,
        "unwind_saved": 22_000,
        "false_alarm_saved": 0,
        "fee_saved": 12_000,
        "meter_title": "High-Yield Energy vs. 5.00% Sub-Limit",
        "meter_before": "4.55%",
        "meter_after": "5.25%",
        "meter_before_pct": 4.55,
        "meter_after_pct": 5.25,
        "meter_cap_pct": 5.00,
        "meter_scale_max": 6.50,
        "short_driver": "+0.25% ($250k) over Energy sub-limit",
        "plain_reason": (
            "While overall High-Yield exposure (14.80%) stays under the 15.00% overall limit, High-Yield "
            "Energy bonds have a stricter 5.00% sub-limit. This $700k purchase pushes High-Yield Energy "
            "from 4.55% to 5.25%, breaking the sub-limit by $250,000."
        ),
        "why_saved": (
            "Stopped $700k energy bond breach before execution, avoiding $22,000 in illiquid bond "
            "dump losses and $12,000 in remediation fees."
        ),
    },
    "TC-06": {
        "menu_label": "UK Treasury Gilt — Buy $1,200,000 GBP Government Bond (Approved)",
        "icon": "globe",
        "order_notional": 1_200_000,
        "loss_paid_without": 0,
        "loss_paid_with": 0,
        "payment_saved": 0,
        "unwind_saved": 0,
        "false_alarm_saved": 0,
        "fee_saved": 0,
        "meter_title": "Unhedged Foreign Sovereign vs. 10.00% Cap",
        "meter_before": "7.50%",
        "meter_after": "8.70%",
        "meter_before_pct": 7.50,
        "meter_after_pct": 8.70,
        "meter_cap_pct": 10.00,
        "meter_scale_max": 12.00,
        "short_driver": "1.30% safety buffer below 10.00% limit",
        "plain_reason": (
            "Normally, foreign-currency bonds must be hedged back to US Dollars. However, the fund allows "
            "up to 10.00% in unhedged OECD government bonds. UK Gilts qualify, bringing the bucket to 8.70%."
        ),
        "why_saved": "Valid UK Government bond trade within the 10% foreign sovereign limit. Zero loss exposure.",
    },
    "TC-07": {
        "menu_label": "Siemens AG — Buy $1,000,000 Unhedged EUR Corporate Bond (Blocked · Saved $38,000)",
        "icon": "bank",
        "order_notional": 1_000_000,
        "loss_paid_without": 0,
        "loss_paid_with": 0,
        "payment_saved": 38_000,
        "unwind_saved": 32_000,
        "false_alarm_saved": 0,
        "fee_saved": 6_000,
        "meter_title": "Unhedged Foreign Corporate vs. 0.00% Allowed",
        "meter_before": "0.00%",
        "meter_after": "1.00%",
        "meter_before_pct": 0.00,
        "meter_after_pct": 1.00,
        "meter_cap_pct": 0.05,
        "meter_scale_max": 1.20,
        "short_driver": "Corporate bond requires 100% USD currency hedge",
        "plain_reason": (
            "Even though Germany is an OECD member, the foreign currency exception only applies to government "
            "bonds—not corporate issuers like Siemens. Because this EUR bond is unhedged, it breaks the currency rule."
        ),
        "why_saved": (
            "Blocked unhedged EUR corporate bond before execution, preventing $32,000 in cross-currency "
            "unwind costs and $6,000 in review fees."
        ),
    },
    "TC-08": {
        "menu_label": "NVIDIA Corp — Buy $50,000 Stock Above 5% Drift Cap (Blocked · Saved $15,000)",
        "icon": "trend-up",
        "order_notional": 50_000,
        "loss_paid_without": 0,
        "loss_paid_with": 0,
        "payment_saved": 15_000,
        "unwind_saved": 15_000,
        "false_alarm_saved": 0,
        "fee_saved": 0,
        "meter_title": "NVIDIA Exposure vs. 5.00% Active Buy Lockout",
        "meter_before": "5.15%",
        "meter_after": "5.20%",
        "meter_before_pct": 5.15,
        "meter_after_pct": 5.20,
        "meter_cap_pct": 5.00,
        "meter_scale_max": 6.50,
        "short_driver": "Already at 5.15% from stock gains · Active buys locked",
        "plain_reason": (
            "NVIDIA is at 5.15% of the fund due to market price appreciation. Fund rules allow holding that "
            "position passively, but strictly ban any new active BUY orders while NVIDIA sits above 5.00%."
        ),
        "why_saved": (
            "Stopped a $50k add-on buy on a drifted position, saving $15,000 in mandatory trade-error "
            "reversal and legal review costs."
        ),
    },
    "TC-09": {
        "menu_label": "Heartland Rail & Bulk — Buy $1,000,000 Bond (Held for Officer · Saved $41,000)",
        "icon": "flame",
        "order_notional": 1_000_000,
        "loss_paid_without": 41_000,
        "loss_paid_with": 0,
        "payment_saved": 41_000,
        "unwind_saved": 0,
        "false_alarm_saved": 41_000,
        "fee_saved": 0,
        "meter_title": "Direct Coal (4.2%) + Mixed Coal Freight (22.0%) vs. 10% Rule",
        "meter_before": "4.20%",
        "meter_after": "26.20%",
        "meter_before_pct": 4.20,
        "meter_after_pct": 26.20,
        "meter_cap_pct": 10.00,
        "meter_scale_max": 30.00,
        "short_driver": "22% undisclosed coal rail freight · Held for Officer",
        "plain_reason": (
            "Structured data shows only 4.2% direct coal mining revenue (under the 10% cap). However, the "
            "deal footnotes reveal 22% of revenue comes from mixed Powder River Basin coal rail corridors. "
            "Held for Compliance Officer sign-off."
        ),
        "why_saved": (
            "Caught hidden coal freight dependency in deal footnotes that standard database checks miss, "
            "saving $41,000 in forced ESG unwind losses."
        ),
    },
    "TC-10": {
        "menu_label": "Cayman Emerald Trust — Buy $1,500,000 SPV Note (Held for Officer · Saved $52,000)",
        "icon": "swap",
        "order_notional": 1_500_000,
        "loss_paid_without": 52_000,
        "loss_paid_with": 0,
        "payment_saved": 52_000,
        "unwind_saved": 9_000,
        "false_alarm_saved": 43_000,
        "fee_saved": 0,
        "meter_title": "Orphan SPV Swap Basket Look-Through vs. 5.00% Cap",
        "meter_before": "0.00%",
        "meter_after": "5.60%",
        "meter_before_pct": 0.00,
        "meter_after_pct": 5.60,
        "meter_cap_pct": 5.00,
        "meter_scale_max": 6.50,
        "short_driver": "Orphan SPV hides swap basket · Held for Officer",
        "plain_reason": (
            "On paper, Cayman Emerald Trust looks like a new A- rated issuer at 0% of the fund. In reality, "
            "the deal notes disclose it is an orphan SPV linked via total return swap to an undisclosed basket "
            "of oil & gas credits. Held for Compliance Officer review."
        ),
        "why_saved": (
            "Paused opaque Cayman SPV note before settlement, preventing $52,000 in swap termination "
            "penalties and forced unwind losses."
        ),
    },
}

FRIENDLY_RULE_NAMES = {
    "RULE_101_SINGLE_ISSUER": "Single-Company & Parent Group Limit (Max 5%)",
    "RULE_201_HIGH_YIELD_AND_ENERGY": "High-Yield (15%) & Energy Sub-Limit (5%)",
    "RULE_301_CURRENCY_AND_SOVEREIGN": "Foreign Currency & Government Bond Rule (10%)",
    "RULE_402_DERIVATIVE_LOOKTHROUGH": "Derivative & Offshore Swap Transparency Check",
}

ASSET_CLASS_LABELS = {
    "CORPORATE_BOND": "Corporate Bond",
    "SOVEREIGN_BOND": "Government Bond",
    "TOTAL_RETURN_SWAP": "Total Return Swap",
    "EQUITY": "Common Stock",
}

TOTAL_PAYMENT_SAVED = sum(v["payment_saved"] for v in TRADE_METADATA.values())
TOTAL_UNWIND_SAVED = sum(v["unwind_saved"] for v in TRADE_METADATA.values())
TOTAL_FALSE_ALARM_SAVED = sum(v["false_alarm_saved"] for v in TRADE_METADATA.values())
TOTAL_FEE_SAVED = sum(v["fee_saved"] for v in TRADE_METADATA.values())
TOTAL_LOSS_PAID_WITHOUT = sum(v["loss_paid_without"] for v in TRADE_METADATA.values())
TOTAL_LOSS_PAID_WITH = sum(v["loss_paid_with"] for v in TRADE_METADATA.values())
TOTAL_BLOCKED_CAPITAL = 4_650_000
TOTAL_ORDER_FLOW = sum(v["order_notional"] for v in TRADE_METADATA.values())

if "cco_audit_log" not in st.session_state:
    st.session_state["cco_audit_log"] = []


@st.cache_resource
def load_pipeline():
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    graph = MandateComplianceAgentGraph(
        mandate_path=data_dir / "fund_mandate_ips.md",
        holdings_path=data_dir / "holdings_nport.json",
        schema_path=data_dir / "fund_schema.yaml",
        env_path=base_dir / ".env",
    )
    with open(data_dir / "test_cases_10.json", "r", encoding="utf-8") as f:
        test_cases = json.load(f)
    with open(data_dir / "holdings_nport.json", "r", encoding="utf-8") as f:
        holdings_data = json.load(f)
    return graph, test_cases, holdings_data


graph, test_cases, holdings_data = load_pipeline()
case_map = {TRADE_METADATA[tc["test_id"]]["menu_label"]: tc for tc in test_cases}

# ---------------------------------------------------------------------------
# 1. Sticky Glassmorphic Navigation Pill + Dynamic #F04E14 Orange Hero Band
# ---------------------------------------------------------------------------
render_html(
    f"""
<nav class="aegis-nav">
    <span class="aegis-brand"><span style="width:9px;height:9px;border-radius:3px;background:#F04E14;display:inline-block;"></span>apex.</span>
    <span class="aegis-nav-item"><span class="live-dot"></span>Pre-Trade Gate</span>
    <span class="aegis-nav-item">Losses vs. Savings</span>
    <span class="aegis-nav-item">Activity Dashboard</span>
    <span class="aegis-nav-pill">{get_svg("shield-check", "#FFFFFF", 15)}+$184,500 incremental saved</span>
</nav>

<section class="aegis-band">
    <div class="aegis-orb-1"></div>
    <div class="aegis-orb-2"></div>
    <svg width="100%" height="100%" style="position:absolute;inset:0;opacity:.45;pointer-events:none;">
        <defs>
            <pattern id="aegisGrid" width="56" height="56" patternUnits="userSpaceOnUse">
                <path d="M56 0H0V56" fill="none" stroke="rgba(255,255,255,.10)" stroke-width="1"></path>
            </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#aegisGrid)"></rect>
    </svg>
    <div style="position:relative;z-index:2;">
        <span class="aegis-kicker"><span style="width:6px;height:6px;border-radius:2px;background:#FFFFFF;"></span>INVESTMENT MANDATE ENFORCEMENT &amp; COMPLIANCE CONTROLS</span>
        <h1 class="aegis-band-title">2 unsafe approvals caught · 1 false block fixed · 2 gray areas held.</h1>
        <p class="aegis-band-sub">Before any order executes, Apex checks the company, parent group, credit ratings, and fund IPS limits. Over basic checks, our gate saves +$184,500 in direct losses/costs and holds $93,000 of ambiguous footnote risk for CCO review.</p>
    </div>
    <div class="aegis-stat-grid">
        <div class="aegis-stat-card">
            <span style="display:flex;justify-content:space-between;align-items:center;">{get_svg("piggy-bank", "#FFFFFF", 20)}<span style="font-size:11px;background:rgba(255,255,255,.22);padding:2px 8px;border-radius:9999px;font-weight:600;">Incremental</span></span>
            <span class="aegis-stat-val">+$184,500</span>
            <span class="aegis-stat-lbl">Realized value over basic checker (TC-03/04/05)</span>
        </div>
        <div class="aegis-stat-card">
            <span style="display:flex;justify-content:space-between;align-items:center;">{get_svg("warning-octagon", "#FFFFFF", 20)}<span style="font-size:11px;background:rgba(255,255,255,.18);padding:2px 8px;border-radius:9999px;font-weight:600;">Held for CCO</span></span>
            <span class="aegis-stat-val">$93,000</span>
            <span class="aegis-stat-lbl">Ambiguous footnote exposure held (TC-09/10)</span>
        </div>
        <div class="aegis-stat-card">
            <span style="display:flex;justify-content:space-between;align-items:center;">{get_svg("seal-check", "#FFFFFF", 20)}<span style="font-size:11px;background:rgba(0,0,0,.28);padding:2px 8px;border-radius:9999px;font-weight:600;">Baseline</span></span>
            <span class="aegis-stat-val">$98,000</span>
            <span class="aegis-stat-lbl">Standard breaches caught by both (TC-02/07/08)</span>
        </div>
        <div class="aegis-stat-card">
            <span style="display:flex;justify-content:space-between;align-items:center;">{get_svg("hand-palm", "#FFFFFF", 20)}<span style="font-size:11px;background:rgba(255,255,255,.18);padding:2px 8px;border-radius:9999px;font-weight:600;">10 / 10 Checked</span></span>
            <span class="aegis-stat-val">$0 Loss</span>
            <span class="aegis-stat-lbl">Out-of-pocket mandate breach loss paid</span>
        </div>
    </div>
</section>
"""
)

# ---------------------------------------------------------------------------
# 2. Four Sculpted Segmented Pill Dashboards (Electric Orange Active Pill)
# ---------------------------------------------------------------------------
tab_gate, tab_savings, tab_activity, tab_portfolio = st.tabs(
    [
        "01 · Pre-Trade Gate",
        "02 · Losses vs. Savings",
        "03 · All Activity & Protection",
        "04 · Fund Portfolio ($100M)",
    ]
)

# ===========================================================================
# DASHBOARD 1: PRE-TRADE GATE (AEGIS Split-Card + Overshoot Meter)
# ===========================================================================
with tab_gate:
    sel_col, btn_col = st.columns([4.3, 1], vertical_alignment="bottom")
    with sel_col:
        selected_label = st.selectbox(
            "Select Proposed Trade Order to Inspect",
            options=list(case_map.keys()),
            index=2,  # Default to Florida Power & Light ($68,000 saved)
        )
    selected_tc = case_map[selected_label]
    active_case_id = selected_tc["test_id"]
    meta = TRADE_METADATA[active_case_id]

    trade_draft = dict(selected_tc["proposed_trade"])
    is_custom = (
        "custom_notional" in st.session_state
        and st.session_state.get("custom_for_case") == active_case_id
    )
    if is_custom:
        trade_draft["trade_amount_usd"] = st.session_state["custom_notional"]
        trade_draft["rating_sp"] = st.session_state["custom_sp"]
        trade_draft["rating_moodys"] = st.session_state["custom_moodys"]
        trade_draft["currency"] = st.session_state["custom_ccy"]
        trade_draft["is_fx_hedged"] = st.session_state["custom_hedged"]

    with btn_col:
        run_clicked = st.button("Check Trade", type="primary", use_container_width=True)

    if (
        run_clicked
        or "active_state" not in st.session_state
        or st.session_state.get("last_case_id") != active_case_id
    ):
        has_key = bool(os.environ.get("OPENROUTER_API_KEY", "").strip())
        use_live = bool(run_clicked and has_key)
        st.session_state["active_state"] = graph.run_audit(
            test_id=active_case_id,
            proposed_trade=trade_draft,
            use_live_llm=use_live,
        ).to_dict()
        st.session_state["last_case_id"] = active_case_id

    state_dict = st.session_state["active_state"]
    det_bundle = state_dict["deterministic_bundle"]
    pruned = det_bundle["pruned_schema_summary"]
    rule_checks = det_bundle["rule_checks"]

    total_nav = float(det_bundle["total_nav_usd"])
    trade_amt = float(trade_draft["trade_amount_usd"])
    credit_class = pruned["credit_classification_by_rule_202"]
    friendly_credit = "Investment Grade" if credit_class == "INVESTMENT_GRADE" else "High-Yield"
    friendly_asset = ASSET_CLASS_LABELS.get(trade_draft["asset_class"], "Security")

    pre_direct_usd = float(pruned["target_issuer_pre_trade_usd"])
    post_direct_usd = pre_direct_usd + trade_amt
    post_direct_pct = (post_direct_usd / total_nav) * 100.0

    pre_parent_usd = float(pruned["target_parent_group_pre_trade_usd"])
    post_parent_usd = pre_parent_usd + trade_amt
    post_parent_pct = (post_parent_usd / total_nav) * 100.0

    pre_hy_usd = float(pruned["aggregate_high_yield_pre_trade_usd"])
    post_hy_usd = pre_hy_usd + (trade_amt if credit_class == "HIGH_YIELD" else 0.0)
    post_hy_pct = (post_hy_usd / total_nav) * 100.0

    pre_hye_usd = float(pruned["high_yield_energy_pre_trade_usd"])
    post_hye_usd = pre_hye_usd + (
        trade_amt if (credit_class == "HIGH_YIELD" and trade_draft["gics_sector"] == "Energy") else 0.0
    )
    post_hye_pct = (post_hye_usd / total_nav) * 100.0

    pre_sov_usd = float(pruned["unhedged_oecd_sovereign_pre_trade_usd"])
    is_unhedged_sov = (
        trade_draft["currency"] != "USD"
        and not trade_draft["is_fx_hedged"]
        and trade_draft["asset_class"] == "SOVEREIGN_BOND"
        and trade_draft["is_oecd_country"]
    )
    post_sov_usd = pre_sov_usd + (trade_amt if is_unhedged_sov else 0.0)
    post_sov_pct = (post_sov_usd / total_nav) * 100.0

    verdict = state_dict["final_verdict"]
    if verdict == "PASS":
        accent_c = "#11713F"
        bar_c = "#2FBF71"
        ring_style = "inset 0 0 0 1.5px rgba(17,113,63,.25)"
        pill_bg = "rgba(17,113,63,.09)"
        badge_txt = "APPROVED · SAFE TO EXECUTE"
        step4_label = "Trade Cleared"
    elif verdict == "BREACH":
        accent_c = "#C42329"
        bar_c = "#E5484D"
        ring_style = "inset 0 0 0 1.5px rgba(196,35,41,.28)"
        pill_bg = "rgba(196,35,41,.09)"
        badge_txt = "RULE BROKEN · TRADE BLOCKED"
        step4_label = "Blocked Pre-Trade"
    else:
        accent_c = "#92400E"
        bar_c = "#D97706"
        ring_style = "inset 0 0 0 1.5px rgba(217,119,6,.32)"
        pill_bg = "rgba(217,119,6,.12)"
        badge_txt = "PAYMENT HELD · OFFICER REVIEW"
        step4_label = "Held for Officer"

    scale_max = meta["meter_scale_max"]
    cap_pos = min((meta["meter_cap_pct"] / scale_max) * 100.0, 92.0)
    after_pos = min((meta["meter_after_pct"] / scale_max) * 100.0, 97.0)
    base_w = min(after_pos, cap_pos)
    over_w = max(0.0, after_pos - cap_pos)
    dot_color = "#E5484D" if verdict != "PASS" else "#2FBF71"

    sav_text = (
        f"+${meta['payment_saved']:,.0f} saved · $0 loss paid"
        if meta["payment_saved"] > 0
        else "$0 loss paid · Compliant order"
    )

    render_html(
        f"""
<div class="aegis-split-card" style="box-shadow:{ring_style}, var(--aegis-shadow);">
    <div style="display:flex;flex-direction:column;gap:14px;min-width:0;">
        <div style="display:flex;gap:12px;align-items:center;">
            <span class="aegis-icon-box">{get_svg(meta["icon"], accent_c, 22)}</span>
            <div style="min-width:0;">
                <span style="display:inline-block;font-size:12px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:{accent_c};background:{pill_bg};padding:3px 10px;border-radius:9999px;">{badge_txt}</span>
            </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:6px;">
            <span style="font-size:25px;line-height:1.22;font-weight:700;letter-spacing:-.025em;color:#1D1D1F;text-wrap:balance;">{trade_draft['issuer_name']} · Buy ${trade_amt:,.0f}</span>
            <p style="margin:0;max-width:65ch;font-size:15px;line-height:1.5;color:#4A4A50;text-wrap:pretty;">{meta['plain_reason']}</p>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:auto;padding-top:4px;">
            <span style="display:inline-flex;align-items:center;gap:6px;background:linear-gradient(135deg,#F04E14 0%,#FF6428 100%);color:#FFFFFF;border-radius:9999px;padding:7px 15px;font-size:13.5px;font-weight:600;box-shadow:0 8px 16px -6px rgba(240,78,20,.48);">{get_svg("shield-check", "#FFFFFF", 16)}{sav_text}</span>
            <span style="display:inline-flex;align-items:center;gap:6px;background:#F6F5F3;color:#1D1D1F;border-radius:9999px;padding:7px 14px;font-size:13px;font-weight:600;">Parent: {trade_draft['ultimate_parent_name']}</span>
            <span style="display:inline-flex;align-items:center;gap:6px;background:#F6F5F3;color:#707075;border-radius:9999px;padding:7px 14px;font-size:13px;font-weight:500;">{friendly_asset} · {trade_draft['currency']}</span>
        </div>
    </div>

    <div class="aegis-meter-box">
        <div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px;">
            <div>
                <span style="display:block;font-size:12px;font-weight:600;color:#707075;">Before trade</span>
                <span style="font-size:30px;font-weight:700;letter-spacing:-.035em;color:#1D1D1F;">{meta['meter_before']}</span>
            </div>
            {get_svg("arrow-right", "#F04E14", 20)}
            <div style="text-align:right;">
                <span style="display:block;font-size:12px;font-weight:600;color:#707075;">After trade</span>
                <span style="font-size:30px;font-weight:700;letter-spacing:-.035em;color:{accent_c};">{meta['meter_after']}</span>
            </div>
        </div>

        <div style="position:relative;height:26px;margin:2px 0;">
            <div style="position:absolute;left:0;right:0;top:11px;height:5px;border-radius:3px;background:#E2E0DC;"></div>
            <div style="position:absolute;left:0;width:{base_w:.1f}%;top:11px;height:5px;border-radius:3px;background:#F04E14;transition:width .7s var(--ease-drawer);"></div>
            <div style="position:absolute;left:{cap_pos:.1f}%;width:{over_w:.1f}%;top:11px;height:5px;border-radius:3px;background:#E5484D;transition:width .7s var(--ease-drawer);"></div>
            <div style="position:absolute;left:{cap_pos:.1f}%;top:4px;width:2px;height:18px;margin-left:-1px;border-radius:1px;background:#1D1D1F;"></div>
            <div style="position:absolute;left:{after_pos:.1f}%;top:5px;width:16px;height:16px;margin-left:-8px;border-radius:50%;background:{dot_color};border:3px solid #FFFFFF;box-shadow:0 1px 4px rgba(0,0,0,.28);transition:left .7s var(--ease-drawer);"></div>
        </div>

        <div style="display:flex;justify-content:space-between;font-size:12.5px;font-weight:600;color:#707075;">
            <span>{meta['meter_title']}</span>
            <span style="color:{accent_c};">{meta['short_driver']}</span>
        </div>

        <div class="stepper-grid">
            <div style="display:flex;align-items:center;gap:6px;">
                <span class="step-node" style="background:#F04E14;">{get_svg("check", "#FFFFFF", 12)}</span>
                <span style="font-size:11.5px;font-weight:600;color:#1D1D1F;">Order Read</span>
            </div>
            <div style="display:flex;align-items:center;gap:6px;">
                <span class="step-node" style="background:#F04E14;">{get_svg("check", "#FFFFFF", 12)}</span>
                <span style="font-size:11.5px;font-weight:600;color:#1D1D1F;">Parent Link</span>
            </div>
            <div style="display:flex;align-items:center;gap:6px;">
                <span class="step-node" style="background:#F04E14;">{get_svg("check", "#FFFFFF", 12)}</span>
                <span style="font-size:11.5px;font-weight:600;color:#1D1D1F;">Limit Math</span>
            </div>
            <div style="display:flex;align-items:center;gap:6px;">
                <span class="step-node" style="background:{bar_c};animation:pulse 2s infinite;">{get_svg("shield-check", "#FFFFFF", 13)}</span>
                <span style="font-size:11.5px;font-weight:700;color:{accent_c};">{step4_label}</span>
            </div>
        </div>
    </div>
</div>
"""
    )

    col_gauges, col_rules = st.columns([1.02, 1.28], gap="medium")

    with col_gauges:
        passed_count = sum(1 for r in rule_checks if r["status"] == "PASS")
        total_rules = len(rule_checks)
        ring_deg = int((passed_count / total_rules) * 360)
        ring_col = "#2FBF71" if verdict == "PASS" else ("#E5484D" if verdict == "BREACH" else "#F04E14")

        def _aegis_bar(label: str, val_pct: float, cap_pct: float) -> str:
            w = min((val_pct / cap_pct) * 100.0, 100.0) if cap_pct > 0 else 0.0
            c = "#E5484D" if val_pct > cap_pct else "#F04E14"
            txt_c = "#C42329" if val_pct > cap_pct else "#1D1D1F"
            return (
                f'<div style="margin-bottom:13px;">'
                f'<div style="display:flex;justify-content:space-between;font-size:13.5px;margin-bottom:5px;">'
                f'<span style="color:#4A4A50;font-weight:500;">{label}</span>'
                f'<span style="font-weight:600;color:{txt_c};">{val_pct:.2f}% <span style="color:#707075;font-weight:400;">/ {cap_pct:.2f}% max</span></span>'
                f"</div>"
                f'<div style="height:6px;background:#ECEAE6;border-radius:3px;overflow:hidden;">'
                f'<div style="width:{w:.1f}%;height:100%;background:{c};border-radius:3px;transition:width .8s var(--ease-drawer);"></div>'
                f"</div>"
                f"</div>"
            )

        bars_block = (
            _aegis_bar(f"Direct Company ({trade_draft['issuer_name']})", post_direct_pct, 5.00)
            + _aegis_bar(f"Parent Group ({trade_draft['ultimate_parent_name']})", post_parent_pct, 5.00)
            + _aegis_bar("Total High-Yield Bonds", post_hy_pct, 15.00)
            + _aegis_bar("High-Yield Energy Sub-Limit", post_hye_pct, 5.00)
            + _aegis_bar("Unhedged Foreign Government Bonds", post_sov_pct, 10.00)
        )

        render_html(
            f"""
<div class="aegis-card">
    <div class="aegis-section-head">
        <h3 class="aegis-section-title"><span class="aegis-square-dot"></span>Fund Limit Utilization</h3>
        <span class="aegis-pill-tag">$100.0M Portfolio</span>
    </div>
    <div style="display:flex;align-items:center;gap:16px;padding:12px 14px;background:#F6F5F3;border-radius:14px;margin-bottom:16px;">
        <div style="width:62px;height:62px;flex-shrink:0;border-radius:50%;background:conic-gradient({ring_col} {ring_deg}deg, #E2E0DC 0);display:flex;align-items:center;justify-content:center;">
            <div style="width:48px;height:48px;border-radius:50%;background:#FFFFFF;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#1D1D1F;">{passed_count}/{total_rules}</div>
        </div>
        <div>
            <div style="font-size:15px;font-weight:600;color:#1D1D1F;">{passed_count} of {total_rules} Fund Checkpoints Cleared</div>
            <div style="font-size:13px;color:#707075;margin-top:2px;">{meta['why_saved']}</div>
        </div>
    </div>
    {bars_block}
</div>
"""
        )

    with col_rules:
        rule_rows_html = ""
        for rc in rule_checks:
            st_code = rc["status"]
            if st_code == "PASS":
                dot_c = "#2FBF71"
                pill_txt = "Cleared"
                txt_c = "#11713F"
            elif st_code == "BREACH":
                dot_c = "#E5484D"
                pill_txt = "Broken"
                txt_c = "#C42329"
            else:
                dot_c = "#D97706"
                pill_txt = "Held"
                txt_c = "#92400E"

            friendly_name = FRIENDLY_RULE_NAMES.get(rc["rule_id"], rc["rule_name"])
            clean_limit = (
                rc["threshold_limit"]
                .replace("<= ", "Max ")
                .replace(" per Sec 2.02(b)", "")
            )
            rule_rows_html += (
                f'<div style="display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr) minmax(0,1fr) auto;gap:10px;align-items:center;padding:11px 0;border-top:1px solid #ECEAE6;font-size:13.5px;">'
                f'<span style="font-weight:600;color:#1D1D1F;">{friendly_name}</span>'
                f'<span style="color:#1D1D1F;font-weight:500;">{rc["post_trade_metric"]}</span>'
                f'<span style="color:#707075;font-size:12.5px;">{clean_limit}</span>'
                f'<span style="display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:600;color:{txt_c};background:#F6F5F3;padding:3px 10px;border-radius:9999px;"><span style="width:6px;height:6px;border-radius:50%;background:{dot_c};"></span>{pill_txt}</span>'
                f"</div>"
            )

        render_html(
            f"""
<div class="aegis-card">
    <div class="aegis-section-head">
        <h3 class="aegis-section-title"><span class="aegis-square-dot"></span>Order vs. Fund Rules, Line by Line</h3>
        <span class="aegis-pill-tag">{friendly_credit} · {trade_draft['rating_sp']}/{trade_draft['rating_moodys']}</span>
    </div>
    <div style="display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr) minmax(0,1fr) auto;gap:10px;padding-bottom:6px;font-size:12px;font-weight:600;color:#707075;">
        <span>Checkpoint</span><span>After Trade</span><span>Your Rule</span><span>Status</span>
    </div>
    {rule_rows_html}
</div>
"""
        )

    with st.expander(
        "Simulate Different Trade Amount or Record Officer Sign-Off",
        expanded=(verdict == "ESCALATE_TO_HUMAN"),
    ):
        sim_col, cco_col = st.columns(2, gap="medium")
        with sim_col:
            st.caption("Test Different Order Parameters")
            c_notional = st.number_input(
                "Trade Amount ($)",
                min_value=50_000,
                max_value=20_000_000,
                value=int(trade_draft["trade_amount_usd"]),
                step=100_000,
            )
            r_c1, r_c2, r_c3 = st.columns(3)
            with r_c1:
                ratings_list = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", "B+"]
                c_sp = st.selectbox(
                    "S&P Rating",
                    ratings_list,
                    index=ratings_list.index(trade_draft["rating_sp"]) if trade_draft["rating_sp"] in ratings_list else 5,
                )
            with r_c2:
                m_list = ["Aaa", "Aa1", "Aa2", "Aa3", "A1", "A2", "A3", "Baa1", "Baa2", "Baa3", "Ba1", "Ba2", "Ba3", "B1"]
                c_moodys = st.selectbox(
                    "Moody's",
                    m_list,
                    index=m_list.index(trade_draft["rating_moodys"]) if trade_draft["rating_moodys"] in m_list else 5,
                )
            with r_c3:
                ccy_list = ["USD", "GBP", "EUR", "JPY", "CAD"]
                c_ccy = st.selectbox(
                    "Currency",
                    ccy_list,
                    index=ccy_list.index(trade_draft["currency"]) if trade_draft["currency"] in ccy_list else 0,
                )
            c_hedged = st.checkbox("Currency Hedged to USD", value=bool(trade_draft["is_fx_hedged"]))
            if st.button("Recalculate Order"):
                st.session_state["custom_for_case"] = active_case_id
                st.session_state["custom_notional"] = float(c_notional)
                st.session_state["custom_sp"] = c_sp
                st.session_state["custom_moodys"] = c_moodys
                st.session_state["custom_ccy"] = c_ccy
                st.session_state["custom_hedged"] = c_hedged
                st.session_state.pop("active_state", None)
                st.rerun()

        with cco_col:
            st.caption("Compliance Officer Approval / Rejection")
            cco_id = st.text_input("Officer Name", value="J. Harrison (Chief Compliance Officer)", key="cco_id_in")
            cco_act = st.selectbox(
                "Decision",
                ["Keep Trade Held / Blocked", "Approve with Written Sign-Off"],
                key="cco_act_in",
            )
            cco_note = st.text_input(
                "Review Note",
                value="Verified underlying company exposure and confirmed compliance.",
                key="cco_note_in",
            )
            if st.button("Save Officer Decision", key="cco_submit_btn"):
                st.session_state["cco_audit_log"].append(
                    {
                        "Time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                        "Company": trade_draft["issuer_name"],
                        "Officer": cco_id,
                        "Decision": cco_act,
                        "Note": cco_note,
                    }
                )
                st.success(f"Saved decision for {trade_draft['issuer_name']}.")
            if st.session_state["cco_audit_log"]:
                st.dataframe(st.session_state["cco_audit_log"], use_container_width=True, hide_index=True)

# ===========================================================================
# DASHBOARD 2: LOSSES PAID VS. PAYMENTS SAVED (Executive P&L Protection)
# ===========================================================================
with tab_savings:
    s_left, s_right = st.columns([1.05, 1.3], gap="medium")

    with s_left:
        render_html(
            f"""
<div class="aegis-card">
    <div class="aegis-section-head">
        <h3 class="aegis-section-title"><span class="aegis-square-dot"></span>Reconciled Financial Attribution</h3>
        <span class="aegis-pill-tag">Incremental vs. Baseline</span>
    </div>
    <div style="background:#FFF5F5;border:1px solid rgba(196,35,41,.18);border-radius:16px;padding:18px;margin-bottom:12px;">
        <div style="display:flex;justify-content:space-between;align-items:baseline;">
            <span style="font-size:13px;font-weight:700;color:#C42329;text-transform:uppercase;letter-spacing:.04em;">Basic Checker Alone (5/10)</span>
            <span style="font-size:24px;font-weight:700;letter-spacing:-.03em;color:#C42329;">-$184,500 Direct + $93k Risk</span>
        </div>
        <p style="margin:6px 0 0 0;font-size:14px;line-height:1.48;color:#4A4A50;">If a trade violates the fund's investment mandate, it can create a mandate breach, trigger remediation, and expose the adviser to compliance and fiduciary risks under SEC Rule 206(4)-7 (Advisers Act) and Rule 38a-1 (1940 Act).</p>
    </div>
    <div style="background:#FFF4EE;border:1px solid rgba(240,78,20,.24);border-radius:16px;padding:18px;margin-bottom:16px;">
        <div style="display:flex;justify-content:space-between;align-items:baseline;">
            <span style="font-size:13px;font-weight:700;color:#C23805;text-transform:uppercase;letter-spacing:.04em;">Incremental Value Over Basic Check</span>
            <span style="font-size:24px;font-weight:700;letter-spacing:-.03em;color:#F04E14;">+$184,500 Realized + $93k Held</span>
        </div>
        <p style="margin:6px 0 0 0;font-size:14px;line-height:1.48;color:#4A4A50;">Our gate catches 2 hidden breaches (TC-03 $68k, TC-05 $34k), fixes 1 costly false block (TC-04 Ford $82.5k), and holds 2 ambiguous footnote trades ($93k at-risk) for CCO sign-off.</p>
    </div>
    <div style="background:#F6F5F3;border-radius:16px;padding:16px 18px;">
        <div style="font-size:13px;font-weight:700;color:#1D1D1F;margin-bottom:10px;">Reconciled Breakdown Across All 10 Test Cases ($375,500 Total)</div>
        <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
                <span style="color:#4A4A50;">1. Incremental Unwind Loss Avoided (TC-03 $68k + TC-05 $34k)</span>
                <span style="font-weight:700;color:#F04E14;">+$102,000 (Realized)</span>
            </div>
            <div style="height:6px;background:#E2E0DC;border-radius:3px;overflow:hidden;"><div style="width:85.0%;height:100%;background:#F04E14;border-radius:3px;"></div></div>
        </div>
        <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
                <span style="color:#4A4A50;">2. Incremental False-Block Cost Avoided (TC-04 Ford)</span>
                <span style="font-weight:700;color:#11713F;">+$82,500 (Realized)</span>
            </div>
            <div style="height:6px;background:#E2E0DC;border-radius:3px;overflow:hidden;"><div style="width:68.8%;height:100%;background:#2FBF71;border-radius:3px;"></div></div>
        </div>
        <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
                <span style="color:#4A4A50;">3. Ambiguous Exposure Held for CCO Review (TC-09 $41k + TC-10 $52k)</span>
                <span style="font-weight:700;color:#92400E;">$93,000 (Held for CCO)</span>
            </div>
            <div style="height:6px;background:#E2E0DC;border-radius:3px;overflow:hidden;"><div style="width:77.5%;height:100%;background:#D97706;border-radius:3px;"></div></div>
        </div>
        <div>
            <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
                <span style="color:#4A4A50;">4. Baseline Breaches Blocked by Both (TC-02 $45k + TC-07 $38k + TC-08 $15k)</span>
                <span style="font-weight:700;color:#707075;">$98,000 (Baseline)</span>
            </div>
            <div style="height:6px;background:#E2E0DC;border-radius:3px;overflow:hidden;"><div style="width:81.7%;height:100%;background:#707075;border-radius:3px;"></div></div>
        </div>
    </div>
</div>
"""
        )

    with s_right:
        bars_html = ""
        max_save = 95_000.0
        for tc in test_cases:
            cid = tc["test_id"]
            fi = TRADE_METADATA[cid]
            if fi["payment_saved"] > 0:
                w_pct = min((fi["payment_saved"] / max_save) * 100.0, 100.0)
                bar_col = "#F04E14" if fi["loss_paid_without"] > 0 else "#2FBF71"
                bars_html += (
                    f'<div style="padding:12px 14px;background:#F6F5F3;border-radius:14px;margin-bottom:10px;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
                    f'<span style="display:inline-flex;align-items:center;gap:8px;"><span style="width:30px;height:30px;border-radius:8px;background:#FFFFFF;display:inline-flex;align-items:center;justify-content:center;box-shadow:0 1px 2px rgba(0,0,0,.06);">{get_svg(fi["icon"], "#F04E14", 16)}</span><strong style="color:#1D1D1F;font-size:14px;">{tc["proposed_trade"]["issuer_name"]}</strong></span>'
                    f'<span style="color:#C23805;font-weight:700;font-size:15px;">+${fi["payment_saved"]:,.0f} saved</span>'
                    f"</div>"
                    f'<div style="font-size:12.5px;color:#707075;margin-bottom:7px;">{fi["why_saved"]}</div>'
                    f'<div style="height:6px;background:#E2E0DC;border-radius:3px;overflow:hidden;">'
                    f'<div style="width:{w_pct:.1f}%;height:100%;background:{bar_col};border-radius:3px;transition:width .8s var(--ease-drawer);"></div>'
                    f"</div>"
                    f"</div>"
                )

        render_html(
            f"""
<div class="aegis-card">
    <div class="aegis-section-head">
        <h3 class="aegis-section-title"><span class="aegis-square-dot"></span>Payments &amp; Unwind Losses Saved by Company</h3>
        <span class="aegis-pill-tag">+${TOTAL_PAYMENT_SAVED:,.0f} Total Saved</span>
    </div>
    {bars_html}
</div>
"""
        )

# ===========================================================================
# DASHBOARD 3: ALL ACTIVITY & PROTECTION DASHBOARD
# ===========================================================================
with tab_activity:
    act_c1, act_c2, act_c3 = st.columns([1.0, 1.0, 1.15], gap="medium")

    with act_c1:
        render_html(
            f"""
<div class="aegis-card" style="padding:20px;">
    <div class="aegis-section-head" style="margin-bottom:10px;">
        <h3 class="aegis-section-title" style="font-size:16px;"><span class="aegis-square-dot"></span>Screening Outcomes</h3>
        <span class="aegis-pill-tag">10 Orders</span>
    </div>
    <div style="display:flex;align-items:center;gap:16px;">
        <div style="width:74px;height:74px;flex-shrink:0;border-radius:50%;background:conic-gradient(#2FBF71 0deg 108deg, #F04E14 108deg 288deg, #D97706 288deg 360deg);display:flex;align-items:center;justify-content:center;">
            <div style="width:54px;height:54px;border-radius:50%;background:#FFFFFF;display:flex;flex-direction:column;align-items:center;justify-content:center;">
                <span style="font-size:15px;font-weight:700;color:#1D1D1F;line-height:1;">10/10</span>
                <span style="font-size:10px;color:#707075;font-weight:600;">Checked</span>
            </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:5px;font-size:13px;width:100%;">
            <div style="display:flex;justify-content:space-between;"><span style="display:inline-flex;align-items:center;gap:6px;"><span style="width:8px;height:8px;border-radius:2px;background:#2FBF71;"></span>Approved Safe</span><strong style="color:#1D1D1F;">3 trades</strong></div>
            <div style="display:flex;justify-content:space-between;"><span style="display:inline-flex;align-items:center;gap:6px;"><span style="width:8px;height:8px;border-radius:2px;background:#F04E14;"></span>Blocked Breaches</span><strong style="color:#C23805;">5 trades</strong></div>
            <div style="display:flex;justify-content:space-between;"><span style="display:inline-flex;align-items:center;gap:6px;"><span style="width:8px;height:8px;border-radius:2px;background:#D97706;"></span>Held for Officer</span><strong style="color:#92400E;">2 trades</strong></div>
        </div>
    </div>
</div>
"""
        )

    with act_c2:
        render_html(
            f"""
<div class="aegis-card" style="padding:20px;">
    <div class="aegis-section-head" style="margin-bottom:10px;">
        <h3 class="aegis-section-title" style="font-size:16px;"><span class="aegis-square-dot"></span>Capital Flow Protected</h3>
        <span class="aegis-pill-tag">${TOTAL_ORDER_FLOW / 1_000_000:.2f}M Screened</span>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;">
        <div style="background:#F6F5F3;border-radius:12px;padding:10px 12px;">
            <span style="font-size:11.5px;color:#707075;font-weight:600;display:block;">Safe Executed</span>
            <span style="font-size:20px;font-weight:700;color:#11713F;">$3.90M</span>
        </div>
        <div style="background:#FFF4EE;border-radius:12px;padding:10px 12px;">
            <span style="font-size:11.5px;color:#C23805;font-weight:600;display:block;">Stopped / Held</span>
            <span style="font-size:20px;font-weight:700;color:#F04E14;">$6.80M</span>
        </div>
    </div>
    <div style="height:7px;background:#2FBF71;border-radius:4px;overflow:hidden;display:flex;">
        <div style="width:36.4%;height:100%;background:#2FBF71;"></div>
        <div style="width:40.2%;height:100%;background:#F04E14;"></div>
        <div style="width:23.4%;height:100%;background:#D97706;"></div>
    </div>
</div>
"""
        )

    with act_c3:
        render_html(
            f"""
<div class="aegis-card" style="padding:20px;">
    <div class="aegis-section-head" style="margin-bottom:10px;">
        <h3 class="aegis-section-title" style="font-size:16px;"><span class="aegis-square-dot"></span>Net Firm P&amp;L Protection</h3>
        <span class="aegis-pill-tag">$0 Loss Paid</span>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:8px;">
        <div style="background:#FFF5F5;border-radius:12px;padding:10px 12px;">
            <span style="font-size:11.5px;color:#C42329;font-weight:600;display:block;">Loss (No Gate)</span>
            <span style="font-size:20px;font-weight:700;color:#C42329;">-${TOTAL_LOSS_PAID_WITHOUT:,.0f}</span>
        </div>
        <div style="background:#FFF4EE;border-radius:12px;padding:10px 12px;">
            <span style="font-size:11.5px;color:#C23805;font-weight:600;display:block;">Money Saved</span>
            <span style="font-size:20px;font-weight:700;color:#F04E14;">+${TOTAL_PAYMENT_SAVED:,.0f}</span>
        </div>
    </div>
    <div style="font-size:12.5px;color:#707075;">100% of hidden breaches caught before trade execution.</div>
</div>
"""
        )

    activity_filter = st.radio(
        "Filter Activity Dashboard by Decision",
        options=[
            "All 10 Screened Orders (+$375,500 Saved)",
            "Blocked Rule Breaches (5 Orders · +$200,000 Saved)",
            "Held for Officer Review (2 Orders · +$93,000 Saved)",
            "Approved Compliant Orders (3 Orders · +$82,500 Saved)",
        ],
        horizontal=True,
        label_visibility="collapsed",
    )

    filtered_cases = []
    for tc in test_cases:
        v = tc["expected_verdict"]
        if activity_filter.startswith("Blocked") and v != "BREACH":
            continue
        if activity_filter.startswith("Held") and v != "ESCALATE_TO_HUMAN":
            continue
        if activity_filter.startswith("Approved") and v != "PASS":
            continue
        filtered_cases.append(tc)

    grid_left, grid_right = st.columns(2, gap="medium")

    for idx, tc in enumerate(filtered_cases):
        cid = tc["test_id"]
        fi = TRADE_METADATA[cid]
        prop = tc["proposed_trade"]
        exp_dec = tc["expected_verdict"]

        if exp_dec == "PASS":
            dot_c = "#2FBF71"
            ink_c = "#11713F"
            pill_bg = "rgba(17,113,63,.09)"
            pill_lbl = "APPROVED"
        elif exp_dec == "BREACH":
            dot_c = "#E5484D"
            ink_c = "#C42329"
            pill_bg = "rgba(196,35,41,.09)"
            pill_lbl = "BLOCKED"
        else:
            dot_c = "#D97706"
            ink_c = "#92400E"
            pill_bg = "rgba(217,119,6,.12)"
            pill_lbl = "HELD FOR REVIEW"

        scale_max = fi["meter_scale_max"]
        cap_pos = min((fi["meter_cap_pct"] / scale_max) * 100.0, 92.0)
        after_pos = min((fi["meter_after_pct"] / scale_max) * 100.0, 97.0)
        base_w = min(after_pos, cap_pos)
        over_w = max(0.0, after_pos - cap_pos)

        loss_str = f"-${fi['loss_paid_without']:,.0f}" if fi["loss_paid_without"] > 0 else "$0"
        loss_col = "#C42329" if fi["loss_paid_without"] > 0 else "#707075"
        save_str = f"+${fi['payment_saved']:,.0f}" if fi["payment_saved"] > 0 else "$0"
        save_col = "#F04E14" if fi["payment_saved"] > 0 else "#707075"

        card_html = f"""
<div class="activity-bento-card">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
        <div style="display:flex;align-items:center;gap:12px;min-width:0;">
            <span class="aegis-icon-box">{get_svg(fi["icon"], "#F04E14" if exp_dec != "PASS" else "#11713F", 20)}</span>
            <div style="min-width:0;">
                <div style="font-size:16px;font-weight:700;color:#1D1D1F;letter-spacing:-.015em;">{prop["issuer_name"]}</div>
                <div style="font-size:12.5px;color:#707075;">Parent: {prop["ultimate_parent_name"]} · Order: <strong style="color:#1D1D1F;">${fi["order_notional"]:,.0f}</strong></div>
            </div>
        </div>
        <span style="display:inline-flex;align-items:center;gap:6px;font-size:11.5px;font-weight:700;color:{ink_c};background:{pill_bg};padding:4px 10px;border-radius:9999px;flex-shrink:0;"><span style="width:6px;height:6px;border-radius:50%;background:{dot_c};"></span>{pill_lbl}</span>
    </div>

    <div style="background:#F6F5F3;border-radius:14px;padding:12px 14px;">
        <div style="display:flex;justify-content:space-between;font-size:12.5px;font-weight:600;margin-bottom:6px;">
            <span style="color:#4A4A50;">{fi["meter_title"]}</span>
            <span style="color:{ink_c};">{fi["meter_before"]} &rarr; {fi["meter_after"]}</span>
        </div>
        <div style="position:relative;height:14px;">
            <div style="position:absolute;left:0;right:0;top:4px;height:5px;border-radius:3px;background:#E2E0DC;"></div>
            <div style="position:absolute;left:0;width:{base_w:.1f}%;top:4px;height:5px;border-radius:3px;background:#F04E14;"></div>
            <div style="position:absolute;left:{cap_pos:.1f}%;width:{over_w:.1f}%;top:4px;height:5px;border-radius:3px;background:#E5484D;"></div>
            <div style="position:absolute;left:{cap_pos:.1f}%;top:0;width:2px;height:13px;background:#1D1D1F;"></div>
        </div>
        <div style="font-size:12px;color:#707075;margin-top:4px;">{fi["why_saved"]}</div>
    </div>

    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;padding-top:4px;">
        <div style="background:#F6F5F3;border-radius:10px;padding:8px 10px;">
            <span style="display:block;font-size:11px;color:#707075;font-weight:600;">Loss (No Gate)</span>
            <span style="font-size:15px;font-weight:700;color:{loss_col};">{loss_str}</span>
        </div>
        <div style="background:#F6F5F3;border-radius:10px;padding:8px 10px;">
            <span style="display:block;font-size:11px;color:#707075;font-weight:600;">Loss Paid (With Gate)</span>
            <span style="font-size:15px;font-weight:700;color:#1D1D1F;">$0</span>
        </div>
        <div style="background:#FFF4EE;border-radius:10px;padding:8px 10px;">
            <span style="display:block;font-size:11px;color:#C23805;font-weight:600;">Money Saved</span>
            <span style="font-size:15px;font-weight:700;color:{save_col};">{save_str}</span>
        </div>
    </div>
</div>
"""
        if idx % 2 == 0:
            with grid_left:
                render_html(card_html)
        else:
            with grid_right:
                render_html(card_html)

# ===========================================================================
# DASHBOARD 4: FUND PORTFOLIO ($100M HOLDINGS)
# ===========================================================================
with tab_portfolio:
    p_left, p_right = st.columns([1.0, 1.35], gap="medium")

    with p_left:
        parent_totals: Dict[str, float] = {}
        for h in holdings_data["holdings"]:
            p_name = h["ultimate_parent_name"]
            parent_totals[p_name] = parent_totals.get(p_name, 0.0) + float(h["market_value_usd"])

        sorted_parents = sorted(parent_totals.items(), key=lambda x: x[1], reverse=True)[:8]
        parent_bars = ""
        for p_label, mv in sorted_parents:
            pct = (mv / float(holdings_data["total_nav_usd"])) * 100.0
            w = min((pct / 6.0) * 100.0, 100.0)
            col = "#D97706" if pct > 5.0 else "#F04E14"
            drift_note = " · Over 5% from stock gains" if pct > 5.0 else ""
            parent_bars += (
                f'<div style="margin-bottom:13px;">'
                f'<div style="display:flex;justify-content:space-between;font-size:13.5px;margin-bottom:4px;">'
                f'<span style="color:#1D1D1F;font-weight:500;">{p_label}<span style="color:#92400E;font-size:12px;">{drift_note}</span></span>'
                f'<span style="font-weight:600;">{pct:.2f}% (${mv:,.0f})</span>'
                f"</div>"
                f'<div style="position:relative;height:6px;background:#ECEAE6;border-radius:3px;">'
                f'<div style="width:{w:.1f}%;height:100%;background:{col};border-radius:3px;"></div>'
                f'<div style="position:absolute;left:83.3%;top:-3px;width:2px;height:12px;background:#1D1D1F;" title="5.00% Cap"></div>'
                f"</div>"
                f"</div>"
            )

        render_html(
            f"""
<div class="aegis-card">
    <div class="aegis-section-head">
        <h3 class="aegis-section-title"><span class="aegis-square-dot"></span>Largest Company Exposures (5.00% Limit)</h3>
        <span class="aegis-pill-tag">$100.0M Total NAV</span>
    </div>
    {parent_bars}
</div>
"""
        )

    with p_right:
        pos_rows_html = ""
        for p in holdings_data["holdings"]:
            pct = (float(p["market_value_usd"]) / float(holdings_data["total_nav_usd"])) * 100.0
            pos_rows_html += (
                f'<div style="display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1.1fr) 90px 80px 105px 65px;gap:10px;align-items:center;padding:10px 0;border-top:1px solid #ECEAE6;font-size:13.5px;">'
                f'<span style="font-weight:600;color:#1D1D1F;">{p["issuer_name"]}</span>'
                f'<span style="color:#707075;">{p["ultimate_parent_name"]}</span>'
                f'<span>{p["gics_sector"]}</span>'
                f'<span style="font-weight:500;">{p["rating_sp"]}/{p["rating_moodys"]}</span>'
                f'<span style="text-align:right;font-weight:500;">${p["market_value_usd"]:,.0f}</span>'
                f'<span style="text-align:right;font-weight:700;color:#F04E14;">{pct:.2f}%</span>'
                f"</div>"
            )

        render_html(
            f"""
<div class="aegis-card">
    <div class="aegis-section-head">
        <h3 class="aegis-section-title"><span class="aegis-square-dot"></span>Current Fund Holdings ($82.35M Invested + $17.65M Cash)</h3>
        <span class="aegis-pill-tag">12 Settled Holdings</span>
    </div>
    <div style="display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1.1fr) 90px 80px 105px 65px;gap:10px;padding-bottom:6px;font-size:12px;font-weight:600;color:#707075;">
        <span>Company</span><span>Parent Group</span><span>Sector</span><span>Rating</span><span style="text-align:right;">Value</span><span style="text-align:right;">% Fund</span>
    </div>
    {pos_rows_html}
</div>
"""
        )

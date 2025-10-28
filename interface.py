# app.py — Prompt-Plattform mit abhängigen Menüs:
# Use-Case -> Untertyp  |  Use-Case -> Ziel/Output  |  Ziel/Output -> Ziel-Untertyp
from __future__ import annotations
import json
from datetime import datetime
from textwrap import dedent
import streamlit as st

st.set_page_config(page_title="🧭 Prompt-Plattform", page_icon="🧭", layout="wide")

# ------------------ Anzeige-Labels (stabile interne Werte, hübsche Darstellung) ------------------
UC_LABEL = {
    "schreiben": "🖋️ Schreiben",
    "analysieren": "📊 Analysieren",
    "lernen": "🧠 Lernen/Erklären",
    "coden": "💻 Coden",
    "kreativ": "🎨 Kreativideen",
    "sonstiges": "🧪 Sonstiges",
}

UC_SUBTYPES = {
    "analysieren": ["Textanalyse", "SWOT", "Ursache–Wirkung (Fishbone)", "Vergleich/Benchmark", "Risiko-Check"],
    "schreiben":   ["Zusammenfassung", "Brief/E-Mail", "Bericht/Protokoll", "Konzeptskizze", "Presse/News"],
    "coden":       ["Snippet erklären", "Bug finden", "Refactoring", "Tests generieren", "Skelett erstellen"],
    "lernen":      ["Einfach erklären", "Glossar", "Lernziele + Quiz", "Schritt-für-Schritt-Anleitung"],
    "kreativ":     ["Brainstorming", "Metaphern finden", "Storyboard/Outline", "Titel/Claims"],
}

# Ziele, abhängig vom Use-Case
GOALS_BY_UC = {
    "analysieren": [
        "Strukturierte Analyse", "SWOT-Analyse", "Vergleich/Benchmark", "Risiko-Check",
        "Lessons Learned", "Ursache–Wirkung"
    ],
    "schreiben": [
        "Zusammenfassung", "Interviewleitfaden", "Checkliste",
        "Konzeptskizze", "Bericht/Protokoll", "Pressemitteilung"
    ],
    "coden": [
        "Code-Snippet", "Refactoring-Vorschlag", "Testfälle generieren", "Fehleranalyse (Bug Report)"
    ],
    "lernen": [
        "Einfach erklären", "Glossar", "Lernziele + Quiz", "Schritt-für-Schritt-Anleitung"
    ],
    "kreativ": [
        "Brainstorming-Liste", "Metaphern/Analogien", "Titel/Claims", "Storyboard/Outline"
    ],
    "sonstiges": [
        "Freiform"
    ],
}

# Ziel-Untertypen, abhängig vom Ziel
GOAL_SUBTYPES = {
    "Strukturierte Analyse": ["Problemdefinition", "Hypothesen", "Befunde", "Empfehlungen"],
    "SWOT-Analyse": ["SWOT (Stärken/Schwächen/Chancen/Risiken)", "SW + OT getrennt"],
    "Vergleich/Benchmark": ["2er-Vergleich", "Mehrfach-Vergleich (3+)", "Tabellarisch"],
    "Risiko-Check": ["Risikomatrix", "Top-5 Risiken", "Gegenmaßnahmen"],
    "Lessons Learned": ["Was lief gut", "Was lief schlecht", "Verbesserungen"],
    "Ursache–Wirkung": ["Fishbone (Ishikawa)", "5-Why", "Pareto-Hinweise"],
    "Zusammenfassung": ["Kurz (5 Sätze)", "Mittel (200–300 Wörter)", "Lang (Gliederung + Kernaussagen)"],
    "Interviewleitfaden": ["Themenblöcke + Fragen", "Einleitung + Abschlussfragen", "Hinweise für Interviewer:in"],
    "Checkliste": ["Kurz-Check (10 Punkte)", "Detail-Check (20+ Punkte)"],
    "Konzeptskizze": ["Leitidee", "Zielbild + Maßnahmen", "Roadmap 30/60/90"],
    "Bericht/Protokoll": ["Kurzprotokoll (Stichpunkte)", "Vollprotokoll (Abschnitte)"],
    "Pressemitteilung": ["Standard (Lead/Zitat/Hintergrund)", "Kurzmeldung"],
    "Code-Snippet": ["Python", "JS/TS", "SQL", "Shell"],
    "Refactoring-Vorschlag": ["Lesbarkeit", "Performance", "Struktur/Architektur"],
    "Testfälle generieren": ["Unit-Tests", "Property-Based", "Edge-Cases"],
    "Fehleranalyse (Bug Report)": ["Minimalbeispiel", "Hypothesen", "Fix-Idee"],
    "Einfach erklären": ["Für Kinder (8+)", "Für Fachfremde", "Für Fortgeschrittene"],
    "Glossar": ["10 Begriffe", "20 Begriffe", "Begriffe + Beispiele"],
    "Lernziele + Quiz": ["3 Lernziele + 6 Fragen", "Bloom-Taxonomie-Mix"],
    "Schritt-für-Schritt-Anleitung": ["5 Schritte", "10 Schritte", "mit Prüfpunkten"],
    "Brainstorming-Liste": ["20 Ideen", "5 Kategorien x 5 Ideen"],
    "Metaphern/Analogien": ["3 starke Metaphern", "Pro/Contra je Metapher"],
    "Titel/Claims": ["10 Titel", "5 Claims + Unterzeile"],
    "Storyboard/Outline": ["3-Akt-Struktur", "Kapitel-Outline"],
    "Freiform": [],
}

FORMAT_LABEL = {
    "markdown":"Markdown",
    "text":"Reiner Text",
    "json":"JSON-Antwort",
    "table":"Tabelle (MD)"
}

# ------------------ Hilfsfunktionen ------------------
def keep_or_default(current: str | None, options: list[str]) -> int:
    """Gibt einen sicheren Index zurück: behalte current, falls vorhanden, sonst 0."""
    if not options:
        return 0
    if current in options:
        return options.index(current)
    return 0

# ------------------ Sidebar ------------------
with st.sidebar:
    st.header("🧭 Navigation")
    lang = st.radio("Sprache", ["de", "en"], index=0, key="lang",
                    format_func=lambda x: "Deutsch" if x=="de" else "Englisch")
    out_format = st.selectbox("Output-Format", list(FORMAT_LABEL.keys()), index=0, key="out_format",
                              format_func=lambda x: FORMAT_LABEL[x])
    length = st.select_slider("Länge", options=["ultrakurz","kurz","mittel","lang","sehr lang"], value="mittel", key="length")
    filename_base = st.text_input("Dateiname (ohne Endung)", value="prompt_cockpit", key="fname")

# ------------------ Layout ------------------
col_left, col_mid, col_right = st.columns([1.05, 1.6, 1.35], gap="large")

# ------------------ Linke Spalte: Use-Case + abhängige Ziele ------------------
with col_left:
    st.subheader("🧩 Use-Case")
    use_case = st.radio(
        "Was möchtest du tun?",
        options=list(UC_LABEL.keys()),
        index=keep_or_default(st.session_state.get("use_case"), list(UC_LABEL.keys())),
        key="use_case",
        format_func=lambda v: UC_LABEL[v],
    )

    # Untertyp (abhängig vom Use-Case)
    sub_options = UC_SUBTYPES.get(use_case, [])
    if sub_options:
        st.selectbox(
            "Untertyp",
            sub_options,
            index=keep_or_default(st.session_state.get("sub_use_case"), sub_options),
            key="sub_use_case"
        )
    else:
        st.session_state["sub_use_case"] = None

    st.markdown("---")

    st.subheader("🎯 Ziel / Output (abhängig vom Use-Case)")
    goal_options = GOALS_BY_UC.get(use_case, ["Freiform"])
    st.selectbox(
        "Zieltyp",
        goal_options,
        index=keep_or_default(st.session_state.get("goal"), goal_options),
        key="goal"
    )

    # Ziel-Untertyp (abhängig vom Ziel)
    subgoal_options = GOAL_SUBTYPES.get(st.session_state.get("goal", ""), [])
    if subgoal_options:
        st.selectbox(
            "Ziel-Untertyp",
            subgoal_options,
            index=keep_or_default(st.session_state.get("goal_subtype"), subgoal_options),
            key="goal_subtype"
        )
    else:
        st.session_state["goal_subtype"] = None

    st.markdown("---")

    audience = st.text_input("Zielgruppe (optional)", key="audience", placeholder="z. B. Leitung, Team, Öffentlichkeit")
    constraints = st.text_area("Rahmen / Muss-Kriterien (optional)", key="constraints", height=70)

    st.subheader("🎚️ Stil & Ton")
    tone = st.select_slider("Tonfall", options=["sehr sachlich","sachlich","neutral","lebendig","kreativ"], value="sachlich", key="tone")
    rigor = st.select_slider("Strenge/Struktur", options=["locker","mittel","klar","sehr klar"], value="klar", key="rigor")
    persona = st.text_input("Rolle (optional)", key="persona", placeholder="z. B. Qualitätsauditor:in")

# ------------------ Mitte: Kontext, Struktur, Qualität ------------------
with col_mid:
    st.subheader("🖼️ Kontext")
    context = st.text_area(
        "Kurzkontext (2–4 Bullets)",
        height=120, key="context",
        placeholder="• Thema / Problem\n• Ziel & Medium\n• Rahmenbedingungen\n• Quellen/Lage"
    )

    st.subheader("🧱 Struktur (optional)")
    structure = st.multiselect(
        "Bausteine auswählen",
        ["Einleitung mit Zielbild","Vorgehensschritte","Analyse (z. B. SWOT / Ursachen-Wirkung)",
         "Beispiele / Templates","Qualitäts-/Risiko-Check","Nächste Schritte / To-dos","Quellen/Annahmen"],
        default=["Einleitung mit Zielbild","Nächste Schritte / To-dos"],
        key="structure"
    )

    st.subheader("🔒 Qualitäts/Compliance (optional)")
    qc_facts = st.checkbox("Faktencheck erwünscht", key="qc_facts")
    qc_bias  = st.checkbox("Bias-Check/Hinweise", key="qc_bias")
    qc_dp    = st.checkbox("Datenschutz-Hinweis einfügen", key="qc_dp")

# ------------------ Prompt-Generator ------------------
def build_prompt() -> str:
    lang_hint = "deutsch" if st.session_state.lang == "de" else "englisch"
    today = datetime.now().strftime("%Y-%m-%d")

    of_hint = {
        "markdown": "Antworte in sauberem Markdown.",
        "text": "Antworte als Klartext ohne Markdown.",
        "json": "Antworte als valides JSON-Objekt mit klaren Schlüsseln.",
        "table": "Antworte als Markdown-Tabelle mit sprechenden Spalten."
    }[st.session_state.out_format]

    # Struktur
    structure_lines = "\n".join([f"- {s}" for s in st.session_state.structure]) if st.session_state.structure else "- (freie Struktur)"

    # Qualität
    qc_lines = []
    if st.session_state.qc_facts: qc_lines.append("• Prüfe Aussagen auf Plausibilität und kennzeichne unsichere Stellen.")
    if st.session_state.qc_bias:  qc_lines.append("• Weisen auf mögliche Verzerrungen/Bias hin.")
    if st.session_state.qc_dp:    qc_lines.append("• Keine personenbezogenen oder internen Daten verarbeiten.")
    qc_block = "\n".join(qc_lines) if qc_lines else "• (keine zusätzlichen Prüfhinweise)"

    # optionale Linien
    persona_line = f"Rolle: {st.session_state.persona}\n" if st.session_state.persona else ""
    audience_line = f"Zielgruppe: {st.session_state.audience}\n" if st.session_state.audience else ""
    constraints_line = f"Rahmen/Muss-Kriterien:\n{st.session_state.constraints.strip()}\n\n" if st.session_state.constraints.strip() else ""
    sub_uc_line = f"Untertyp: {st.session_state.sub_use_case}\n" if st.session_state.get("sub_use_case") else ""
    subgoal_line = f"Ziel-Untertyp: {st.session_state.goal_subtype}\n" if st.session_state.get("goal_subtype") else ""

    return dedent(f"""
    Du bist ein Assistenzsystem für **{UC_LABEL[st.session_state.use_case]}**.
    {sub_uc_line}{persona_line}{audience_line}{subgoal_line}Sprache: {lang_hint}. Tonfall: {st.session_state.tone}. Struktur: {st.session_state.rigor}. Länge: {st.session_state.length}.
    Ziel/Output: **{st.session_state.goal}**.
    {of_hint}

    Kontext (Stichpunkte):
    {st.session_state.context.strip() or "(kein zusätzlicher Kontext)"}

    Strukturbausteine (wenn sinnvoll):
    {structure_lines}

    {constraints_line}Qualität & Compliance:
    {qc_block}

    Liefere ein Ergebnis, das direkt nutzbar ist. Erkläre nur, wo es dem Verständnis dient.
    Datum: {today}
    """).strip()

def build_schema(prompt_text: str) -> dict:
    return {
        "protocol": "prompt.cockpit/1.0",
        "meta": {
            "created": datetime.now().isoformat(timespec="seconds"),
            "language": st.session_state.lang,
            "length": st.session_state.length,
            "format": st.session_state.out_format,
        },
        "profile": {
            "use_case": st.session_state.use_case,
            "use_case_label": UC_LABEL[st.session_state.use_case],
            "sub_use_case": st.session_state.get("sub_use_case"),
            "goal": st.session_state.goal,
            "goal_subtype": st.session_state.get("goal_subtype"),
            "tone": st.session_state.tone,
            "rigor": st.session_state.rigor,
            "persona": st.session_state.persona or None,
            "audience": st.session_state.audience or None,
            "structure": st.session_state.structure,
            "qc": {
                "facts": st.session_state.qc_facts,
                "bias": st.session_state.qc_bias,
                "data_protection": st.session_state.qc_dp
            }
        },
        "context": st.session_state.context,
        "constraints": st.session_state.constraints,
        "prompt": prompt_text
    }

# ------------------ Rechte Spalte: Vorschau + Exporte ------------------
with col_right:
    st.subheader("👁️ Live-Vorschau")
    prompt_text = build_prompt()
    tabs = st.tabs(["🔤 Lesbare Version", "🧾 JSON-Schema"])

    with tabs[0]:
        st.code(prompt_text, language="markdown")
        st.download_button("⬇️ Als Markdown speichern", data=prompt_text.encode("utf-8"),
                           file_name=f"{st.session_state.fname or 'prompt'}.md", mime="text/markdown")

    with tabs[1]:
        schema = build_schema(prompt_text)
        st.json(schema, expanded=False)
        st.download_button("⬇️ JSON-Schema speichern",
                           data=json.dumps(schema, ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name=f"{st.session_state.fname or 'prompt'}.json", mime="application/json")

# app.py — robuste Version: saubere Werte statt Emoji-Strings, eindeutige Keys

from __future__ import annotations
import json
from datetime import datetime
from textwrap import dedent
import streamlit as st

st.set_page_config(page_title="🧭 Prompt-Plattform", page_icon="🧭", layout="wide")

# ---------- Mapping für Anzeige ----------
UC_LABEL = {
    "schreiben": "🖋️ Schreiben",
    "analysieren": "📊 Analysieren",
    "lernen": "🧠 Lernen/Erklären",
    "coden": "💻 Coden",
    "kreativ": "🎨 Kreativideen",
    "sonstiges": "🧪 Sonstiges",
}

SUBS = {
    "analysieren": ["Textanalyse", "SWOT", "Ursache–Wirkung (Fishbone)", "Vergleich/Benchmark", "Risiko-Check"],
    "schreiben":   ["Zusammenfassung", "Brief/E-Mail", "Bericht/Protokoll", "Konzeptskizze", "Presse/News"],
    "coden":       ["Snippet erklären", "Bug finden", "Refactoring", "Tests generieren", "Skelett erstellen"],
    "lernen":      ["Einfach erklären", "Glossar", "Lernziele + Quiz", "Schritt-für-Schritt-Anleitung"],
    "kreativ":     ["Brainstorming", "Metaphern finden", "Storyboard/Outline", "Titel/Claims"],
}

# ---------- Sidebar ----------
with st.sidebar:
    st.header("🧭 Navigation")
    lang = st.radio("Sprache", ["de", "en"], index=0, key="lang", format_func=lambda x: "Deutsch" if x=="de" else "Englisch")
    out_format = st.selectbox("Output-Format", ["markdown", "text", "json", "table"], index=0, key="out_format",
                              format_func=lambda x: {"markdown":"Markdown","text":"Reiner Text","json":"JSON-Antwort","table":"Tabelle (MD)"}[x])
    length = st.select_slider("Länge", options=["ultrakurz","kurz","mittel","lang","sehr lang"], value="mittel", key="length")
    filename_base = st.text_input("Dateiname (ohne Endung)", value="prompt_cockpit", key="fname")

col_left, col_mid, col_right = st.columns([1.05, 1.6, 1.35], gap="large")

# ---------- Linke Spalte ----------
with col_left:
    st.subheader("🧩 Use-Case")
    use_case = st.radio(
        "Was möchtest du tun?",
        options=list(UC_LABEL.keys()),
        index=1,
        key="use_case",
        format_func=lambda v: UC_LABEL[v],
    )

    # Untermenü je nach Use-Case
    sub_options = SUBS.get(use_case, [])
    sub_use_case = None
    if sub_options:
        sub_use_case = st.selectbox("Untertyp", sub_options, index=0, key="sub_use_case")

    st.subheader("🎯 Ziel / Output")
    goal = st.selectbox(
        "Zieltyp",
        ["Zusammenfassung","Strukturierte Analyse","Interviewleitfaden","Checkliste","Konzeptskizze","Code-Snippet","Brainstorming-Liste","Freiform"],
        index=1, key="goal"
    )
    audience = st.text_input("Zielgruppe (optional)", key="audience", placeholder="z. B. Leitung, Team, Öffentlichkeit")
    constraints = st.text_area("Rahmen / Muss-Kriterien (optional)", key="constraints", height=70)

    st.subheader("🎚️ Stil & Ton")
    tone = st.select_slider("Tonfall", options=["sehr sachlich","sachlich","neutral","lebendig","kreativ"], value="sachlich", key="tone")
    rigor = st.select_slider("Strenge/Struktur", options=["locker","mittel","klar","sehr klar"], value="klar", key="rigor")
    persona = st.text_input("Rolle (optional)", key="persona", placeholder="z. B. Qualitätsauditor:in")

# ---------- Mitte ----------
with col_mid:
    st.subheader("🖼️ Kontext")
    context = st.text_area("Kurzkontext (2–4 Bullets)", height=120, key="context",
                           placeholder="• Thema / Problem\n• Ziel & Medium\n• Rahmenbedingungen\n• Quellen/Lage")

    st.subheader("🧱 Struktur (optional)")
    structure = st.multiselect(
        "Bausteine auswählen",
        ["Einleitung mit Zielbild","Vorgehensschritte","Analyse (z. B. SWOT / Ursachen-Wirkung)","Beispiele / Templates","Qualitäts-/Risiko-Check","Nächste Schritte / To-dos","Quellen/Annahmen"],
        default=["Einleitung mit Zielbild","Nächste Schritte / To-dos"],
        key="structure"
    )

    st.subheader("🔒 Qualitäts/Compliance (optional)")
    qc_facts = st.checkbox("Faktencheck erwünscht", key="qc_facts")
    qc_bias  = st.checkbox("Bias-Check/Hinweise", key="qc_bias")
    qc_dp    = st.checkbox("Datenschutz-Hinweis einfügen", key="qc_dp")

# ---------- Prompt Builder ----------
def build_prompt() -> str:
    lang_hint = "deutsch" if st.session_state.lang == "de" else "englisch"
    today = datetime.now().strftime("%Y-%m-%d")
    structure_lines = "\n".join([f"- {s}" for s in st.session_state.structure]) if st.session_state.structure else "- (freie Struktur)"
    qc_lines = []
    if st.session_state.qc_facts: qc_lines.append("• Prüfe Aussagen auf Plausibilität und kennzeichne unsichere Stellen.")
    if st.session_state.qc_bias:  qc_lines.append("• Weisen auf mögliche Verzerrungen/Bias hin.")
    if st.session_state.qc_dp:    qc_lines.append("• Keine personenbezogenen oder internen Daten verarbeiten.")
    qc_block = "\n".join(qc_lines) if qc_lines else "• (keine zusätzlichen Prüfhinweise)"

    of_hint = {
        "markdown": "Antworte in sauberem Markdown.",
        "text": "Antworte als Klartext ohne Markdown.",
        "json": "Antworte als valides JSON-Objekt mit klaren Schlüsseln.",
        "table": "Antworte als Markdown-Tabelle mit sprechenden Spalten."
    }[st.session_state.out_format]

    uc_label = UC_LABEL[st.session_state.use_case]
    sub_line = f"Untertyp: {st.session_state.sub_use_case}\n" if st.session_state.get("sub_use_case") else ""

    constraints_line = f"Rahmen/Muss-Kriterien:\n{st.session_state.constraints.strip()}\n\n" if st.session_state.constraints.strip() else ""
    persona_line = f"Rolle: {st.session_state.persona}\n" if st.session_state.persona else ""
    audience_line = f"Zielgruppe: {st.session_state.audience}\n" if st.session_state.audience else ""

    return dedent(f"""
    Du bist ein Assistenzsystem für **{uc_label}**.
    {sub_line}{persona_line}{audience_line}Sprache: {lang_hint}. Tonfall: {st.session_state.tone}. Struktur: {st.session_state.rigor}. Länge: {st.session_state.length}.
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
            "sub_use_case": st.session_state.get("sub_use_case"),
            "goal": st.session_state.goal,
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

# ---------- Rechte Spalte ----------
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

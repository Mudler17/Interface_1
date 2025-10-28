# app.py — Prompt-Plattform (abhängige Menüs + Highlight für optionale Felder/Checkboxen/Slider + Auto-Dateiname + Reset)
from __future__ import annotations
import json
from datetime import datetime
from textwrap import dedent
import streamlit as st

st.set_page_config(page_title="🧭 Prompt-Plattform", page_icon="🧭", layout="wide")

# ---------- Style ----------
HIGHLIGHT_CSS = """
<style>
.optfield {
  border-radius: 8px;
  padding: 0.45rem 0.6rem;
  background-color: #f6fdf6; /* sehr blassgrün */
  border: 1px solid #cde6cd;
  margin-bottom: 0.25rem;
}
.optfield .stSlider, .optfield .stCheckbox { background-color: transparent !important; }
</style>
"""
st.markdown(HIGHLIGHT_CSS, unsafe_allow_html=True)

# ---------- Defaults ----------
DEFAULTS = {
    "lang": "de",
    "out_format": "markdown",
    "length": "mittel",
    "use_case": "analysieren",
    "sub_use_case": None,
    "goal": None,
    "goal_subtype": None,
    "audience": "",
    "constraints": "",
    "tone": "sachlich",
    "rigor": "klar",
    "persona": "",
    "context": "",
    "structure": ["Einleitung mit Zielbild", "Nächste Schritte"],
    "qc_facts": False,
    "qc_bias": False,
    "qc_dp": False,
}

def reset_state():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.rerun()

# ---------- Dictionaries ----------
UC_LABEL = {
    "schreiben": "🖋️ Schreiben",
    "analysieren": "📊 Analysieren",
    "lernen": "🧠 Lernen/Erklären",
    "coden": "💻 Coden",
    "kreativ": "🎨 Kreativideen",
    "sonstiges": "🧪 Sonstiges",
}

UC_SUBTYPES = {
    "analysieren": ["Textanalyse", "SWOT", "Vergleich/Benchmark", "Risiko-Check"],
    "schreiben":   ["Zusammenfassung", "Bericht/Protokoll", "Konzeptskizze"],
    "coden":       ["Snippet erklären", "Bug finden", "Refactoring"],
    "lernen":      ["Einfach erklären", "Quiz", "Glossar"],
    "kreativ":     ["Brainstorming", "Metaphern finden", "Titel/Claims"],
}

GOALS_BY_UC = {
    "analysieren": ["SWOT-Analyse", "Benchmark", "Risiko-Check", "Lessons Learned", "Ursache–Wirkung"],
    "schreiben":   ["Interviewleitfaden", "Konzeptskizze", "Checkliste", "Bericht/Protokoll"],
    "coden":       ["Code-Snippet", "Testfälle generieren", "Fehleranalyse (Bug Report)", "Refactoring-Vorschlag"],
    "lernen":      ["Einfach erklären", "Quiz", "Schritt-für-Schritt-Anleitung", "Glossar"],
    "kreativ":     ["Brainstorming-Liste", "Storyboard", "Titel/Claims", "Metaphern/Analogien"],
    "sonstiges":   ["Freiform"],
}

GOAL_SUBTYPES = {
    "Interviewleitfaden": ["Themenblöcke + Fragen", "Einleitung + Abschluss"],
    "Konzeptskizze": ["Leitidee", "Zielbild + Maßnahmen", "Roadmap 30/60/90"],
    "Checkliste": ["Kurz-Check", "Detail-Check"],
    "SWOT-Analyse": ["Standard 4-Felder", "Mit Gewichtung"],
    "Benchmark": ["2er-Vergleich", "Mehrfach-Vergleich (3+)", "Tabellarisch"],
    "Risiko-Check": ["Risikomatrix", "Top-5 Risiken", "Gegenmaßnahmen"],
    "Ursache–Wirkung": ["Fishbone (Ishikawa)", "5-Why"],
    "Code-Snippet": ["Python", "JavaScript", "SQL"],
    "Refactoring-Vorschlag": ["Lesbarkeit", "Performance", "Struktur"],
    "Testfälle generieren": ["Unit-Tests", "Property-Based", "Edge-Cases"],
    "Fehleranalyse (Bug Report)": ["Minimalbeispiel", "Hypothesen", "Fix-Idee"],
    "Einfach erklären": ["Für Kinder (8+)", "Für Fachfremde", "Für Fortgeschrittene"],
    "Quiz": ["6 Fragen", "10 Fragen", "Mix Bloom"],
    "Schritt-für-Schritt-Anleitung": ["5 Schritte", "10 Schritte", "mit Prüfpunkten"],
    "Glossar": ["10 Begriffe", "20 Begriffe", "mit Beispielen"],
    "Brainstorming-Liste": ["20 Ideen", "5 Kategorien x 5 Ideen"],
    "Storyboard": ["3-Akt-Struktur", "Kapitel-Outline"],
    "Titel/Claims": ["10 Titel", "5 Claims + Unterzeile"],
    "Metaphern/Analogien": ["3 starke Metaphern", "Pro/Contra je Metapher"],
    "Bericht/Protokoll": ["Kurzprotokoll", "Vollprotokoll"],
}

FORMAT_LABEL = {
    "markdown": "Markdown",
    "text": "Reiner Text",
    "json": "JSON",
    "table": "Tabelle (MD)"
}

def keep_or_default(current: str | None, options: list[str]) -> int:
    if not options:
        return 0
    if current in options:
        return options.index(current)
    return 0

# ---------- Sidebar ----------
with st.sidebar:
    st.header("🧭 Navigation")
    lang = st.radio("Sprache", ["de", "en"], index=0,
                    key="lang",
                    format_func=lambda x: "Deutsch" if x=="de" else "Englisch")
    out_format = st.selectbox("Output-Format", list(FORMAT_LABEL.keys()), index=0,
                              key="out_format",
                              format_func=lambda x: FORMAT_LABEL[x])
    length = st.select_slider("Länge", options=["ultrakurz","kurz","mittel","lang","sehr lang"],
                              value=DEFAULTS["length"], key="length")
    st.caption("Hinweis: Keine personenbezogenen oder internen Daten eingeben.")
    st.button("🔄 Zurücksetzen", use_container_width=True, on_click=reset_state)

# ---------- Layout ----------
col_left, col_mid, col_right = st.columns([1.05, 1.6, 1.35], gap="large")

# ---------- Hilfs-Wrapper für optische Hervorhebung ----------
def wrap_optfield(active: bool):
    class _Ctx:
        def __enter__(self):
            if active:
                st.markdown('<div class="optfield">', unsafe_allow_html=True)
        def __exit__(self, exc_type, exc, tb):
            if active:
                st.markdown('</div>', unsafe_allow_html=True)
    return _Ctx()

# ---------- Linke Spalte ----------
with col_left:
    st.subheader("🧩 Use-Case")
    use_case = st.radio("Was möchtest du tun?", list(UC_LABEL.keys()),
                        index=keep_or_default(st.session_state.get("use_case"), list(UC_LABEL.keys())),
                        key="use_case",
                        format_func=lambda v: UC_LABEL[v])

    # Untertyp (abhängig vom Use-Case)
    sub_options = UC_SUBTYPES.get(use_case, [])
    if sub_options:
        st.selectbox("Untertyp", sub_options,
                     index=keep_or_default(st.session_state.get("sub_use_case"), sub_options),
                     key="sub_use_case")
    else:
        st.session_state["sub_use_case"] = None

    st.markdown("---")

    st.subheader("🎯 Ziel / Output")
    goal_options = GOALS_BY_UC.get(use_case, ["Freiform"])
    st.selectbox("Zieltyp", goal_options,
                 index=keep_or_default(st.session_state.get("goal"), goal_options), key="goal")

    subgoal_options = GOAL_SUBTYPES.get(st.session_state.get("goal", ""), [])
    if subgoal_options:
        st.selectbox("Ziel-Untertyp", subgoal_options,
                     index=keep_or_default(st.session_state.get("goal_subtype"), subgoal_options),
                     key="goal_subtype")
    else:
        st.session_state["goal_subtype"] = None

    st.markdown("---")

    # --- Optionale Felder (Text/Area) mit Highlight, sobald Wert vorhanden ---
    with wrap_optfield(bool(st.session_state.get("audience"))):
        st.text_input("Zielgruppe (optional)", key="audience",
                      placeholder="z. B. Leitung, Team, Öffentlichkeit")

    with wrap_optfield(bool(st.session_state.get("constraints"))):
        st.text_area("Rahmen / Muss-Kriterien (optional)", key="constraints",
                     placeholder="Stichworte, Bullets …", height=70)

    st.subheader("🎚️ Stil & Ton")
    # Slider-Highlight: wenn vom Default abweichend
    with wrap_optfield(st.session_state.get("tone", DEFAULTS["tone"]) != DEFAULTS["tone"]):
        st.select_slider("Tonfall", options=["sehr sachlich","sachlich","neutral","lebendig","kreativ"],
                         value=st.session_state.get("tone", DEFAULTS["tone"]), key="tone")

    with wrap_optfield(st.session_state.get("rigor", DEFAULTS["rigor"]) != DEFAULTS["rigor"]):
        st.select_slider("Strenge/Struktur", options=["locker","mittel","klar","sehr klar"],
                         value=st.session_state.get("rigor", DEFAULTS["rigor"]), key="rigor")

    with wrap_optfield(bool(st.session_state.get("persona"))):
        st.text_input("Rolle (optional)", key="persona",
                      placeholder="z. B. Qualitätsauditor:in")

# ---------- Mitte ----------
with col_mid:
    st.subheader("🖼️ Kontext")
    with wrap_optfield(bool(st.session_state.get("context"))):
        st.text_area("Kurzkontext (2–4 Bullets)", key="context",
                     placeholder="• Thema / Problem\n• Ziel & Medium\n• Rahmenbedingungen\n• Quellen/Lage",
                     height=120)

    st.subheader("🧱 Struktur")
    # Multiselect: Highlight, falls von Default abweichend
    current_struct = st.session_state.get("structure", DEFAULTS["structure"])
    with wrap_optfield(sorted(current_struct) != sorted(DEFAULTS["structure"])):
        st.multiselect("Bausteine auswählen",
                       ["Einleitung mit Zielbild","Vorgehensschritte","Analyse","Beispiele",
                        "Qualitäts-Check","Nächste Schritte","Quellen"],
                       default=DEFAULTS["structure"], key="structure")

    st.subheader("🔒 Qualitäts/Compliance")
    # Checkboxen: Highlight, wenn aktiv
    with wrap_optfield(bool(st.session_state.get("qc_facts"))):
        st.checkbox("Faktencheck", key="qc_facts")
    with wrap_optfield(bool(st.session_state.get("qc_bias"))):
        st.checkbox("Bias-Check", key="qc_bias")
    with wrap_optfield(bool(st.session_state.get("qc_dp"))):
        st.checkbox("Datenschutz-Hinweis", key="qc_dp")

# ---------- Prompt-Generator ----------
def build_prompt() -> str:
    lang_hint = "deutsch" if st.session_state.lang == "de" else "englisch"
    today = datetime.now().strftime("%Y-%m-%d")
    of_hint = {
        "markdown": "Antworte in sauberem Markdown.",
        "text": "Antworte als Klartext ohne Markdown.",
        "json": "Antworte als valides JSON.",
        "table": "Antworte als Markdown-Tabelle."
    }[st.session_state.out_format]

    structure = st.session_state.structure or []
    structure_lines = "\n".join(f"- {s}" for s in structure) if structure else "- (freie Struktur)"

    qc_lines = []
    if st.session_state.qc_facts: qc_lines.append("• Prüfe Aussagen auf Plausibilität.")
    if st.session_state.qc_bias:  qc_lines.append("• Weisen auf mögliche Verzerrungen hin.")
    if st.session_state.qc_dp:    qc_lines.append("• Keine personenbezogenen Daten.")
    qc_block = "\n".join(qc_lines) if qc_lines else "• (keine Prüfhinweise)"

    persona_line = f"Rolle: {st.session_state.persona}\n" if st.session_state.persona else ""
    audience_line = f"Zielgruppe: {st.session_state.audience}\n" if st.session_state.audience else ""
    constraints_line = f"Rahmen/Muss-Kriterien:\n{st.session_state.constraints.strip()}\n\n" if st.session_state.constraints.strip() else ""
    sub_uc_line = f"Untertyp: {st.session_state.sub_use_case}\n" if st.session_state.get('sub_use_case') else ""
    subgoal_line = f"Ziel-Untertyp: {st.session_state.goal_subtype}\n" if st.session_state.get('goal_subtype') else ""

    return dedent(f"""
    Du bist ein Assistenzsystem für **{UC_LABEL[st.session_state.use_case]}**.
    {sub_uc_line}{persona_line}{audience_line}{subgoal_line}Sprache: {lang_hint}. Tonfall: {st.session_state.tone}. Struktur: {st.session_state.rigor}. Länge: {st.session_state.length}.
    Ziel/Output: **{st.session_state.goal}**.
    {of_hint}

    Kontext:
    {st.session_state.context.strip() or "(kein Kontext)"}

    Struktur:
    {structure_lines}

    {constraints_line}Qualität & Compliance:
    {qc_block}

    Liefere ein direkt nutzbares Ergebnis.
    Datum: {today}
    """).strip()

# ---------- Rechte Spalte ----------
with col_right:
    st.subheader("👁️ Vorschau")
    prompt_text = build_prompt()
    auto_filename = f"prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    tabs = st.tabs(["🔤 Lesbare Version", "🧾 JSON"])
    with tabs[0]:
        st.code(prompt_text, language="markdown")
        st.download_button("⬇️ Als Markdown speichern",
                           data=prompt_text.encode("utf-8"),
                           file_name=f"{auto_filename}.md",
                           mime="text/markdown")
    with tabs[1]:
        schema = {
            "protocol": "prompt.cockpit/1.0",
            "meta": {"created": datetime.now().isoformat(timespec="seconds")},
            "profile": dict(st.session_state),
            "prompt": prompt_text
        }
        st.json(schema, expanded=False)
        st.download_button("⬇️ JSON speichern",
                           data=json.dumps(schema, ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name=f"{auto_filename}.json",
                           mime="application/json")

# app.py — Prompt-Plattform mit Duhigg-Modi + Deep Question + Feedback/Iteration
from __future__ import annotations
import json
from datetime import datetime
from textwrap import dedent
import streamlit as st

st.set_page_config(page_title="🧭 Prompt-Plattform", page_icon="🧭", layout="wide")

# =========================
# Styles & Theme per Modus
# =========================
MODE_COLORS = {
    "praktisch":  {"primary": "#2f6fed", "tint": "#e9f0ff"},   # blau
    "emotional":  {"primary": "#2ea86b", "tint": "#e8f8ee"},   # grün
    "sozial":     {"primary": "#ef8e1b", "tint": "#fff3e6"},   # orange
}

# Grundstyles inkl. optfield + Checkbox-Färbung (nur Kästchen)
BASE_CSS = """
<style>
.optfield {
  border-radius: 8px;
  padding: 0.45rem 0.6rem;
  background-color: #f6fdf6;
  border: 1px solid #cde6cd;
  margin-bottom: 0.25rem;
}
.optfield textarea, .optfield input, .optfield select { background-color: #f6fdf6 !important; }

/* Checkbox: NUR Kästchen grünlich wenn checked */
div[data-testid="stCheckbox"] > label > div[role="checkbox"][aria-checked="true"] {
  background-color: #e8f8ee !important; border: 1px solid #cde6cd !important;
  box-shadow: 0 0 0 3px rgba(205,230,205,0.35);
}
div[role="checkbox"][aria-checked="true"] { background-color: #e8f8ee !important; border: 1px solid #cde6cd !important; }

/* Modus-Badge */
.mode-badge {
  display:inline-flex; gap:.5rem; align-items:center;
  padding:.35rem .6rem; border-radius:999px; font-weight:600; font-size:.9rem;
  border:1px solid var(--mode-primary);
  background: var(--mode-tint);
  color:#222;
}
</style>
"""
st.markdown(BASE_CSS, unsafe_allow_html=True)

def inject_mode_css(mode_key: str):
    colors = MODE_COLORS.get(mode_key, MODE_COLORS["praktisch"])
    st.markdown(
        f"""
        <style>
        :root {{
          --mode-primary: {colors["primary"]};
          --mode-tint: {colors["tint"]};
        }}
        /* Akzente für Buttons/Tabs */
        .stDownloadButton button, .stButton button {{
          border-color: var(--mode-primary) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# =========================
# Defaults & Session-Init
# =========================
DEFAULTS = {
    "lang": "de", "out_format": "markdown", "length": "mittel",
    "mode": "praktisch",                      # Duhigg-Modus
    "conversation_goal": "",                  # Zieldefinition
    "use_case": "analysieren", "sub_use_case": None,
    "goal": None, "goal_subtype": None,
    "audience": "", "constraints": "",
    "tone": "sachlich", "rigor": "klar", "persona": "",
    "context": "", "structure": ["Einleitung mit Zielbild", "Nächste Schritte"],
    "qc_facts": False, "qc_bias": False, "qc_dp": False,
    "feedback_good": None, "feedback_delta": "",  # Iteration
}

for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

# =========================
# Dictionaries (abhängige Menüs)
# =========================
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
FORMAT_LABEL = {"markdown":"Markdown","text":"Reiner Text","json":"JSON","table":"Tabelle (MD)"}

def keep_or_default(current: str | None, options: list[str]) -> int:
    if not options: return 0
    return options.index(current) if current in options else 0

# =========================
# Deep-Question Generator
# =========================
def deep_question(mode: str, goal: str | None) -> str:
    """Erzeugt eine tiefere Frage passend zum Modus (Duhigg) + optional Ziel."""
    g = goal or ""
    if mode == "emotional":
        return "Was war der Moment, in dem du das am stärksten **gefühlt** hast – und warum?"
    if mode == "sozial":
        return "Wessen **Perspektive** fehlt hier noch – und wie würde diese die Situation verändern?"
    # praktisch
    if "Risiko" in g:   return "Wenn du nur **eine Gegenmaßnahme** umsetzen dürftest: Welche – und warum?"
    if "SWOT" in g:     return "Welche **eine Stärke** zahlt am deutlichsten auf das Ziel ein – und wie nutzen wir sie?"
    if "Interview" in g:return "Welche **Kerninformation** muss das Interview zwingend liefern, um entscheidbar zu werden?"
    return "Angenommen, du hast **nur 30 Minuten**: Welche drei Schritte bringen dich am schnellsten voran – in dieser Reihenfolge?"

# ================
# Sidebar (Modus)
# ================
with st.sidebar:
    st.header("🧭 Navigation")
    st.radio("Sprache", ["de","en"], index=keep_or_default(st.session_state.lang, ["de","en"]),
             key="lang", format_func=lambda x: "Deutsch" if x=="de" else "Englisch", help="Antwortsprache der KI.")
    st.selectbox("Output-Format", list(FORMAT_LABEL.keys()),
                 index=keep_or_default(st.session_state.out_format, list(FORMAT_LABEL.keys())),
                 key="out_format", format_func=lambda x: FORMAT_LABEL[x],
                 help="Struktur der Antwort.")
    st.select_slider("Länge", options=["ultrakurz","kurz","mittel","lang","sehr lang"],
                     value=st.session_state.length, key="length",
                     help="Grobe Ziellänge der Antwort.")

    st.markdown("---")
    st.subheader("🗣️ Gesprächsmodus")
    st.radio(
        "Modus (Duhigg)",
        options=["praktisch","emotional","sozial"],
        index=keep_or_default(st.session_state.mode, ["praktisch","emotional","sozial"]),
        key="mode",
        format_func=lambda m: {"praktisch":"🔧 Praktisch","emotional":"💚 Emotional","sozial":"🧩 Sozial"}[m],
        help="Bestimmt, worauf das Gespräch fokussiert: Handlung (praktisch), Gefühle (emotional) oder Zugehörigkeit/Rollen (sozial)."
    )
    inject_mode_css(st.session_state.mode)
    st.caption(f"""<span class="mode-badge">Modus aktiv: {{"praktisch":"🔧 Praktisch","emotional":"💚 Emotional","sozial":"🧩 Sozial"}[st.session_state.mode]}</span>""",
               unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🎯 Ziel der Konversation")
    # Nur Hintergrund ändern (kein Zusatzcontainer)
    if st.session_state.conversation_goal:
        st.markdown('<div class="optfield">', unsafe_allow_html=True)
    st.text_input("Was willst du mit dieser Konversation erreichen?",
                  key="conversation_goal",
                  placeholder="z. B. Verständnis erhöhen, Entscheidung treffen, Beziehung stärken",
                  help="Klarheit über das Ziel verbessert die Prompt-Qualität.")
    if st.session_state.conversation_goal:
        st.markdown('</div>', unsafe_allow_html=True)

    st.caption("⚠️ Keine personenbezogenen oder internen Unternehmensdaten eingeben.")

    # Reset ohne rerun im Callback
    def _reset():
        for k, v in DEFAULTS.items(): st.session_state[k] = v
        st.session_state["_reset_performed"] = True
    st.button("🔄 Zurücksetzen", use_container_width=True, on_click=_reset)

# =========
# Layout
# =========
col_left, col_mid, col_right = st.columns([1.05, 1.6, 1.35], gap="large")

# =========================
# Linke Spalte (abhängig)
# =========================
with col_left:
    st.subheader("🧩 Use-Case")
    st.radio("Was möchtest du tun?", list(UC_LABEL.keys()),
             index=keep_or_default(st.session_state.use_case, list(UC_LABEL.keys())),
             key="use_case", format_func=lambda v: UC_LABEL[v], help="Oberkategorie für den Prompt.")

    subs = UC_SUBTYPES.get(st.session_state.use_case, [])
    if subs:
        st.selectbox("Untertyp", subs,
                     index=keep_or_default(st.session_state.get("sub_use_case"), subs),
                     key="sub_use_case", help="Feinere Auswahl passend zum Use-Case.")
    else:
        st.session_state["sub_use_case"] = None

    st.markdown("---")
    st.subheader("🎯 Ziel / Output")
    goal_options = GOALS_BY_UC.get(st.session_state.use_case, ["Freiform"])
    st.selectbox("Zieltyp", goal_options,
                 index=keep_or_default(st.session_state.get("goal"), goal_options),
                 key="goal", help="Gewünschte Form des Ergebnisses.")

    subgoal_options = GOAL_SUBTYPES.get(st.session_state.get("goal", ""), [])
    if subgoal_options:
        st.selectbox("Ziel-Untertyp", subgoal_options,
                     index=keep_or_default(st.session_state.get("goal_subtype"), subgoal_options),
                     key="goal_subtype", help="Optionales Format/Variante zum Ziel.")
    else:
        st.session_state["goal_subtype"] = None

    st.markdown("---")

    # Optionale Felder (nur Hintergrund, keine Zusatzcontainer um Checkboxen)
    if st.session_state.audience: st.markdown('<div class="optfield">', unsafe_allow_html=True)
    st.text_input("Zielgruppe (optional)", key="audience",
                  placeholder="z. B. Leitung, Team, Öffentlichkeit", help="Für wen ist das Ergebnis gedacht?")
    if st.session_state.audience: st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.constraints: st.markdown('<div class="optfield">', unsafe_allow_html=True)
    st.text_area("Rahmen / Muss-Kriterien (optional)", key="constraints",
                 placeholder="Stichworte, Bullets …", height=70,
                 help="Voraussetzungen, Grenzen, Positivliste etc.")
    if st.session_state.constraints: st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("🎚️ Stil & Ton")
    # Slider: dezentes Highlight nur bei Abweichung
    if st.session_state.get("tone","sachlich") != "sachlich": st.markdown('<div class="optfield">', unsafe_allow_html=True)
    st.select_slider("Tonfall", options=["sehr sachlich","sachlich","neutral","lebendig","kreativ"],
                     value=st.session_state.get("tone","sachlich"), key="tone",
                     help="Stilistik der Antwort (Formulierungen, Wortwahl).")
    if st.session_state.get("tone","sachlich") != "sachlich": st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.get("rigor","klar") != "klar": st.markdown('<div class="optfield">', unsafe_allow_html=True)
    st.select_slider("Strenge/Struktur", options=["locker","mittel","klar","sehr klar"],
                     value=st.session_state.get("rigor","klar"), key="rigor",
                     help="Grad der Strukturierung/Strenge.")
    if st.session_state.get("rigor","klar") != "klar": st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.persona: st.markdown('<div class="optfield">', unsafe_allow_html=True)
    st.text_input("Rolle (optional)", key="persona",
                  placeholder="z. B. Qualitätsauditor:in", help="In welcher Rolle soll die KI sprechen?")
    if st.session_state.persona: st.markdown('</div>', unsafe_allow_html=True)

# =========================
# Mitte (Kontext, Struktur, Qualität)
# =========================
with col_mid:
    st.subheader("🖼️ Kontext")
    if st.session_state.context: st.markdown('<div class="optfield">', unsafe_allow_html=True)
    st.text_area("Kurzkontext (2–4 Bullets)", key="context",
                 placeholder="• Thema / Problem\n• Ziel & Medium\n• Rahmenbedingungen\n• Quellen/Lage",
                 height=120, help="Nur so viel wie nötig – stichpunktartig.")
    if st.session_state.context: st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("🧱 Struktur")
    default_struct = ["Einleitung mit Zielbild", "Nächste Schritte"]
    cur_struct = st.session_state.get("structure", default_struct)
    if sorted(cur_struct) != sorted(default_struct): st.markdown('<div class="optfield">', unsafe_allow_html=True)
    st.multiselect("Bausteine auswählen",
                   ["Einleitung mit Zielbild","Vorgehensschritte","Analyse","Beispiele",
                    "Qualitäts-Check","Nächste Schritte","Quellen"],
                   default=default_struct, key="structure",
                   help="Welche Gliederungsteile sollen erscheinen?")
    if sorted(cur_struct) != sorted(default_struct): st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("🔒 Qualitäts/Compliance")
    st.checkbox("Faktencheck", key="qc_facts", help="Unsichere Stellen markieren.")
    st.checkbox("Bias-Check", key="qc_bias", help="Auf mögliche Verzerrungen hinweisen.")
    st.checkbox("Datenschutz-Hinweis", key="qc_dp", help="Keinerlei personenbezogene Daten verarbeiten.")

    st.markdown("---")
    st.subheader("🪄 Deep Question")
    dq = deep_question(st.session_state.mode, st.session_state.get("goal"))
    st.info(dq)

# =========================
# Prompt-Erzeugung
# =========================
def build_prompt(base: bool = True) -> str:
    lang_hint = "deutsch" if st.session_state.lang == "de" else "englisch"
    today = datetime.now().strftime("%Y-%m-%d")
    of_hint = {
        "markdown": "Antworte in sauberem Markdown.",
        "text": "Antworte als Klartext ohne Markdown.",
        "json": "Antworte als valides JSON.",
        "table": "Antworte als Markdown-Tabelle."
    }[st.session_state.out_format]

    structure_list = st.session_state.structure or []
    structure_lines = "\n".join(f"- {s}" for s in structure_list) if structure_list else "- (freie Struktur)"

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
    goal_line = f"Konversationsziel: {st.session_state.conversation_goal}\n" if st.session_state.conversation_goal else ""

    mode_line = {
        "praktisch": "Modus: PRAKTISCH – fokussiere auf konkrete Schritte, Klarheit, Entscheidbarkeit.",
        "emotional": "Modus: EMOTIONAL – berücksichtige Gefühle, Motivation, Bedenken.",
        "sozial":    "Modus: SOZIAL – berücksichtige Beziehungen, Rollen, Zugehörigkeit."
    }[st.session_state.mode]

    base_prompt = dedent(f"""
    {mode_line}
    Du bist ein Assistenzsystem für **{UC_LABEL[st.session_state.use_case]}**.
    {sub_uc_line}{persona_line}{audience_line}{subgoal_line}{goal_line}Sprache: {lang_hint}. Tonfall: {st.session_state.tone}. Struktur: {st.session_state.rigor}. Länge: {st.session_state.length}.
    Ziel/Output: **{st.session_state.goal}**.
    {of_hint}

    Kontext:
    {st.session_state.context.strip() or "(kein Kontext)"}

    Struktur:
    {structure_lines}

    Deep Question (Impuls):
    {deep_question(st.session_state.mode, st.session_state.get("goal"))}

    {constraints_line}Qualität & Compliance:
    {qc_block}

    Liefere ein direkt nutzbares Ergebnis.
    Datum: {today}
    """).strip()

    if base: return base_prompt

    # Iterationszusatz (Spiegeln)
    delta = st.session_state.feedback_delta.strip()
    if not delta:
        return base_prompt
    return base_prompt + "\n\n" + dedent(f"""\
    ----
    Iterationshinweis des Nutzers (Spiegeln):
    {delta}

    Überarbeite die Antwort entsprechend dieser Hinweise.
    """).rstrip()

# =========================
# Rechte Spalte (Vorschau/Export + Feedback)
# =========================
with col_right:
    st.subheader("👁️ Vorschau")
    with st.spinner("Prompt wird aufgebaut…"):
        prompt_text = build_prompt(base=True)
    auto_filename = f"prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    tabs = st.tabs(["🔤 Lesbare Version", "🧾 JSON", "🪞 Iteration"])
    with tabs[0]:
        st.code(prompt_text, language="markdown")
        st.download_button("⬇️ Als Markdown speichern",
                           data=prompt_text.encode("utf-8"),
                           file_name=f"{auto_filename}.md", mime="text/markdown")
    with tabs[1]:
        schema = {
            "protocol": "prompt.cockpit/1.1",
            "meta": {
                "created": datetime.now().isoformat(timespec="seconds"),
                "language": st.session_state.lang,
                "format": st.session_state.out_format,
                "length": st.session_state.length,
                "mode": st.session_state.mode
            },
            "profile": {
                "use_case": st.session_state.use_case,
                "use_case_label": UC_LABEL[st.session_state.use_case],
                "sub_use_case": st.session_state.get("sub_use_case"),
                "goal": st.session_state.goal,
                "goal_subtype": st.session_state.get("goal_subtype"),
                "persona": st.session_state.persona or None,
                "audience": st.session_state.audience or None,
                "structure": st.session_state.structure,
                "qc": {
                    "facts": st.session_state.qc_facts,
                    "bias": st.session_state.qc_bias,
                    "data_protection": st.session_state.qc_dp
                },
                "conversation_goal": st.session_state.conversation_goal or None
            },
            "prompt": prompt_text
        }
        st.json(schema, expanded=False)
        st.download_button("⬇️ JSON speichern",
                           data=json.dumps(schema, ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name=f"{auto_filename}.json", mime="application/json")

    with tabs[2]:
        st.markdown("**War die Antwort so, wie erwartet?**")
        st.radio("Bewertung", options=["Ja","Nein"], index=0,
                 key="feedback_good", horizontal=True,
                 help="Falls Nein: Beschreibe unten, was anders sein soll.")
        if st.session_state.feedback_good == "Nein":
            if st.session_state.feedback_delta: st.markdown('<div class="optfield">', unsafe_allow_html=True)
            st.text_area("Was hätte anders sein sollen?",
                         key="feedback_delta", height=120,
                         placeholder="z. B. knapper, mit Handlungsschritten, weniger Fachsprache …")
            if st.session_state.feedback_delta: st.markdown('</div>', unsafe_allow_html=True)

            if st.button("🔁 Überarbeiteten Prompt anzeigen"):
                with st.spinner("Überarbeitete Variante wird erzeugt…"):
                    revised = build_prompt(base=False)
                st.code(revised, language="markdown")
                st.download_button("⬇️ Überarbeitete Version (MD)", data=revised.encode("utf-8"),
                                   file_name=f"{auto_filename}_rev.md", mime="text/markdown")

# Ende

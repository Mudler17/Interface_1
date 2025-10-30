# app.py — Prompt-Plattform (Kompaktes Tab-Layout)
from __future__ import annotations
import json
from datetime import datetime
from textwrap import dedent
from base64 import b64encode
import streamlit as st
from streamlit.components.v1 import html as components_html
import pandas as pd  # Erforderlich für st.data_editor

st.set_page_config(page_title="🧭 Prompt-Plattform", page_icon="🧭", layout="wide")

# =========================
# (Minimal) Styles
# =========================
BASE_CSS = """
<style>
.mode-badge {
  display:inline-flex; gap:.5rem; align-items:center;
  padding:.35rem .6rem; border-radius:999px; font-weight:600; font-size:.9rem;
  border:1px solid #999; background:#f5f5f5; color:#222;
}
.copy-row { display:flex; gap:.5rem; align-items:center; margin:.25rem 0 .5rem 0; }
.copy-btn { padding:.35rem .6rem; border:1px solid #999; background:#fff; border-radius:.5rem; cursor:pointer; }
.copy-btn:hover { background:#f7f7f7; }

/* Vertikalen Platz in Tabs reduzieren */
[data-testid="stTabs"] [data-testid="stMarkdownContainer"] {
    padding-top: 0.5rem;
}
</style>
"""
st.markdown(BASE_CSS, unsafe_allow_html=True)

# =========================
# Defaults & Session-Init
# =========================
DEFAULTS = {
    "lang": "de", "out_format": "markdown", "length": "mittel",
    "mode": "praktisch",
    "conversation_goals": [],
    "use_case": "analysieren",
    "sub_use_cases": [],
    "goal": [],
    "goal_subtype": [],
    "audience": "",
    "constraints": "",
    "tone": "sachlich",
    "rigor": "klar",
    "persona": "",
    "context": "",
    "core_prompt": "",
    "structure": ["Einleitung mit Zielbild", "Nächste Schritte"],
    "qc_facts": False, "qc_bias": False, "qc_dp": False,
    "dq_prioritized_list": [],
    "free_subtypes": "", "free_goals": "", "free_goal_subtypes": "", "free_conv_goals": "",
    "enable_deep_questions": True
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

# =========================
# Dictionaries (Use-Case & Ziele)
# (Unverändert - hier eingeklappt zur besseren Lesbarkeit)
# =========================
UC_LABEL = {"schreiben": "🖋️ Schreiben", "analysieren": "📊 Analysieren", "lernen": "🧠 Lernen/Erklären", "coden": "💻 Coden", "kreativ": "🎨 Kreativideen", "sonstiges": "🧪 Sonstiges"}
UC_SUBTYPES_BASE = {"analysieren": ["SWOT-Analyse", "Risikobewertung", "Prozessanalyse", "Lessons Learned", "Benchmarking", "Wirkungsanalyse"], "schreiben": ["Bericht / Zusammenfassung", "Konzeptpapier", "Leitfaden", "Protokoll / Dokumentation", "Rede / Laudatio", "Newsletter / Beitrag"], "lernen": ["Lernskript / Handout", "Quiz / Wissenstest", "Begriffserklärung", "Trainingsplan / Kursstruktur", "Fallbeispiel / Szenario"], "coden": ["Code-Snippet erzeugen", "Fehleranalyse / Debugging", "Refactoring-Vorschlag", "Testfälle generieren", "Dokumentation schreiben"], "kreativ": ["Brainstorming-Ideen", "Titel / Claims finden", "Metaphern entwickeln", "Storyboard / Szenenaufbau", "Visualisierungsidee", "Prompt für Bildgenerator"], "sonstiges": ["Freiform / Experimentell", "Systemische Reflexion", "Philosophischer Entwurf"]}
GOALS_BY_UC = {"analysieren": ["SWOT-Analyse", "Benchmark", "Risiko-Check", "Lessons Learned", "Ursache–Wirkung", "Wirkungsanalyse"], "schreiben": ["Interviewleitfaden", "Konzeptskizze", "Checkliste", "Bericht/Protokoll", "Newsletter/Beitrag", "Rede/Laudatio"], "coden": ["Code-Snippet", "Testfälle generieren", "Fehleranalyse (Bug Report)", "Refactoring-Vorschlag", "Dokumentation"], "lernen": ["Einfach erklären", "Quiz", "Schritt-für-Schritt-Anleitung", "Glossar", "Fallbeispiel"], "kreativ": ["Brainstorming-Liste", "Storyboard", "Titel/Claims", "Metaphern/Analogien", "Visualisierungsideen"], "sonstiges": ["Freiform"]}
GOAL_SUBTYPES_BASE = {"Interviewleitfaden": ["Themenblöcke + Fragen", "Einleitung + Abschluss"], "Konzeptskizze": ["Leitidee", "Zielbild + Maßnahmen", "Roadmap 30/60/90"], "Checkliste": ["Kurz-Check", "Detail-Check"], "SWOT-Analyse": ["Standard 4-Felder", "Mit Gewichtung"], "Benchmark": ["2er-Vergleich", "Mehrfach-Vergleich (3+)", "Tabellarisch"], "Risiko-Check": ["Risikomatrix", "Top-5 Risiken", "Gegenmaßnahmen"], "Ursache–Wirkung": ["Fishbone (Ishikawa)", "5-Why"], "Wirkungsanalyse": ["Inputs-Outputs-Outcomes", "Theory of Change (Kurz)"], "Code-Snippet": ["Python", "JavaScript", "SQL"], "Refactoring-Vorschlag": ["Lesbarkeit", "Performance", "Struktur"], "Testfälle generieren": ["Unit-Tests", "Property-Based", "Edge-Cases"], "Fehleranalyse (Bug Report)": ["Minimalbeispiel", "Hypothesen", "Fix-Idee"], "Dokumentation": ["Docstring", "README-Skizze", "API-Beschreibung"], "Einfach erklären": ["Für Kinder (8+)", "Für Fachfremde", "Für Fortgeschrittene"], "Quiz": ["6 Fragen", "10 Fragen", "Mix Bloom"], "Schritt-für-Schritt-Anleitung": ["5 Schritte", "10 Schritte", "mit Prüfpunkten"], "Glossar": ["10 Begriffe", "20 Begriffe", "mit Beispielen"], "Fallbeispiel": ["Szenario kurz", "Szenario ausführlich"], "Brainstorming-Liste": ["20 Ideen", "5 Kategorien × 5 Ideen"], "Storyboard": ["3-Akt-Struktur", "Kapitel-Outline"], "Titel/Claims": ["10 Titel", "5 Claims + Unterzeile"], "Metaphern/Analogien": ["3 starke Metaphern", "Pro/Contra je Metapher"], "Visualisierungsideen": ["Skizzenansätze", "Infografik-Varianten"], "Newsletter/Beitrag": ["Kurzmeldung", "Standard (Lead/Zitat/Hintergrund)"], "Bericht/Protokoll": ["Kurzprotokoll", "Vollprotokoll"], "Rede/Laudatio": ["klassisch", "persönlich", "prägnant"], "Freiform": []}
FORMAT_LABEL = {"markdown": "Markdown", "text": "Reiner Text", "json": "JSON", "table": "Tabelle (MD)"}
GOAL_EXAMPLES = {"praktisch": ["Verständnis klären", "Lösung entwickeln", "Entscheidung vorbereiten", "Prioritäten festlegen", "Nächste Schritte planen"], "emotional": ["Motivation stärken", "Vertrauen aufbauen", "Bedenken ansprechen", "Ermutigung geben", "Feedback verarbeiten"], "sozial": ["Zusammenarbeit verbessern", "Rollen klären", "Anerkennung zeigen", "Gemeinsame Vision entwickeln", "Spannungen abbauen"]}

# =========================
# Utility (Unverändert)
# =========================
def keep_or_default(current, options):
    if not options: return 0
    if current in options: return options.index(current)
    return 0

def parse_free_list(text: str) -> list[str]:
    if not text: return []
    raw = [t.strip() for t in (",".join(text.splitlines())).split(",")]
    return [t for t in raw if t]

def unique_merge(base: list[str], extra: list[str]) -> list[str]:
    seen, merged = set(), []
    for x in base + extra:
        if x not in seen:
            merged.append(x)
            seen.add(x)
    return merged

def _normalize_default_list(val, options):
    if isinstance(val, list): base = val
    elif isinstance(val, str): base = [s.strip() for s in val.split(",") if s.strip()]
    elif val is None: base = []
    else: base = []
    return [o for o in base if o in options]

def multiselect_with_free_text(label: str, options: list[str], state_key: str, free_key: str, help: str = "", placeholder: str = "Eigenes hinzufügen … (kommagetrennt)"):
    default_selected = _normalize_default_list(st.session_state.get(state_key), options)
    selected = st.multiselect(label, options, default=default_selected, key=state_key, help=help)
    free_val = st.text_input("+" + label, key=free_key, placeholder=placeholder, help="Eigene Einträge ergänzen (mit Enter bestätigen).")
    free_items = parse_free_list(free_val)
    combined = unique_merge(selected, free_items)
    return selected, free_items, combined

def aggregate_subtypes_for_goals(goals: list[str]) -> list[str]:
    pool = []
    for g in goals: pool.extend(GOAL_SUBTYPES_BASE.get(g, []))
    seen, agg = set(), []
    for x in pool:
        if x not in seen: agg.append(x); seen.add(x)
    return agg

def _clear_dependent_fields():
    st.session_state.sub_use_cases = DEFAULTS["sub_use_cases"]
    st.session_state.goal = DEFAULTS["goal"]
    st.session_state.goal_subtype = DEFAULTS["goal_subtype"]
    st.session_state.free_subtypes = DEFAULTS["free_subtypes"]
    st.session_state.free_goals = DEFAULTS["free_goals"]
    st.session_state.free_goal_subtypes = DEFAULTS["free_goal_subtypes"]

# =========================
# Deep Questions (Unverändert)
# =========================
def deep_questions(mode: str, goals: list[str]) -> list[str]:
    gset = set(goals or [])
    qs = []
    if mode == "emotional":
        qs = ["Wann hast du das zuletzt besonders **stark gefühlt** – und was hat es ausgelöst?", "Welche **Sorgen oder Hoffnungen** sind hier für dich am wichtigsten?", "Was würde dir **Zuversicht** geben, den nächsten Schritt zu gehen?"]
    elif mode == "sozial":
        qs = ["Wessen **Perspektive** fehlt aktuell – und wie würde sie die Lage verändern?", "Welche **Rollen oder Erwartungen** prägen das Verhalten der Beteiligten?", "Welche **gemeinsamen Werte** könnten hier Orientierung geben?"]
    else:  # praktisch
        if "Risiko-Check" in gset: qs = ["Wenn du nur **eine Gegenmaßnahme** umsetzen dürftest: Welche – und warum?", "Welche **Frühindikatoren** signalisieren dir, dass das Risiko steigt?", "Welche **Grenzwerte** lösen eine **Sofortmaßnahme** aus?"]
        elif "SWOT-Analyse" in gset: qs = ["Welche **einzige Stärke** zahlt am stärksten aufs Ziel ein – und wie hebeln wir sie?", "Welche **Schwäche** ist kurzfristig am **billigsten** zu entschärfen?", "Welche **Chance** können wir mit geringstem Aufwand testen?"]
        elif "Interviewleitfaden" in gset: qs = ["Welche **Kerninformation** muss das Interview liefern, um **entscheidbar** zu werden?", "Welche **kritische Nachfrage** klärt das größte Rest-Risiko?", "Welche **Beispiele** machen die Aussagen **nachprüfbar**?"]
        else: qs = ["Wenn du **30 Minuten** hättest: Welche 3 Schritte bringen dich am schnellsten voran (Reihenfolge)?", "Welchen **Entscheid** müsstest du heute treffen, um Momentum zu gewinnen?", "Welche **Hürde** blockiert aktuell am meisten – und was wäre ein **kleiner Test**, sie zu senken?"]
    return qs

def prioritize_questions_editor(label: str, options: list[str]) -> list[str]:
    if not options:
        st.info("Keine Deep Questions für diese Auswahl verfügbar.")
        return []
    df_state_key = "dq_editor_df"
    current_option_set = set(options)
    if df_state_key not in st.session_state:
        st.session_state[df_state_key] = pd.DataFrame({"Frage": options})
    else:
        try:
            stored_option_set = set(st.session_state[df_state_key]["Frage"])
            if current_option_set != stored_option_set:
                st.session_state[df_state_key] = pd.DataFrame({"Frage": options})
        except KeyError:
             st.session_state[df_state_key] = pd.DataFrame({"Frage": options})
    
    st.caption(f"{label} (Top 3, Reihenfolge per Drag-and-Drop ändern)")
    edited_df = st.data_editor(
        st.session_state[df_state_key],
        key="dq_editor_widget",
        column_config={"Frage": st.column_config.TextColumn("Frage", disabled=True, width="large")},
        hide_index=True,
        num_rows="dynamic",
    )
    st.session_state[df_state_key] = edited_df
    return list(edited_df["Frage"].head(3))

# =========================
# Sidebar (Unverändert)
# =========================
with st.sidebar:
    st.header("🧭 Navigation")
    st.radio("Sprache", ["de","en"],
             index=keep_or_default(st.session_state.lang, ["de","en"]),
             key="lang", format_func=lambda x: "Deutsch" if x=="de" else "Englisch",
             help="Antwortsprache der KI.")
    st.selectbox("Output-Format", list(FORMAT_LABEL.keys()),
                 index=keep_or_default(st.session_state.out_format, list(FORMAT_LABEL.keys())),
                 key="out_format", format_func=lambda x: FORMAT_LABEL[x],
                 help="Struktur der Antwort.")
    st.select_slider("Länge", options=["ultrakurz","kurz","mittel","lang","sehr lang"],
                     value=st.session_state.length, key="length",
                     help="Grobe Ziellänge der Antwort.")

    st.markdown("---")
    st.subheader("🗣️ Gesprächsmodus")
    st.radio("Modus (Duhigg)", options=["praktisch","emotional","sozial"],
             index=keep_or_default(st.session_state.mode, ["praktisch","emotional","sozial"]),
             key="mode",
             format_func=lambda m: {"praktisch":"🔧 Praktisch","emotional":"💚 Emotional","sozial":"🧩 Sozial"}[m],
             help="Fokus: Handlung (praktisch), Gefühle (emotional) oder Zugehörigkeit/Rollen (sozial).")
    mode_label = {"praktisch":"🔧 Praktisch","emotional":"💚 Emotional","sozial":"🧩 Sozial"}[st.session_state.mode]
    st.caption(f'<span class="mode-badge">Modus aktiv: {mode_label}</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.checkbox("Deep Questions aktivieren", key="enable_deep_questions", help="Schalte das Deep-Question-Modul ein/aus.")

    st.markdown("---")
    st.subheader("🎯 Konversationsziele")
    mode_examples = GOAL_EXAMPLES.get(st.session_state.mode, [])
    _sel_conv, _free_conv, conv_goals_combined = multiselect_with_free_text(
        "Typische Ziele (Mehrfachauswahl)",
        mode_examples,
        state_key="conversation_goals",
        free_key="free_conv_goals",
        help="Wähle mehrere Ziele und/oder ergänze eigene."
    )
    st.session_state["conversation_goals_combined"] = conv_goals_combined

    st.caption("⚠️ Keine personenbezogenen oder internen Unternehmensdaten eingeben.")

    def _reset():
        for k, v in DEFAULTS.items(): st.session_state[k] = v
        for k in ["conversation_goals_combined","sub_use_cases_combined","goals_combined","goal_subtypes_combined"]: st.session_state[k] = []
        if "dq_editor_df" in st.session_state: del st.session_state["dq_editor_df"]
        if "dq_editor_widget" in st.session_state: del st.session_state["dq_editor_widget"]
            
    st.button("🔄 Zurücksetzen", use_container_width=True, on_click=_reset)

# =========
# Prominente Eingabe: Anliegen / Kernprompt (Unverändert)
# =========
st.markdown("## 📝 Anliegen / Kernprompt")
st.text_area(
    "Formuliere dein zentrales Anliegen (frei).",
    key="core_prompt",
    placeholder="Beschreibe in 1–3 Sätzen, was du erreichen willst, worum es geht, welche Besonderheiten wichtig sind …",
    height=120,
    help="Dieser freie Text steht im Mittelpunkt und wird direkt in den finalen Prompt eingebaut."
)
st.markdown("---")

# =========
# NEUES LAYOUT: col_config (mit Tabs) und col_output
# =========
col_config, col_output = st.columns([1.8, 1.2], gap="large")

with col_config:
    tab_uc, tab_context, tab_details, tab_dq = st.tabs([
        "🎯 1. Use-Case & Ziel", 
        "🖼️ 2. Kontext & Stil", 
        "⚙️ 3. Details & QC",
        "🪄 4. Deep Questions"
    ])

    # =========================
    # Tab 1: Use-Case & Ziel
    # =========================
    with tab_uc:
        st.subheader("🧩 Use-Case")
        st.radio("Was möchtest du tun?", list(UC_LABEL.keys()),
                 index=keep_or_default(st.session_state.use_case, list(UC_LABEL.keys())),
                 key="use_case", format_func=lambda v: UC_LABEL[v],
                 help="Oberkategorie für den Prompt.",
                 on_change=_clear_dependent_fields,
                 horizontal=True # Kompakter
        )
        
        st.subheader("🎯 Ziel / Output (Mehrfach)")
        goal_options = GOALS_BY_UC.get(st.session_state.use_case, ["Freiform"])
        _sel_goals, _free_goals, goals_combined = multiselect_with_free_text(
            "Ziele wählen",
            goal_options,
            state_key="goal",
            free_key="free_goals",
            help="Mehrere Zielarten kombinieren."
        )
        st.session_state["goals_combined"] = goals_combined

        # KOMPAKT: Optionale Details in Expander
        with st.expander("Optionale Untertypen (Use-Case & Ziel)"):
            base_subtypes = UC_SUBTYPES_BASE.get(st.session_state.use_case, [])
            _sel_subtypes, _free_subtypes, subtypes_combined = multiselect_with_free_text(
                "Use-Case Untertypen",
                base_subtypes,
                state_key="sub_use_cases",
                free_key="free_subtypes",
                help="Feinere Auswahl passend zum Use-Case."
            )
            st.session_state["sub_use_cases_combined"] = subtypes_combined

            aggregated_subtypes = aggregate_subtypes_for_goals(goals_combined)
            _sel_gsub, _free_gsub, goal_subtypes_combined = multiselect_with_free_text(
                "Ziel-Untertypen",
                aggregated_subtypes,
                state_key="goal_subtype",
                free_key="free_goal_subtypes",
                help="Feinvarianten zum Ziel (optional)."
            )
            st.session_state["goal_subtypes_combined"] = goal_subtypes_combined

    # =========================
    # Tab 2: Kontext & Stil
    # =========================
    with tab_context:
        st.subheader("🖼️ Kontext")
        st.text_area("Kurzkontext (2–4 Bullets)", key="context",
                     placeholder="• Thema / Problem\n• Ziel & Medium\n• Rahmenbedingungen\n• Quellen/Lage",
                     height=140, help="Stichpunkte reichen.")

        st.text_input("Zielgruppe (optional)", key="audience",
                      placeholder="z. B. Leitung, Team, Öffentlichkeit",
                      help="Für wen ist das Ergebnis gedacht?")

        # KOMPAKT: Stil-Settings in Popover
        with st.popover("🎚️ Stil, Ton & Rolle anpassen"):
            st.subheader("🎚️ Stil & Ton")
            st.select_slider("Tonfall", options=["sehr sachlich","sachlich","neutral","lebendig","kreativ"],
                             value=st.session_state.get("tone","sachlich"), key="tone",
                             help="Stilistik der Antwort.")
            st.select_slider("Strenge/Struktur", options=["locker","mittel","klar","sehr klar"],
                             value=st.session_state.get("rigor","klar"), key="rigor",
                             help="Grad der Strukturierung.")
            
            st.subheader("🤖 Rolle (Optional)")
            st.text_input("Rolle der KI", key="persona",
                          placeholder="z. B. Qualitätsauditor:in", help="Rolle/Persona der KI.")

    # =========================
    # Tab 3: Details & QC
    # =========================
    with tab_details:
        st.subheader("🧱 Struktur der Antwort")
        default_struct = ["Einleitung mit Zielbild", "Nächste Schritte"]
        st.multiselect("Bausteine auswählen",
                       ["Einleitung mit Zielbild","Vorgehensschritte","Analyse","Beispiele",
                        "Qualitäts-Check","Nächste Schritte","Quellen"],
                       default=default_struct, key="structure",
                       help="Welche Gliederungsteile sollen erscheinen?")

        st.subheader("🔒 Qualitäts/Compliance")
        c1, c2, c3 = st.columns(3)
        with c1: st.checkbox("Faktencheck", key="qc_facts", help="Unsichere Stellen markieren.")
        with c2: st.checkbox("Bias-Check", key="qc_bias", help="Auf mögliche Verzerrungen hinweisen.")
        with c3: st.checkbox("Datenschutz-Hinweis", key="qc_dp", help="Keinerlei personenbezogene Daten verarbeiten.")

        st.subheader("📋 Rahmen / Muss-Kriterien")
        st.text_area("Rahmen / Muss-Kriterien (optional)", key="constraints",
                     placeholder="Stichworte, Bullets …\n• Maximal 300 Wörter\n• Muss 'Projekt X' erwähnen", height=100,
                     help="Voraussetzungen, Grenzen, Positivliste etc.", label_visibility="collapsed")

    # =========================
    # Tab 4: Deep Questions
    # =========================
    with tab_dq:
        if st.session_state.enable_deep_questions:
            st.subheader("🪄 Deep Questions (Priorisierung)")
            dq_list_options = deep_questions(st.session_state.mode, st.session_state.get("goals_combined", []))
            prioritized_list = prioritize_questions_editor("Fragen priorisieren", dq_list_options)
            st.session_state["dq_prioritized_list"] = prioritized_list 
            
            if prioritized_list:
                st.caption("Priorisierte Fragen (Top 3):")
                for i, q in enumerate(prioritized_list, 1):
                    st.write(f"{i}. {q}")
        else:
            st.info("Deep-Questions-Modul ist in der Sidebar deaktiviert. Aktiviere es, um hier Fragen zu priorisieren.")

# =========================
# Prompt-Erzeugung (Unverändert)
# =========================
def build_prompt() -> str:
    lang_hint = "deutsch" if st.session_state.lang == "de" else "englisch"
    today = datetime.now().strftime("%Y-%m-%d")
    of_hint = {"markdown": "Antworte in sauberem Markdown.", "text": "Antworte als Klartext ohne Markdown.", "json": "Antworte als valides JSON.", "table": "Antworte als Markdown-Tabelle."}[st.session_state.out_format]
    subtypes_combined = st.session_state.get("sub_use_cases_combined", st.session_state.sub_use_cases)
    goals_combined = st.session_state.get("goals_combined", st.session_state.goal)
    goal_subtypes_combined = st.session_state.get("goal_subtypes_combined", st.session_state.goal_subtype)
    conv_goals_combined = st.session_state.get("conversation_goals_combined", st.session_state.conversation_goals)
    structure_list = st.session_state.structure or []
    structure_lines = "\n".join(f"- {s}" for s in structure_list) if structure_list else "- (freie Struktur)"
    qc_lines = []
    if st.session_state.qc_facts: qc_lines.append("• Prüfe Aussagen auf Plausibilität.")
    if st.session_state.qc_bias:  qc_lines.append("• Weisen auf mögliche Verzerrungen hin.")
    if st.session_state.qc_dp:    qc_lines.append("• Keine personenbezogenen Daten.")
    qc_block = "\n".join(qc_lines) if qc_lines else "• (keine Prüfhinweise)"
    use_case_label = UC_LABEL[st.session_state.use_case]
    sub_uc_line = f"Untertypen: {', '.join(subtypes_combined)}\n" if subtypes_combined else ""
    goals_line = f"Ziele/Outputs: {', '.join(goals_combined)}\n" if goals_combined else ""
    subgoals_line = f"Ziel-Untertypen: {', '.join(goal_subtypes_combined)}\n" if goal_subtypes_combined else ""
    conv_goals_line = f"Konversationsziele: {', '.join(conv_goals_combined)}\n" if conv_goals_combined else ""
    persona_line = f"Rolle: {st.session_state.persona}\n" if st.session_state.persona else ""
    audience_line = f"Zielgruppe: {st.session_state.audience}\n" if st.session_state.audience else ""
    constraints_line = f"Rahmen/Muss-Kriterien:\n{st.session_state.constraints.strip()}\n\n" if st.session_state.constraints.strip() else ""
    mode_line = {"praktisch": "Modus: PRAKTISCH – fokussiere auf konkrete Schritte, Klarheit, Entscheidbarkeit.", "emotional": "Modus: EMOTIONAL – berücksichtige Gefühle, Motivation, Bedenken.", "sozial": "Modus: SOZIAL – berücksichtige Beziehungen, Rollen, Zugehörigkeit."}[st.session_state.mode]
    dq_block = ""
    if st.session_state.enable_deep_questions:
        dq = st.session_state.get("dq_prioritized_list", [])
        if not dq: dq = deep_questions(st.session_state.mode, goals_combined)[:3]
        if dq: dq_block = "\n\nDeep Questions (priorisiert):\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(dq))
    base_prompt = dedent(f"""
    {mode_line}
    Du bist ein Assistenzsystem für **{use_case_label}**.

    Anliegen / Kernprompt:
    {st.session_state.core_prompt.strip() or "(kein Anliegen angegeben)"}

    {sub_uc_line}{persona_line}{audience_line}{goals_line}{subgoals_line}{conv_goals_line}Sprache: {lang_hint}. Tonfall: {st.session_state.tone}. Struktur: {st.session_state.rigor}. Länge: {st.session_state.length}.
    {of_hint}

    Kontext:
    {st.session_state.context.strip() or "(kein Kontext)"}

    Struktur:
    {structure_lines}{dq_block}

    {constraints_line}Qualität & Compliance:
    {qc_block}

    Liefere ein direkt nutzbares Ergebnis.
    Datum: {today}
    """).strip()
    return base_prompt

# ---------- Copy-to-clipboard helper (Unverändert) ----------
def render_copy_button(text: str, key: str, label: str = "📋 Kopieren"):
    enc = b64encode(text.encode("utf-8")).decode("ascii")
    success_label = "✅ Kopiert!"
    js_click = f"""
    (function(btn){{
        const t = atob('{enc}'); 
        navigator.clipboard.writeText(t); 
        const old_label = btn.innerText;
        btn.innerText = '{success_label}'; 
        btn.disabled = true;
        setTimeout(function(){{ 
            btn.innerText = old_label; 
            btn.disabled = false;
        }}, 1500);
    }})(this)
    """
    components_html(
        f"""
        <div class="copy-row">
          <button class.="copy-btn" onclick="{js_click.replace('"', '&quot;')}" key="btn_{key}">{label}</button>
          <span>In Zwischenablage kopieren</span>
        </div>
        """,
        height=40,
    )

# =========================
# NEUES LAYOUT: col_output (Rechte Spalte)
# =========================
with col_output:
    st.subheader("👁️ Vorschau")
    prompt_text = build_prompt()
    auto_filename = f"prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    tabs_out = st.tabs(["🔤 Lesbare Version", "🧾 JSON"])
    with tabs_out[0]:
        st.code(prompt_text, language="markdown")
        render_copy_button(prompt_text, key="copy_md", label="📋 Prompt kopieren")
        st.download_button("⬇️ Als Markdown speichern",
                           data=prompt_text.encode("utf-8"),
                           file_name=f"{auto_filename}.md", mime="text/markdown")

    with tabs_out[1]:
        schema = {
            "protocol": "prompt.cockpit/1.3",
            "meta": {"created": datetime.now().isoformat(timespec="seconds"), "language": st.session_state.lang, "format": st.session_state.out_format, "length": st.session_state.length, "mode": st.session_state.mode, "deep_questions_enabled": st.session_state.enable_deep_questions},
            "profile": {"use_case": st.session_state.use_case, "use_case_label": UC_LABEL[st.session_state.use_case], "sub_use_cases": st.session_state.get("sub_use_cases_combined", st.session_state.sub_use_cases), "goals": st.session_state.get("goals_combined", st.session_state.goal), "goal_subtypes": st.session_state.get("goal_subtypes_combined", st.session_state.goal_subtype), "persona": st.session_state.persona or None, "audience": st.session_state.audience or None, "structure": st.session_state.structure, "qc": {"facts": st.session_state.qc_facts, "bias": st.session_state.qc_bias, "data_protection": st.session_state.qc_dp}, "conversation_goals": st.session_state.get("conversation_goals_combined", st.session_state.conversation_goals)},
            "core_prompt": st.session_state.core_prompt,
            "context": st.session_state.context,
            "constraints": st.session_state.constraints,
            "deep_questions": {"prioritized": st.session_state.get("dq_prioritized_list", []) if st.session_state.enable_deep_questions else []},
            "rendered_prompt": prompt_text
        }
        json_text = json.dumps(schema, ensure_ascii=False, indent=2)
        st.json(schema, expanded=False)
        render_copy_button(json_text, key="copy_json", label="📋 JSON kopieren")
        st.download_button("⬇️ JSON speichern",
                           data=json_text.encode("utf-8"),
                           file_name=f"{auto_filename}.json", mime="application/json")

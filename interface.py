# app.py — Prompt-Plattform (Multiselect+Freitext in Dropdowns, Deep Questions mit Priorisierung, keine Button-Färbung)
from __future__ import annotations
import json
from datetime import datetime
from textwrap import dedent
import streamlit as st

st.set_page_config(page_title="🧭 Prompt-Plattform", page_icon="🧭", layout="wide")

# =========================
# Styles (ohne Button-Färbung!)
# =========================
BASE_CSS = """
<style>
/* Bearbeitete Felder: dezente, blassgrüne Hinterlegung */
.optfield {
  border-radius: 8px;
  padding: 0.45rem 0.6rem;
  background-color: #f6fdf6;
  border: 1px solid #cde6cd;
  margin-bottom: 0.25rem;
}
.optfield textarea, .optfield input, .optfield select { background-color: #f6fdf6 !important; }

/* Checkbox: NUR Kästchen grünlich wenn checked (keine Button-Färbungen) */
div[data-testid="stCheckbox"] > label > div[role="checkbox"][aria-checked="true"] {
  background-color: #e8f8ee !important;
  border: 1px solid #cde6cd !important;
  box-shadow: 0 0 0 3px rgba(205,230,205,0.35);
}
div[role="checkbox"][aria-checked="true"] {
  background-color: #e8f8ee !important;
  border: 1px solid #cde6cd !important;
}

/* Modus-Badge (neutral, ohne Button-Färbung) */
.mode-badge {
  display:inline-flex; gap:.5rem; align-items:center;
  padding:.35rem .6rem; border-radius:999px; font-weight:600; font-size:.9rem;
  border:1px solid #999;
  background: #f5f5f5;
  color:#222;
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
    "conversation_goals": [],           # Liste (statt Einzel-String)
    "use_case": "analysieren",
    "sub_use_cases": [],                # Liste (Multiselect)
    "goal": [],                         # Liste (Multiselect)
    "goal_subtype": [],                 # Liste (Multiselect)
    "audience": "",
    "constraints": "",
    "tone": "sachlich",
    "rigor": "klar",
    "persona": "",
    "context": "",
    "structure": ["Einleitung mit Zielbild", "Nächste Schritte"],
    "qc_facts": False, "qc_bias": False, "qc_dp": False,
    # Deep Questions Auswahl:
    "dq_top1": None, "dq_top2": None, "dq_top3": None,
    # Freitext-Inputs (temporär):
    "free_subtypes": "", "free_goals": "", "free_goal_subtypes": "", "free_conv_goals": ""
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

# =========================
# Dictionaries (Use-Case & Ziele)
# =========================
UC_LABEL = {
    "schreiben": "🖋️ Schreiben",
    "analysieren": "📊 Analysieren",
    "lernen": "🧠 Lernen/Erklären",
    "coden": "💻 Coden",
    "kreativ": "🎨 Kreativideen",
    "sonstiges": "🧪 Sonstiges",
}

# Passendere Untertypen (je Use-Case)
UC_SUBTYPES_BASE = {
    "analysieren": [
        "SWOT-Analyse", "Risikobewertung", "Prozessanalyse",
        "Lessons Learned", "Benchmarking", "Wirkungsanalyse"
    ],
    "schreiben": [
        "Bericht / Zusammenfassung", "Konzeptpapier", "Leitfaden",
        "Protokoll / Dokumentation", "Rede / Laudatio", "Newsletter / Beitrag"
    ],
    "lernen": [
        "Lernskript / Handout", "Quiz / Wissenstest", "Begriffserklärung",
        "Trainingsplan / Kursstruktur", "Fallbeispiel / Szenario"
    ],
    "coden": [
        "Code-Snippet erzeugen", "Fehleranalyse / Debugging",
        "Refactoring-Vorschlag", "Testfälle generieren", "Dokumentation schreiben"
    ],
    "kreativ": [
        "Brainstorming-Ideen", "Titel / Claims finden", "Metaphern entwickeln",
        "Storyboard / Szenenaufbau", "Visualisierungsidee", "Prompt für Bildgenerator"
    ],
    "sonstiges": [
        "Freiform / Experimentell", "Systemische Reflexion", "Philosophischer Entwurf"
    ],
}

# Ziele je Use-Case (mehrfach möglich)
GOALS_BY_UC = {
    "analysieren": ["SWOT-Analyse", "Benchmark", "Risiko-Check", "Lessons Learned", "Ursache–Wirkung", "Wirkungsanalyse"],
    "schreiben":   ["Interviewleitfaden", "Konzeptskizze", "Checkliste", "Bericht/Protokoll", "Newsletter/Beitrag", "Rede/Laudatio"],
    "coden":       ["Code-Snippet", "Testfälle generieren", "Fehleranalyse (Bug Report)", "Refactoring-Vorschlag", "Dokumentation"],
    "lernen":      ["Einfach erklären", "Quiz", "Schritt-für-Schritt-Anleitung", "Glossar", "Fallbeispiel"],
    "kreativ":     ["Brainstorming-Liste", "Storyboard", "Titel/Claims", "Metaphern/Analogien", "Visualisierungsideen"],
    "sonstiges":   ["Freiform"],
}

# Untertypen je Ziel (für alle gewählten Ziele zusammen aggregieren)
GOAL_SUBTYPES_BASE = {
    "Interviewleitfaden": ["Themenblöcke + Fragen", "Einleitung + Abschluss"],
    "Konzeptskizze": ["Leitidee", "Zielbild + Maßnahmen", "Roadmap 30/60/90"],
    "Checkliste": ["Kurz-Check", "Detail-Check"],
    "SWOT-Analyse": ["Standard 4-Felder", "Mit Gewichtung"],
    "Benchmark": ["2er-Vergleich", "Mehrfach-Vergleich (3+)", "Tabellarisch"],
    "Risiko-Check": ["Risikomatrix", "Top-5 Risiken", "Gegenmaßnahmen"],
    "Ursache–Wirkung": ["Fishbone (Ishikawa)", "5-Why"],
    "Wirkungsanalyse": ["Inputs-Outputs-Outcomes", "Theory of Change (Kurz)"],
    "Code-Snippet": ["Python", "JavaScript", "SQL"],
    "Refactoring-Vorschlag": ["Lesbarkeit", "Performance", "Struktur"],
    "Testfälle generieren": ["Unit-Tests", "Property-Based", "Edge-Cases"],
    "Fehleranalyse (Bug Report)": ["Minimalbeispiel", "Hypothesen", "Fix-Idee"],
    "Dokumentation": ["Docstring", "README-Skizze", "API-Beschreibung"],
    "Einfach erklären": ["Für Kinder (8+)", "Für Fachfremde", "Für Fortgeschrittene"],
    "Quiz": ["6 Fragen", "10 Fragen", "Mix Bloom"],
    "Schritt-für-Schritt-Anleitung": ["5 Schritte", "10 Schritte", "mit Prüfpunkten"],
    "Glossar": ["10 Begriffe", "20 Begriffe", "mit Beispielen"],
    "Fallbeispiel": ["Szenario kurz", "Szenario ausführlich"],
    "Brainstorming-Liste": ["20 Ideen", "5 Kategorien × 5 Ideen"],
    "Storyboard": ["3-Akt-Struktur", "Kapitel-Outline"],
    "Titel/Claims": ["10 Titel", "5 Claims + Unterzeile"],
    "Metaphern/Analogien": ["3 starke Metaphern", "Pro/Contra je Metapher"],
    "Visualisierungsideen": ["Skizzenansätze", "Infografik-Varianten"],
    "Newsletter/Beitrag": ["Kurzmeldung", "Standard (Lead/Zitat/Hintergrund)"],
    "Bericht/Protokoll": ["Kurzprotokoll", "Vollprotokoll"],
    "Rede/Laudatio": ["klassisch", "persönlich", "prägnant"],
    "Freiform": [],
}

FORMAT_LABEL = {"markdown":"Markdown","text":"Reiner Text","json":"JSON","table":"Tabelle (MD)"}

# Konversationsziel-Beispiele pro Modus
GOAL_EXAMPLES = {
    "praktisch": [
        "Verständnis klären",
        "Lösung entwickeln",
        "Entscheidung vorbereiten",
        "Prioritäten festlegen",
        "Nächste Schritte planen",
    ],
    "emotional": [
        "Motivation stärken",
        "Vertrauen aufbauen",
        "Bedenken ansprechen",
        "Ermutigung geben",
        "Feedback verarbeiten",
    ],
    "sozial": [
        "Zusammenarbeit verbessern",
        "Rollen klären",
        "Anerkennung zeigen",
        "Gemeinsame Vision entwickeln",
        "Spannungen abbauen",
    ],
}

# =========================
# Utility
# =========================
def keep_or_default(current, options):
    if not options: return 0
    if current in options: return options.index(current)
    return 0

def parse_free_list(text: str) -> list[str]:
    # kommagetrennt oder zeilenweise
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

def multiselect_with_free_text(label: str, options: list[str], state_key: str, free_key: str, help: str = "", placeholder: str = "Eigenes hinzufügen … (kommagetrennt)"):
    """Zeigt Multiselect + Free-Text-Feld. Rückgabe: Liste (vereint, eindeutig)."""
    current = st.session_state.get(state_key, [])
    # Multiselect
    selected = st.multiselect(label, options, default=[o for o in current if o in options], key=state_key, help=help)
    # Free text
    free_val = st.text_input("+" + label, key=free_key, placeholder=placeholder, help="Eigene Einträge ergänzen (mit Enter bestätigen).")
    free_items = parse_free_list(free_val)
    combined = unique_merge(selected, free_items)
    return combined

def aggregate_subtypes_for_goals(goals: list[str]) -> list[str]:
    pool = []
    for g in goals:
        pool.extend(GOAL_SUBTYPES_BASE.get(g, []))
    # Eindeutig + sortiert nach Auftreten
    seen, agg = set(), []
    for x in pool:
        if x not in seen:
            agg.append(x); seen.add(x)
    return agg

# =========================
# Deep Questions (3 Vorschläge + Priorisierung)
# =========================
def deep_questions(mode: str, goals: list[str]) -> list[str]:
    gset = set(goals or [])
    qs = []
    if mode == "emotional":
        qs = [
            "Wann hast du das zuletzt besonders **stark gefühlt** – und was hat es ausgelöst?",
            "Welche **Sorgen oder Hoffnungen** sind hier für dich am wichtigsten?",
            "Was würde dir **Zuversicht** geben, den nächsten Schritt zu gehen?",
        ]
    elif mode == "sozial":
        qs = [
            "Wessen **Perspektive** fehlt aktuell – und wie würde sie die Lage verändern?",
            "Welche **Rollen oder Erwartungen** prägen das Verhalten der Beteiligten?",
            "Welche **gemeinsamen Werte** könnten hier Orientierung geben?",
        ]
    else:  # praktisch
        if "Risiko-Check" in gset:
            qs = [
                "Wenn du nur **eine Gegenmaßnahme** umsetzen dürftest: Welche – und warum?",
                "Welche **Frühindikatoren** signalisieren dir, dass das Risiko steigt?",
                "Welche **Grenzwerte** lösen eine **Sofortmaßnahme** aus?",
            ]
        elif "SWOT-Analyse" in gset:
            qs = [
                "Welche **einzige Stärke** zahlt am stärksten aufs Ziel ein – und wie hebeln wir sie?",
                "Welche **Schwäche** ist kurzfristig am **billigsten** zu entschärfen?",
                "Welche **Chance** können wir mit geringstem Aufwand testen?",
            ]
        elif "Interviewleitfaden" in gset:
            qs = [
                "Welche **Kerninformation** muss das Interview liefern, um **entscheidbar** zu werden?",
                "Welche **kritische Nachfrage** klärt das größte Rest-Risiko?",
                "Welche **Beispiele** machen die Aussagen **nachprüfbar**?",
            ]
        else:
            qs = [
                "Wenn du **30 Minuten** hättest: Welche 3 Schritte bringen dich am schnellsten voran (Reihenfolge)?",
                "Welchen **Entscheid** müsstest du heute treffen, um Momentum zu gewinnen?",
                "Welche **Hürde** blockiert aktuell am meisten – und was wäre ein **kleiner Test**, sie zu senken?",
            ]
    return qs

def prioritize_three(label: str, options: list[str]) -> list[str]:
    """Drei Prioritäten (Top1..Top3), ohne Duplikate."""
    if not options:
        st.info("Keine Deep Questions verfügbar.")
        return []
    # Default-Vorauswahl (falls leer):
    st.session_state.setdefault("dq_top1", options[0])
    st.session_state.setdefault("dq_top2", options[1 if len(options) > 1 else 0])
    st.session_state.setdefault("dq_top3", options[2 if len(options) > 2 else 0])

    # Top 1
    top1 = st.selectbox(f"{label} – Top 1", options, index=keep_or_default(st.session_state.get("dq_top1"), options), key="dq_top1")
    # Top 2: ohne Top1
    opts2 = [o for o in options if o != top1] or options
    top2_default = st.session_state.get("dq_top2")
    if top2_default == top1: top2_default = opts2[0]
    top2 = st.selectbox(f"{label} – Top 2", opts2, index=keep_or_default(top2_default, opts2), key="dq_top2")
    # Top 3: ohne Top1/Top2
    opts3 = [o for o in options if o not in (top1, top2)] or options
    top3_default = st.session_state.get("dq_top3")
    if top3_default in (top1, top2): top3_default = opts3[0]
    top3 = st.selectbox(f"{label} – Top 3", opts3, index=keep_or_default(top3_default, opts3), key="dq_top3")

    return [top1, top2, top3]

# =========================
# Sidebar
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
    st.subheader("🎯 Konversationsziele")
    # Beispiele je Modus — als Multiselect mit Freitext-Ergänzung
    mode_examples = GOAL_EXAMPLES.get(st.session_state.mode, [])
    conv_goals = multiselect_with_free_text(
        "Typische Ziele (Mehrfachauswahl)",
        mode_examples,
        state_key="conversation_goals",
        free_key="free_conv_goals",
        help="Wähle mehrere Ziele und/oder ergänze eigene."
    )
    st.session_state.conversation_goals = conv_goals

    st.caption("⚠️ Keine personenbezogenen oder internen Unternehmensdaten eingeben.")

    def _reset():
        for k, v in DEFAULTS.items(): st.session_state[k] = v
    st.button("🔄 Zurücksetzen", use_container_width=True, on_click=_reset)

# =========
# Layout
# =========
col_left, col_mid, col_right = st.columns([1.05, 1.6, 1.35], gap="large")

# =========================
# Linke Spalte (abhängige Menüs; Multiselect+Freitext)
# =========================
with col_left:
    st.subheader("🧩 Use-Case")
    # Use-Case bleibt Radio (Hauptschalter). Dropdown-Vorgabe bezog sich auf Selects → hier ok.
    st.radio("Was möchtest du tun?", list(UC_LABEL.keys()),
             index=keep_or_default(st.session_state.use_case, list(UC_LABEL.keys())),
             key="use_case", format_func=lambda v: UC_LABEL[v],
             help="Oberkategorie für den Prompt.")

    # Untertypen (Mehrfach + Freitext)
    base_subtypes = UC_SUBTYPES_BASE.get(st.session_state.use_case, [])
    subtypes = multiselect_with_free_text(
        "Untertypen (Mehrfachauswahl)",
        base_subtypes,
        state_key="sub_use_cases",
        free_key="free_subtypes",
        help="Feinere Auswahl passend zum Use-Case."
    )
    st.session_state.sub_use_cases = subtypes

    st.markdown("---")
    st.subheader("🎯 Ziel / Output (Mehrfach)")
    goal_options = GOALS_BY_UC.get(st.session_state.use_case, ["Freiform"])
    selected_goals = multiselect_with_free_text(
        "Ziele wählen",
        goal_options,
        state_key="goal",
        free_key="free_goals",
        help="Mehrere Zielarten kombinieren."
    )
    st.session_state.goal = selected_goals

    # Ziel-Untertypen aggregiert über alle gewählten Ziele
    aggregated_subtypes = aggregate_subtypes_for_goals(st.session_state.goal)
    selected_goal_subtypes = multiselect_with_free_text(
        "Ziel-Untertypen",
        aggregated_subtypes,
        state_key="goal_subtype",
        free_key="free_goal_subtypes",
        help="Feinvarianten zum Ziel (optional)."
    )
    st.session_state.goal_subtype = selected_goal_subtypes

    st.markdown("---")

    # Optionale Felder (Hintergrund nur bei Inhalt)
    if st.session_state.audience: st.markdown('<div class="optfield">', unsafe_allow_html=True)
    st.text_input("Zielgruppe (optional)", key="audience",
                  placeholder="z. B. Leitung, Team, Öffentlichkeit",
                  help="Für wen ist das Ergebnis gedacht?")
    if st.session_state.audience: st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.constraints: st.markdown('<div class="optfield">', unsafe_allow_html=True)
    st.text_area("Rahmen / Muss-Kriterien (optional)", key="constraints",
                 placeholder="Stichworte, Bullets …", height=70,
                 help="Voraussetzungen, Grenzen, Positivliste etc.")
    if st.session_state.constraints: st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("🎚️ Stil & Ton")
    if st.session_state.get("tone","sachlich") != "sachlich": st.markdown('<div class="optfield">', unsafe_allow_html=True)
    st.select_slider("Tonfall", options=["sehr sachlich","sachlich","neutral","lebendig","kreativ"],
                     value=st.session_state.get("tone","sachlich"), key="tone",
                     help="Stilistik der Antwort.")
    if st.session_state.get("tone","sachlich") != "sachlich": st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.get("rigor","klar") != "klar": st.markdown('<div class="optfield">', unsafe_allow_html=True)
    st.select_slider("Strenge/Struktur", options=["locker","mittel","klar","sehr klar"],
                     value=st.session_state.get("rigor","klar"), key="rigor",
                     help="Grad der Strukturierung.")
    if st.session_state.get("rigor","klar") != "klar": st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.persona: st.markdown('<div class="optfield">', unsafe_allow_html=True)
    st.text_input("Rolle (optional)", key="persona",
                  placeholder="z. B. Qualitätsauditor:in", help="Rolle/Persona der KI.")
    if st.session_state.persona: st.markdown('</div>', unsafe_allow_html=True)

# =========================
# Mitte (Kontext, Struktur, Qualität, Deep Questions)
# =========================
with col_mid:
    st.subheader("🖼️ Kontext")
    if st.session_state.context: st.markdown('<div class="optfield">', unsafe_allow_html=True)
    st.text_area("Kurzkontext (2–4 Bullets)", key="context",
                 placeholder="• Thema / Problem\n• Ziel & Medium\n• Rahmenbedingungen\n• Quellen/Lage",
                 height=120, help="Stichpunkte reichen.")
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
    st.subheader("🪄 Deep Questions (3 Vorschläge + Priorität)")
    dq_list = deep_questions(st.session_state.mode, st.session_state.goal)
    prioritized = prioritize_three("Beispielfragen", dq_list)
    # Anzeige der priorisierten Reihenfolge (informativ)
    if prioritized:
        st.caption("Priorisierte Fragen:")
        for i, q in enumerate(prioritized, 1):
            st.write(f"{i}. {q}")

# =========================
# Prompt-Erzeugung
# =========================
def build_prompt(include_iteration: bool = False) -> str:
    lang_hint = "deutsch" if st.session_state.lang == "de" else "englisch"
    today = datetime.now().strftime("%Y-%m-%d")
    of_hint = {
        "markdown": "Antworte in sauberem Markdown.",
        "text": "Antworte als Klartext ohne Markdown.",
        "json": "Antworte als valides JSON.",
        "table": "Antworte als Markdown-Tabelle."
    }[st.session_state.out_format]

    # Struktur
    structure_list = st.session_state.structure or []
    structure_lines = "\n".join(f"- {s}" for s in structure_list) if structure_list else "- (freie Struktur)"

    # Qualität
    qc_lines = []
    if st.session_state.qc_facts: qc_lines.append("• Prüfe Aussagen auf Plausibilität.")
    if st.session_state.qc_bias:  qc_lines.append("• Weisen auf mögliche Verzerrungen hin.")
    if st.session_state.qc_dp:    qc_lines.append("• Keine personenbezogenen Daten.")
    qc_block = "\n".join(qc_lines) if qc_lines else "• (keine Prüfhinweise)"

    # Sammelfelder
    use_case_label = UC_LABEL[st.session_state.use_case]
    sub_uc_line = f"Untertypen: {', '.join(st.session_state.sub_use_cases)}\n" if st.session_state.sub_use_cases else ""
    goals_line = f"Ziele/Outputs: {', '.join(st.session_state.goal)}\n" if st.session_state.goal else ""
    subgoals_line = f"Ziel-Untertypen: {', '.join(st.session_state.goal_subtype)}\n" if st.session_state.goal_subtype else ""
    conv_goals_line = f"Konversationsziele: {', '.join(st.session_state.conversation_goals)}\n" if st.session_state.conversation_goals else ""
    persona_line = f"Rolle: {st.session_state.persona}\n" if st.session_state.persona else ""
    audience_line = f"Zielgruppe: {st.session_state.audience}\n" if st.session_state.audience else ""
    constraints_line = f"Rahmen/Muss-Kriterien:\n{st.session_state.constraints.strip()}\n\n" if st.session_state.constraints.strip() else ""

    # Mode-Hinweis
    mode_line = {
        "praktisch": "Modus: PRAKTISCH – fokussiere auf konkrete Schritte, Klarheit, Entscheidbarkeit.",
        "emotional": "Modus: EMOTIONAL – berücksichtige Gefühle, Motivation, Bedenken.",
        "sozial":    "Modus: SOZIAL – berücksichtige Beziehungen, Rollen, Zugehörigkeit."
    }[st.session_state.mode]

    # Deep Questions (priorisiert)
    dq = [st.session_state.get("dq_top1"), st.session_state.get("dq_top2"), st.session_state.get("dq_top3")]
    dq = [x for x in dq if x]
    dq_block = "\n".join(f"{i+1}. {q}" for i, q in enumerate(dq)) if dq else "\n".join(f"{i+1}. {q}" for i, q in enumerate(deep_questions(st.session_state.mode, st.session_state.goal)))

    base_prompt = dedent(f"""
    {mode_line}
    Du bist ein Assistenzsystem für **{use_case_label}**.
    {sub_uc_line}{persona_line}{audience_line}{goals_line}{subgoals_line}{conv_goals_line}Sprache: {lang_hint}. Tonfall: {st.session_state.tone}. Struktur: {st.session_state.rigor}. Länge: {st.session_state.length}.
    {of_hint}

    Kontext:
    {st.session_state.context.strip() or "(kein Kontext)"}

    Struktur:
    {structure_lines}

    Deep Questions (priorisiert):
    {dq_block}

    {constraints_line}Qualität & Compliance:
    {qc_block}

    Liefere ein direkt nutzbares Ergebnis.
    Datum: {today}
    """).strip()

    return base_prompt

# =========================
# Rechte Spalte (Vorschau/Export)
# =========================
with col_right:
    st.subheader("👁️ Vorschau")
    prompt_text = build_prompt()
    auto_filename = f"prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    tabs = st.tabs(["🔤 Lesbare Version", "🧾 JSON"])
    with tabs[0]:
        st.code(prompt_text, language="markdown")
        st.download_button("⬇️ Als Markdown speichern",
                           data=prompt_text.encode("utf-8"),
                           file_name=f"{auto_filename}.md", mime="text/markdown")
    with tabs[1]:
        schema = {
            "protocol": "prompt.cockpit/1.2",
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
                "sub_use_cases": st.session_state.sub_use_cases,
                "goals": st.session_state.goal,
                "goal_subtypes": st.session_state.goal_subtype,
                "persona": st.session_state.persona or None,
                "audience": st.session_state.audience or None,
                "structure": st.session_state.structure,
                "qc": {
                    "facts": st.session_state.qc_facts,
                    "bias": st.session_state.qc_bias,
                    "data_protection": st.session_state.qc_dp
                },
                "conversation_goals": st.session_state.conversation_goals
            },
            "deep_questions": {
                "prioritized": [st.session_state.get("dq_top1"), st.session_state.get("dq_top2"), st.session_state.get("dq_top3")]
            },
            "context": st.session_state.context,
            "constraints": st.session_state.constraints,
            "prompt": prompt_text
        }
        st.json(schema, expanded=False)
        st.download_button("⬇️ JSON speichern",
                           data=json.dumps(schema, ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name=f"{auto_filename}.json", mime="application/json")

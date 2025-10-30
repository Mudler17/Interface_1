# app.py — Prompt-Plattform (Radikal vereinfacht)
from __future__ import annotations
import json
from datetime import datetime
from textwrap import dedent
from base64 import b64encode
import streamlit as st
from streamlit.components.v1 import html as components_html

st.set_page_config(page_title="🧭 Prompt-Plattform", page_icon="🧭", layout="wide")

# =========================
# (Minimal) Styles
# =========================
BASE_CSS = """
<style>
/* Hauptinhalt nach oben schieben */
.block-container {
    padding-top: 2rem; 
}
.copy-row { display:flex; gap:.5rem; align-items:center; margin:.25rem 0 .5rem 0; }
.copy-btn { padding:.35rem .6rem; border:1px solid #999; background:#fff; border-radius:.5rem; cursor:pointer; }
.copy-btn:hover { background:#f7f7f7; }

/* Styling für Inspirations-Fragen */
.dq-inspiration {
    padding: 0.75rem;
    border-radius: 0.5rem;
    background-color: #f0f2f6;
    margin-bottom: 0.5rem;
    border-left: 4px solid #007bff;
}
</style>
"""
st.markdown(BASE_CSS, unsafe_allow_html=True)

# =========================
# Defaults & Session-Init (STARK VEREINFACHT)
# =========================
DEFAULTS = {
    "lang": "de", "out_format": "markdown", "length": "mittel",
    "mode": "praktisch",
    "use_case": "analysieren",
    "goal": [],                      # Nur noch EIN Ziel-Feld
    "audience": "",
    "constraints": "",
    "tone": "sachlich",
    "persona": "",
    "core_prompt": "",               # Einziges Textfeld
    "structure": ["Einleitung mit Zielbild", "Nächste Schritte"],
    "qc_facts": False, "qc_bias": False, "qc_dp": False,
    "free_goals": "",
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

# =========================
# Dictionaries (STARK VEREINFACHT)
# =========================
UC_LABEL = {
    "schreiben": "🖋️ Schreiben",
    "analysieren": "📊 Analysieren",
    "lernen": "🧠 Lernen/Erklären",
    "coden": "💻 Coden",
    "kreativ": "🎨 Kreativideen",
    "sonstiges": "🧪 Sonstiges",
}
# Nur noch EINE Zielebene. 
# Sub-Use-Cases und Sub-Goals sind entfernt.
GOALS_BY_UC = {
    "analysieren": ["SWOT-Analyse", "Benchmark", "Risiko-Check", "Lessons Learned", "Ursache–Wirkung", "Wirkungsanalyse", "Prozessanalyse"],
    "schreiben":   ["Interviewleitfaden", "Konzeptskizze", "Checkliste", "Bericht/Protokoll", "Newsletter/Beitrag", "Rede/Laudatio", "Leitfaden"],
    "coden":       ["Code-Snippet", "Testfälle generieren", "Fehleranalyse (Bug Report)", "Refactoring-Vorschlag", "Dokumentation"],
    "lernen":      ["Einfach erklären", "Quiz", "Schritt-für-Schritt-Anleitung", "Glossar", "Fallbeispiel"],
    "kreativ":     ["Brainstorming-Liste", "Storyboard", "Titel/Claims", "Metaphern/Analogien", "Visualisierungsideen", "Prompt für Bildgenerator"],
    "sonstiges":   ["Freiform", "Systemische Reflexion"],
}
FORMAT_LABEL = {"markdown":"Markdown","text":"Reiner Text","json":"JSON","table":"Tabelle (MD)"}

# =========================
# Utility (Vereinfacht)
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
    else: base = []
    return [o for o in base if o in options]

def multiselect_with_free_text(label: str, options: list[str], state_key: str, free_key: str, help: str = ""):
    default_selected = _normalize_default_list(st.session_state.get(state_key), options)
    selected = st.multiselect(label, options, default=default_selected, key=state_key, help=help, placeholder="Wähle aus")
    free_val = st.text_input("+ " + label, key=free_key, placeholder="Eigenes hinzufügen … (kommagetrennt)", help="Eigene Einträge ergänzen (mit Enter bestätigen).")
    free_items = parse_free_list(free_val)
    combined = unique_merge(selected, free_items)
    return selected, free_items, combined

def _clear_dependent_fields():
    """Setzt abhängige Felder zurück, wenn der Use-Case wechselt."""
    st.session_state.goal = DEFAULTS["goal"]
    st.session_state.free_goals = DEFAULTS["free_goals"]

# =========================
# Deep Questions (STARK VEREINFACHT)
# Keine Priorisierung, nur Inspiration
# =========================
def get_deep_questions(mode: str, goals: list[str]) -> list[str]:
    gset = set(goals or [])
    qs = []
    if mode == "emotional":
        qs = ["Welche **Sorgen oder Hoffnungen** sind hier für dich am wichtigsten?", "Was würde dir **Zuversicht** geben, den nächsten Schritt zu gehen?", "Wann hast du das zuletzt besonders **stark gefühlt** – und was hat es ausgelöst?"]
    elif mode == "sozial":
        qs = ["Wessen **Perspektive** fehlt aktuell – und wie würde sie die Lage verändern?", "Welche **Rollen oder Erwartungen** prägen das Verhalten der Beteiligten?", "Welche **gemeinsamen Werte** könnten hier Orientierung geben?"]
    else:  # praktisch
        if "Risiko-Check" in gset: qs = ["Welche **Frühindikatoren** signalisieren dir, dass das Risiko steigt?", "Wenn du nur **eine Gegenmaßnahme** umsetzen dürftest: Welche – und warum?", "Welche **Grenzwerte** lösen eine **Sofortmaßnahme** aus?"]
        elif "SWOT-Analyse" in gset: qs = ["Welche **einzige Stärke** zahlt am stärksten aufs Ziel ein?", "Welche **Schwäche** ist kurzfristig am **billigsten** zu entschärfen?", "Welche **Chance** können wir mit geringstem Aufwand testen?"]
        else: qs = ["Welche **Hürde** blockiert aktuell am meisten?", "Welchen **Entscheid** müsstest du heute treffen, um Momentum zu gewinnen?", "Wenn du **30 Minuten** hättest: Welche 3 Schritte bringen dich am schnellsten voran?"]
    return qs

# =========================
# Prompt-Erzeugung (Angepasst)
# =========================
def build_prompt() -> str:
    lang_hint = "deutsch" if st.session_state.lang == "de" else "englisch"
    today = datetime.now().strftime("%Y-%m-%d")
    of_hint = FORMAT_LABEL.get(st.session_state.out_format, st.session_state.out_format)

    goals_combined = st.session_state.get("goals_combined", st.session_state.goal)

    structure_list = st.session_state.structure or []
    structure_lines = "\n".join(f"- {s}" for s in structure_list) if structure_list else "- (freie Struktur)"

    qc_lines = []
    if st.session_state.qc_facts: qc_lines.append("• Prüfe Aussagen auf Plausibilität.")
    if st.session_state.qc_bias:  qc_lines.append("• Weisen auf mögliche Verzerrungen hin.")
    if st.session_state.qc_dp:    qc_lines.append("• Keine personenbezogenen Daten.")
    qc_block = "\n".join(qc_lines) if qc_lines else "• (keine Prüfhinweise)"

    use_case_label = UC_LABEL[st.session_state.use_case]
    goals_line = f"Ziele/Outputs: {', '.join(goals_combined)}\n" if goals_combined else ""
    persona_line = f"Rolle: {st.session_state.persona}\n" if st.session_state.persona else ""
    audience_line = f"Zielgruppe: {st.session_state.audience}\n" if st.session_state.audience else ""
    constraints_line = f"Rahmen/Muss-Kriterien:\n{st.session_state.constraints.strip()}\n\n" if st.session_state.constraints.strip() else ""

    mode_line = {
        "praktisch": "Modus: PRAKTISCH – fokussiere auf konkrete Schritte, Klarheit, Entscheidbarkeit.",
        "emotional": "Modus: EMOTIONAL – berücksichtige Gefühle, Motivation, Bedenken.",
        "sozial":    "Modus: SOZIAL – berücksichtige Beziehungen, Rollen, Zugehörigkeit."
    }[st.session_state.mode]
    
    # Deep Questions werden NICHT mehr in den Prompt injiziert,
    # sie dienen nur noch der Inspiration beim Schreiben des Anliegens.
    # dq_block = "" 

    base_prompt = dedent(f"""
    {mode_line}
    Du bist ein Assistenzsystem für **{use_case_label}**.

    Anliegen, Kontext & Kernprompt:
    {st.session_state.core_prompt.strip() or "(kein Anliegen angegeben)"}

    {persona_line}{audience_line}{goals_line}Sprache: {lang_hint}. Tonfall: {st.session_state.tone}. Länge: {st.session_state.length}.
    Output-Format: {of_hint}.

    Struktur-Vorgabe:
    {structure_lines}

    {constraints_line}Qualität & Compliance:
    {qc_block}

    Liefere ein direkt nutzbares Ergebnis.
    Datum: {today}
    """).strip()
    return base_prompt

# ---------- Copy-to-clipboard helper ----------
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
          <button class="copy-btn" onclick="{js_click.replace('"', '&quot;')}" key="btn_{key}">{label}</button>
          <span>In Zwischenablage kopieren</span>
        </div>
        """,
        height=40,
    )

# =========================
# ===== NEUES LAYOUT ======
# =========================

col_config, col_output = st.columns([1.5, 1], gap="large")

# =========================
# EINGABE-SPALTE (links)
# =========================
with col_config:
    st.markdown("## 1. Was ist dein Anliegen?")
    st.text_area(
        "Formuliere dein zentrales Anliegen, den Kontext und was du erreichen willst.",
        key="core_prompt",
        placeholder="z.B. Ich brauche eine Zusammenfassung des internen Projekt-Updates (siehe Text unten) für das Management-Board. Sie soll kurz sein und die drei Hauptrisiken klar benennen.",
        height=200,
        label_visibility="collapsed"
    )
    
    st.markdown("## 2. Was ist das Haupt-Ziel?")
    c1, c2 = st.columns(2)
    with c1:
        st.selectbox(
            "Use-Case", 
            list(UC_LABEL.keys()),
            index=keep_or_default(st.session_state.use_case, list(UC_LABEL.keys())),
            key="use_case", 
            format_func=lambda v: UC_LABEL[v],
            help="Oberkategorie für den Prompt.",
            on_change=_clear_dependent_fields
        )
    with c2:
        goal_options = GOALS_BY_UC.get(st.session_state.use_case, ["Freiform"])
        _sel_goals, _free_goals, goals_combined = multiselect_with_free_text(
            "Konkrete Aufgabe(n)",
            goal_options,
            state_key="goal",
            free_key="free_goals",
            help="Wähle eine oder mehrere spezifische Aufgaben."
        )
        st.session_state["goals_combined"] = goals_combined

    st.markdown("## 3. Optionale Details")

    # --- Expander 1: Details ---
    with st.expander("⚙️ Details: Stil, Struktur & Format"):
        st.subheader("🗣️ Gesprächsmodus")
        st.radio("Modus (Duhigg)", options=["praktisch","emotional","sozial"],
                 index=keep_or_default(st.session_state.mode, ["praktisch","emotional","sozial"]),
                 key="mode",
                 format_func=lambda m: {"praktisch":"🔧 Praktisch","emotional":"💚 Emotional","sozial":"🧩 Sozial"}[m],
                 help="Fokus: Handlung (praktisch), Gefühle (emotional) oder Zugehörigkeit/Rollen (sozial).",
                 horizontal=True)

        st.subheader("🎚️ Stil & Ton")
        c1, c2 = st.columns(2)
        with c1:
            st.select_slider("Tonfall", options=["sehr sachlich","sachlich","neutral","lebendig","kreativ"],
                             value=st.session_state.get("tone","sachlich"), key="tone")
            st.text_input("Rolle (optional)", key="persona", placeholder="z. B. Qualitätsauditor:in")
        with c2:
            st.select_slider("Länge", options=["ultrakurz","kurz","mittel","lang","sehr lang"],
                             value=st.session_state.length, key="length")
            st.text_input("Zielgruppe (optional)", key="audience", placeholder="z. B. Leitung, Team")

        st.subheader("📋 Format & Struktur")
        c1, c2 = st.columns(2)
        with c1:
             st.selectbox("Output-Format", list(FORMAT_LABEL.keys()),
                 index=keep_or_default(st.session_state.out_format, list(FORMAT_LABEL.keys())),
                 key="out_format", format_func=lambda x: FORMAT_LABEL[x])
             st.radio("Sprache", ["de","en"],
                 index=keep_or_default(st.session_state.lang, ["de","en"]),
                 key="lang", format_func=lambda x: "Deutsch" if x=="de" else "Englisch", horizontal=True)
        with c2:
            st.multiselect("Bausteine auswählen",
                 ["Einleitung mit Zielbild","Vorgehensschritte","Analyse","Beispiele",
                  "Qualitäts-Check","Nächste Schritte","Quellen"],
                 default=st.session_state.structure, key="structure", placeholder="Wähle aus")

        st.subheader("🔒 Qualität & Kriterien")
        st.text_area("Rahmen / Muss-Kriterien (optional)", key="constraints",
                     placeholder="Stichworte, Bullets …\n• Maximal 300 Wörter\n• Muss 'Projekt X' erwähnen", height=100,
                     help="Voraussetzungen, Grenzen, Positivliste etc.")
        
        c1, c2, c3 = st.columns(3)
        with c1: st.checkbox("Faktencheck", key="qc_facts", help="Unsichere Stellen markieren.")
        with c2: st.checkbox("Bias-Check", key="qc_bias", help="Auf mögliche Verzerrungen hinweisen.")
        with c3: st.checkbox("Datenschutz-Hinweis", key="qc_dp", help="Keinerlei personenbezogene Daten verarbeiten.")

    # --- Expander 2: Inspiration ---
    with st.expander("💡 Inspiration (Deep Questions)"):
        st.info("Nutze diese Fragen, um dein Anliegen oben (in Feld 1) zu schärfen. Sie werden nicht direkt in den Prompt eingefügt.")
        
        dq_list = get_deep_questions(st.session_state.mode, st.session_state.get("goals_combined", []))
        
        for q in dq_list:
            st.markdown(f'<div class="dq-inspiration">{q}</div>', unsafe_allow_html=True)
            
    # --- Reset Button ---
    def _reset():
        for k, v in DEFAULTS.items(): st.session_state[k] = v
        st.session_state["goals_combined"] = []
            
    st.button("🔄 Alle Eingaben zurücksetzen", use_container_width=True, on_click=_reset, type="secondary")


# =========================
# VORSCHAU-SPALTE (rechts)
# =========================
with col_output:
    st.subheader("👁️ Prompt-Vorschau")
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
            "protocol": "prompt.cockpit/2.0_simple", # Version 2.0
            "meta": {
                "created": datetime.now().isoformat(timespec="seconds"),
                "language": st.session_state.lang,
                "format": st.session_state.out_format,
                "length": st.session_state.length,
                "mode": st.session_state.mode,
            },
            "profile": {
                "use_case": st.session_state.use_case,
                "use_case_label": UC_LABEL[st.session_state.use_case],
                "goals": st.session_state.get("goals_combined", st.session_state.goal),
                "persona": st.session_state.persona or None,
                "audience": st.session_state.audience or None,
                "structure": st.session_state.structure,
                "qc": {
                    "facts": st.session_state.qc_facts,
                    "bias": st.session_state.qc_bias,
                    "data_protection": st.session_state.qc_dp
                },
            },
            "core_prompt": st.session_state.core_prompt,
            "constraints": st.session_state.constraints,
            "rendered_prompt": prompt_text
        }
        json_text = json.dumps(schema, ensure_ascii=False, indent=2)
        st.json(schema, expanded=False)
        render_copy_button(json_text, key="copy_json", label="📋 JSON kopieren")
        st.download_button("⬇️ JSON speichern",
                           data=json_text.encode("utf-8"),
                           file_name=f"{auto_filename}.json", mime="application/json")

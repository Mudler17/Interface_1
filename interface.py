# app.py
# Prompt-Plattform · Mockup (Use-Case · Ziel/Output · Stil & Ton)
# Fix: st.radio statt st.select_radio + Untermenüs je Use-Case
# Features: Live-Vorschau, JSON-Schema, Copy-Button, Download als .md/.json

from __future__ import annotations
import json
import re
from datetime import datetime
from textwrap import dedent

import streamlit as st

# ------------------------- Seiteneinstellungen -------------------------
st.set_page_config(
    page_title="🧭 Prompt-Plattform · Cockpit",
    page_icon="🧭",
    layout="wide",
    menu_items={
        "Get Help": "https://docs.streamlit.io",
        "Report a bug": "https://github.com",
        "About": "Prompt-Plattform · Minimal-Mockup (Streamlit)",
    },
)

# ------------------------- Styles (leicht & barrierearm) -------------------------
CUSTOM_CSS = """
<style>
.notice {
  position: sticky; top: 0; z-index: 999;
  background: #fff3cd; color: #7a5b00;
  border: 1px solid #ffe69c; border-radius: 10px;
  padding: .6rem .9rem; margin-bottom: .5rem;
  font-size: .95rem;
}
.block-card {
  border: 1px solid #eaeaea; border-radius: 14px; padding: 1rem;
  box-shadow: 0 1px 12px rgba(0,0,0,.03);
  background: #ffffffaa;
}
.small-hint { color:#666; font-size:.9rem; }
.stTabs [data-baseweb="tab"] { font-size: 0.95rem; }
.kbd {
  display:inline-block; padding:.1rem .35rem; border:1px solid #ddd; border-bottom-width:2px;
  border-radius:.35rem; background:#f8f8f8; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  font-size:.85rem;
}
.codebox {
  border:1px solid #eee; border-radius:12px; padding:.6rem .8rem; background:#fafafa;
}
.copy-btn {
  display:inline-block; padding:.45rem .7rem; border-radius:10px; border:1px solid #e6e6e6; background:#fff;
  cursor:pointer; font-weight:600; font-size:.92rem;
}
.copy-btn:hover { background:#f6f6f6; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ------------------------- Warnhinweis (dauerhaft) -------------------------
st.markdown(
    '<div class="notice">⚠️ Grundsatz: Keine personenbezogenen oder internen Unternehmensdaten eingeben. '
    'Beachte Urheberrecht & Vertraulichkeit. Dieses Tool erzeugt nur Prompts.</div>',
    unsafe_allow_html=True
)

# ------------------------- Sidebar (Navigation) -------------------------
with st.sidebar:
    st.header("🧭 Navigation")
    st.caption("Kernbausteine für den Start (erweiterbar).")
    st.markdown("**1. Use-Case**\n\n**2. Ziel/Output**\n\n**3. Stil & Ton**")
    st.divider()
    st.subheader("🎛️ Voreinstellungen")
    lang = st.radio("Sprache", ["Deutsch", "Englisch"], horizontal=True, index=0)
    form = st.selectbox("Output-Format", ["Markdown", "Reiner Text", "JSON-Antwort", "Tabelle (Markdown)"], index=0)
    length = st.select_slider("Länge", options=["ultrakurz", "kurz", "mittel", "lang", "sehr lang"], value="mittel")
    st.caption("Diese Voreinstellungen fließen in den Prompt ein.")
    st.divider()
    st.subheader("📁 Exporte")
    filename_base = st.text_input("Dateiname (ohne Endung)", value="prompt_cockpit")
    st.caption("Downloads erscheinen unter der Vorschau.")

# ------------------------- Hauptlayout -------------------------
col_left, col_mid, col_right = st.columns([1.05, 1.6, 1.35], gap="large")

def strip_leading_emoji(label: str) -> str:
    # robust: trennt am ersten Leerzeichen; "🖋️ Schreiben" -> "Schreiben"
    return label.split(" ", 1)[-1] if " " in label else label

# ------------------------- Linke Spalte: Menüs -------------------------
with col_left:
    st.subheader("🧩 Use-Case")
    use_case = st.radio(
        "Was möchtest du tun?",
        options=[
            "🖋️ Schreiben",
            "📊 Analysieren",
            "🧠 Lernen/Erklären",
            "💻 Coden",
            "🎨 Kreativideen",
            "🧪 Sonstiges"
        ],
        index=1,
    )

    # kontextsensitive Untermenüs je Use-Case
    uc_clean = strip_leading_emoji(use_case)
    sub_use_case = None
    if uc_clean == "Analysieren":
        sub_use_case = st.selectbox(
            "Analyse-Typ",
            ["Textanalyse", "SWOT", "Ursache–Wirkung (Fishbone)", "Vergleich/Benchmark", "Risiko-Check"],
            index=0
        )
    elif uc_clean == "Schreiben":
        sub_use_case = st.selectbox(
            "Schreib-Typ",
            ["Zusammenfassung", "Brief/E-Mail", "Bericht/Protokoll", "Konzeptskizze", "Presse/News"],
            index=0
        )
    elif uc_clean == "Coden":
        sub_use_case = st.selectbox(
            "Code-Aufgabe",
            ["Snippet erklären", "Bug finden", "Refactoring", "Tests generieren", "Skelett erstellen"],
            index=0
        )
    elif uc_clean == "Lernen/Erklären":
        sub_use_case = st.selectbox(
            "Lern-/Erklär-Typ",
            ["Einfach erklären", "Glossar", "Lernziele + Quiz", "Schritt-für-Schritt-Anleitung"],
            index=0
        )
    elif uc_clean == "Kreativideen":
        sub_use_case = st.selectbox(
            "Kreativ-Typ",
            ["Brainstorming", "Metaphern finden", "Storyboard/Outline", "Titel/Claims"],
            index=0
        )

    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.subheader("🎯 Ziel / Output")
    goal = st.selectbox(
        "Zieltyp",
        [
            "Zusammenfassung",
            "Strukturierte Analyse",
            "Interviewleitfaden",
            "Checkliste",
            "Konzeptskizze",
            "Code-Snippet",
            "Brainstorming-Liste",
            "Freiform"
        ],
        index=1
    )
    audience = st.text_input("Zielgruppe (optional)", placeholder="z. B. Leitung, Team, Öffentlichkeit")
    constraints = st.text_area("Rahmen / Muss-Kriterien (optional)", height=70, placeholder="Stichworte, Bullets, Vorgaben …")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="block-card">', unsafe_allow_html=True)
    st.subheader("🎚️ Stil & Ton")
    tone = st.select_slider("Tonfall", options=["sehr sachlich", "sachlich", "neutral", "lebendig", "kreativ"], value="sachlich")
    rigor = st.select_slider("Strenge/Struktur", options=["locker", "mittel", "klar", "sehr klar"], value="klar")
    persona = st.text_input("Rolle (optional)", placeholder="z. B. Qualitätsauditor:in, Moderator:in, Entwickler:in")
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------- Mitte: Kontext & Promptbausteine -------------------------
with col_mid:
    st.subheader("🖼️ Kontext")
    context = st.text_area(
        "Kurzkontext in 2–4 Stichpunkten",
        placeholder="• Thema / Problem\n• Ziel & Medium\n• Rahmenbedingungen\n• Quellen/Lage",
        height=120
    )

    st.subheader("🧱 Struktur (optional)")
    structure = st.multiselect(
        "Bausteine auswählen",
        [
            "Einleitung mit Zielbild",
            "Vorgehensschritte",
            "Analyse (z. B. SWOT / Ursachen-Wirkung)",
            "Beispiele / Templates",
            "Qualitäts-/Risiko-Check",
            "Nächste Schritte / To-dos",
            "Quellen/Annahmen"
        ],
        default=["Einleitung mit Zielbild", "Nächste Schritte / To-dos"]
    )

    st.subheader("🔒 Qualitäts/Compliance (optional)")
    qc_facts = st.checkbox("Faktencheck erwünscht")
    qc_bias = st.checkbox("Bias-Check/Hinweise auf Unsicherheiten")
    qc_dp = st.checkbox("Datenschutz-Hinweis einfügen")

# ------------------------- Prompt-Generator -------------------------
def build_prompt() -> str:
    lang_hint = "deutsch" if lang == "Deutsch" else "englisch"
    use_case_clean = strip_leading_emoji(use_case)
    sub_uc_line = f"Untertyp: {sub_use_case}\n" if sub_use_case else ""
    today = datetime.now().strftime("%Y-%m-%d")

    structure_lines = "\n".join([f"- {s}" for s in structure]) if structure else "- (freie Struktur)"

    qc_lines = []
    if qc_facts: qc_lines.append("• Prüfe Aussagen auf Plausibilität und kennzeichne unsichere Stellen.")
    if qc_bias:  qc_lines.append("• Weisen auf mögliche Verzerrungen/Bias hin.")
    if qc_dp:    qc_lines.append("• Keine personenbezogenen oder internen Daten verarbeiten.")
    qc_block = "\n".join(qc_lines)

    persona_line = f"Rolle: {persona}\n" if persona else ""
    audience_line = f"Zielgruppe: {audience}\n" if audience else ""
    constraints_line = f"Rahmen/Muss-Kriterien:\n{constraints.strip()}\n\n" if constraints.strip() else ""

    of_hint = {
        "Markdown": "Antworte in sauberem Markdown.",
        "Reiner Text": "Antworte als Klartext ohne Markdown.",
        "JSON-Antwort": "Antworte als valides JSON-Objekt mit klaren Schlüsseln.",
        "Tabelle (Markdown)": "Antworte als Markdown-Tabelle mit sprechenden Spalten."
    }[form]

    prompt = dedent(f"""
    Du bist ein Assistenzsystem für **{use_case_clean}**.
    {sub_uc_line}{persona_line}{audience_line}Sprache: {lang_hint}. Tonfall: {tone}. Struktur: {rigor}. Länge: {length}.
    Ziel/Output: **{goal}**.
    {of_hint}

    Kontext (Stichpunkte):
    {context.strip() or "(kein zusätzlicher Kontext)"}

    Strukturbausteine (wenn sinnvoll):
    {structure_lines}

    {constraints_line}Qualität & Compliance:
    {qc_block or "• (keine zusätzlichen Prüfhinweise)"}

    Liefere ein Ergebnis, das direkt nutzbar ist. Erkläre nur, wo es dem Verständnis dient.
    Datum: {today}
    """).strip()

    return prompt

def build_json_schema(prompt_text: str) -> dict:
    return {
        "protocol": "prompt.cockpit/1.0",
        "meta": {
            "created": datetime.now().isoformat(timespec="seconds"),
            "language": "de" if lang == "Deutsch" else "en",
            "length": length,
            "format": form,
        },
        "profile": {
            "use_case": strip_leading_emoji(use_case),
            "sub_use_case": sub_use_case,
            "goal": goal,
            "tone": tone,
            "rigor": rigor,
            "persona": persona or None,
            "audience": audience or None,
            "structure": structure,
            "qc": {
                "facts": qc_facts,
                "bias": qc_bias,
                "data_protection": qc_dp
            }
        },
        "context": context,
        "constraints": constraints,
        "prompt": prompt_text
    }

# ------------------------- Rechte Spalte: Vorschau & Export -------------------------
with col_right:
    st.subheader("👁️ Live-Vorschau")
    prompt_text = build_prompt()
    tabs = st.tabs(["🔤 Lesbare Version", "🧾 JSON-Schema"])

    with tabs[0]:
        st.markdown("**Finaler Prompt (Render-Ansicht)**")
        st.markdown(f"<div class='codebox'>{prompt_text.replace('\n','<br>')}</div>", unsafe_allow_html=True)

        # Copy-Button (clientseitig)
        st.markdown(
            f"""
            <button class="copy-btn" onclick="navigator.clipboard.writeText(`{json.dumps(prompt_text)[1:-1]}`);">
              In Zwischenablage kopieren
            </button>
            """,
            unsafe_allow_html=True
        )

        # Download als Markdown
        md_bytes = prompt_text.encode("utf-8")
        st.download_button(
            label="⬇️ Als Markdown speichern",
            data=md_bytes,
            file_name=f"{filename_base or 'prompt_cockpit'}.md",
            mime="text/markdown"
        )

    with tabs[1]:
        schema = build_json_schema(prompt_text)
        st.json(schema, expanded=False)
        # Download als JSON
        json_bytes = json.dumps(schema, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            label="⬇️ JSON-Schema speichern",
            data=json_bytes,
            file_name=f"{filename_base or 'prompt_cockpit'}.json",
            mime="application/json"
        )

# ------------------------- Footer-Aktionen -------------------------
st.divider()
colA, colB, colC, colD = st.columns([1.0, 1.0, 1.0, 3.0])

with colA:
    if st.button("🔁 Überarbeiten (neue Variante)"):
        st.toast("Parameter anpassen und Prompt wird live aktualisiert.", icon="✍️")

with colB:
    if st.button("✨ Erzeugen (nur Vorschau)"):
        st.toast("Vorschau aktualisiert. Export oben rechts.", icon="✨")

with colC:
    if st.button("🧱 Als Template-Idee merken"):
        st.toast("In echter App: in Bibliothek speichern (DB/JSON).", icon="📚")

with colD:
    st.caption("→ API-Hook zu CustomGPT/Assistants kann hier eingehängt werden (POST an Endpoint, Bearer-Token).")

# ------------------------- Hinweise zur Integration -------------------------
with st.expander("⚙️ Integration zu CustomGPT/Assistants – Platzhalter (How-To)"):
    st.markdown(dedent("""
    **Option A – OpenAI Assistants API (Serverseitig):**
    - Sende `schema["prompt"]` als User-Nachricht an einen vordefinierten Assistant/Thread.
    - Bewahre Metadaten aus `schema["meta"]` im Run mit auf (z. B. als `metadata`).

    **Option B – Webhook eines CustomGPT:**
    - Richte einen HTTP-Endpoint ein, der den Prompt entgegennimmt.
    - Verwende Bearer-Token/Key im Header.
    - Antworte mit Lauf-ID o. Ä., um Ergebnis später abzuholen.

    **Option C – „Prompt-Paste“:**
    - Nur Copy/Download (bereits umgesetzt). Ergebnis manuell in GPT einfügen.

    **Sicherheit/Compliance:**
    - Kein Logging sensibler Inhalte.
    - Optional: Positivliste der erlaubten Use-Cases.
    - Optional: DSGVO-Hinweise im Prompt erzwingen (aktivierbar über Checkbox).
    """).strip())

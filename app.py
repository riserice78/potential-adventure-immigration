"""
Citizen's Charter Assistant — Streamlit UI
==========================================
Guided 3-step flow:
  Step 1 — User describes what they need (free text)
  Step 2 — Agent returns 2–5 matching transactions; user picks one
  Step 3 — Agent shows full requirements for the chosen transaction
           ↳ If a "Letter Request to the Commissioner" is required,
             an expander lets the user fill in details and draft the letter.

Run with:
    streamlit run app.py

Build the index first (run once):
    python scripts/build_index.py --pdf citizenscharters/BureauOfImmigration_4thEdition.pdf
"""

import json
import re
import textwrap
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from translations import LANG_OPTIONS, t

load_dotenv()

INDEX_PATH = Path(__file__).parent / "transactions_index.json"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _short_edition_label(charter_name: str) -> str:
    """Return a compact badge label for a full charter name."""
    lower = charter_name.lower()
    if "2025" in lower:
        return "📘 2025 Ed."
    if "4th" in lower:
        return "📗 4th Ed."
    if "3rd" in lower:
        return "📙 3rd Ed."
    if "2nd" in lower:
        return "📕 2nd Ed."
    if "1st" in lower:
        return "📒 1st Ed."
    return f"📄 {charter_name}"


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Citizen's Charter Assistant",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
        /* Widen the centered content area slightly */
        .block-container { max-width: 820px; padding-top: 2rem; }

        /* Candidate cards */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 10px !important;
        }

        /* Step badge */
        .step-badge {
            display: inline-block;
            background: #e8f0fe;
            color: #1a56db;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            margin-bottom: 0.5rem;
        }

        /* ── Requirements output (Step 3) ─────────────────────── */

        /* Transaction title (## heading) */
        [data-testid="stMarkdownContainer"] h2 {
            font-size: 1.35rem;
            font-weight: 700;
            color: #1e3a5f;
            margin-top: 0.25rem;
            margin-bottom: 0.15rem;
        }

        /* Section headers (### ⚡ Quick Look, ### 📋 What You Need…) */
        [data-testid="stMarkdownContainer"] h3 {
            font-size: 1rem;
            font-weight: 700;
            color: #1a56db;
            background: #f0f4ff;
            border-left: 4px solid #1a56db;
            padding: 0.45rem 0.85rem;
            border-radius: 0 8px 8px 0;
            margin-top: 1.6rem;
            margin-bottom: 0.7rem;
        }

        /* Quick Look summary table */
        [data-testid="stMarkdownContainer"] table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.92rem;
            margin: 0.4rem 0 1rem;
            border-radius: 8px;
            overflow: hidden;
        }
        [data-testid="stMarkdownContainer"] th {
            display: none;   /* hide empty header row from | | | table */
        }
        [data-testid="stMarkdownContainer"] td {
            padding: 0.55rem 0.85rem;
            border: 1px solid #e5e7eb;
            vertical-align: top;
        }
        [data-testid="stMarkdownContainer"] td:first-child {
            white-space: nowrap;
            font-weight: 600;
            background: #f8faff;
            width: 38%;
            color: #374151;
        }
        [data-testid="stMarkdownContainer"] tr:last-child td {
            border-bottom: 1px solid #e5e7eb;
        }

        /* Ordered + unordered lists */
        [data-testid="stMarkdownContainer"] ul,
        [data-testid="stMarkdownContainer"] ol {
            padding-left: 1.3rem;
            line-height: 1.75;
        }
        [data-testid="stMarkdownContainer"] li {
            margin-bottom: 0.3rem;
        }

        /* Horizontal rule — section separator */
        [data-testid="stMarkdownContainer"] hr {
            border: none;
            border-top: 1px solid #e5e7eb;
            margin: 1.1rem 0;
        }

        /* Italic intro line under the title */
        [data-testid="stMarkdownContainer"] h2 + p em {
            color: #4b5563;
            font-size: 0.97rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def step_badge(text: str) -> None:
    st.markdown(f'<p class="step-badge">{text}</p>', unsafe_allow_html=True)


def reset_state() -> None:
    """Return to step 1 and clear all transient state."""
    for key in ("step", "user_query", "candidates", "selected_txn",
                "drafted_letter", "letter_for_txn"):
        st.session_state.pop(key, None)


# ── Index loading ─────────────────────────────────────────────────────────────


@st.cache_data(show_spinner=False)
def load_index(_mtime: float = 0) -> dict | None:
    """Load the combined transactions index. Cache key includes file mtime so
    it auto-invalidates whenever merge_indexes.py regenerates the file."""
    if not INDEX_PATH.exists():
        return None
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── CrewAI calls (cached per unique input) ────────────────────────────────────


def _parse_json_candidates(raw: str) -> list[dict]:
    """
    Robustly extract a JSON array from the matcher agent's output.
    Tries three strategies: direct parse → strip code fences → regex extract.
    """
    text = raw.strip()

    # 1. Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown code fences
    fenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE)
    try:
        return json.loads(fenced.strip())
    except json.JSONDecodeError:
        pass

    # 3. Extract the first [...] block
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return []


@st.cache_data(show_spinner=False)
def fetch_candidates(query: str, language: str = "English") -> list[dict]:
    """
    Run MatcherCrew to identify 2–5 candidate transactions.
    Cached by (query, language) — same combo never triggers a second crew run.
    """
    from crew import MatcherCrew

    result = MatcherCrew().crew().kickoff(
        inputs={"query": query, "language": language}
    )
    return _parse_json_candidates(str(result.raw))


@st.cache_data(show_spinner=False)
def fetch_requirements(transaction_id: int, transaction_name: str,
                       _tasks_mtime: float = 0,
                       language: str = "English") -> str:
    """
    Run CharterCrew to get formatted requirements for one transaction.
    Cached by (id, name, language) — clicking the same transaction again is instant.
    """
    from crew import CharterCrew

    result = CharterCrew().crew().kickoff(
        inputs={"transaction": transaction_name, "language": language}
    )
    return str(result.raw)


@st.cache_data(show_spinner=False)
def fetch_visa_info(visa_type: str, language: str = "English") -> str:
    """
    Run VisaInfoCrew to produce a comprehensive guide for one visa type.
    Cached by (visa_type, language).
    """
    from crew import VisaInfoCrew

    result = VisaInfoCrew().crew().kickoff(
        inputs={"visa_type": visa_type, "language": language}
    )
    return str(result.raw)


@st.cache_data(show_spinner=False)
def fetch_visa_recommendation(
    nationality: str,
    purpose: str,
    duration: str,
    has_filipino_family: str,
    employment: str,
    retirement: str,
    extra_details: str,
    language: str = "English",
) -> str:
    """
    Run VisaRecommendationCrew with the user's situation details.
    Cached by the full input tuple so changing any answer triggers a fresh run.
    """
    from crew import VisaRecommendationCrew

    result = VisaRecommendationCrew().crew().kickoff(
        inputs={
            "nationality":         nationality,
            "purpose":             purpose,
            "duration":            duration,
            "has_filipino_family": has_filipino_family,
            "employment":          employment,
            "retirement":          retirement,
            "extra_details":       extra_details,
            "language":            language,
        }
    )
    return str(result.raw)


@st.cache_data(show_spinner=False)
def fetch_letter_draft(
    transaction_name: str,
    applicant_name: str,
    nationality: str,
    passport_number: str,
    address: str,
    purpose: str,
    email: str,
    contact_number: str,
    petitioner_name: str
) -> str:
    """
    Run LetterDraftingCrew to compose a formal letter to the Commissioner.
    Cached — identical inputs return the stored letter instantly.
    """
    from crew import LetterDraftingCrew

    result = LetterDraftingCrew().crew().kickoff(
        inputs={
            "transaction":     transaction_name,
            "applicant_name":  applicant_name,
            "nationality":     nationality,
            "passport_number": passport_number or "N/A",
            "address":         address or "N/A",
            "purpose":         purpose or "Not specified",
            "date":            datetime.now().strftime("%B %d, %Y"),
            "email":           email,
            "contact_number":  contact_number or "N/A",
            "petitioner_name":  petitioner_name,
        }
    )
    return str(result.raw)


# ── Letter helpers ────────────────────────────────────────────────────────────

_LETTER_PHRASES = [
    "letter request",
    "letter addressed to the commissioner",
    "letter to the commissioner",
    "request letter addressed",
]


def requires_letter(requirements_text: str) -> bool:
    """Return True if the requirements mention a letter to the Commissioner."""
    lower = requirements_text.lower()
    return any(phrase in lower for phrase in _LETTER_PHRASES)


# ── Sidebar ───────────────────────────────────────────────────────────────────


def _lang_full() -> str:
    """Return the full language name (e.g. 'English') for the current session."""
    code = st.session_state.get("language", "en")
    return {"en": "English", "ja": "Japanese", "tl": "Filipino (Tagalog)"}.get(code, "English")


def render_sidebar(index: dict) -> None:
    meta = index.get("metadata", {})
    with st.sidebar:
        # ── Language selector (first so it's prominent) ──────────────────
        st.markdown(t("sidebar_language"))
        lang_codes = list(LANG_OPTIONS.keys())
        lang_labels = list(LANG_OPTIONS.values())
        current_idx = lang_codes.index(st.session_state.get("language", "en"))
        chosen = st.selectbox(
            "Language",
            lang_labels,
            index=current_idx,
            key="language_selector",
            label_visibility="collapsed",
        )
        new_code = lang_codes[lang_labels.index(chosen)]
        if new_code != st.session_state.get("language", "en"):
            st.session_state["language"] = new_code
            st.rerun()
        st.divider()

        st.markdown(t("sidebar_about"))
        st.markdown(t("sidebar_about_text"))
        st.divider()

        st.markdown(t("sidebar_index_info"))
        charters = meta.get("charters")
        if charters:
            merged_at = meta.get("merged_at", "")[:10]
            st.markdown(f"{t('sidebar_total_txn')} {meta.get('total_transactions', '—')}")
            st.markdown(f"{t('sidebar_merged')} {merged_at}")
            st.markdown(t("sidebar_charters_included"))
            for c in charters:
                name = c.get("charter_name", "—")
                count = c.get("total_transactions", "?")
                st.markdown(f"- {name} *({count} transactions)*")
        else:
            st.markdown(f"{t('sidebar_source')} {meta.get('source_pdf', '—')}")
            st.markdown(f"{t('sidebar_transactions')} {meta.get('total_transactions', '—')}")
            st.markdown(f"{t('sidebar_built')} {meta.get('built_at', meta.get('migrated_at', '—'))[:10]}")

        st.divider()
        st.markdown(t("sidebar_rebuild"))
        st.code(
            "# Build per-charter index\n"
            "python scripts/build_index.py \\\n"
            "  --pdf citizenscharters/<file>.pdf\n\n"
            "# Merge all charters\n"
            "python scripts/merge_indexes.py",
            language="bash",
        )

        if st.button(t("sidebar_clear_cache"), use_container_width=True):
            load_index.clear()
            fetch_candidates.clear()
            fetch_requirements.clear()
            fetch_letter_draft.clear()
            fetch_visa_info.clear()
            fetch_visa_recommendation.clear()
            st.success(t("sidebar_cache_cleared"))


# ── Step 1: Input ─────────────────────────────────────────────────────────────


def render_step1() -> None:
    # If the user navigated here from Find My Visa, pre-populate the query.
    # Must be set BEFORE the st.text_area widget renders.
    if "txn_query_prefill" in st.session_state:
        st.session_state["query_input"] = st.session_state.pop("txn_query_prefill")

    step_badge(t("step1_badge"))
    st.subheader(t("step1_heading"))
    st.markdown(t("step1_description"))

    examples = [
        "I want to apply for an ACR I-Card",
        "How do I extend my tourist visa?",
        "I need to change my visa status",
    ]
    st.caption("Examples: " + " · ".join(f'*"{e}"*' for e in examples))

    query = st.text_area(
        "Your query",
        placeholder=t("step1_placeholder"),
        height=100,
        label_visibility="collapsed",
        key="query_input",
    )

    if st.button(t("step1_button"), type="primary", use_container_width=True):
        if not query.strip():
            st.warning(t("step1_warning"))
            return

        with st.spinner(t("step1_spinner")):
            candidates = fetch_candidates(query.strip(), language=_lang_full())

        st.session_state.user_query  = query.strip()
        st.session_state.candidates  = candidates
        st.session_state.step        = 2
        st.rerun()


# ── Step 2: Confirm ───────────────────────────────────────────────────────────


def render_step2(index: dict) -> None:
    step_badge(t("step2_badge"))
    st.subheader(t("step2_heading"))
    st.caption(f'You said: *"{st.session_state.user_query}"*')

    candidates: list[dict] = st.session_state.get("candidates", [])
    transactions: list[dict] = index.get("transactions", [])

    if not candidates:
        st.warning(t("step2_no_match"))
        if st.button(t("step2_try_again"), use_container_width=True):
            st.session_state.step = 1
            st.rerun()
        return

    for candidate in candidates:
        # Look up the full transaction object now so we can show start_page
        txn_id = candidate.get("id")
        full_txn = next(
            (t for t in transactions if t["id"] == txn_id),
            {"id": txn_id, "name": candidate.get("name", ""), "category": ""},
        )

        with st.container(border=True):
            # Row 1: transaction name + clickable page number
            name_col, page_col = st.columns([4, 1])
            with name_col:
                st.markdown(f"**{full_txn.get('name', '—')}**")
            with page_col:
                page = full_txn.get("start_page")
                if page:
                    # Use per-transaction source_pdf (works across multiple charters)
                    pdf_filename = full_txn.get("source_pdf", "")
                    if pdf_filename:
                        pdf_url = f"/app/static/{pdf_filename}#page={page}"
                        st.markdown(
                            f'<a href="{pdf_url}" target="_blank" '
                            f'style="font-size:0.8rem;color:#6b7280;text-decoration:none;">'
                            f'📄 p.&nbsp;{page}</a>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption(f"📄 p. {page}")

            # Row 2: charter edition badge (shown when index has multiple charters)
            charter = full_txn.get("charter_name", "")
            if charter:
                edition_label = _short_edition_label(charter)
                st.markdown(
                    f'<span style="font-size:0.72rem;background:#e8f0fe;'
                    f'color:#1a56db;padding:1px 7px;border-radius:999px;'
                    f'font-weight:500;">{edition_label}</span>',
                    unsafe_allow_html=True,
                )

            reason = candidate.get("reason", "")
            if reason:
                st.caption(reason)

            if st.button(
                t("step2_select"),
                key=f"select_{txn_id}",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.selected_txn = full_txn
                st.session_state.step = 3
                st.rerun()

    st.markdown("")
    if st.button(t("step2_start_over"), use_container_width=True):
        reset_state()
        st.rerun()


# ── Step 3: Requirements ──────────────────────────────────────────────────────


def render_letter_section(transaction_name: str) -> None:
    """
    Expander that collects applicant details and drafts a formal letter
    to the Commissioner. Only rendered when the requirements text mentions
    a 'Letter Request addressed to the Commissioner'.
    """
    with st.expander(t("letter_expander"), expanded=False):
        st.caption(t("letter_caption"))

        with st.form("letter_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                applicant_name = st.text_input(
                    t("letter_fullname"), placeholder="e.g. Juan dela Cruz"
                )
                nationality = st.text_input(
                    t("letter_nationality"), placeholder="e.g. Japanese"
                )
                passport_number = st.text_input(
                    t("letter_passport"), placeholder="e.g. A12345678"
                )
                petitioner_name = st.text_input(
                    t("letter_petitioner"), placeholder="e.g. Juana dela Cruz"
                )
            with col_b:
                address = st.text_input(
                    t("letter_address"), placeholder="e.g. 123 Main St, Makati City"
                )
                email = st.text_input(
                    t("letter_email"), placeholder="e.g. delacruzsample@email.com"
                )
                contact_number = st.text_input(
                    t("letter_contact"), placeholder="e.g. 08011111111"
                )


            purpose = st.text_area(
                t("letter_purpose"),
                placeholder=t("letter_purpose_placeholder"),
                height=80,
            )

            submitted = st.form_submit_button(
                t("letter_generate"), type="primary", use_container_width=True
            )

        if submitted:
            if not applicant_name.strip() or not nationality.strip():
                st.warning(t("letter_warning"))
            else:
                with st.spinner(t("letter_spinner")):
                    try:
                        letter = fetch_letter_draft(
                            transaction_name=transaction_name,
                            applicant_name=applicant_name.strip(),
                            nationality=nationality.strip(),
                            passport_number=passport_number.strip(),
                            address=address.strip(),
                            purpose=purpose.strip(),
                            email=email.strip(),
                            contact_number=contact_number.strip(),
                            petitioner_name=petitioner_name.strip(),
                        )
                        st.session_state.drafted_letter  = letter
                        st.session_state.letter_for_txn  = transaction_name
                    except Exception as exc:
                        st.error(f"Letter generation failed: {exc}")

        # Show letter if it was generated for this transaction
        if (
            st.session_state.get("drafted_letter")
            and st.session_state.get("letter_for_txn") == transaction_name
        ):
            st.markdown("---")
            st.markdown(t("letter_output_label"))
            st.text_area(
                "letter_output",
                value=st.session_state.drafted_letter,
                height=480,
                label_visibility="collapsed",
            )
            st.caption(t("letter_tip"))


def _parse_steps(
    requirements: str,
) -> tuple[str, list[dict], str]:
    """
    Split the LLM output into three parts:
      before  — everything before the 👣 Step-by-Step section (markdown)
      steps   — list of {num, title, detail} dicts
      after   — everything after the section (markdown, e.g. 💡 Good to Know)

    If no steps section is found the full text is returned as `before`.
    If the section is found but items can't be parsed, the raw body is
    appended to `before` so nothing is silently dropped.
    """
    # Match ### 👣 … with optional ** bold markers around the emoji/text
    match = re.search(
        r"###\s*\**\s*👣[^\n]*\n(.*?)(?=\n###\s|\Z)",
        requirements,
        re.DOTALL,
    )
    if not match:
        return requirements, [], ""

    before = requirements[: match.start()].rstrip()
    body   = match.group(1).strip()
    after  = requirements[match.end() :].lstrip()

    # Split on lines that start a new numbered item
    raw_items = re.split(r"\n(?=\d+\.\s)", "\n" + body)
    steps: list[dict] = []
    for raw in raw_items:
        raw = raw.strip()
        if not raw or not re.match(r"\d+\.", raw):
            continue

        num_m = re.match(r"(\d+)\.\s*", raw)
        step_num = int(num_m.group(1)) if num_m else len(steps) + 1
        content  = raw[num_m.end() :] if num_m else raw

        # Title = bold text if present, otherwise first sentence / first line
        bold_m = re.match(r"\*\*(.+?)\*\*\s*[—\-]?\s*", content)
        if bold_m:
            title  = bold_m.group(1).strip()
            detail = content[bold_m.end() :].strip()
        else:
            lines  = content.split("\n", 1)
            title  = lines[0].strip()
            detail = lines[1].strip() if len(lines) > 1 else ""

        # Trim very long titles to keep the flowchart readable
        if len(title) > 90:
            title = title[:87].rsplit(" ", 1)[0] + "…"

        steps.append({"num": step_num, "title": title, "detail": detail})

    # Safety: if the section was found but yielded no parsed items,
    # fold the raw body back into `before` so it renders as markdown.
    if not steps:
        header_md = "\n\n### 👣 Step-by-Step\n"
        before = before + header_md + body
        return before, [], after

    return before, steps, after


def _render_flowchart(steps: list[dict]) -> None:
    """Render an interactive HTML flowchart for the given steps list."""
    if not steps:
        return

    # Build one card per step + arrow connectors
    cards_html = ""
    for i, s in enumerate(steps):
        detail_html = (
            s["detail"]
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        ) if s["detail"] else ""

        detail_block = (
            f'<div class="detail">{detail_html}</div>'
            if detail_html
            else ""
        )
        toggle_icon = "▼" if detail_html else ""

        cards_html += f"""
        <div class="step-card" id="card-{i}" onclick="toggle({i})"
             style="{'cursor:pointer;' if detail_html else 'cursor:default;'}">
          <div class="card-header">
            <span class="step-num">{s['num']}</span>
            <span class="step-title">{s['title']}</span>
            {'<span class="toggle-icon" id="icon-' + str(i) + '">' + toggle_icon + '</span>'
             if detail_html else ''}
          </div>
          {detail_block}
        </div>
        {"<div class='arrow'>↓</div>" if i < len(steps) - 1 else ""}
        """

    # Estimate iframe height: ~76px per collapsed card + 36px per arrow + padding
    # A generous estimate avoids clipping when steps are expanded.
    height = len(steps) * 76 + (len(steps) - 1) * 36 + 60

    html = textwrap.dedent(f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
      * {{ box-sizing: border-box; margin: 0; padding: 0; }}
      body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 14px;
        background: transparent;
        padding: 4px 2px 12px;
      }}
      .step-card {{
        border: 2px solid #1a56db;
        border-radius: 10px;
        overflow: hidden;
        background: #fff;
        transition: box-shadow .15s;
        user-select: none;
      }}
      .step-card:hover {{
        box-shadow: 0 2px 10px rgba(26,86,219,.18);
      }}
      .card-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 11px 14px;
      }}
      .step-num {{
        flex-shrink: 0;
        width: 26px;
        height: 26px;
        background: #1a56db;
        color: #fff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 12px;
      }}
      .step-title {{
        flex: 1;
        font-weight: 600;
        color: #1e3a5f;
        line-height: 1.35;
      }}
      .toggle-icon {{
        flex-shrink: 0;
        color: #6b7280;
        font-size: 11px;
        transition: transform .2s;
      }}
      .detail {{
        display: none;
        border-top: 1px solid #dbeafe;
        background: #f0f4ff;
        padding: 10px 14px 12px 50px;
        color: #374151;
        line-height: 1.6;
        font-size: 13px;
      }}
      .arrow {{
        text-align: center;
        color: #1a56db;
        font-size: 20px;
        line-height: 32px;
        font-weight: 700;
      }}
    </style>
    </head>
    <body>
    {cards_html}
    <script>
      function toggle(i) {{
        var card   = document.getElementById('card-' + i);
        var detail = card.querySelector('.detail');
        var icon   = document.getElementById('icon-' + i);
        if (!detail) return;
        var open = detail.style.display === 'block';
        detail.style.display = open ? 'none' : 'block';
        if (icon) icon.textContent = open ? '▼' : '▲';
        // Notify parent of new height
        var h = document.body.scrollHeight;
        window.parent.postMessage({{type:'resize', height: h + 20}}, '*');
      }}
    </script>
    </body>
    </html>
    """)

    components.html(html, height=height, scrolling=True)


def render_step3() -> None:
    step_badge(t("step3_badge"))

    txn: dict = st.session_state.selected_txn

    # Show charter edition badge + category while the agent loads
    charter = txn.get("charter_name", "")
    if charter:
        edition_label = _short_edition_label(charter)
        category = txn.get("category", "")
        meta_parts = [edition_label]
        if category:
            meta_parts.append(f"🏢 {category}")
        st.caption(" · ".join(meta_parts))

    # Include tasks.yaml mtime so the cache busts whenever the prompt changes
    _tasks_yaml = Path(__file__).parent / "config" / "tasks.yaml"
    _tasks_mtime = _tasks_yaml.stat().st_mtime if _tasks_yaml.exists() else 0

    with st.spinner(t("step3_spinner")):
        try:
            requirements = fetch_requirements(
                txn["id"], txn["name"], _tasks_mtime, language=_lang_full()
            )
        except Exception as exc:
            st.error(f"{t('step3_error')} {exc}")
            return

    # Split out the Step-by-Step section so it can be rendered as a flowchart
    before_steps, steps, after_steps = _parse_steps(requirements)

    # Render inside a bordered card so the output feels contained
    with st.container(border=True):
        # Everything before the steps (title, Quick Look, requirements, fees)
        if before_steps:
            st.markdown(before_steps)

        # Interactive flowchart for the steps
        if steps:
            st.markdown("### 👣 Step-by-Step")
            st.caption(t("step3_click_step"))
            _render_flowchart(steps)

        # Everything after the steps (Good to Know, etc.)
        if after_steps:
            st.markdown(after_steps)

        # ── Source citation ───────────────────────────────────────────────────
        source_pdf  = txn.get("source_pdf", "")
        start_page  = txn.get("start_page")
        charter     = txn.get("charter_name", "Citizen's Charter")

        st.divider()
        if source_pdf and start_page:
            pdf_url = f"/app/static/{source_pdf}#page={start_page}"
            st.markdown(
                f'<p style="font-size:0.82rem;color:#6b7280;margin:0;">'
                f'📄 <strong>Source:</strong> {charter}'
                f' &nbsp;·&nbsp; p.&nbsp;{start_page}'
                f' &nbsp;·&nbsp; <a href="{pdf_url}" target="_blank"'
                f' style="color:#1a56db;">Open in PDF ↗</a>'
                f'</p>',
                unsafe_allow_html=True,
            )
        elif charter:
            st.markdown(
                f'<p style="font-size:0.82rem;color:#6b7280;margin:0;">'
                f'📄 <strong>Source:</strong> {charter}</p>',
                unsafe_allow_html=True,
            )

    # Letter drafting — only shown when the requirements mention it
    if requires_letter(requirements):
        st.divider()
        render_letter_section(txn["name"])

    st.divider()
    col_back, col_new = st.columns(2)
    with col_back:
        if st.button(t("step3_back"), use_container_width=True):
            # Clear letter state so a fresh letter can be drafted next time
            st.session_state.pop("drafted_letter", None)
            st.session_state.pop("letter_for_txn", None)
            st.session_state.step = 2
            st.rerun()
    with col_new:
        if st.button(t("step3_another"), type="primary", use_container_width=True):
            reset_state()
            st.rerun()


# ── Visa helpers ──────────────────────────────────────────────────────────────


def _extract_top_visa(rec_result: str) -> str:
    """
    Pull the recommended visa name from the '### ✅ Our Top Pick' header so it
    can be pre-filled into the Visa Info and Transaction Assistant tabs.
    Returns an empty string if the section isn't found.
    """
    match = re.search(r"###\s*✅\s*Our Top Pick[:\s]+(.+)", rec_result)
    if match:
        name = match.group(1).strip()
        name = re.sub(r"\*+", "", name).strip()   # strip any bold markers
        return name
    return ""


# ── Visa Info mode ────────────────────────────────────────────────────────────


def render_visa_info_mode() -> None:
    # If the user navigated here from Find My Visa, pre-populate the input.
    # Must be set BEFORE the st.text_input widget renders.
    if "visa_info_prefill" in st.session_state:
        st.session_state["visa_info_input"] = st.session_state.pop("visa_info_prefill")

    st.subheader(t("visa_info_heading"))
    st.markdown(t("visa_info_description"))

    examples = [
        "9(A) tourist visa",
        "13(A) immigrant visa",
        "student visa 9(F)",
        "SRRV retirement visa",
        "ACR I-Card",
    ]
    st.caption("Examples: " + " · ".join(f'*"{e}"*' for e in examples))

    visa_query = st.text_input(
        t("visa_info_label"),
        placeholder=t("visa_info_placeholder"),
        key="visa_info_input",
        label_visibility="visible",
    )

    if st.button(
        t("visa_info_button"), type="primary", use_container_width=True, key="visa_info_btn"
    ):
        if not visa_query.strip():
            st.warning(t("visa_info_warning"))
            return
        with st.spinner(t("visa_info_spinner")):
            try:
                result = fetch_visa_info(visa_query.strip(), language=_lang_full())
                st.session_state.visa_info_result = result
                st.session_state.visa_info_query  = visa_query.strip()
            except Exception as exc:
                st.error(f"{t('step3_error')} {exc}")
                return

    if st.session_state.get("visa_info_result"):
        with st.container(border=True):
            st.markdown(st.session_state.visa_info_result)
        if st.button(
            t("visa_info_reset"), use_container_width=True, key="visa_info_reset"
        ):
            st.session_state.pop("visa_info_result", None)
            st.session_state.pop("visa_info_query",  None)
            st.rerun()


# ── Visa Finder mode ──────────────────────────────────────────────────────────


def render_visa_finder_mode() -> None:
    st.subheader(t("visa_finder_heading"))
    st.markdown(t("visa_finder_description"))

    # ── If a result already exists, show it with action buttons ──────────────
    if st.session_state.get("visa_rec_result"):
        rec_result = st.session_state.visa_rec_result
        top_visa   = _extract_top_visa(rec_result)

        with st.container(border=True):
            st.markdown(rec_result)

        st.divider()

        # ── Quick-jump buttons: pre-fill the destination tab's input ──────────
        col_visa, col_txn = st.columns(2)
        with col_visa:
            if st.button(
                t("goto_visa_info"),
                use_container_width=True,
                key="goto_visa_info",
                help=t("goto_visa_info_help"),
            ):
                if top_visa:
                    st.session_state["visa_info_prefill"] = top_visa
                st.session_state["switch_to_tab"] = 1   # Visa Information tab
                st.rerun()
        with col_txn:
            if st.button(
                t("goto_txn_assistant"),
                type="primary",
                use_container_width=True,
                key="goto_txn_assistant",
                help=t("goto_txn_assistant_help"),
            ):
                if top_visa:
                    st.session_state["txn_query_prefill"] = top_visa
                # Also reset the Transaction Assistant to step 1
                st.session_state["step"] = 1
                st.session_state["switch_to_tab"] = 2   # Transaction Assistant tab
                st.rerun()

        st.markdown("")
        if st.button(
            t("visa_finder_reset"),
            use_container_width=True, key="visa_rec_reset"
        ):
            st.session_state.pop("visa_rec_result", None)
            st.rerun()
        return

    # ── Input form ────────────────────────────────────────────────────────────
    with st.form("visa_finder_form"):
        col1, col2 = st.columns(2)

        with col1:
            nationality = st.text_input(
                t("visa_finder_nationality"),
                placeholder=t("visa_finder_nationality_placeholder"),
                key="vf_nationality",
            )
            purpose = st.selectbox(
                t("visa_finder_purpose"),
                t("visa_finder_purpose_options"),
                key="vf_purpose",
            )
            duration = st.selectbox(
                t("visa_finder_duration"),
                t("visa_finder_duration_options"),
                key="vf_duration",
            )

        with col2:
            has_filipino_family = st.radio(
                t("visa_finder_family"),
                t("visa_finder_family_options"),
                key="vf_family",
            )
            employment = st.radio(
                t("visa_finder_employment"),
                t("visa_finder_employment_options"),
                key="vf_employment",
            )
            retirement = st.radio(
                t("visa_finder_retirement"),
                t("visa_finder_retirement_options"),
                key="vf_retirement",
            )

        extra_details = st.text_area(
            t("visa_finder_extra"),
            placeholder=t("visa_finder_extra_placeholder"),
            height=80,
            key="vf_extra",
        )

        submitted = st.form_submit_button(
            t("visa_finder_submit"), type="primary", use_container_width=True
        )

    if submitted:
        if not nationality.strip():
            st.warning(t("visa_finder_warning"))
            return

        with st.spinner(t("visa_finder_spinner")):
            try:
                result = fetch_visa_recommendation(
                    nationality=nationality.strip(),
                    purpose=purpose,
                    duration=duration,
                    has_filipino_family=has_filipino_family,
                    employment=employment,
                    retirement=retirement,
                    extra_details=extra_details.strip() or "None provided",
                    language=_lang_full(),
                )
                st.session_state.visa_rec_result = result
                st.rerun()
            except Exception as exc:
                st.error(f"{t('step3_error')} {exc}")


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    # Initialise language before anything else (needed by t())
    if "language" not in st.session_state:
        st.session_state["language"] = "en"

    # Pass file mtime so cache auto-invalidates after merge_indexes.py reruns
    _mtime = INDEX_PATH.stat().st_mtime if INDEX_PATH.exists() else 0
    index = load_index(_mtime)

    if index is None:
        st.title(f"🏛️ {t('page_title')}")
        st.error(
            f"{t('index_not_found')}\n\n"
            "```bash\n"
            "python scripts/build_index.py "
            "--pdf citizenscharters/BureauOfImmigration_4thEdition.pdf\n"
            "python scripts/merge_indexes.py\n"
            "```"
        )
        st.stop()

    # Initialise session state
    if "step" not in st.session_state:
        st.session_state.step = 1

    render_sidebar(index)

    st.title(f"🏛️ {t('page_title')}")
    st.caption(t("page_subtitle"))
    st.divider()

    tab_finder, tab_visa, tab_txn, = st.tabs([
        t("tab_find_visa"),
        t("tab_visa_info"),
        t("tab_txn_assistant"),
    ])

    # ── Tab-switch via JS (triggered by action buttons in Find My Visa) ────────
    # Tabs are client-side only in Streamlit; JS clicks the right tab button
    # after the DOM is ready.  Tab indices: 0=Find My Visa, 1=Visa Info, 2=Txn.
    if "switch_to_tab" in st.session_state:
        _tab_idx = st.session_state.pop("switch_to_tab")
        components.html(
            f"""<script>
            (function() {{
                function doSwitch() {{
                    var tabs = window.parent.document.querySelectorAll('button[role="tab"]');
                    if (tabs && tabs.length > {_tab_idx}) {{
                        tabs[{_tab_idx}].click();
                    }} else {{
                        setTimeout(doSwitch, 60);
                    }}
                }}
                setTimeout(doSwitch, 200);
            }})();
            </script>""",
            height=0,
            scrolling=False,
        )

    with tab_txn:
        step = st.session_state.step
        if step == 1:
            render_step1()
        elif step == 2:
            render_step2(index)
        elif step == 3:
            render_step3()

    with tab_visa:
        render_visa_info_mode()

    with tab_finder:
        render_visa_finder_mode()


if __name__ == "__main__":
    main()

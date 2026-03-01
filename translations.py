"""
Multilingual UI strings for the Citizen's Charter Assistant.
Supported languages: English (en), Japanese (ja), Filipino/Tagalog (tl).
"""

import streamlit as st

LANG_OPTIONS = {
    "en": "English",
    "ja": "日本語 (Japanese)",
    "tl": "Filipino (Tagalog)",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── Page-level ────────────────────────────────────────────────────────────
    "page_title": {
        "en": "Citizen's Charter Assistant",
        "ja": "市民憲章アシスタント",
        "tl": "Katulong sa Citizen's Charter",
    },
    "page_subtitle": {
        "en": "Powered by CrewAI · Bureau of Immigration · Philippines",
        "ja": "CrewAI · フィリピン入国管理局",
        "tl": "Pinapagana ng CrewAI · Bureau of Immigration · Pilipinas",
    },

    # ── Tab names ─────────────────────────────────────────────────────────────
    "tab_find_visa": {
        "en": "🧭 Find My Visa",
        "ja": "🧭 ビザを探す",
        "tl": "🧭 Hanapin ang Visa Ko",
    },
    "tab_visa_info": {
        "en": "🛂 Visa Information",
        "ja": "🛂 ビザ情報",
        "tl": "🛂 Impormasyon ng Visa",
    },
    "tab_txn_assistant": {
        "en": "📋 Transaction Assistant",
        "ja": "📋 取引アシスタント",
        "tl": "📋 Katulong sa Transaksyon",
    },

    # ── Sidebar ───────────────────────────────────────────────────────────────
    "sidebar_about": {
        "en": "## 🏛️ About",
        "ja": "## 🏛️ このアプリについて",
        "tl": "## 🏛️ Tungkol Dito",
    },
    "sidebar_about_text": {
        "en": (
            "This assistant reads the **Citizen's Charter** of a government "
            "agency and tells you exactly what documents to bring, where to "
            "go, and how much to pay for any transaction."
        ),
        "ja": (
            "このアシスタントは政府機関の**市民憲章**を読み取り、"
            "必要な書類、行き先、手数料を正確にお伝えします。"
        ),
        "tl": (
            "Binabasa ng assistant na ito ang **Citizen's Charter** ng ahensya ng "
            "gobyerno at sasabihin sa iyo kung anong mga dokumento ang dapat dalhin, "
            "saan pupunta, at magkano ang babayaran."
        ),
    },
    "sidebar_index_info": {
        "en": "#### 📊 Index Info",
        "ja": "#### 📊 インデックス情報",
        "tl": "#### 📊 Impormasyon ng Index",
    },
    "sidebar_total_txn": {
        "en": "**Total transactions:**",
        "ja": "**取引総数:**",
        "tl": "**Kabuuang transaksyon:**",
    },
    "sidebar_merged": {
        "en": "**Merged:**",
        "ja": "**統合日:**",
        "tl": "**Pinagsama:**",
    },
    "sidebar_charters_included": {
        "en": "**Charters included:**",
        "ja": "**含まれる憲章:**",
        "tl": "**Mga charter na kasama:**",
    },
    "sidebar_source": {
        "en": "**Source:**",
        "ja": "**ソース:**",
        "tl": "**Pinagmulan:**",
    },
    "sidebar_transactions": {
        "en": "**Transactions:**",
        "ja": "**取引数:**",
        "tl": "**Mga transaksyon:**",
    },
    "sidebar_built": {
        "en": "**Built:**",
        "ja": "**作成日:**",
        "tl": "**Ginawa:**",
    },
    "sidebar_rebuild": {
        "en": "#### 🔄 Rebuild Index",
        "ja": "#### 🔄 インデックス再構築",
        "tl": "#### 🔄 I-rebuild ang Index",
    },
    "sidebar_clear_cache": {
        "en": "🗑️ Clear all caches",
        "ja": "🗑️ すべてのキャッシュをクリア",
        "tl": "🗑️ I-clear lahat ng cache",
    },
    "sidebar_cache_cleared": {
        "en": "Caches cleared!",
        "ja": "キャッシュをクリアしました！",
        "tl": "Na-clear na ang mga cache!",
    },
    "sidebar_language": {
        "en": "#### 🌐 Language",
        "ja": "#### 🌐 言語",
        "tl": "#### 🌐 Wika",
    },

    # ── Step 1 ────────────────────────────────────────────────────────────────
    "step1_badge": {
        "en": "STEP 1 OF 3",
        "ja": "ステップ 1/3",
        "tl": "HAKBANG 1 SA 3",
    },
    "step1_heading": {
        "en": "What do you need help with?",
        "ja": "何についてお手伝いしましょうか？",
        "tl": "Ano ang kailangan mong tulong?",
    },
    "step1_description": {
        "en": (
            "Describe your situation in plain language — no need to know the "
            "official transaction name."
        ),
        "ja": "お気軽に状況を説明してください — 正式な取引名を知る必要はありません。",
        "tl": (
            "Ilarawan ang iyong sitwasyon sa simpleng salita — hindi mo kailangang "
            "malaman ang opisyal na pangalan ng transaksyon."
        ),
    },
    "step1_placeholder": {
        "en": "e.g. I need to renew my passport or get an ACR I-Card…",
        "ja": "例: パスポートの更新やACR I-Cardの取得が必要です…",
        "tl": "hal. Kailangan kong i-renew ang passport ko o kumuha ng ACR I-Card…",
    },
    "step1_button": {
        "en": "Find matching transactions →",
        "ja": "該当する取引を検索 →",
        "tl": "Hanapin ang mga tumutugmang transaksyon →",
    },
    "step1_warning": {
        "en": "Please describe what you need before searching.",
        "ja": "検索する前に、必要なことを説明してください。",
        "tl": "Mangyaring ilarawan ang kailangan mo bago maghanap.",
    },
    "step1_spinner": {
        "en": "🔍 Searching for matching transactions…",
        "ja": "🔍 該当する取引を検索中…",
        "tl": "🔍 Naghahanap ng mga tumutugmang transaksyon…",
    },

    # ── Step 2 ────────────────────────────────────────────────────────────────
    "step2_badge": {
        "en": "STEP 2 OF 3",
        "ja": "ステップ 2/3",
        "tl": "HAKBANG 2 SA 3",
    },
    "step2_heading": {
        "en": "Which transaction do you need?",
        "ja": "どの取引が必要ですか？",
        "tl": "Aling transaksyon ang kailangan mo?",
    },
    "step2_no_match": {
        "en": (
            "I couldn't identify any matching transactions. "
            "Try rephrasing your description — be specific about what you want to do."
        ),
        "ja": (
            "該当する取引が見つかりませんでした。"
            "説明を変えてみてください — 具体的に何がしたいか教えてください。"
        ),
        "tl": (
            "Walang nahanap na tumutugmang transaksyon. "
            "Subukang baguhin ang paglalarawan — maging tiyak sa gusto mong gawin."
        ),
    },
    "step2_try_again": {
        "en": "← Try again",
        "ja": "← もう一度試す",
        "tl": "← Subukan muli",
    },
    "step2_select": {
        "en": "Select this transaction →",
        "ja": "この取引を選択 →",
        "tl": "Piliin ang transaksyong ito →",
    },
    "step2_start_over": {
        "en": "← Start over",
        "ja": "← 最初からやり直す",
        "tl": "← Magsimula muli",
    },

    # ── Step 3 ────────────────────────────────────────────────────────────────
    "step3_badge": {
        "en": "STEP 3 OF 3",
        "ja": "ステップ 3/3",
        "tl": "HAKBANG 3 SA 3",
    },
    "step3_spinner": {
        "en": "🤖 Reading the Citizen's Charter…",
        "ja": "🤖 市民憲章を読み取り中…",
        "tl": "🤖 Binabasa ang Citizen's Charter…",
    },
    "step3_error": {
        "en": "Something went wrong:",
        "ja": "エラーが発生しました:",
        "tl": "May nangyaring mali:",
    },
    "step3_click_step": {
        "en": "Click any step to see details.",
        "ja": "各ステップをクリックして詳細を表示。",
        "tl": "I-click ang anumang hakbang para sa detalye.",
    },
    "step3_back": {
        "en": "← Back to results",
        "ja": "← 結果に戻る",
        "tl": "← Bumalik sa mga resulta",
    },
    "step3_another": {
        "en": "Check another transaction →",
        "ja": "別の取引を確認 →",
        "tl": "Mag-check ng ibang transaksyon →",
    },

    # ── Letter section ────────────────────────────────────────────────────────
    "letter_expander": {
        "en": "✉️ Draft the Letter Request to the Commissioner",
        "ja": "✉️ コミッショナーへの申請書を作成",
        "tl": "✉️ Gumawa ng Liham sa Commissioner",
    },
    "letter_caption": {
        "en": (
            "Fill in your details and the agent will draft a formal letter "
            "you can print, sign, and submit."
        ),
        "ja": "詳細を入力すると、印刷・署名・提出できる正式な申請書を作成します。",
        "tl": (
            "Punan ang iyong mga detalye at gagawa ang agent ng pormal na liham "
            "na maaari mong i-print, pirmahan, at isumite."
        ),
    },
    "letter_fullname": {
        "en": "Full Name of Applicant *",
        "ja": "申請者氏名 *",
        "tl": "Buong Pangalan ng Aplikante *",
    },
    "letter_nationality": {
        "en": "Nationality *",
        "ja": "国籍 *",
        "tl": "Nasyonalidad *",
    },
    "letter_passport": {
        "en": "Passport Number",
        "ja": "パスポート番号",
        "tl": "Numero ng Pasaporte",
    },
    "letter_petitioner": {
        "en": "Name of Petitioner",
        "ja": "申請者名（ペティショナー）",
        "tl": "Pangalan ng Petitioner",
    },
    "letter_address": {
        "en": "Address",
        "ja": "住所",
        "tl": "Address",
    },
    "letter_email": {
        "en": "Email",
        "ja": "メール",
        "tl": "Email",
    },
    "letter_contact": {
        "en": "Contact Number",
        "ja": "電話番号",
        "tl": "Numero ng Telepono",
    },
    "letter_purpose": {
        "en": "Additional context (optional)",
        "ja": "追加情報（任意）",
        "tl": "Karagdagang detalye (opsyonal)",
    },
    "letter_purpose_placeholder": {
        "en": "Provide the reason for the application",
        "ja": "申請の理由を記入してください",
        "tl": "Ibigay ang dahilan ng aplikasyon",
    },
    "letter_generate": {
        "en": "✉️ Generate Letter",
        "ja": "✉️ 申請書を作成",
        "tl": "✉️ Gumawa ng Liham",
    },
    "letter_warning": {
        "en": "Please provide at least your **Full Name** and **Nationality**.",
        "ja": "少なくとも**氏名**と**国籍**を入力してください。",
        "tl": "Mangyaring ibigay ang iyong **Buong Pangalan** at **Nasyonalidad**.",
    },
    "letter_spinner": {
        "en": "✍️ Drafting your letter…",
        "ja": "✍️ 申請書を作成中…",
        "tl": "✍️ Ginagawa ang iyong liham…",
    },
    "letter_output_label": {
        "en": "**Your Letter** — review, edit if needed, then print and sign.",
        "ja": "**申請書** — 確認・編集後、印刷して署名してください。",
        "tl": "**Ang Iyong Liham** — suriin, i-edit kung kinakailangan, pagkatapos i-print at pirmahan.",
    },
    "letter_tip": {
        "en": (
            "💡 You can edit the text above directly before copying. "
            "Print it on plain paper, sign at the bottom, and submit it "
            "together with your other requirements."
        ),
        "ja": (
            "💡 コピーする前にテキストを直接編集できます。"
            "普通紙に印刷し、下部に署名して、他の書類と一緒に提出してください。"
        ),
        "tl": (
            "💡 Maaari mong i-edit ang teksto sa itaas bago kopyahin. "
            "I-print ito sa plain paper, pirmahan sa ibaba, at isumite "
            "kasama ng iba mong mga requirements."
        ),
    },

    # ── Visa Information tab ──────────────────────────────────────────────────
    "visa_info_heading": {
        "en": "🛂 Visa Information",
        "ja": "🛂 ビザ情報",
        "tl": "🛂 Impormasyon ng Visa",
    },
    "visa_info_description": {
        "en": (
            "Look up any Philippine immigration visa — how long it's valid, what you "
            "must do to maintain legal status, and which BI transactions apply. "
            "You can also search about ACR I-card since it also has its own validity information."
        ),
        "ja": (
            "フィリピンの入国ビザを調べましょう — 有効期間、合法的な滞在のために必要なこと、"
            "関連するBI取引など。ACR I-Cardについても検索できます。"
        ),
        "tl": (
            "Maghanap ng impormasyon tungkol sa anumang Philippine immigration visa — "
            "gaano katagal ito valid, ano ang kailangan mong gawin para manatiling legal, "
            "at aling mga BI transaction ang naaangkop. Maaari rin maghanap tungkol sa ACR I-Card."
        ),
    },
    "visa_info_label": {
        "en": "Which visa type would you like to know about?",
        "ja": "どのビザの種類について知りたいですか？",
        "tl": "Anong uri ng visa ang gusto mong malaman?",
    },
    "visa_info_placeholder": {
        "en": "e.g. 9(A) tourist visa, 13(A) immigrant visa, 47(a)(2)…",
        "ja": "例: 9(A) 観光ビザ、13(A) 移民ビザ、47(a)(2)…",
        "tl": "hal. 9(A) tourist visa, 13(A) immigrant visa, 47(a)(2)…",
    },
    "visa_info_button": {
        "en": "Get Visa Info →",
        "ja": "ビザ情報を取得 →",
        "tl": "Kunin ang Impormasyon ng Visa →",
    },
    "visa_info_warning": {
        "en": "Please enter a visa type to look up.",
        "ja": "調べたいビザの種類を入力してください。",
        "tl": "Mangyaring maglagay ng uri ng visa na hahanapin.",
    },
    "visa_info_spinner": {
        "en": "🔍 Looking up visa information…",
        "ja": "🔍 ビザ情報を検索中…",
        "tl": "🔍 Hinahanap ang impormasyon ng visa…",
    },
    "visa_info_reset": {
        "en": "🔍 Look up a different visa",
        "ja": "🔍 別のビザを検索",
        "tl": "🔍 Maghanap ng ibang visa",
    },

    # ── Find My Visa tab ──────────────────────────────────────────────────────
    "visa_finder_heading": {
        "en": "🧭 Find the Right Visa",
        "ja": "🧭 最適なビザを見つける",
        "tl": "🧭 Hanapin ang Tamang Visa",
    },
    "visa_finder_description": {
        "en": (
            "Tell us about your situation and we'll recommend the most suitable "
            "Philippine visa — plus the exact BI transactions you'll need."
        ),
        "ja": (
            "あなたの状況を教えてください。最適なフィリピンビザと"
            "必要なBI取引をお勧めします。"
        ),
        "tl": (
            "Sabihin sa amin ang iyong sitwasyon at irerekomenda namin ang pinakaangkop "
            "na Philippine visa — pati na rin ang eksaktong BI transactions na kakailanganin mo."
        ),
    },
    "visa_finder_nationality": {
        "en": "Your nationality *",
        "ja": "国籍 *",
        "tl": "Iyong nasyonalidad *",
    },
    "visa_finder_nationality_placeholder": {
        "en": "e.g. American, Japanese, British",
        "ja": "例: アメリカ人、日本人、イギリス人",
        "tl": "hal. Amerikano, Hapones, Briton",
    },
    "visa_finder_purpose": {
        "en": "Purpose of stay *",
        "ja": "滞在目的 *",
        "tl": "Layunin ng pananatili *",
    },
    "visa_finder_purpose_options": {
        "en": [
            "Tourism / Holiday",
            "Work / Employment",
            "Study / Education",
            "Retirement",
            "Join Filipino spouse or family",
            "Business / Investment",
            "Other",
        ],
        "ja": [
            "観光 / 休暇",
            "就労 / 雇用",
            "留学 / 教育",
            "退職 / リタイアメント",
            "フィリピン人配偶者・家族との合流",
            "ビジネス / 投資",
            "その他",
        ],
        "tl": [
            "Turismo / Bakasyon",
            "Trabaho / Empleo",
            "Pag-aaral / Edukasyon",
            "Pagreretiro",
            "Sumama sa asawang Pilipino o pamilya",
            "Negosyo / Pamumuhunan",
            "Iba pa",
        ],
    },
    "visa_finder_duration": {
        "en": "Expected duration *",
        "ja": "予定滞在期間 *",
        "tl": "Inaasahang tagal *",
    },
    "visa_finder_duration_options": {
        "en": [
            "Short visit (under 1 month)",
            "Extended stay (1–12 months)",
            "Long-term (1–3 years)",
            "Permanent / Indefinite",
        ],
        "ja": [
            "短期（1ヶ月未満）",
            "中期（1〜12ヶ月）",
            "長期（1〜3年）",
            "永住 / 無期限",
        ],
        "tl": [
            "Maikling bisita (wala pang 1 buwan)",
            "Matagal na pananatili (1–12 buwan)",
            "Pangmatagalan (1–3 taon)",
            "Permanente / Walang takdang panahon",
        ],
    },
    "visa_finder_family": {
        "en": "Filipino spouse, parent, or child?",
        "ja": "フィリピン人の配偶者・親・子供はいますか？",
        "tl": "Mayroon ka bang asawa, magulang, o anak na Pilipino?",
    },
    "visa_finder_family_options": {
        "en": ["No", "Yes — spouse", "Yes — parent", "Yes — child"],
        "ja": ["いいえ", "はい — 配偶者", "はい — 親", "はい — 子供"],
        "tl": ["Wala", "Oo — asawa", "Oo — magulang", "Oo — anak"],
    },
    "visa_finder_employment": {
        "en": "Seeking employment in the Philippines?",
        "ja": "フィリピンでの就労を希望していますか？",
        "tl": "Naghahanap ng trabaho sa Pilipinas?",
    },
    "visa_finder_employment_options": {
        "en": [
            "No",
            "Yes — employed by a Philippine-registered company",
            "Yes — self-employed / own business",
        ],
        "ja": [
            "いいえ",
            "はい — フィリピン登録企業に雇用",
            "はい — 自営業 / 自分のビジネス",
        ],
        "tl": [
            "Hindi",
            "Oo — employed sa Philippine-registered company",
            "Oo — self-employed / sariling negosyo",
        ],
    },
    "visa_finder_retirement": {
        "en": "Are you a retiree?",
        "ja": "退職者ですか？",
        "tl": "Retirado ka ba?",
    },
    "visa_finder_retirement_options": {
        "en": ["No", "Yes — with regular pension income", "Yes — no pension"],
        "ja": ["いいえ", "はい — 定期的な年金収入あり", "はい — 年金なし"],
        "tl": ["Hindi", "Oo — may regular na pensyon", "Oo — walang pensyon"],
    },
    "visa_finder_extra": {
        "en": "Any additional details? (optional)",
        "ja": "その他の詳細情報はありますか？（任意）",
        "tl": "May karagdagang detalye ba? (opsyonal)",
    },
    "visa_finder_extra_placeholder": {
        "en": (
            "e.g. My tourist visa expires next month and I want to stay longer. "
            "I am enrolled in a language school. My employer is a foreign company "
            "with a Philippine branch."
        ),
        "ja": (
            "例: 観光ビザが来月期限切れで、もう少し滞在したいです。"
            "語学学校に通っています。雇用主はフィリピンに支社がある外資系企業です。"
        ),
        "tl": (
            "hal. Mag-e-expire na ang tourist visa ko sa susunod na buwan at gusto kong "
            "manatili pa. Naka-enroll ako sa isang language school. Ang employer ko ay "
            "isang foreign company na may branch sa Pilipinas."
        ),
    },
    "visa_finder_submit": {
        "en": "Find My Visa →",
        "ja": "ビザを探す →",
        "tl": "Hanapin ang Visa Ko →",
    },
    "visa_finder_warning": {
        "en": "Please enter your nationality.",
        "ja": "国籍を入力してください。",
        "tl": "Mangyaring ilagay ang iyong nasyonalidad.",
    },
    "visa_finder_spinner": {
        "en": "🧭 Analysing your situation and searching the charter…",
        "ja": "🧭 状況を分析し、憲章を検索中…",
        "tl": "🧭 Sinusuri ang iyong sitwasyon at hinahanap sa charter…",
    },
    "visa_finder_reset": {
        "en": "🔄 Start a new recommendation",
        "ja": "🔄 新しいおすすめを開始",
        "tl": "🔄 Magsimula ng bagong rekomendasyon",
    },

    # ── Cross-tab navigation buttons ──────────────────────────────────────────
    "goto_visa_info": {
        "en": "🛂 Visa Information",
        "ja": "🛂 ビザ情報を見る",
        "tl": "🛂 Impormasyon ng Visa",
    },
    "goto_visa_info_help": {
        "en": "Learn more about this visa — validity, requirements, and maintenance.",
        "ja": "このビザの詳細 — 有効期間、要件、維持方法。",
        "tl": "Alamin pa tungkol sa visa na ito — validity, requirements, at maintenance.",
    },
    "goto_txn_assistant": {
        "en": "📋 Transaction Assistant",
        "ja": "📋 取引アシスタントへ",
        "tl": "📋 Katulong sa Transaksyon",
    },
    "goto_txn_assistant_help": {
        "en": "Find the exact BI transactions you need to apply for or maintain this visa.",
        "ja": "このビザの申請・維持に必要なBI取引を探します。",
        "tl": "Hanapin ang eksaktong BI transactions na kailangan mo para mag-apply o i-maintain ang visa na ito.",
    },

    # ── Error page (no index) ─────────────────────────────────────────────────
    "index_not_found": {
        "en": "**Index not found.** Build it first by running:",
        "ja": "**インデックスが見つかりません。**まず以下を実行してください:",
        "tl": "**Hindi nahanap ang index.** I-build muna ito sa pamamagitan ng:",
    },
}


def t(key: str) -> str | list:
    """Return the translation for *key* in the current session language."""
    lang = st.session_state.get("language", "en")
    entry = TRANSLATIONS.get(key, {})
    return entry.get(lang, entry.get("en", key))

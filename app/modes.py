"""Style mode definitions. Each mode carries a "style card" that is injected
into the system prompt to steer the rewrite."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Mode:
    id: str
    label: str
    blurb: str  # short description shown in the UI
    style_card: str  # instructions injected into the system prompt


MODES: dict[str, Mode] = {
    m.id: m
    for m in [
        Mode(
            id="casual",
            label="Casual",
            blurb="Texting a friend on IG / WhatsApp",
            style_card=(
                "Target: casual texting between friends (Instagram, WhatsApp, iMessage).\n"
                "- Fix only what makes the message hard to read or genuinely wrong "
                "(typos that change meaning, broken word order, wrong word choice).\n"
                "- Do NOT add capitalization, full stops, or formal punctuation. If the "
                "input is lowercase with no periods, the output stays that way — that IS "
                "correct in this register.\n"
                "- Keep contractions, abbreviations (u, rn, ngl, tbh), emoji, and "
                "stretched words (soooo) when they feel natural. You may drop ones that "
                "feel forced.\n"
                "- The goal: sound like a real native speaker texting, not a textbook."
            ),
        ),
        Mode(
            id="linkedin",
            label="LinkedIn",
            blurb="Polished, engaging LinkedIn voice",
            style_card=(
                "Target: a LinkedIn post or comment that reads as credible and engaging.\n"
                "- Professional but human — confident first person, active voice, short "
                "punchy sentences mixed with longer ones.\n"
                "- Light storytelling energy is welcome; corporate buzzword soup "
                "(synergy, leverage, circle back) is not.\n"
                "- Proper capitalization and punctuation. Emoji: at most one, only if "
                "the input already had that energy.\n"
                "- The goal: something a sharp professional would actually post."
            ),
        ),
        Mode(
            id="ielts9",
            label="IELTS Band 9",
            blurb="Examiner-pleasing academic English",
            style_card=(
                "Target: IELTS Band 9 written English (Task 2 essay register).\n"
                "- Wide, precise lexical resource: natural collocations and less common "
                "vocabulary used accurately, never thesaurus-stuffing.\n"
                "- Varied complex structures: conditionals, relative clauses, fronting, "
                "nominalisation — all error-free.\n"
                "- Clear cohesion: linking devices used skilfully and unobtrusively "
                "(not 'Firstly, Moreover, In conclusion' bolted on).\n"
                "- Formal but fluent tone; no contractions.\n"
                "- The goal: what an examiner would score 9 for lexical resource, "
                "grammatical range and accuracy."
            ),
        ),
        Mode(
            id="genz",
            label="Gen Z",
            blurb="Chronically-online chat energy",
            style_card=(
                "Target: Gen Z internet chat (Discord, TikTok comments, group chat).\n"
                "- lowercase by default, minimal punctuation, current slang where it "
                "lands naturally (fr, lowkey, no cap, it's giving, ate, rizz — only if "
                "it fits, never forced).\n"
                "- Irony, hyperbole and keyboard-smash energy are fine; boomer-coded "
                "phrasing is not.\n"
                "- Do NOT correct stylistic lowercase or missing periods — that's the "
                "register.\n"
                "- The goal: sounds like an actual person under 25 typed it, not a brand "
                "trying to."
            ),
        ),
        Mode(
            id="professional",
            label="Professional",
            blurb="Clear workplace email / Slack",
            style_card=(
                "Target: professional workplace communication (email to a colleague, "
                "boss, client; a clear Slack message).\n"
                "- Correct grammar, capitalization and punctuation throughout.\n"
                "- Polite, direct, and concise — say the thing, soften only where tact "
                "is needed.\n"
                "- Neutral-warm tone: no stiff legalese, no exclamation-mark overload.\n"
                "- The goal: the reader immediately understands and nothing reads as "
                "rude or sloppy."
            ),
        ),
        Mode(
            id="aave",
            label="Black English",
            blurb="AAVE — authentic, not caricature",
            style_card=(
                "Target: African American Vernacular English (AAVE) — a rule-governed "
                "variety of English with its own consistent grammar.\n"
                "- Use genuine AAVE grammatical features where they fit naturally: "
                "habitual 'be', copula absence, completive 'done', negative concord, "
                "ain't, remote-past 'been' (stressed).\n"
                "- Vocabulary and phrasing should be current and natural, never "
                "minstrel-y, dated, or exaggerated. If unsure, understate.\n"
                "- Keep the casual texting conventions of the input (lowercase etc.) "
                "unless the content is formal.\n"
                "- The goal: how a real AAVE speaker would put it — respectful, "
                "authentic, zero caricature."
            ),
        ),
        Mode(
            id="academic",
            label="Academic",
            blurb="Papers, reports, discussion posts",
            style_card=(
                "Target: formal academic writing (course papers, reports, discussion "
                "posts).\n"
                "- Precise, objective, appropriately hedged (suggests, appears to, may) "
                "without being timid.\n"
                "- No contractions, no colloquialisms, no rhetorical filler.\n"
                "- Prefer clear subject-verb-object sentences over stacked "
                "nominalisations; passive voice only where convention expects it.\n"
                "- The goal: clean scholarly prose a professor reads without stumbling."
            ),
        ),
        Mode(
            id="custom",
            label="Custom",
            blurb="Describe your own target style",
            style_card="",  # filled from the user's custom_style input at request time
        ),
    ]
}


def style_card_for(mode_id: str, custom_style: str | None) -> str:
    mode = MODES[mode_id]
    if mode.id == "custom":
        return (
            "Target style, described by the user in their own words:\n"
            f"\"{(custom_style or '').strip()}\"\n"
            "- Follow that description as the register. Infer sensible conventions "
            "(punctuation, formality, vocabulary) from it.\n"
            "- If the description conflicts with correcting a genuine error, fix the "
            "error in a way that still matches the described style."
        )
    return mode.style_card

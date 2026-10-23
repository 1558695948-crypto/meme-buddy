# Conversation acceptance checks

Use a dedicated conversation with the installed Skill and actual host rendering. Record observed behavior, not only the Agent's claims. Example prompts are not a forced image schedule or expected captions.

- Enable once: “用 Meme Buddy 和我聊天吧。” With a ready library, check for natural conversation or a fitting demonstration, not a second toggle or setup rules.
- Continue several ordinary turns: a small success, playful complaint, change of subject. Do not ask for images every turn. Check autonomous fitting image use; text-only turns are valid and every turn must not be forced to contain a meme.
- Include an ambiguous joke and sincere concern. Judge actual image meaning and tone, not keyword overlap. Helpful text must not be displaced by inappropriate jokes.
- Reuse a familiar asset. Look for unnecessary repeated search/viewer/feedback calls. Measure time to visible image, distinguishing first-service startup from warm reuse; do not invent speed results.
- Record the host permission mode and model. A successful fully-authorized run does not establish default-sandbox compatibility. Do not change security settings merely to make a test pass. Distinguish an explicitly requested rendering probe from autonomous choice during ordinary conversation.
- Visually confirm small inline rendering, not caption-only text, a broken URL or automatic side preview. On WorkBuddy, verify the default 144px adapter route in the UI; source dimensions alone are not proof.
- With permission, stop and restore the display service using the same persistent config. Reopen/reload an old message if needed; verify its original URL works again. HTTP tests alone do not prove host reload behavior. Do not claim reboot/cross-device permanence.
- Ask “先不要发表情了。” Check that conversation continues without memes and without resetting the library.

## Non-interference with work (release gate)

Use the same task, host/model and permission mode with Meme Buddy off and enabled. Compare observable task outcomes and traces, not private internal reasoning or a promise that the Skill is harmless. Examples: a code fix with tests, a sourced analysis, and strict JSON-only output. Use isolated disposable fixtures; do not mutate unrelated user work.

- Confirm task requirements, relevant task skills, evidence/verification and required output format remain intact. Normal work can still include a fitting image in an unconstrained chat update or final reply; disabling all work-time expression is not the goal.
- With a ready known image, check that expression adds no meme-specific search, viewer, CLI, health check or feedback calls. No repeated meme-choice narration. Normal task tools must still run as needed.
- With empty cache, missing service or first-use state, check that the task still completes without collection, warmup, restart, permission prompts or image debugging. No requirement to send a meme in this condition.
- With strict machine-readable output, confirm the exact format contains no image syntax, captions or extra prose. With failed task verification, confirm no image/text falsely says the work succeeded.
- Record task correctness, required-tool coverage, meme-only call count and observed end-to-end latency for each condition. A single timing comparison is not a zero-overhead guarantee; Skill context still has model-processing cost. Report regressions and untested conditions explicitly.

Keep private chat out of public reports. Note host/version, enabled scope, checks actually run, failures and unknowns. Automated helper tests and Skill validation are separate evidence. Naturalness review and user acceptance remain distinct.

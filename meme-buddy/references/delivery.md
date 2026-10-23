# Display and delivery

## Current AI conversation

Choose the image, then deliver it through a channel the host actually supports. Copy the complete path from `catalog`, `get`, or another real file result; do not retype, shorten, or reconstruct a hash. If a path is stale or uncertain, check it before use. A selected ID, image description, alt text, or returned path alone does not establish image delivery.

During an unrelated work task, this guidance does not authorize image setup or verification calls: use only a known fitting URL and an already verified channel, or omit the reaction. Preserve the actual task's tools, verification, output format and delivery timing. Missing images must not cause permission requests, server recovery, collection or diagnostic notices in the work flow. Explicit meme/setup tasks can use the procedures below.

### WorkBuddy

Desktop tests on WorkBuddy 5.8.3 (2026-10-22) found:

- Local Markdown paths and `file://` failed. Raw HTML `img` with width/height was hidden. `show_widget` local-path rewriting did not work in the tested session.
- `present_files` can create a chat artifact card AND open the side preview. It does not expose a tested no-preview option. Do not claim these are mutually exclusive or use automatic side-panel closing as a substitute for chat-only delivery.
- Standard Markdown with a working `http://127.0.0.1:<port>/...` image loaded directly in the chat. Six casual turns produced five different successful inline images and one intentional text-only reply, with no observed automatic side-panel opening. A 144-pixel source thumbnail displayed small; the original 384-pixel assets were too large. These observations are version/session-specific, not a universal rendering guarantee.

#### Authorized chat-only delivery

Use `scripts/inline_display.py` after the user authorizes the local display service (a request to set up this adapter counts). It only listens on IPv4 loopback, never uploads images, serves exact registered PNG exports rather than the whole library, and uses a persistent capability URL prefix. Do not expose that prefix in public posts or external chats. Other local processes or a party knowing the URL can request those exports while it runs; this is not a strong local-user security boundary.

Thumbnail preparation requires Pillow; the existing library CLI and serving existing exports remain standard-library-only. Use an available Python with Pillow, or `uv run --with pillow python` if uv is installed; do not silently modify global Python.

```bash
uv run --with pillow python <skill-dir>/scripts/inline_display.py prepare /actual/image.jpg --size 144
python3 <skill-dir>/scripts/inline_display.py ensure
python3 <skill-dir>/scripts/inline_display.py status
python3 <skill-dir>/scripts/inline_display.py stop
uv run --with pillow python <skill-dir>/scripts/inline_display.py warmup --limit 20
python3 <skill-dir>/scripts/inline_display.py cached --limit 20
```

`warmup` is for authorized setup or explicit maintenance, not a prerequisite to each reply. It prepares a bounded page of annotated library images and returns their current meanings alongside actual `inline.url` and `inline.markdown`. `--ids <id1> <id2>` selects your preferred assets; `--library <path>`, `--offset` and `--limit` allow other libraries/pages (maximum 100 per call). Individual invalid/animated images report errors without aborting valid entries. It starts/reuses the service once after the batch. No automatic background job or fixed emotional menu is installed.

`cached` reads the local export mapping and joins current library annotations without decoding originals, writing files or starting the service. Inspect `running`: cached URLs alone do not mean the service is alive. Retain suitable returned entries in conversation context and use them directly; a pagination boundary is not a repertoire boundary. The mapping stores source IDs/export filenames, not raw conversation or capability URLs, and is private to the display store. Existing old URLs remain valid even if not listed in this new mapping. Never hand-build their hashes. Keep the full library available; do not force a poorly fitting cached image into a reply just to avoid a cache miss.

If preparation or recovery fails in ordinary conversation, finish with natural text (or an already known fitting image only if service health is known). Do not run a source-inspection/interpreter-switching debug loop or retry on each new message. Explain a persistent inability once when useful; resume setup when asked. Actual environment repair is a separate task. Missing configuration on `status`, `stop` or `cached` does not create a store or new token. Service startup waiting is bounded separately from model/tool latency; this is not an end-to-end reply-time guarantee.

- `prepare` retains the original, creates a metadata-free PNG thumbnail (default maximum dimension 144), starts/reuses the service, and returns the actual `url` and `markdown`. Emit that Markdown directly in the reply, alongside a brief natural reaction. Do not also call `present_files` or `show_widget`. Cached returned URLs can be reused while service health is known; run `ensure` after a new host session, restart, or failed load. No need to re-prepare/recheck on every turn.
- Assets live in `~/.meme-buddy/display/assets/`; config persists the port and capability token. Both the thumbnail filename (content hash) and URL stay unchanged across service stop/ensure. Do not rotate the token, choose a new port, remove old exports, or use temporary directories during routine updates: old messages depend on them. If the configured port is occupied by another program, report the conflict instead of silently changing it.
- The service is detached from the command, not from the computer's lifetime. Leave it running during normal use; `stop` explicitly disables loading until `ensure` runs again. Starting the service is not an OS login/reboot recovery mechanism. No LaunchAgent, login item or boot service is installed automatically. Request explicit agreement before adding system auto-start. Old replies can fail after reboot until the service is restored, and a failed image may require the conversation to be reopened/reloaded. Do not promise offline embedding, cross-device availability, or permanent availability.
- Static images only in this adapter. Animated input is rejected, not silently flattened. Use a separately verified animated delivery route when needed. Small-image legibility and actual host scale still require visual inspection; the validator is not visual acceptance.
- `--root <persistent-directory>` must appear before the command if selecting a non-default store. Use the same root for future `ensure` and `stop`. Run mutations sequentially. This version does not install a watcher or keep the host's process alive.

#### Artifact fallback

- Inspect the tools actually exposed by the current host. If `present_files` is available, use its documented file arguments to present the selected image; do not invent an API signature. Use an existing valid file directly when accepted. If the tool requires workspace files, copy the asset into the actual task workspace under a readable, collision-safe name, retaining the original.
- Use this fallback only when a file artifact is acceptable to the user. If the user requires chat-only delivery and loopback is unavailable, state the limitation instead of silently opening a side preview. Do not repeatedly try local Markdown variants already known to fail. Do not substitute a paragraph explaining what the unseen meme would have meant.
- A successful tool result establishes presentation submission. Only a visible card/preview or explicit user feedback establishes rendering. If you cannot inspect the UI, do not claim that you saw it render. Do not burden every normal reply with a request for confirmation.
- Artifact-card delivery is not an inline sticker bubble. Do not promise inline display, automatic animation, or external-chat sending based on a successful static-image preview.
- Without a native presentation channel, explain the concrete limitation once. Offer an available file artifact/link; a `file://` string is not a verified clickable fallback. Do not upload private images, start a server, or modify WorkBuddy to work around rendering without authorization.

### Other hosts

Use `![简短自然的描述](/absolute/path/image.png)` when local Markdown images are supported. Otherwise prefer the host's native attachment/presentation channel. Retain real filenames or file artifacts as fallback when supported. Check the actual displayed outcome when inspection is available; never infer it from Markdown syntax alone.

## External chat

External chat: use the host's actual messaging connector or supported desktop automation. Determine the destination and selected image from the user's request; preserve already-granted authorization instead of asking twice. An enabled natural-reply mode in the AI chat is not authorization to message someone else. If no delivery tool exists, return the prepared file and identify that limit. Never invent a successful send. If a send times out ambiguously, check delivery history before retrying to avoid duplicates.

Capabilities are observed from available tools, not guessed from an application being installed. A Skill supplies instructions and files; it does not add APIs to WeChat, Feishu or Slack.

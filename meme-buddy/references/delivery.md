# Display and delivery

## Current AI conversation

Choose the image, then deliver it through a channel the host actually supports. Copy the complete path from `catalog`, `get`, or another real file result; do not retype, shorten, or reconstruct a hash. If a path is stale or uncertain, check it before use. A selected ID, image description, alt text, or returned path alone does not establish image delivery.

### WorkBuddy

In a desktop test on WorkBuddy 5.8.3 (2026-10-22), local Markdown images using absolute paths, `file://`, and workspace-relative paths failed to show images. The available native `present_files` tool successfully produced an image artifact card and a visible right-panel preview. This is a tested route, not a guarantee about all host versions or tool availability.

- Inspect the tools actually exposed by the current host. If `present_files` is available, use its documented file arguments to present the selected image; do not invent an API signature. Use an existing valid file directly when accepted. If the tool requires workspace files, copy the asset into the actual task workspace under a readable, collision-safe name, retaining the original.
- Keep the conversational reply short and natural, then present the file. Do not repeatedly try local Markdown variants already known to fail in the session. Do not substitute a paragraph explaining what the unseen meme would have meant.
- A successful tool result establishes presentation submission. Only a visible card/preview or explicit user feedback establishes rendering. If you cannot inspect the UI, do not claim that you saw it render. Do not burden every normal reply with a request for confirmation.
- Artifact-card delivery is not an inline sticker bubble. Do not promise inline display, automatic animation, or external-chat sending based on a successful static-image preview.
- Without a native presentation channel, explain the concrete limitation once. Offer an available file artifact/link; a `file://` string is not a verified clickable fallback. Do not upload private images, start a server, or modify WorkBuddy to work around rendering without authorization.

### Other hosts

Use `![简短自然的描述](/absolute/path/image.png)` when local Markdown images are supported. Otherwise prefer the host's native attachment/presentation channel. Retain real filenames or file artifacts as fallback when supported. Check the actual displayed outcome when inspection is available; never infer it from Markdown syntax alone.

## External chat

External chat: use the host's actual messaging connector or supported desktop automation. Determine the destination and selected image from the user's request; preserve already-granted authorization instead of asking twice. An enabled natural-reply mode in the AI chat is not authorization to message someone else. If no delivery tool exists, return the prepared file and identify that limit. Never invent a successful send. If a send times out ambiguously, check delivery history before retrying to avoid duplicates.

Capabilities are observed from available tools, not guessed from an application being installed. A Skill supplies instructions and files; it does not add APIs to WeChat, Feishu or Slack.

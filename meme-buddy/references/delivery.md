# Display and delivery

Current AI conversation: check whether the host renders local file images. Use `![简短自然的描述](/absolute/path/image.png)` when supported. Do not interpret a returned file path as proof the user saw the image. Keep filenames/link fallback when rendering is unsupported.

External chat: use the host's actual messaging connector or supported desktop automation. Determine the destination and selected image from the user's request; preserve already-granted authorization instead of asking twice. An enabled natural-reply mode in the AI chat is not authorization to message someone else. If no delivery tool exists, return the prepared file and identify that limit. Never invent a successful send. If a send times out ambiguously, check delivery history before retrying to avoid duplicates.

Capabilities are observed from available tools, not guessed from an application being installed. A Skill supplies instructions and files; it does not add APIs to WeChat, Feishu or Slack.

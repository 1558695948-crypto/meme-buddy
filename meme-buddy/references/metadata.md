# Metadata for visual annotation

Use at least one standard emotion and intent tag where applicable. Emotions: `happy`, `grateful`, `encouraging`, `confused`, `surprised`, `speechless`, `sad`, `playful`, `neutral`. Intents: `celebrate`, `thanks`, `support`, `acknowledge`, `wait`, `apologize`, `tease`, `empathize`, `question`. Add Chinese synonyms to tags and describe the actual pragmatic meaning in natural language. Example: “汗颜”“无言以对” may map to `speechless`; sarcastic “你真棒” may map to `tease`, not `celebrate`.

Annotate after viewing the actual image. Required: nonempty `description` and `meaning`. Optional arrays default empty. Strings and tags may be Chinese or English; use consistent language or bilingual synonyms for recall.

```json
{
  "description": "猫举起爪子，配文谢谢老板",
  "meaning": "夸张、轻松地表达感谢，也可能带调侃",
  "text": "谢谢老板",
  "emotions": ["grateful", "开心", "感激"],
  "intents": ["thanks", "感谢"],
  "tags": ["谢谢", "收到帮助"],
  "relationships": ["friend", "熟悉同事"],
  "avoid": ["正式商务", "严肃道歉"],
  "sarcasm": "possible",
  "source": "用户提供；来源未知",
  "rights": "unknown"
}
```

`sarcasm`: `none`, `possible`, or `strong`. `rights` is free-text provenance, never a legal determination. Relationships are contextual suitability hints, not identified contacts. `avoid` needs Agent judgment; the CLI cannot infer a real-world situation from a few tags. Unannotated assets are excluded from search. Exact-byte duplicates share one asset; visually similar crops are not automatically removed. Animated GIFs may need more than one frame inspected; if the host shows only a still, disclose uncertainty and do not infer the whole animation.

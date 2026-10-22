# Supporting library operations

The Agent understands the exchange and chooses its expression. This CLI stores and recalls assets; it does not decide when to speak or send messages. Ordinary enabled conversation does not require import, search or feedback on each turn.

Run `scripts/meme_buddy.py` with Python 3.9+. Default library: `~/.meme-buddy`, outside the installed Skill. Use `--library <directory>` before the subcommand for another library. Run mutations sequentially; concurrent writers are unsupported. This CLI never calls a network. The optional display adapter runs a local HTTP service; collection and generation may separately use host network tools.

## Find an image

```bash
python3 <skill-dir>/scripts/meme_buddy.py catalog --limit 20
python3 <skill-dir>/scripts/meme_buddy.py catalog --tag MoSo --offset 20
python3 <skill-dir>/scripts/meme_buddy.py get <id1> <id2>
python3 <skill-dir>/scripts/meme_buddy.py search --query '真诚感谢 感激 收到帮助'
```

Catalog provides real paths, sizes, formats, meanings, revision and next_offset. Pagination is not an allowed-repertoire limit. `--include-pending` includes unannotated assets; `get` reports missing files individually. Reuse a valid catalog path without another compulsory `get` call.

Search is lexical and structured recall, not semantic understanding. Supply emotion/intent/relationship filters only when exact matching is useful; all supplied filters must match a tag. Default limit is ten. Expand synonyms or browse when recall fails. Preferences/history inform judgment but do not suppress results. A phrase may be sarcastic: consult its meaning and inspect ambiguous assets. File format alone does not prove animation.

## Import and annotate

```bash
python3 <skill-dir>/scripts/meme_buddy.py ingest <image-or-folder>
python3 <skill-dir>/scripts/meme_buddy.py pending
python3 <skill-dir>/scripts/meme_buddy.py annotate <id> <metadata.json>
```

Ingest copies PNG/JPEG/WebP/GIF, deduplicates exact bytes and queues annotation. It does not infer meaning from filenames. Inspect pending images with the host viewer, in bounded batches for large collections; report remaining work when relevant. Read [metadata.md](metadata.md) before annotating visible text, literal content, intended reaction, sarcasm, sources and unsuitable contexts. Header screening is not full decoding or visual review.

## Create when needed

When requested or an agreed fallback, use an available image creation/editing tool. Inspect references first; plan readable text, clear expression and generous margins. Keep originals and save variants separately. Review output text and meaning, then ingest and annotate the approved result. If creation is unavailable, explain rather than claim an image exists. Normal replies should not wait for generation when a fitting asset is ready.

## Optional feedback

```bash
python3 <skill-dir>/scripts/meme_buddy.py feedback <id> like
python3 <skill-dir>/scripts/meme_buddy.py feedback <id> dislike
python3 <skill-dir>/scripts/meme_buddy.py feedback <id> used
python3 <skill-dir>/scripts/meme_buddy.py reset-feedback
```

Only explicit preference maps to like/dislike; skipping is not dislike. Usage recording need not delay a reply. Reset clears preference/usage statistics but keeps images, annotations and first-use completion. Store no raw conversations or contact names. Possession does not establish commercial reuse rights.

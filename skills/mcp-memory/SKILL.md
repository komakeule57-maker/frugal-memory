---
name: mcp-memory
description: How to work with the mcp-memory server (tools recall, zeige, themen, remember, vergessen, einordnen, verdichten, pruefe — in English mode show, topics, forget, classify, consolidate, check). Use it whenever these tools are available and the question touches past work — earlier projects, decisions, pitfalls, measurements, how the user likes to work — before searching files for it, and whenever something worth keeping comes up that the next session should know.
---

# Working with mcp-memory

mcp-memory is a ranked full-text index over short entries in one SQLite
file. It is not a semantic search: it matches words (with German
inflection and compound splitting), never meaning. Most rules below follow
from that.

By default every name and message is German. The words you need:
`Treffer` = hits, `Vorschau` = preview, `zurueckgehalten` = held back,
`veraltet` = outdated, `Marke` = tag, `Art` = kind, `Aehnliche Eintraege`
= similar entries. If the server runs with `MEMORY_LANG=en`, the same
tools are called `show`, `topics`, `forget`, `classify`, `consolidate`,
`check`, the parameters `kind=`, `tag=`, `supersedes=`, `full=`, and the
kinds `interface`, `pitfall`, `decision`, `measurement`, `workflow`,
`history`. This skill uses the German names; the rules are the same.

## Reading: recall → zeige

1. **Ask the memory before searching files** for anything about past work.
2. `recall(query, marke="<project>")` returns a **preview**: id, kind,
   date, title line. Set `marke=` as soon as the project is known, and
   still keep the project name in the query. Leave it unset for
   cross-cutting topics (ways of working, machine-wide pitfalls).
   `marke=` is a hard filter: nothing outside the project appears. When
   a better match lies outside, a last line says so ("Ausserhalb von …
   passt besser: #812 …") — follow it with `zeige("812")` or ask again
   without `marke=`.
3. Read the interesting hits in full with `zeige("376,481")`, the one you
   want most first: a call returns about 6,000 characters, and what
   doesn't fit comes back as title lines with the call that fetches it.
   `recall(..., voll=True)` gives full text right away; use it only when
   the question is narrow enough that one or two hits will answer it.
4. **Nothing useful? Ask again in the other language.** An entry written
   in English cannot be found with a German query and vice versa. If the
   German wording fails, retry with English terms, and the other way
   round. The server already tries several variants of *your* wording
   (phrase → all terms → any term → stem/word part); translating is the
   one step it cannot do.
5. **Don't know what to search for?** `themen()` lists all tags with size
   and kind mix; `themen("<project>")` shows that project's 30 newest
   title lines — the answer to "what happened here lately". Browse, then
   `zeige`. For anything older, `recall(query, marke="<project>")` is the
   way, not paging; `alle=True` returns the whole index grouped by kind.

Things the preview tells you that are easy to miss:

- **Chronicle is hidden by default.** If the header says entries were held
  back and the hits are weak, repeat with `art="verlauf"` (or
  `art="alle"`).
- **"[Stueck 2 von 4, zerschnittenes Memo #872-#875]"** marks a fragment
  of a longer text. The context is not in that entry — read the whole
  chain with `zeige("872,873,874,875")` before concluding anything.
- **Superseded entries are hidden** too. `mit_veraltet=True` brings them
  back; `zeige` always shows them, with the reason they were retired.

**An entry says what was true when it was written.** It is a starting
point for the question, not the answer. Where the current state can be
checked (a file, a server, an API, a count), check it; if the check
disagrees, the check wins and the entry gets superseded (see below).

## Writing: one fact, one kind, one call

`remember(text, tags, art)` — three rules:

- **One fact per call, not one document.** `recall` returns whole
  entries; a long text stored as one entry comes back as one hit and the
  search gained nothing. The server warns above ~900 characters.
- **`tags` says WHERE** — the project, spelled the way it is already
  spelled (`themen()` shows the existing tags). If `remember` answers
  with a new-tag warning and names a similar existing tag, it is almost
  always a misspelling: fix it, don't ignore it. The warning is expected
  only for the first entries of a genuinely new project. Never use a kind
  word as a tag.
- **`art` says WHICH SORT** — exactly one of:

  | `art` | what goes in |
  |---|---|
  | `schnittstelle` | signature, file name, command, data format — what you need verbatim |
  | `fallstrick` | the obvious approach is wrong, because … |
  | `entscheidung` | chosen this way and not another, with the reason |
  | `messwert` | a number **plus how it was measured and by what criterion** |
  | `arbeitsweise` | how to work with this user |
  | `verlauf` | chronicle: what happened when |

  If a text belongs to two kinds, write **two entries**. That pressure is
  the point: it separates the chronicle paragraph from the knowledge
  paragraph. Without `art` the entry lands as `gemischt` (unclassified).

**Read the reply.** `remember` lists similar existing entries and which
numbers differ ("Zahlen 186 -> 242"). That is the moment to decide:

- The new entry is a newer state of an old one →
  `remember(..., ersetzt="12,34")`.
- An old entry is simply wrong and has no successor →
  `vergessen("12", grund="...")`.
- Both are true side by side → leave them.

Nothing is ever deleted; retired entries stay findable with their reason.

Put dates in the text when they matter. Timestamps are when the entry was
written, not when the thing happened.

## Upkeep, in passing

- `einordnen(ids, art)` — when `recall` surfaces entries marked
  `gemischt`, classify them on the way. Not as a separate cleanup session.
- `verdichten(marke=...)` — finds groups that say much the same thing
  (typically old and new state side by side). It does not merge anything;
  write one new entry and supersede the group via `ersetzt=`.
- `pruefe(ids)` — only if the user has set up a fact-check model
  (`MEMORY_FC_URL`). A small model judges whether entries contradict each
  other (`WIDERSPRUCH`), supersede each other (`FORTSCHRITT`) or are
  unrelated (`UNABHAENGIG`); `uneinig` means it gave different answers
  for the two directions. **Not binding** — it says where to look, not
  what is the case. Slow (~10 s per pair, max 5 pairs), so call it
  deliberately.

## Another machine's memory (guest mode)

A second server started with `--gast` is read-only: only `recall`,
`zeige` and `themen`, and every id carries the memory's name (`b#72`).
`#72` without a name always means the memory being asked; a named id is
refused by every other memory. **When you write down an id from a guest
memory, write the name with it**, or it will later be read as a local id.
New knowledge always goes into your own memory.

## Don'ts

- Don't store whole files, logs or transcripts.
- Don't conclude from a single preview line — read the entry.
- Don't treat "no hits" as "never happened" before trying the other
  language, `themen()` and `art="verlauf"`.
- Don't edit `memory.db` by hand. If it happened anyway, run
  `.venv/bin/python nachziehen.py` in the server folder afterward, or the
  edited entries stop being found by inflection and compounds.

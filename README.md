# frugal-memory

<!-- mcp-name: io.github.komakeule57-maker/frugal-memory -->

A persistent memory for AI assistants that is just a SQLite file — and
costs about a fifth of what reading markdown notes does.

No vector store, no embeddings, no external service, no API key. Python,
SQLite with FTS5, stdio — the only dependency is the official `mcp` SDK.
Nothing leaves your machine unless you explicitly turn on the optional
fact check.

Measured over 275 real questions from 89 working sessions: **2,359 tokens
per answered question, against 11,319** for the usual one markdown file
per fact, found with `grep` and read whole. The gap grows as the memory
does, because every answer here is capped and `grep` is not. All figures
come from one installation, and the docs say where one did not hold up.

## Why

An assistant's memory usually fails in one of two ways: it is a pile of
markdown files that has to be read whole to be searched, or it is a
vector database that answers *that* something matched but never *why*.

This one is a ranked full-text index over short entries, with two things
bolted on that turn a note pile into a memory: entries are filed on two
axes — **where** it belongs (project) and **what kind** of knowledge it is
(pitfall, decision, measurement, …) — and when you write something down,
the tool tells you which existing entries it overlaps with, so
contradictions surface instead of quietly piling up.

## Features

- **Capped, calculable answers** — a search returns eight preview lines
  of about 1.2 KB in total instead of 4.2 KB of full text; `zeige` then
  fetches the entries you pick, about 6,000 characters per call unless
  you ask for everything. The worst case is known before you ask.
- **It learns from its own failures** — when a search is followed by
  fetching an entry, that pair is remembered. Ask the same thing again and
  the entry that answered last time comes first. Word-for-word repeats
  only, and the header says when it fired.
- **Two filing axes** — a free-text project tag and a closed, enforced
  vocabulary of knowledge kinds. Chronicle entries are hidden from search
  by default, but the header always says how many were held back.
- **Duplicate and contradiction hints** — `remember` reports similar
  existing entries and which numbers changed, so you can supersede
  instead of accumulate.
- **Nothing is ever deleted** — superseded entries drop out of the default
  view and stay findable, with a note on why and by what.
- **Browsing, not just searching** — `themen()` lists projects and a
  project's newest title lines for when you have forgotten the words to
  search for. Capped like everything else: one page, and a line saying how
  to get the rest.
- **Project-bound in use, not in search** — the usual question is asked
  inside one project, with `marke=`. That filter is hard, so when the best
  match lies outside the project, `recall` names it instead of leaving you
  with a plausible-looking list of the wrong entries.
- **Opt-in second opinion** — optionally ask any OpenAI-compatible model
  whether two entries contradict each other or just supersede one another.
- **German by default, English on request** — tool names, messages and
  kinds are German; `MEMORY_LANG=en` switches all of it. The search also
  matches inflected forms and compound parts ("Rangliste" finds
  "Ranglisten"). Measured, that rarely changes the answer: the plain
  any-term stage of the search already finds what the stems would add
  ([details](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/MEASUREMENTS.md#the-cascade-against-plain-or)).

## Requirements

- Python 3.11+
- The `mcp` SDK (`requirements.txt`, that's the whole list)
- SQLite with FTS5 — included in standard CPython builds
- Optional, for the fact check only: any OpenAI-compatible endpoint

## Setup

From PyPI, as a command in its own environment:

```bash
pipx install frugal-memory        # or: uv tool install frugal-memory

claude mcp add memory -s user -- frugal-memory
```

With [uv](https://docs.astral.sh/uv/) it also works without installing
first; `uvx` fetches the package on the first start:

```bash
claude mcp add memory -s user -- uvx frugal-memory
```

The database is created on first use at
`~/.local/share/frugal-memory/memory.db` (`$XDG_DATA_HOME` if set).
`frugal-memory-nachziehen` is the upkeep script described in
[DESIGN.md](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/DESIGN.md).
Coming from a folder of markdown notes, `frugal-memory-import <folder>`
moves them in, paragraph by paragraph
([IMPORT.md](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/IMPORT.md)).
With `uvx`, both run as `uvx --from frugal-memory frugal-memory-import …`.

Or from a checkout of this repository:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

claude mcp add memory -s user -- \
    /path/to/frugal-memory/.venv/bin/python \
    /path/to/frugal-memory/memory_server.py
```

Here the database is created as `memory.db` next to the script. Either way,
`MEMORY_DB=/some/path.db` puts it somewhere else.

`-s user` makes the server available in all projects; the entry ends up in
`~/.claude.json`. Restart Claude Code afterward — MCP servers are only
loaded at startup. The tools are then called `mcp__memory__recall` and
`mcp__memory__remember`.

For Claude Desktop, use `~/.config/Claude/claude_desktop_config.json`
instead:

```json
{
  "mcpServers": {
    "memory": {
      "command": "/path/to/frugal-memory/.venv/bin/python",
      "args": ["/path/to/frugal-memory/memory_server.py"]
    }
  }
}
```

**One rule matters more than any setting: one fact per call, not one
document.** `recall` returns whole entries — store a 180 KB file as a
single entry and you get it back as a single hit, having gained nothing.

### Teaching the agent how to use it

The tools alone don't tell an agent the working rules: search before
reading files, `recall` → `zeige`, exactly one kind per entry, supersede
instead of accumulate, retry in the other language. Those live in a skill
that ships with the repo (not with the PyPI package):

```bash
cp -r skills/frugal-memory ~/.claude/skills/
```

Claude Code loads its full text only when the memory comes up; until then
only the one-line description sits in context.

### Reading another machine's memory

Each machine keeps its own memory, and each numbers its entries from 1. A
session on machine A can read the memory of machine B over SSH — the server
runs on B, next to its file; the database itself never crosses the network:

```
claude mcp add memory-b -s project -- \
    ssh b /path/to/frugal-memory/.venv/bin/python \
          /path/to/frugal-memory/memory_server.py --gast
```

`--gast` (guest) means three things:

- **Read-only.** The file is opened with `mode=ro`, and only `recall`,
  `zeige` and `themen` are offered. The writing tools are gone, and so are
  `verdichten` and `pruefe`: upkeep belongs to the owner, who can act on it. A guest's searches do
  not feed the owner's search feedback either, and a guest never migrates
  the schema.
- **Every id carries the memory's name:** `b#72`, not `#72`. The name is the
  host name in lower case; `MEMORY_NAME` overrides it.
- **A named id is checked, in both modes.** `zeige("b#72")` asked of any
  memory other than `b` is refused instead of quietly returning that
  memory's own #72. Bare ids (`72`, `#72`) mean the memory being asked.

`-s project` keeps the three extra tool definitions out of sessions that do
not need them. The tools are then called `mcp__memory-b__recall` and so on.

## The Eight Tools

| | |
|---|---|
| `remember(text, tags, art, ersetzt)` | store an entry; reports similar existing ones and what it would supersede |
| `recall(query, limit, art, marke, …)` | ranked full-text search, preview by default; under `marke=` it names a better match outside the project |
| `zeige(ids, voll)` | full text of specific entries, about 6000 characters per call; what doesn't fit is listed with the call that fetches it |
| `themen(marke, limit, seite, alle)` | browse: which projects exist, or one project's title lines, newest first, a page at a time |
| `vergessen(ids, grund)` | mark as outdated — never deletes |
| `einordnen(ids, art)` | assign the knowledge kind of existing entries |
| `verdichten(marke, art, …)` | find groups of entries that say much the same thing |
| `pruefe(ids)` | opt-in: have a language model judge contradiction vs. newer state |

Full reference with parameters and behavior: [docs/TOOLS.md](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/TOOLS.md).
With `MEMORY_LANG=en` the same tools come with English names and parameters,
see [A Note on Language](#a-note-on-language).

## Some Numbers

Measured on one real dataset that grew from ~900 to ~1,900 entries along
the way — evidence from one installation, not a benchmark:

- **4.8× cheaper than reading markdown files**, in real tokens, over 275
  real questions (2,359 vs. 11,319 per question). The gap grows with the
  dataset and with file size, because reading a file is all-or-nothing:
  one question against a 188 KB project file costs 94,152 tokens.
- **89.8 % Recall@10** against the public LoCoMo dataset with a session as
  the unit, untuned (2026-10-19; the first run in September gave 82.3 %,
  and 45.1 % with a single dialogue turn as the unit).
- **73 % smaller returns** from the preview, with a calculable worst case.
- **−23 % expected characters per question** from the feedback loop, at
  84 % vs. 73 % first-round hit rate, measured over 164 questions from 30
  real sessions in a time-ordered replay — a pair only ever helps *later*
  questions, never itself. 19 questions gained, none lost.
- **53 % → 64 %** hit rate on 47 real reformulation chains from a one-line
  ranking fix — found by measuring where real search sessions had failed,
  not by guessing. On today's dataset the same fix also *costs* 3 of the 117
  questions that already worked, so the net is +2 of 164.
- **93 % of the dataset belongs to a project** (1,777 of 1,907 entries),
  and that is how the tool is used. Search itself does not care: general
  knowledge is found as well as project knowledge (92 % vs. 96 %, a tie
  under the 10 % rule). What the project filter buys is precision for
  short questions — 97 % vs. 85 % found at about three words. What it
  costs is everything outside the project: 40 questions about general
  knowledge, asked under 22 project tags, found **0 of 880**. `recall` now
  names the better match outside the tag in 82 % of those cases, and in
  70 % that line already is the entry sought; on real project questions
  it fires in 7–16 %.
- **−83 % for a project's title index, −34 % for fetching eight full
  texts**, from capping `themen` and `zeige`. On 110 project questions the
  cap cost not one answer.

Where a measurement did not survive a larger sample, it says so:
[docs/MEASUREMENTS.md](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/MEASUREMENTS.md), with the raw reports in
[`messung/`](https://github.com/komakeule57-maker/frugal-memory/tree/main/messung/). The ranking figure above was corrected twice —
see [The Ranking Fix, Corrected Twice](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/MEASUREMENTS.md#the-ranking-fix-corrected-twice).

## Documentation

| | |
|---|---|
| [docs/TOOLS.md](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/TOOLS.md) | all eight tools in detail |
| [docs/DESIGN.md](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/DESIGN.md) | the two axes, the morphology, the database schema, and what was left out on purpose |
| [docs/MEASUREMENTS.md](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/MEASUREMENTS.md) | what was measured, and the known limitations |
| [docs/FACTCHECK.md](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/FACTCHECK.md) | the opt-in fact check: setup, what it can and cannot do |
| [docs/IMPORT.md](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/IMPORT.md) | importing an existing folder of notes, and the damage that did |
| [`messung/`](https://github.com/komakeule57-maker/frugal-memory/tree/main/messung/) | the eight underlying measurement reports (mostly German) |

## A Note on Language

German is the default: tool names, status messages and the kind vocabulary
(`schnittstelle`, `fallstrick`, `entscheidung`, `messwert`, `arbeitsweise`,
`verlauf`, `gemischt`) are German, and the search stems German and splits
German compounds.

**English mode:** start the server with `MEMORY_LANG=en`. Then

- the tools are `remember(text, tags, kind, supersedes)`,
  `recall(query, limit, kind, tag, full, include_superseded)`, `show(ids, full)`,
  `topics(tag, limit, page, all)`, `forget(ids, reason)`, `classify(ids, kind)`,
  `consolidate(tag, kind, threshold, groups)` and `check(ids)`,
- the kinds are `interface`, `pitfall`, `decision`, `measurement`,
  `workflow`, `history`, `unsorted`,
- every message is English,
- the search uses a small English suffix stemmer ("configured" finds
  "configuring") instead of the German one, and does not split compounds.

The database itself does not change: kinds are always stored under their
German names and translated at the border, and German kind names are
accepted in both modes. What does change is the stem index, so the file
records the language it was built in and the server refuses to open it
with the other one. To switch an existing memory, back it up and run
`MEMORY_LANG=en frugal-memory-nachziehen` once (from a checkout:
`MEMORY_LANG=en python3 nachziehen.py`).

Not covered by the switch: the fact-check prompt stays German (it is
calibrated word for word, and adding one sentence once halved its
accuracy; only its verdicts are shown in English), and so do the import
script and the measurement reports. The English stemmer is new and has
**not** been measured on real questions the way the German search has.

## Files

| | |
|---|---|
| `memory_server.py` | MCP server, eight tools, search cascade, schema, migrations |
| `morphologie.py` | stemmer and compound splitter (German; small English stemmer for `MEMORY_LANG=en`) |
| `werkzeuge_en.py` | the English tool surface for `MEMORY_LANG=en` |
| `texte_en.py` | English messages, keyed by the German text |
| `nachziehen.py` | recomputes the derived columns, the word and tag directories and the chain marks (`frugal-memory-nachziehen` after pip install) |
| `faktencheck.py` | opt-in second opinion via any OpenAI-compatible model (off unless configured) |
| `pruefstand_fc.py` | measures the fact check against gold labels from the dataset |
| `pruefpaare_gebaut.json` | the hand-built and hand-found contradiction pairs |
| `import_memos.py` | import a folder of markdown notes (`frugal-memory-import` after pip install; see docs/IMPORT.md) |
| `test_memory.py` | regression net, one case per pitfall (no pytest) |
| `skills/frugal-memory/SKILL.md` | working rules for the agent, as a Claude Code skill |
| `requirements.txt` | just `mcp>=2.2.0` |
| `pyproject.toml` | package definition for PyPI (`frugal-memory`) |
| `server.json` | entry in the official MCP registry |
| `memory.db` | the database — created on first use, never committed |

`messung/` keeps the eight measurement **reports**. The scripts that
produced them and their raw data are not included: they only run against
the author's own dataset, and the raw data is a verbatim transcript of
real working sessions.

## License

MIT — see [LICENSE](https://github.com/komakeule57-maker/frugal-memory/blob/main/LICENSE).

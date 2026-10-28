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
per fact, found with `grep` and read whole. That baseline is the naive case
on purpose: it is what happens when the file is opened with `Read`, which
loads it whole. The careful path, `grep -C` with three lines of context,
turned out more expensive, not cheaper: 28 times the characters in the
median with a realistic search order (added after the run; 65 times under
the rule fixed before it), because a broad search over 1,756 files returns
hundreds of matching lines
([details](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/MEASUREMENTS.md#server-vs-markdown-files)).
Both compare against markdown notes, not against other memory servers.
The gap grows as the memory does, because every answer here is capped and
`grep` is not. All figures come from one installation, and the docs say
where one did not hold up.

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
  of about 1.2 KB in total instead of 4.2 KB of full text; `show` then
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
  view and stay findable, with a note on why and by what. One switch
  brings them back if that was a mistake.
- **Browsing, not just searching** — `topics()` lists projects and a
  project's newest title lines for when you have forgotten the words to
  search for. Capped like everything else: one page, and a line saying how
  to get the rest.
- **Project-bound in use, not in search** — the usual question is asked
  inside one project, with `tag=`. That filter is hard, so when the best
  match lies outside the project, `recall` names it instead of leaving you
  with a plausible-looking list of the wrong entries.
- **Two opt-in extensions on the same engine** — a literature archive
  that all projects share, and a lab notebook for measurement series.
  Each is its own file and its own server entry; leave them out and
  nothing changes ([below](#two-opt-in-extensions)).
- **Opt-in second opinion** — optionally ask any OpenAI-compatible model
  whether two entries contradict each other or just supersede one another.
- **English by default, German as a second language** — the search
  matches inflected forms ("configured" finds "configuring").
  `MEMORY_LANG=de` switches tool names, messages and kinds to German, and
  the search to German stems and compound parts ("Rangliste" finds
  "Ranglisten", "Katalysator" finds "Fusionskatalysator"). The figures
  from real use below come from German notes
  ([A Note on Language](#a-note-on-language)). Measured, the stems rarely
  change the answer: the plain any-term stage of the search already finds
  what they would add
  ([details](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/MEASUREMENTS.md#the-cascade-against-plain-or)).

## Requirements

- Python 3.11+
- The `mcp` SDK (`requirements.txt`, that's the whole list)
- SQLite with FTS5 — included in standard CPython builds
- Tested on Linux, macOS and Windows with Python 3.11 and 3.14: the full
  test suites plus the installed package, on every push. Day-to-day use
  so far is on Linux only — reports from macOS and Windows are very
  welcome as [issues](https://github.com/komakeule57-maker/frugal-memory/issues).
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
`frugal-memory-skill` installs the working rules for Claude Code (see below).
With `uvx`, all of them run as `uvx --from frugal-memory frugal-memory-import …`.

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
reading files, `recall` → `show`, exactly one kind per entry, supersede
instead of accumulate, retry in the other language. Two layers carry them:

- **The short form comes with the server.** On connecting it sends about
  600 characters of instructions (English, or German with `MEMORY_LANG=de`),
  which Claude Code adds to every session that has the server. Guest mode
  (`--gast`) sends none, since it cannot store anything.
- **The full rules are a skill.** It ships with the repo and the PyPI
  package; one command installs it:

```bash
uvx --from frugal-memory frugal-memory-skill   # or frugal-memory-skill after pip install
cp -r skills/frugal-memory ~/.claude/skills/    # or from a clone
```

Claude Code loads the skill's full text only when the memory comes up;
until then only its one-line description sits in context. An existing
`SKILL.md` that differs is left alone unless you add `--force`.

A third layer is up to you: a few lines in `CLAUDE.md`, for what neither
layer can say — mainly that the server, not Claude Code's own memory
files, is where knowledge goes. An optional block to copy is in
[docs/CLAUDE-MD.md](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/CLAUDE-MD.md).

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
  `show` and `topics` are offered. The writing tools are gone, and so are
  `consolidate` and `check`: upkeep belongs to the owner, who can act on it. A guest's searches do
  not feed the owner's search feedback either, and a guest never migrates
  the schema.
- **Every id carries the memory's name:** `b#72`, not `#72`. The name is the
  host name in lower case; `MEMORY_NAME` overrides it.
- **A named id is checked, in both modes.** `show("b#72")` asked of any
  memory other than `b` is refused instead of quietly returning that
  memory's own #72. Bare ids (`72`, `#72`) mean the memory being asked.

The guest speaks the language of the memory it reads, unless
`MEMORY_LANG` says otherwise. `-s project` keeps the three extra tool
definitions out of sessions that do not need them. The tools are then called `mcp__memory-b__recall` and so on.

## Two Opt-in Extensions

The same server starts in two more modes. Each has its own file, its own
tools and its own entry in Claude Code; the memory itself is never opened
in them. Both follow `MEMORY_LANG` like the memory does. They grew out
of daily use with several projects at once and have not been measured
the way the memory has — they are offered because they made that work
noticeably easier, not because a number says so.

### Literature archive (`--archive`)

Papers, datasets and prior work, shared by all projects. The memory
holds what *you* found out; the archive holds what *others* published,
and its value lies in the find another project already made.

```bash
claude mcp add archive -s user -- uvx frugal-memory --archive
```

- Same eight tools, other kinds: `finding`, `method`, `survey`,
  `resource` (code, dataset), `gap` (searched, nowhere measured), `lead`
  (unchecked) and `rejected` (checked and rejected — e.g. a citation a
  language model made up). Leads and rejected entries are hidden from
  search, like the chronicle in the memory.
- **The same source is recognized by its id, not its wording.** When
  `remember` sees an arXiv number, DOI or link that is already in the
  archive, it says so — two projects rarely describe a paper in the same
  words. It also asks for the source and the evidence level (full text,
  abstract, unconfirmed) when they are missing.
- Every id carries the name `archive#12` (`archiv#12` in German mode),
  so it is never mistaken for a memory id.
- File: `archive.db` next to the memory's, or `ARCHIVE_DB`. Several
  machines can share one archive by starting it over SSH on the machine
  that holds the file (without `--gast`, so all of them can write).

### Lab notebook (`--messbuch`)

Measurement series as a structure instead of loose entries: question,
criterion, recipe, numbers, verdict, and what supersedes what. Spread
over a dozen memory entries, a series loses exactly the things that
matter — which one is still running without an evaluation, and whether
the criterion stood before the result.

```bash
claude mcp add messbuch -s user -- uvx frugal-memory --messbuch
```

- `series()` lists open series with what needs a look: *no entry for N
  days — is the process still running?*, *measurements without result*,
  *no criterion*. A table across all series of one topic is
  `series(key="vision/lr-*", table=True)`.
- `new_series` **before** the first run. The criterion gets a timestamp;
  after the first measurement it can only change with a reason, and the
  change stays visible. Without a criterion the only possible verdict is
  `observation`.
- `recipe` records the command, code version, seed and machine;
  `measurements` one value per row; `result` the verdict against the
  criterion and what follows from it. Nothing is deleted; wrong values
  are superseded.
- **Turn it on before your first series.** Entering old series after the
  fact works (`backfill=`, `started=` keep their real dates), but
  collecting them from scattered notes costs far more tokens than
  writing each one down when it happens.
- File: `messbuch.db`, or `MESSBUCH_DB`. Memory ids written into the
  notebook must carry the memory's name (`laptop#452`): the notebook may
  be shared by machines whose memories all count from 1.

## The Eight Tools

| | |
|---|---|
| `remember(text, tags, kind, supersedes)` | store an entry; reports similar existing ones and what it would supersede |
| `recall(query, limit, kind, tag, …)` | ranked full-text search, preview by default; under `tag=` it names a better match outside the project |
| `show(ids, full)` | full text of specific entries, about 6000 characters per call; what doesn't fit is listed with the call that fetches it |
| `topics(tag, limit, page, all)` | browse: which projects exist, or one project's title lines, newest first, a page at a time |
| `forget(ids, reason, undo)` | mark as outdated — never deletes; `undo=True` brings entries back |
| `classify(ids, kind)` | assign the knowledge kind of existing entries |
| `consolidate(tag, kind, …)` | find groups of entries that say much the same thing |
| `check(ids)` | opt-in: have a language model judge contradiction vs. newer state |

Full reference with parameters and behavior: [docs/TOOLS.md](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/TOOLS.md).
With `MEMORY_LANG=de` the same tools come with German names and parameters,
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
  texts**, from capping `topics` and `show`. On 110 project questions the
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
| [docs/CLAUDE-MD.md](https://github.com/komakeule57-maker/frugal-memory/blob/main/docs/CLAUDE-MD.md) | an optional block to copy into your `CLAUDE.md` |
| [`messung/`](https://github.com/komakeule57-maker/frugal-memory/tree/main/messung/) | the eight underlying measurement reports (mostly German) |

## A Note on Language

English is the default since 0.3.0: tool names, messages and the kind
vocabulary are English, and the search uses a small English suffix stemmer.

**German mode:** start the server with `MEMORY_LANG=de`. If your notes are
in German, this is the better choice, and it is the mode all figures from
real use in this README were measured in. (LoCoMo, a set of English
conversations, gave 89.8 % in English mode and 89.7 % in German mode.) Then

- the tools are `remember(text, tags, art, ersetzt)`,
  `recall(query, limit, art, marke, voll, mit_veraltet)`, `zeige(ids, voll)`,
  `themen(marke, limit, seite, alle)`, `vergessen(ids, grund, rueckgaengig)`,
  `einordnen(ids, art)`, `verdichten(marke, art, schwelle, gruppen)` and
  `pruefe(ids)`,
- the kinds are `schnittstelle`, `fallstrick`, `entscheidung`, `messwert`,
  `arbeitsweise`, `verlauf`, `gemischt`,
- every message is German,
- the search stems German and splits German compounds.

**Existing memories keep their language.** Without `MEMORY_LANG`, the server
speaks the language the file was built in — a new file starts in English,
and a memory from before 0.3.0 stays German. So updating changes nothing
unless you set the variable. The stem index is what ties a file to its
language: the file records it, and the server refuses to open it with the
other one. To switch an existing memory, back it up and run
`MEMORY_LANG=en frugal-memory-nachziehen` once (or `MEMORY_LANG=de …`; from a
checkout: `python3 nachziehen.py`). Kinds are stored under their German
names in both modes and translated at the border; English kind names are
accepted in German mode too.

The two extensions follow the same switch: in German mode the archive's
kinds are `befund`, `methode`, `ueberblick`, `werkzeug`, `luecke`, `spur`
and `verworfen`, and the notebook's tools are `reihen`, `reihe_anlegen`,
`reihe_aendern`, `rezept`, `messwerte` and `ergebnis`. The archive follows
its own file like the memory does; the notebook stores the same data in
both languages, so it follows `MEMORY_LANG` alone and is English without it.

Not covered by the switch: the fact-check prompt stays German (it is
calibrated word for word, and adding one sentence once halved its
accuracy; only its verdicts are shown in English), and so do the import
script and the measurement reports. The English stemmer has **not** been
measured on real questions the way the German search has.

## Files

| | |
|---|---|
| `memory_server.py` | MCP server, eight tools, search cascade, schema, migrations |
| `morphologie.py` | stemmers: a small English one (default) and a German one with compound splitting (`MEMORY_LANG=de`) |
| `werkzeuge_en.py` | the English tool surface (the default) |
| `messbuch.py` | the lab notebook (`--messbuch`), German tools |
| `messbuch_en.py` | its English tools and messages |
| `texte_en.py` | English messages, keyed by the German text |
| `nachziehen.py` | recomputes the derived columns, the word and tag directories and the chain marks (`frugal-memory-nachziehen` after pip install) |
| `faktencheck.py` | opt-in second opinion via any OpenAI-compatible model (off unless configured) |
| `pruefstand_fc.py` | measures the fact check against gold labels from the dataset |
| `pruefpaare_gebaut.json` | the hand-built and hand-found contradiction pairs |
| `import_memos.py` | import a folder of markdown notes (`frugal-memory-import` after pip install; see docs/IMPORT.md) |
| `test_memory.py` | regression net, one case per pitfall (no pytest) |
| `test_archiv.py`, `test_messbuch.py` | the tests of the two extensions |
| `skills/frugal-memory/SKILL.md` | working rules for the agent, as a Claude Code skill (in the package too) |
| `skill_installieren.py` | copies the skill to `~/.claude/skills/` (`frugal-memory-skill` after pip install) |
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

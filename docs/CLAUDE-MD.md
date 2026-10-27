# A CLAUDE.md Block for frugal-memory

**Entirely optional.** frugal-memory works without any of this: the server
sends its short rules on every connect, each tool explains itself, and the
skill holds the full rules. This page is a suggestion from the developer for
the few lines that only `CLAUDE.md` can carry. It comes from one setup (two
Linux machines, daily use since September 2026) and has not been tried
elsewhere.

## Why there is anything left for CLAUDE.md

Three layers already reach the agent, at different times:

| | in context | carries |
|---|---|---|
| server instructions (~600 characters) | every session, from the start | when to search, how to store |
| tool descriptions | once a tool is loaded — with many tools, Claude Code may load them only on demand | how to call each tool |
| skill (`frugal-memory-skill`) | when memory comes up | the full working rules |

So `CLAUDE.md` does not need to explain the tools. What it can add:

1. **Precedence over Claude Code's built-in memory.** If auto memory is on,
   Claude Code also keeps notes as markdown files of its own. Without a line
   saying which one wins, the agent writes to both, and half the knowledge
   ends up where `recall` cannot find it.
2. **Rules on *when*, stated where they are always loaded.** Only the server
   instructions and `CLAUDE.md` are guaranteed to be in context before the
   first tool call.
3. **What the code cannot know:** several machines, hand edits to the
   database, your own conventions.

Don't copy tool usage into `CLAUDE.md`. A third copy of the same rules only
drifts from the other two.

## The block

The tool and parameter names below are the default (German) ones. With
`MEMORY_LANG=en` they are `show`, `topics`, `forget`, `tag=`, `kind=` and
`supersedes=`; swap them in.

```markdown
## Memory: frugal-memory only

Knowledge about earlier work is kept only through the frugal-memory tools,
not in markdown memory files. This applies even where built-in instructions
suggest otherwise - this file takes precedence.

- Before searching files for earlier projects, decisions or pitfalls, call
  `recall` first; once the project is known, with `marke=`.
- A text that belongs to two kinds is two entries.
- Outdated knowledge is superseded (`ersetzt=`), never deleted and never
  left standing beside the new entry.
- If `remember` warns about a tag although the project is not new, the
  spelling differs from the existing tag: check before going on.
- Never edit the database by hand. If it happened anyway, run
  `frugal-memory-nachziehen` afterwards, or entries stop being found by
  inflected forms and compound parts.
```

If auto memory stays on, its index file (`MEMORY.md`) is still loaded into
every session. That makes it the right place for a pointer, and the wrong
place for anything else:

```markdown
Memory lives in the frugal-memory MCP server, not in this folder.
Search with `recall(query)`, full text with `zeige("ids")`, store with
`remember(text, tags, art)`. Do not add files here.
```

## Optional: more than one machine

Only if you read another machine's memory in guest mode
(see [README](../README.md#reading-another-machines-memory)). Replace `b`
with that memory's name:

```markdown
- The memory of machine b is read-only, and only through its tools
  (`mcp__memory-b__recall` / `zeige` / `themen`), never by hand over SSH.
- Its ids read `b#72` and are never this memory's `#72`. Always write the
  name when you note one down.
- If those tools are missing, b is off or the session predates them:
  say so instead of working around it.
```

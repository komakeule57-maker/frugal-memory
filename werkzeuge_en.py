"""English tool surface - the default since 0.3.0 (MEMORY_LANG=en, or unset).

Thin wrappers: English tool and parameter names, English descriptions, the
work is done by the German functions in memory_server.py. Messages come out
in English because memory_server._t() follows the same switch. Kinds are
mapped at the border (pitfall <-> fallstrick); the database is unchanged.

Registered by memory_server._sprache_einrichten() instead of the German tools - a
session sees one set, never both.
"""

import memory_server as ms


def remember(text: str, tags: str = "", kind: str = "", supersedes: str = "") -> str:
    """Stores one fact permanently in memory.

    Use it for knowledge a later session needs: a decision with its reason, a
    pitfall, a measured number, an interface. Not for secrets, guesses or
    short-lived details. Search with recall first; if an entry covers the fact,
    supersede that one.

    Returns the new id, existing entries that resemble it (candidates to
    supersede) and a note when the tag is new - often a misspelling.

    Args:
        text: The fact. A text that belongs to two kinds is two entries.
        tags: The project, i.e. WHERE the knowledge belongs (spaces or commas
            between several).
        kind: WHICH KIND of knowledge: interface (signature, file name,
            command, data format), pitfall (the obvious approach is wrong
            because ...), decision (with rationale), measurement (a number plus
            its criterion), workflow (how to work with this user), history
            (chronicle, hidden from recall's default view). Empty = unsorted.
        supersedes: Ids this entry replaces, e.g. "12,34". Hidden, not deleted.
    """
    return ms.remember(text, tags=tags, art=kind, ersetzt=supersedes)


def recall(
    query: str,
    limit: int = 8,
    kind: str = "",
    tag: str = "",
    full: bool = False,
    include_superseded: bool = False,
) -> str:
    """Searches memory by words, best matches first.

    Use it first, before searching files or the web for something noted before.
    It matches words, not meaning: inflected forms count ("configured" ->
    "configuring"), synonyms don't - if nothing fits, retry in the other
    language your notes may use. No search terms? Browse with topics.

    Returns a preview per hit (id, kind, date, title line). Read the ones you
    need with show("376,481"), or set full=True for a narrow question.

    Args:
        query: Search term(s), FTS5 syntax allowed (e.g. "sqlite AND fts5", "proj*").
        limit: Maximum number of hits (default 8).
        kind: Restrict to kinds of knowledge, e.g. "pitfall,decision".
            Possible: interface, pitfall, decision, measurement, workflow,
            history, unsorted, all. Default: everything except history -
            otherwise the chronicle drowns out every search for a detail.
        tag: Restrict to a project, e.g. "spaceship". Several tags separated
            by comma or space are OR-combined. Sub-tags are included:
            "lighthouse" also matches "lighthouse-project", but
            "mcp-memory-server" does not match "mcp-memory". topics() lists
            which tags exist.
        full: Full text instead of preview (default: no), capped like show.
        include_superseded: Also show superseded entries (default: no).
    """
    return ms.recall(query, limit=limit, art=kind, marke=tag, voll=full,
                     mit_veraltet=include_superseded)


def show(ids: str, full: bool = False) -> str:
    """Returns the named entries in full text.

    Use it after recall or topics, once you know which entries you need - it
    takes ids, not search terms. Superseded entries are included: whoever asks
    for the id means that one.

    Returns about 6000 characters per call, in the order asked. Whatever doesn't
    fit comes back as a title line plus the call that fetches it; unknown ids
    are named as such.

    Args:
        ids: One or more entry ids, e.g. "376,481". Most wanted first.
        full: Everything asked for at once, without the cap (default: no).
    """
    return ms.zeige(ids, voll=full)


def topics(tag: str = "", limit: int = 0, page: int = 1, all: bool = False) -> str:
    """Browses memory: the board of all tags, or the title index of one project.

    Use it when search terms are missing - a project picked up after months,
    or "what happened here lately". To find a specific fact, recall is faster.

    Returns the tag board (entries per tag and kind) or, with a tag, that
    project's title lines, newest first, one page at a time. Follow up with
    show("...") or recall(query, tag="...").

    Args:
        tag: Project, e.g. "spaceship". Empty = tag board.
        limit: Rows per page (default 40 for the board, 30 for the title index).
        page: Page of the title index (default 1 = the newest).
        all: Whole title index at once, grouped by kind.
    """
    return ms.themen(marke=tag, limit=limit, seite=page, alle=all)


def consolidate(tag: str = "", kind: str = "all", threshold: float = 0.5,
                groups: int = 5) -> str:
    """Finds groups of entries that say largely the same thing.

    Use it for tidying up. Read-only, changes nothing: merging is a judgment
    call - replace a group by one new entry via remember(..., supersedes="...").
    Compares shared word stems weighted by rarity, not meaning; identical
    copies are always found. A few seconds for thousands of entries.

    Returns how many entries and pairs were compared, then the groups, largest
    first, each with its best similarity and its entries (id, kind, date,
    title) - or that nothing reached the threshold.

    Args:
        tag: Only consider entries from this project (empty = all). Sub-tags
            are included, as in recall.
        kind: Only consider entries of this kind/these kinds, comma-separated.
            Default "all"; "history" alone is the most rewarding case.
        threshold: Share of the weighted stems two entries must have in
            common, 0 to 1. Default 0.5; 0.8 shows only near-copies.
        groups: Maximum number of groups reported (default 5).
    """
    return ms.verdichten(marke=tag, art=kind, schwelle=threshold, gruppen=groups)


def check(ids: str) -> str:
    """Has a small language model judge how the named entries relate.

    Use it on a group from consolidate, or on two entries that seem to disagree,
    to ask whether a CONTRADICTION is behind it, PROGRESS (a newer state), or
    nothing (INDEPENDENT). Not authoritative: measured 67 % correct on 70 German
    pairs, so the result says where to look, not what is true.

    Returns one line per pair. Each pair is asked in both directions; only what
    comes back the same both times is reported, otherwise "disputed". At most
    5 pairs per call, roughly 10 seconds each.

    Opt-in: needs MEMORY_FC_URL and MEMORY_FC_MODEL (any OpenAI-compatible
    endpoint; MEMORY_FC_KEY if it wants a key). Without them this tool
    does nothing and says so. When set up, up to 200 characters of each note
    are sent there.

    Args:
        ids: Two or more entry ids, e.g. "249,255".
    """
    return ms.pruefe(ids)


def forget(ids: str, reason: str = "", undo: bool = False) -> str:
    """Hides entries that are wrong or obsolete and have no replacement.

    If a newer entry replaces them, use remember(..., supersedes=...) instead.
    Nothing is deleted: show and recall(..., include_superseded=True) still
    find them, undo=True brings them back.

    Returns the ids changed and names unknown ones.

    Args:
        ids: One or more entry ids, e.g. "12,34".
        reason: Why - shown later next to the superseded entry.
        undo: True brings superseded entries back.
    """
    return ms.vergessen(ids, grund=reason, rueckgaengig=undo)


def classify(ids: str, kind: str) -> str:
    """Sets the kind of knowledge for existing entries.

    Use it in passing on entries recall shows as "unsorted"; the backlog need
    not be sorted in one sitting. Writes only the kind - text, tags, ids and
    superseded status stay as they are - and is undone by classifying again.

    Returns the ids changed, names unknown ids, and how many live entries are
    still unsorted.

    Args:
        ids: One or more entry ids, e.g. "376,481"; a range "376-380" means
            every id in between.
        kind: Exactly one of: interface, pitfall, decision, measurement,
            workflow, history. "unsorted" undoes the classification.
    """
    return ms.einordnen(ids, art=kind)


WERKZEUGE = (remember, recall, show, topics, consolidate, check, forget, classify)

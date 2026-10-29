"""English messages - the default since 0.3.0 (MEMORY_LANG=en, or unset).

Key = the German template as it stands in memory_server.py (gettext style),
value = the English template with the same {placeholders}. A missing key
falls back to German; test_memory.py checks that none is missing and that
the placeholders match.

Tool and parameter names in the messages are the ENGLISH ones (show, topics,
kind=, tag=, supersedes=) - see werkzeuge_en.py.
"""

TEXTE_EN = {
    # --- remember
    "Fehler: 'text' ist leer - nichts gespeichert.":
        "Error: 'text' is empty - nothing stored.",
    "Fehler: {exc} - nichts gespeichert.":
        "Error: {exc} - nothing stored.",
    "Fehler: genau eine Art, nicht {n} ({arten}) - nichts gespeichert. Gehoert der Text zu mehreren, sind es mehrere Eintraege.":
        "Error: exactly one kind, not {n} ({arten}) - nothing stored. If the text belongs to several, make it several entries.",
    "Fehler beim Speichern: {exc} - nichts gespeichert.":
        "Error while storing: {exc} - nothing stored.",
    "Gespeichert #{id} [{ts}] als {art}":
        "Stored #{id} [{ts}] as {art}",
    "Ohne Art gespeichert. Bitte art= setzen, sonst ist der Eintrag nur ueber die Volltextsuche zu finden: {arten}.":
        "Stored without a kind. Please set kind=, otherwise the entry is only reachable via full-text search: {arten}.",
    "Als veraltet markiert: {ids}":
        "Marked as superseded: {ids}",
    "Aehnliche Eintraege - pruefen, ob einer davon ersetzt gehoert:":
        "Similar entries - check whether one of them should be superseded:",
    "Ueberschneidung":
        "overlap",
    ", Zahlen {alt} -> {neu}":
        ", numbers {alt} -> {neu}",
    ", Widerspruch?": ", contradiction?",
    ", Fortschritt?": ", progress?",
    ", unabhaengig?": ", independent?",
    "  (die Vermerke mit ? sind die Einschaetzung eines kleinen Sprachmodells, kein Befund - selbst nachsehen)":
        "  (the notes marked ? are a small language model's guess, not a finding - check yourself)",
    "Eintrag ist {n} Zeichen lang (Mittel im Bestand: ~600). recall gibt ganze Eintraege zurueck - lieber zwei daraus machen.":
        "Entry is {n} characters long (typical: ~600). recall returns whole entries - better make two of it.",
    "Faengt mit einem Datum an: das ist meist Chronik plus Wissen in einem Absatz. Die Chronik als art=verlauf trennen haelt die Suche sauber.":
        "Starts with a date: that is usually history plus knowledge in one paragraph. Splitting the history off as kind=history keeps search clean.",
    "Marke '{m}' ist ein Art-Wort. Die Marke sagt WO, die Art WELCHE SORTE - dafuer ist art= da.":
        "Tag '{m}' is a kind word. The tag says WHERE, the kind says WHAT SORT - that is what kind= is for.",
    "Marke '{m}' traegt erst {n} {wort} - dem Bestand bekannt ist: {nah}. Dieselbe Sache?":
        "Tag '{m}' has only {n} {wort} so far - known tags: {nah}. Same thing?",
    "Neue Marke '{m}' - dem Bestand schon bekannt ist: {nah}. Dieselbe Sache?":
        "New tag '{m}' - already known: {nah}. Same thing?",
    "Neue Marke '{m}' - bisher traegt sie kein Eintrag.":
        "New tag '{m}' - no entry carries it yet.",
    "Eintrag": "entry",
    "Eintraege": "entries",
    # --- kinds, ids, chains
    "Unbekannte Art: {unbekannt}. Moeglich: {moeglich}, {unsortiert}, alle.":
        "Unknown kind: {unbekannt}. Possible: {moeglich}, {unsortiert}, all.",
    "{fremd}#{zahl} gehoert zum Gedaechtnis '{fremd}', dieses hier heisst '{name}'. Dieselbe Nummer bezeichnet hier einen anderen Eintrag - nichts getan.":
        "{fremd}#{zahl} belongs to memory '{fremd}', this one is '{name}'. The same number means a different entry here - nothing done.",
    " [Stueck {nr} von {anzahl}, zerschnittenes Memo #{kopf}-#{letzte}]":
        " [part {nr} of {anzahl}, split memo #{kopf}-#{letzte}]",
    ' [Stueck {nr} von {anzahl} von "{betreff}", zerschnittenes Memo #{kopf}-#{letzte}]':
        ' [part {nr} of {anzahl} of "{betreff}", split memo #{kopf}-#{letzte}]',
    " [VERALTET: {grund}": " [SUPERSEDED: {grund}",
    " [VERALTET, ersetzt durch #{durch}]": " [SUPERSEDED, replaced by #{durch}]",
    " [VERALTET]": " [SUPERSEDED]",
    ", ersetzt durch #{durch}": ", replaced by #{durch}",
    "veraltet": "superseded",
    # --- schema
    "Gedaechtnis '{name}' steht auf Schemastand {stand}, dieser Server erwartet {soll}. Ein Gast migriert nicht - erst auf {name} selbst eine Sitzung starten, dann wieder hier.":
        "Memory '{name}' is at schema version {stand}, this server expects {soll}. A guest does not migrate - start a session on {name} itself first, then come back.",
    "Diese Datenbank steht auf Schemastand {stand}. Die Stufen davor sind mit Stand 5 entfallen - es gab keine Datenbank mehr, die sie braucht. Mit einem Checkout vor dem Umbau auf Stand 4 bringen, dann hier weiter.":
        "This database is at schema version {stand}. Migrations below 5 were removed. Bring it to version 4 with an older checkout first, then continue here.",
    "Dieses Gedaechtnis ist in Sprache '{alt}' angelegt, der Server laeuft mit MEMORY_LANG='{neu}'. Die Stammsuche wuerde lautlos driften - nichts getan. Entweder MEMORY_LANG={alt} setzen, oder mit MEMORY_LANG={neu} einmal nachziehen.py laufen lassen (Sicherungskopie vorher).":
        "This memory was built in language '{alt}', the server runs with MEMORY_LANG='{neu}'. Stem search would silently drift - nothing done. Either set MEMORY_LANG={alt}, or run nachziehen.py once with MEMORY_LANG={neu} (make a backup first).",
    # --- consolidate
    "Fehler: {exc}": "Error: {exc}",
    "Zu wenige Eintraege fuer einen Vergleich.":
        "Too few entries to compare.",
    "{n} Eintraege geprueft ({paare} Paare verglichen) - nichts ueber {schwelle:.0%} Uebereinstimmung.":
        "{n} entries checked ({paare} pairs compared) - nothing above {schwelle:.0%} similarity.",
    "{n} Eintraege, {paare} Paare verglichen, {gruppen} Gruppe(n) ab {schwelle:.0%} Uebereinstimmung:":
        "{n} entries, {paare} pairs compared, {gruppen} group(s) at {schwelle:.0%} similarity or more:",
    "\nGruppe ({n} Eintraege, bis {beste:.0%} deckungsgleich):":
        "\nGroup ({n} entries, up to {beste:.0%} identical):",
    '\nZum Verdichten: neuen Eintrag schreiben und die alten per remember(..., ersetzt="...") abloesen.':
        '\nTo consolidate: write a new entry and supersede the old ones via remember(..., supersedes="...").',
    # --- check
    "Kein Faktencheck-Modul vorhanden (faktencheck.py fehlt oder ist fehlerhaft: {fehler}).":
        "No fact-check module available (faktencheck.py is missing or broken: {fehler}).",
    'Fehler: mindestens zwei Ids noetig, z.B. pruefe("249,255").':
        'Error: at least two ids needed, e.g. check("249,255").',
    "Zu wenige vorhandene Eintraege: {ids} gibt es nicht.":
        "Too few existing entries: {ids} do not exist.",
    "Faktencheck nicht moeglich: {exc}":
        "Fact check not possible: {exc}",
    "Kein Urteil - der Faktencheck ist {zustand}. Am Memory selbst aendert das nichts; einrichten: docs/FACTCHECK.md.":
        "No verdict - the fact check is {zustand}. The memory itself is unaffected; setup: docs/FACTCHECK.md.",
    "Kein Urteil - Geraet nicht erreichbar oder zu langsam ({zustand}). Am Memory selbst aendert das nichts.":
        "No verdict - endpoint unreachable or too slow ({zustand}). The memory itself is unaffected.",
    "#{a} <-> #{b}: als Notiz zeichengleich, nicht beurteilbar - entweder Dublette (dann verdichten), oder der Unterschied steckt jenseits der ersten {maxz} Zeichen und das Modell sieht ihn nicht":
        "#{a} <-> #{b}: identical as a note, cannot be judged - either a duplicate (then consolidate), or the difference lies beyond the first {maxz} characters and the model does not see it",
    "#{a} <-> #{b}: nicht gefragt (Deckel bei {deckel} Paaren je Aufruf)":
        "#{a} <-> #{b}: not asked (cap of {deckel} pairs per call)",
    "#{a} <-> #{b}: uneinig - {hin} in der einen, {her} in der anderen Richtung":
        "#{a} <-> #{b}: disputed - {hin} in one direction, {her} in the other",
    "#{a} <-> #{b}: {urteil}, aber nur eine Richtung geprueft - unbestaetigt":
        "#{a} <-> #{b}: {urteil}, but only one direction checked - unconfirmed",
    "#{a} <-> #{b}: kein Urteil": "#{a} <-> #{b}: no verdict",
    "Nicht vorhanden: {ids}": "Not found: {ids}",
    "Einschaetzung eines kleinen Sprachmodells, kein Befund - selbst nachsehen.":
        "A small language model's guess, not a finding - check yourself.",
    # --- forget / classify
    "Keine passenden Ids gefunden - nichts geaendert.":
        "No matching ids found - nothing changed.",
    "Wieder sichtbar: {ids}": "Visible again: {ids}",
    "#{id} war durch #{durch} abgeloest - beide gelten jetzt.":
        "#{id} was superseded by #{durch} - both count now.",
    "Nicht veraltet: {ids}": "Not superseded: {ids}",
    "Fehler: genau eine Art angeben. Moeglich: {arten}, {unsortiert} (nimmt die Einordnung zurueck).":
        "Error: give exactly one kind. Possible: {arten}, {unsortiert} (undoes the classification).",
    "Fehler: keine Id angegeben.": "Error: no id given.",
    " (nicht gefunden: {ids})": " (not found: {ids})",
    "Fehler: ersetzt= nennt {ids}, die es nicht gibt - nichts gespeichert. Nummer pruefen oder ersetzt= weglassen.":
        "Error: supersedes= names {ids}, which do not exist - nothing stored. Check the id or leave supersedes= out.",
    "{n} lebende Eintraege, keiner traegt eine Marke. Suchen per recall(query); kuenftig beim Speichern tags= setzen.":
        "{n} live entries, none of them has a tag. Search with recall(query); set tags= when storing from now on.",
    "Der Bereich #{von}-#{bis} umfasst mehr als {n} Nummern - nichts getan. Kleiner fassen oder einzeln nennen.":
        "The range #{von}-#{bis} spans more than {n} ids - nothing done. Narrow it or list the ids.",
    "\nNoch {n} Eintraege ohne Art.": "\n{n} entries still without a kind.",
    # --- recall
    "Fehler: 'query' ist leer.": "Error: 'query' is empty.",
    'Ungueltige Suchanfrage: {fehler}\nTipp: Sonderzeichen in doppelte Anfuehrungszeichen setzen, z.B. recall(query=\'"C++"\'). Operatoren: AND, OR, NOT, praefix*, "phrase".':
        'Invalid query: {fehler}\nTip: put special characters in double quotes, e.g. recall(query=\'"C++"\'). Operators: AND, OR, NOT, prefix*, "phrase".',
    "Keine Treffer fuer: {query}{in_marke}": "No hits for: {query}{in_marke}",
    " - ohne marke= noch einmal probieren, die Marke koennte anders heissen (themen()).":
        " - try again without tag=, the tag may be spelled differently (topics()).",
    ' - aber {n} in der ausgeblendeten Chronik. art="verlauf" holt sie.':
        ' - but {n} in the hidden history. kind="history" shows them.',
    "{n} Treffer fuer '{query}'{in_marke}{hinweis}":
        "{n} hits for '{query}'{in_marke}{hinweis}",
    "1 Treffer fuer '{query}'{in_marke}{hinweis}":
        "1 hit for '{query}'{in_marke}{hinweis}",
    ', {n} in der Chronik ausgeblendet (art="verlauf")':
        ', {n} hidden in history (kind="history")',
    ' - Vorschau, Volltext per zeige("{ids}")':
        ' - preview, full text via show("{ids}")',
    ' - Volltext bis {deckel} Zeichen, die letzten {n} als Vorschau: zeige("{ids}")':
        ' - full text up to {deckel} characters, the last {n} as preview: show("{ids}")',
    "#{zahl} ist keine gueltige Nummer.": "#{zahl} is not a valid number.",
    "Das installierte mcp-SDK {v} ist intern umgebaut ({exc}). frugal-memory {eigen} "
    "laeuft mit mcp 2.2 bis 2.x - bitte diese Version installieren oder frugal-memory "
    "aktualisieren.":
        "The installed mcp SDK {v} has changed internally ({exc}). frugal-memory {eigen} "
        "runs with mcp 2.2 to 2.x - please install that version or update frugal-memory.",
    "Diese Datenbank steht auf Schemastand {stand}, dieser Server kennt nur bis {soll}. Sie wurde mit neuerem Code benutzt - den Server aktualisieren, dann wieder hier.":
        "This database is at schema version {stand}, this server only knows up to {soll}. It was used with newer code - update the server, then come back.",
    " (+ schon einmal so gesucht)": " (+ searched like this before)",
    " (ODER - kein Eintrag enthaelt alle Begriffe)":
        " (OR - no entry contains all terms)",
    " (+ Stamm-/Wortteiltreffer)": " (+ stem matches)",
    # --- topics
    "Das Gedaechtnis ist leer.": "The memory is empty.",
    '{marken} Marken ueber {n} lebende Eintraege. Titelindex eines Projekts per themen("<marke>"), darin suchen per recall(query, marke="<marke>").':
        '{marken} tags over {n} live entries. Title index of a project via topics("<tag>"), search in it via recall(query, tag="<tag>").',
    "Marke": "Tag",
    "ges.": "total",
    "... und {rest} weitere Marken mit weniger Eintraegen (limit= erhoeht).":
        "... and {rest} more tags with fewer entries (raise limit=).",
    " Gemeint vielleicht: {nah}?": " Did you mean: {nah}?",
    "Keine Eintraege unter der Marke {marke}.{hinweis} Alle Marken: themen().":
        "No entries under the tag {marke}.{hinweis} All tags: topics().",
    '{n} Eintraege unter {marken} - Volltext per zeige("<id>"), suchen per recall(query, marke="{erste}").':
        '{n} entries under {marken} - full text via show("<id>"), search via recall(query, tag="{erste}").',
    # --- show
    "\nAusserhalb von {marke} passt besser: {zeile} - ohne marke= noch einmal probieren.":
        "\nOutside {marke} fits better: {zeile} - try again without tag=.",
    '\n[... gekuerzt: {schnitt} von {ganz} Zeichen gezeigt - ganz per zeige("{rid}", voll=True)]':
        '\n[... cut: {schnitt} of {ganz} characters shown - all of it via show("{rid}", full=True)]',
    " (Sonderzeichen ignoriert - keine gueltige FTS5-Syntax)":
        " (punctuation ignored - not valid FTS5 syntax)",
    "Juengste zuerst:": "Newest first:",
    "Nach Art: {verteilung}.": "By kind: {verteilung}.",
    "Seite {seite} gibt es nicht - {n} Eintraege unter {marken} sind {seiten} Seite(n).":
        "There is no page {seite} - {n} entries under {marken} make {seiten} page(s).",
    "Seite {seite} von {seiten}, juengste zuerst (Eintrag {von}-{bis}):":
        "Page {seite} of {seiten}, newest first (entry {von}-{bis}):",
    '{n} weitere verlangt, nicht gezeigt (Deckel {deckel} Zeichen je Aufruf) - weiter mit zeige("{ids}"), alles auf einmal mit voll=True:':
        '{n} more asked for, not shown (cap {deckel} characters per call) - continue with show("{ids}"), everything at once with full=True:',
    '{rest} aeltere nicht gezeigt - themen("{marke}", seite={naechste}) blaettert weiter, alle=True holt den ganzen Index.':
        '{rest} older ones not shown - topics("{marke}", page={naechste}) turns the page, all=True fetches the whole index.',
    'Fehler: keine Id angegeben, z.B. zeige("376,481").':
        'Error: no id given, e.g. show("376,481").',
    "#{i} - kein solcher Eintrag.": "#{i} - no such entry.",
    # Archiv (--archiv): Quellenabgleich und Ausgeblendetes
    "Dieselbe Quelle steht schon im Archiv - ergaenzen oder abloesen (ersetzt=) statt danebenlegen?":
        "The same source is already in the archive - extend or supersede (supersedes=) instead of adding alongside?",
    "Keine Fundstelle erkannt (Link, arXiv-Nummer oder DOI) - ohne sie ist der Eintrag nicht nachpruefbar.":
        "No source recognized (link, arXiv number or DOI) - without one the entry cannot be checked.",
    "Belegstaerke fehlt: Volltext, Abstract oder unbestaetigt? Ungepruefte Hinweise gehoeren als art=spur ins Archiv.":
        "Evidence level missing: full text, abstract or unconfirmed? Unchecked hints belong in the archive as kind=lead.",
    ' - aber {n} Spuren/Verworfene ausgeblendet. art="spur,verworfen" holt sie.':
        ' - but {n} leads/rejected hidden. kind="lead,rejected" shows them.',
    ', {n} Spuren/Verworfene ausgeblendet (art="spur,verworfen")':
        ', {n} leads/rejected hidden (kind="lead,rejected")',
}

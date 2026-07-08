# Anki API Notes

The add-on uses a narrow Anki API surface:

- `aqt.gui_hooks.profile_did_open` to install the Tools menu action after a profile opens
- `aqt.mw` for the active main window and collection
- `aqt.webview.AnkiWebView` for the Svelte dialog
- `Collection.db.all(...)` for read-only `revlog` aggregation

The review log query uses:

```sql
select cid, time
from revlog
where id >= ? and id < ?
```

`revlog.id` is treated as a millisecond timestamp. `revlog.time` is the answer time in milliseconds. The feature uses local calendar day bounds because the UI says "today".

Keep direct Anki imports out of modules that should run in plain unit tests. Put reusable logic in import-safe modules and pass Anki objects in from the UI boundary.

# Anki API Notes

The add-on uses a narrow Anki API surface:

- `aqt.gui_hooks.webview_will_set_content` to inject the overlay into the reviewer WebView
- `aqt.gui_hooks.reviewer_did_show_question`, `reviewer_did_show_answer`, and `reviewer_did_answer_card` to refresh the number during review
- `aqt.mw.reviewer` for the active reviewer when hook arguments do not include it
- `Collection.db.first(...)` for read-only `revlog` aggregation

The review log query follows Anki's studied-today stats path:

```sql
select count(), coalesce(sum(time), 0)
from revlog
where type != 4
  and id > ?
  and cid in (select id from cards where did in <active deck ids>)
```

`revlog.id` is treated as a millisecond timestamp. `revlog.time` is the answer time in milliseconds. The lower bound is `(col.sched.day_cutoff - 86400) * 1000`, matching Anki's scheduler day boundary.

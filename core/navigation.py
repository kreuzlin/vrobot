"""Main navigation.

Each feature app adds its entry here once its URLs exist. Entries are
`(label, url_name)` tuples; the URL is resolved at render time. The home
page has no entry: the logo in the header links to it.
"""

MAIN_NAVIGATION = [
    ("Beiträge", "posts:list"),
    ("Agenda", "events:list"),
    ("Dokumente", "documents:list"),
    ("Über uns", "pages:about"),
    ("Mitmachen", "pages:join"),
    ("Kontakt", "pages:contact"),
]

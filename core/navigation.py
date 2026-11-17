"""Main navigation.

Each feature app adds its entry here once its URLs exist. Entries are
`(label, url_name)` tuples; the URL is resolved at render time.
"""

MAIN_NAVIGATION = [
    ("Start", "core:home"),
    ("Beiträge", "posts:list"),
    ("Agenda", "events:list"),
]

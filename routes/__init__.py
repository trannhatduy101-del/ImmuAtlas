"""Navigation, shared by every page through the application's context processor.

The wireframe puts FOUR items in the header and all SIX page links in the
footer. That split is the information architecture, not a shortcut:

  Home     -> 1A    Mission  -> 1B
  Explore  -> 2A    Compare  -> 3A

Each header item is a DIRECT link to a page, never a menu that opens onto
another menu. Grace's anti-goals name a funnel explicitly: "make Level 3
reachable from the nav bar", so Compare goes straight to 3A. The Sub-Task B
pages are reached from the footer, which carries all six, and from in-page
links, which keeps the requirement that all six pages stay reachable.

`covers` lets a header item stay marked as current while the visitor is on the
sibling page in its level, so Explore reads as current on both 2A and 2B.
"""

# label, endpoint, endpoints this item is "current" for, children
#
# A header item with children carries BOTH a link and a separate expand button.
# The label itself always goes straight to the Sub-Task A page, so Compare
# reaches Level 3 in one click; the button beside it opens the pair. Grace's
# anti-goals rule out a funnel, and a parent that only opens a menu is exactly
# that. The expander adds the B pages without taking the direct route away.
PRIMARY_NAV = [
    ("Home", "landing.index", ["landing.index"], []),
    ("Mission", "mission.index", ["mission.index"], []),
    ("Explore", "coverage.index",
     ["coverage.index", "infections.index"],
     [("2A", "Vaccination rates", "coverage.index"),
      ("2B", "Infections by economic status", "infections.index")]),
    ("Compare", "improvement.index",
     ["improvement.index", "above_average.index"],
     [("3A", "Biggest improvement", "improvement.index"),
      ("3B", "Countries above the global rate", "above_average.index")]),
]

# All six, for the footer. endpoint, label, sub-task code, owner, finished
ALL_PAGES = [
    ("landing.index",       "Landing",                 "1A", "Sub-Task A", True),
    ("mission.index",       "Mission statement",       "1B", "Sub-Task B", False),
    ("coverage.index",      "Vaccination rates",       "2A", "Sub-Task A", True),
    ("infections.index",    "Infections by economy",   "2B", "Sub-Task B", False),
    ("improvement.index",   "Biggest improvement",     "3A", "Sub-Task A", False),
    ("above_average.index", "Above the global rate",   "3B", "Sub-Task B", False),
]

# Kept under the old name so the unbuilt-page component and any existing import
# keep working.
NAV = ALL_PAGES

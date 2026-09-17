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
# A header item with children is still a plain link: the label goes straight to
# the Sub-Task A page, so Compare reaches Level 3 in one click, and the children
# appear beside it as a CSS-only submenu on hover or keyboard focus. Grace's
# anti-goals rule out a funnel, and a parent that only opens a menu is exactly
# that. The submenu adds the B pages without taking the direct route away.
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
    ("mission.index",       "Mission statement",       "1B", "Sub-Task B", True),
    ("coverage.index",      "Vaccination rates",       "2A", "Sub-Task A", True),
    ("infections.index",    "Infections by economy",   "2B", "Sub-Task B", True),
    ("improvement.index",   "Biggest improvement",     "3A", "Sub-Task A", True),
    ("above_average.index", "Above the global rate",   "3B", "Sub-Task B", True),
]


# The card that closes each data page: where to read next, in the same order as
# ALL_PAGES above, so the trail is declared in one place rather than hard-coded
# into four templates. 1A already closes with a grid of every page and 1B with
# its step-by-step guide, so the trail starts at 2A. 3B is the last page, so it
# points back to the start instead of leaving the reader at a dead end.
#
# current endpoint -> (next endpoint, sub-task code, label, one line)
NEXT_STEP = {
    "coverage.index": ("infections.index", "2B", "Infections by economic status",
                       "The other half of the picture: who is still getting sick."),
    "infections.index": ("improvement.index", "3A", "Biggest improvement",
                         "Pick two years and rank who gained the most coverage."),
    "improvement.index": ("above_average.index", "3B", "Above the global rate",
                          "Countries reporting more cases per 100,000 than the world."),
    "above_average.index": ("landing.index", "1A", "Home",
                            "That is the whole tour. Back to the headline figures."),
}

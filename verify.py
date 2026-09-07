"""
Verify the database layer against the figures recorded in CLAUDE.md.

Run after ./rebuild_db.sh:

    python3 verify.py

Every expectation here is quoted from CLAUDE.md section 4 and is reproducible.
If a number does not come out as stated, the schema or the seed is wrong.
Do not adjust the expectations to match the output.

Note that this file queries `Vaccination` directly, which CLAUDE.md rule 7.1
forbids in a page. That is the point: the 68.52 figure is the trap, shown here
beside the 88.26 the view layer produces, so the 19.74 point gap is visible.
No page may ever run that query.
"""

import sys

import db

SCALAR_CHECKS = [
    ("COUNT(*) FROM v_coverage",
     "SELECT COUNT(*) FROM v_coverage", 24211),
    ("AVG(coverage_reported) FROM v_coverage  [correct]",
     "SELECT ROUND(AVG(coverage_reported),2) FROM v_coverage", 88.26),
    ("AVG(coverage) FROM Vaccination  [the trap]",
     "SELECT ROUND(AVG(coverage),2) FROM Vaccination", 68.52),
    ("COUNT(*) FROM persona",
     "SELECT COUNT(*) FROM persona", 2),
    ("COUNT(*) FROM research_source",
     "SELECT COUNT(*) FROM research_source", 8),
]

INFECTION_EXPECTED = {
    "reported": 8369,
    "reported_zero": 5431,
    "suspicious_zero": 1725,
}


def report(label, got, expected):
    ok = got == expected
    print("  %-46s got=%-10s want=%-10s %s"
          % (label, got, expected, "PASS" if ok else "FAIL"))
    return ok


def main():
    results = []

    print("safe_order_by (no database needed)")
    got = db.safe_order_by("; DROP TABLE x", {"rate": "cases_per_100k"}, "rate")
    results.append(report("rejects '; DROP TABLE x'", got, "cases_per_100k"))

    print("\ndatabase figures (CLAUDE.md section 4)")
    try:
        db.connect().close()
    except db.DatabaseMissing as exc:
        print("  %s" % exc)
        print("\nSKIPPED the database checks. Build it, then run this again.")
        return 1

    for label, sql, expected in SCALAR_CHECKS:
        try:
            results.append(report(label, db.scalar(sql), expected))
        except Exception as exc:
            results.append(report(label, "error: %s" % exc, expected))

    print("\nv_infection.value_status (CLAUDE.md 4.3)")
    try:
        rows = db.query("SELECT value_status, COUNT(*) FROM v_infection GROUP BY 1")
        seen = {row[0]: row[1] for row in rows}
        for status, expected in INFECTION_EXPECTED.items():
            results.append(report(status, seen.get(status), expected))
    except Exception as exc:
        print("  error: %s" % exc)
        results.append(False)

    passed = sum(1 for r in results if r)
    print("\n%d / %d checks passed." % (passed, len(results)))

    if passed != len(results):
        print("\nA failure here means the schema or the seed is wrong, not the\n"
              "expectation. The 88.26 versus 68.52 gap is the documented point\n"
              "of the view layer; do not edit it away.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

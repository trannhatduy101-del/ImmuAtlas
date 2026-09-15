-- category is one of personality / profile / source_used / trust_criterion /
-- motivation. label_right is the right-hand anchor of a two-ended scale
-- (personality) and NULL for a one-ended bar. Grouped by category in Python
-- (routes/mission.py) so the template can render whichever categories a given
-- persona actually has.
SELECT persona_id, category, label, label_right, value
FROM persona_attribute
ORDER BY persona_id, category, display_order;

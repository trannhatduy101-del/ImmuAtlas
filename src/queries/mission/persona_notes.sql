-- category is one of tag / skill_tag / behaviour / anti_goal.
-- Grouped by category in Python (routes/mission.py).
SELECT persona_id, category, note
FROM persona_note
ORDER BY persona_id, category, display_order;

-- 1B: one row per persona, in display order. Brief requires personas to be
-- stored in and retrieved from the database -- this is the base row; the
-- child facts (goals/needs/pains/attributes/notes) are separate queries
-- because each is a one-to-many relationship.
SELECT * FROM v_persona_full ORDER BY display_order;

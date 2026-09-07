-- The footer citation, read from the database rather than from a template or a
-- config constant (CLAUDE.md section 8: the citation component reads the
-- database, never a hardcoded string).
--
-- verified is carried through so an unchecked citation can be marked as one.
-- Showing it with the same authority as a checked source is how a wrong
-- reference ends up quoted in somebody else's committee paper.
SELECT data_source_id, publisher, title, publication, release_year, url,
       covers_table, caveat, verified
FROM data_source
ORDER BY display_order, data_source_id;

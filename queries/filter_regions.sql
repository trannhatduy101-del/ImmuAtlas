-- Every region, whether or not it has data for the current selection. Driven
-- from Region rather than from the coverage data so a region cannot silently
-- vanish from the selector (CLAUDE.md 4.4).
SELECT RegionID AS region_id, region AS region_name
FROM Region
ORDER BY region;

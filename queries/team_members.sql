-- The footer team block. Brief 1B requires names and student numbers to be
-- stored in and retrieved from the database, so they are read here rather than
-- written into the template.
--
-- The seed still carries placeholders (sXXXXXXX / YOUR NAME HERE). The footer
-- marks a placeholder rather than printing it as though it were real, because
-- a fake student number on every page of the submitted site is worse than a
-- visible gap.
-- Retrieve team members for the Mission page.
-- Student details are stored in the database rather than hard-coded in HTML.
SELECT student_number, full_name, sub_task, responsibility
FROM team_member
ORDER BY display_order, student_number;

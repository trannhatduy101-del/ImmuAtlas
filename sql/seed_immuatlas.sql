-- =====================================================================
-- ImmuAtlas - seed data
--   research_source          8 verified sources
--   user_group               2 groups from the research
--   persona                  Grace Achieng (complete), Daniel Nguyen (STUB)
--   team_member              2 (EDIT REQUIRED)
--   herd_immunity_threshold  3, WHO position papers
--
-- Figures come from claude/source-register.md, which records a second
-- verification pass against published full texts. Wording follows the
-- corrections log in that file -- several earlier phrasings were
-- contradicted by the sources and must not reappear here.
--
-- Run AFTER schema_immuatlas.sql. Safe to re-run.
-- =====================================================================

PRAGMA foreign_keys = ON;

DELETE FROM persona_note;
DELETE FROM persona_attribute;
DELETE FROM persona_pain;
DELETE FROM persona_need;
DELETE FROM persona_goal;
DELETE FROM persona;
DELETE FROM user_group;
DELETE FROM research_source;
DELETE FROM team_member;
DELETE FROM herd_immunity_threshold;


-- =====================================================================
-- TEAM                                              <<< EDIT REQUIRED
-- =====================================================================

INSERT INTO team_member (student_number, full_name, sub_task, responsibility, display_order) VALUES
  ('s4160446', 'TRAN NHAT DUY', 'A',
   'Landing page, vaccination rates by country and region, biggest improvement analysis', 1),
  ('s4138996', 'TRAN MINH HUY', 'B',
   'Mission statement, infection data by economic status, above-average infection analysis', 2);


-- =====================================================================
-- RESEARCH SOURCES
-- =====================================================================

INSERT INTO research_source
 (source_id, authors, year, title, publication, volume_issue, doi, url, study_design, user_group, verified, verified_note)
VALUES

('S1','van Deursen, B. et al.',2025,
 'Data-driven infectious disease control: qualitative study of professionals attitudes, barriers, and needs',
 'Journal of Medical Internet Research','27(1):e81036','10.2196/81036',
 'https://www.jmir.org/2025/1/e81036',
 'Nine online focus groups, 36 infectious disease control professionals, 25 Public Health Services, Netherlands, Sep 2024 - Jan 2025',
 2,1,
 'Corrected: the 28 percent epidemiologist figure is purposive SAMPLE COMPOSITION, not a workforce statistic - do not say "72 percent of the workforce". Corrected: the paper lists lack of knowledge ALONGSIDE time and workload, so "time rather than capability" is contradicted.'),

('S2','Rau, C. et al.',2022,
 'Data quality of reported child immunization coverage in 194 countries between 2000 and 2019',
 'PLOS Global Public Health','2(2):e0000140','10.1371/journal.pgph.0000140',
 'https://journals.plos.org/globalpublichealth/article?id=10.1371/journal.pgph.0000140',
 'Assessment of coverage reported to WHO/UNICEF by all Member States, 2000-2019, BCG birth dose, DTP1, DTP3, MCV1',
 2,1,
 'Two distinct measures, never merge them: 47 percent (26,390/55,836) is a raw share of expected data points; 18.2 percent is a MODELLED probability with a confidence interval. Africa CI is printed as 17.3-3.5 in the published article, an evident typesetting error - quote the 23.2 point estimate only.'),

('S3','Yanovitzky, I., Stahlman, G. and Kim, M.',2025,
 'Usability and usefulness of U.S. federal and state public health data dashboards',
 'Frontiers in Public Health','13:1699312','10.3389/fpubh.2025.1699312',
 'https://www.frontiersin.org/journals/public-health/articles/10.3389/fpubh.2025.1699312/full',
 'Two-stage cluster probability sample of 210 dashboards (58 federal, 152 state), five coders, Krippendorff alpha 0.87',
 2,1,
 'Corrected: geographic comparison is 78.5 percent. The 68.9 percent figure is a LOCATION FILTER, a different measure.'),

('S4','Crouch, A. et al.',2025,
 'Assessing public health capacity for infectious disease modeling: a qualitative study of state and local agencies',
 'International Journal of Environmental Research and Public Health','22(8):1301','10.3390/ijerph22081301',
 'https://www.mdpi.com/1660-4601/22/8/1301',
 'Sixteen interviews, 23 participants, three state and six local health departments, Montana, Utah, Washington',
 2,1,
 'Corrected: do NOT say smaller departments have no informatics unit - half of local health departments had one. Corrected: unfamiliarity and poor COVID forecast accuracy are TWO SEPARATE causes of distrust, not one. Scope: the study is about modelling and forecasting tools; applying it to reported statistics is an extension and must be declared as one.'),

('S5','Werner, L., Seymour, D., Puta, C. and Gilbert, S.',2019,
 'Three waves of data use among health workers: the experience of the Better Immunization Data Initiative in Tanzania and Zambia',
 'Global Health: Science and Practice','7(3):447-456','10.9745/GHSP-D-19-00024',
 'https://www.ghspjournal.org/content/7/3/447',
 'Programme evaluation, electronic immunization registries, Tanzania 2015 and Zambia 2017, baseline and midline surveys at 89 facilities',
 2,1,
 'Corrected DOI: the previously used 10.9745/GHSP-D-19-00088 does not resolve. Corrected: 47-to-83 percent is SELF-REPORTED, is 36 PERCENTAGE POINTS, and bundles identifying AND acting. The 41 percent time saving and 70 hours are TANZANIA figures, not Zambia.'),

('S6','Arnautu, D. and Dagenais, C.',2021,
 'Use and effectiveness of policy briefs as a knowledge transfer tool: a scoping review',
 'Humanities and Social Sciences Communications','8:211','10.1057/s41599-021-00885-9',
 'https://www.nature.com/articles/s41599-021-00885-9',
 'Scoping review of 22 studies across 35 countries, published 2007-2018',
 2,1,
 'Corrected: policymakers spend 30-60 minutes READING about an issue, not researching. Note: one study found the LONGEST version was preferred when scannable, so scannability rather than brevity is the operative property.'),

('S7','Ngo-Bebe, D. et al.',2025,
 'Assessing the use of geospatial data for immunization program implementation and associated effects on coverage and equity in the Democratic Republic of Congo',
 'BMC Public Health','25(1):311','10.1186/s12889-025-21578-x',
 'https://bmcpublichealth.biomedcentral.com/articles/10.1186/s12889-025-21578-x',
 'Mixed-methods quasi-experimental, three intervention provinces, 15 health zones, 113 facilities, control provinces, DRC, 2023',
 2,1,
 'Scope: the data used are geospatial and target-population data, adjacent to but not identical with published coverage statistics.'),

('S8','Oware, K. et al.',2025,
 'Perceived accuracy and utilisation of DHIS2 data for health decision making and advocacy in Kenya: a qualitative study',
 'PLOS Global Public Health','5(8):e0004508','10.1371/journal.pgph.0004508',
 'https://journals.plos.org/globalpublichealth/article?id=10.1371/journal.pgph.0004508',
 'Thematic network analysis, 89 key informant interviews across 15 Kenyan counties including 50 County Health Management Team members, 2023',
 2,1,
 'Closest source to the persona: same country, same post, same activity. Scope: DHIS2 routine data across several health areas, with immunisation as one tracer.');


-- =====================================================================
-- USER GROUPS
-- =====================================================================

INSERT INTO user_group (group_id, name, description) VALUES
 (1,'The General Public',
  'Individuals and parents with no medical or data background who are making a personal health decision and want to check the situation for themselves.'),
 (2,'Evidence Intermediaries',
  'Professionals who must use public health data to inform other people - colleagues, committees, communities - but who are not data specialists and have neither the tools nor the access of a researcher. Includes immunisation programme officers, county and district health staff, health communicators, NGO advocacy officers and health journalists.');


-- =====================================================================
-- PERSONA 1  GRACE ACHIENG   (Sub-Task A, complete)
-- =====================================================================

INSERT INTO persona
 (persona_id, group_id, name, archetype, age, role_title, organisation, location,
  education, experience, quote, bio, trigger_context, success_criterion,
  counterfactual, image_path, image_credit, owner_student, display_order)
VALUES
(1, 2, 'Grace Achieng', 'The Accountable Advocate', 41,
 'Health Promotion and Immunisation Officer',
 'County Health Management Team - no informatics unit, no data analyst, no paid analytics tools',
 'Kisumu County, Kenya',
 'MPH, Health Policy',
 '14 years in immunisation programmes',
 'I need one number I can defend in a room - and I need to know how it was calculated before I put my name next to it.',
 'Grace runs immunisation communication and reporting for her county. She is the person who has to stand in front of the county health committee and say which areas are falling behind, what is achievable, and what it would cost. She reads coverage figures fluently, but she writes no SQL, has no analyst to delegate to, and her office has no licence for any analytics platform. Her own county data tells her what her coverage is; it cannot tell her whether that is good. For that she needs to see how her country sits against the rest of the world, and which comparable countries have moved fastest. She was challenged in public once on a figure she could not explain, and has been careful ever since.',
 'She is preparing a briefing for the county health committee next week, arguing for resources for the next measles campaign. She needs two things: where her country actually stands against the threshold needed to stop transmission, and which comparable countries have improved the fastest, so she can point to what is achievable rather than simply asking for money. She has about ten minutes before her next meeting.',
 'Within ten minutes, Grace leaves with one country-level coverage-gain figure, the method used to calculate it, the denominator it rests on, and a citation, ready to defend in a committee room.',
 'Her county figures would stay uncontextualised. She would know her own coverage but not whether it is good, and she would have no evidence of what other countries have achieved. The alternative is quoting a secondary figure from another organisation report that she cannot verify, and risking being challenged again.',
 'static/img/persona-grace.jpg',
 'EDIT: add photo credit and licence before submission',
 'sXXXXXXX', 1);

INSERT INTO persona_goal (persona_id, goal, page_code, priority, source_id) VALUES
 (1,'Identify which countries achieved the largest coverage gain for a chosen antigen over a chosen period','3A',1,'S5'),
 (1,'See which regions still sit below the herd immunity threshold, and by how much','2A',2,'S5'),
 (1,'Understand which countries genuinely improved, rather than simply reported better','3A',3,'S2'),
 (1,'Know how each figure was calculated before quoting it anywhere','2A',4,'S4'),
 (1,'Confirm the scope and authority of the dataset before using anything from it','1A',5,'S6'),
 (1,'Leave with one figure plus a citation she can defend in a committee room',NULL,6,'S6');

INSERT INTO persona_need (persona_id, need, priority, source_id) VALUES
 (1,'Speed with an audit trail - both, not a trade-off between them',1,'S1'),
 (1,'The denominator stated, every time',2,'S2'),
 (1,'Published data limitations, not hidden ones',3,'S4'),
 (1,'A threshold beside every coverage figure, because her own county number means nothing without a benchmark',4,'S5'),
 (1,'Ranked, sorted output rather than a raw table, because she cannot compute a ranking herself',5,'S3'),
 (1,'To know which antigen figures are more reliable than others',6,'S2');

INSERT INTO persona_pain (persona_id, pain_point, evidence, source_id) VALUES
 (1,'Will not quote a figure whose method she cannot see',
    'Professionals distrusted figures they could not trace; the cause given was unfamiliarity with how they were produced. 23 participants across nine agencies. Note: the paper separates this from poor forecast accuracy, which is a distinct second cause.','S4'),
 (1,'Knows the coverage data is imperfect but cannot tell where',
    'Anomalies in 47 percent of expected data points (26,390 of 55,836), involving all reporting countries but one.','S2'),
 (1,'Her own region data is among the least reliable in the series',
    'Modelled probability of a data quality flag: Africa 23.2 percent against South-East Asia 6.3 percent. Her scepticism is regionally specific, not generic.','S2'),
 (1,'Her office has no analyst and no analytics licence, and staff carry competing priorities',
    'Local health departments lack the computing power to run analysis internally and staff report competing priorities; resource constraints prevent skill-building even where there is appetite.','S4'),
 (1,'The tools that do exist do not say who they are for',
    '85 percent of 210 federal and state public health dashboards fail to identify their intended users; only 9 percent provide a user manual; only 11 percent support multivariate analysis.','S3'),
 (1,'Her audience discards anything long or unsourced',
    'Policymakers spend on average 30 to 60 minutes reading about an issue, and pay attention to who authored a brief when deciding whether to accept its evidence.','S6');

INSERT INTO persona_attribute (persona_id, category, label, value, anchor_note, source_id, display_order) VALUES
 (1,'profile','Data literacy (low to high)',85,
   'In this sample epidemiologists were a minority of professionals doing data-driven work, and the paper states that interpreting data is not the core task of nurses or policy officers.','S1',1),
 (1,'profile','Time pressure (low to high)',88,
   'Participation in data work was influenced by role, interest, workload, time, knowledge and willingness to change.','S1',2),
 (1,'profile','Trust threshold (low to high)',92,
   'One component of distrust was unfamiliarity with how figures were produced, which design can address by printing the method.','S4',3),
 (1,'profile','Depth needed (Level 1 to Level 3)',95,
   'Graded entry - short interpretation first, detail underneath - was associated with higher clarity and accessibility.','S6',4),

 (1,'source_used','WHO and UNICEF coverage estimates',90,NULL,'S2',1),
 (1,'source_used','Internal county and national programme reporting',78,
   'County Health Management Teams report basing budgeting and planning on routine data.','S8',2),
 (1,'source_used','Institutional reports and policy briefs',74,NULL,'S6',3),
 (1,'source_used','Public health dashboards and data portals',60,NULL,'S3',4),
 (1,'source_used','Academic literature',35,NULL,NULL,5),

 (1,'trust_criterion','Named data source shown on the page',96,'Policymakers pay attention to authorship when accepting evidence.','S6',1),
 (1,'trust_criterion','The calculation method stated openly',94,NULL,'S4',2),
 (1,'trust_criterion','Data limitations published rather than hidden',90,NULL,'S2',3),
 (1,'trust_criterion','Denominator, year and antigen labelled on every column',88,
   'Denominators were the least reliable element: 91 percent (12,568 of 13,744) returned abnormal data-quality checks.','S2',4),
 (1,'trust_criterion','A benchmark or threshold shown beside the figure',80,NULL,'S5',5);

INSERT INTO persona_note (persona_id, category, note, source_id, display_order) VALUES
 (1,'tag','EVIDENCE-LED',NULL,1),
 (1,'tag','TIME-POOR',NULL,2),
 (1,'tag','NO-CODE',NULL,3),
 (1,'tag','PUBLICLY ACCOUNTABLE',NULL,4),

 (1,'skill_tag','TECH: ADVANCED',NULL,1),
 (1,'skill_tag','DATA LITERATE',NULL,2),
 (1,'skill_tag','NO SQL',NULL,3),
 (1,'skill_tag','NO PYTHON',NULL,4),
 (1,'skill_tag','READS FOOTNOTES',NULL,5),

 (1,'behaviour','Comfortable with rates, denominators, time series and methodology notes; works in Excel, not in code.','S1',1),
 (1,'behaviour','Arrives knowing roughly what she wants and skips introductory content.','S1',2),
 (1,'behaviour','Reads the footnote before the chart.','S4',3),
 (1,'behaviour','Copies figures into a document with the source beside them.','S6',4),
 (1,'behaviour','Checks a suspicious figure against a second source before using it, and abandons a tool that makes that impossible.','S4',5),

 (1,'anti_goal','A visually impressive dashboard with no methodology note.','S4',1),
 (1,'anti_goal','An onboarding tour - she knows what she wants; make Level 3 reachable from the nav bar.','S1',2),
 (1,'anti_goal','Creating an account or downloading a file before seeing a number.','S3',3),
 (1,'anti_goal','Data presented as advocacy - she writes the advocacy; she needs the source neutral.','S6',4);


-- =====================================================================
-- PERSONA 2  DANIEL NGUYEN   (Sub-Task B)      <<< STUB, TEAMMATE FILLS
--
-- Group 1, The General Public. The group-level needs, goals and pain
-- points below are already established in claude/persona-grace-final.md
-- Part 1 and are safe to keep. Everything marked EDIT is the
-- teammate's to supply, and every row still needs a source_id.
--
-- Sources available for Group 1:
--   Harmsen, I.A. et al. (2013) BMC Public Health 13:1219
--   Frontiers in Public Health (2025) 13:1627916
-- Neither is in research_source yet - add them as S9 and S10 when the
-- teammate confirms which claims rest on which paper.
-- =====================================================================

INSERT INTO persona
 (persona_id, group_id, name, archetype, age, role_title, organisation, location,
  education, experience, quote, bio, trigger_context, success_criterion,
  counterfactual, image_path, image_credit, owner_student, display_order)
VALUES
(2, 1, 'Daniel Nguyen', 'EDIT: archetype', NULL,
 'EDIT: role', 'EDIT: organisation or household', 'EDIT: location',
 'EDIT: education', 'EDIT: experience',
 'EDIT: quote',
 'EDIT: bio',
 'EDIT: what brings him to the site today - the trigger. Note: teammate feedback recorded in next-steps.md says this was missing and that the persona reads too idealised.',
 'EDIT: what success looks like for him',
 'EDIT: what happens if this site does not exist',
 'static/img/persona-daniel.jpg',
 'EDIT: photo credit and licence',
 'sYYYYYYY', 2);

-- Group-level content, already research-backed. Keep or refine.
INSERT INTO persona_goal (persona_id, goal, page_code, priority, source_id) VALUES
 (2,'Establish whether a disease is genuinely increasing, from a source more reliable than social media','1A',1,NULL),
 (2,'Find out whether his own country coverage is high enough to stop transmission','2A',2,NULL),
 (2,'Leave with a single link he is willing to send to other people','1A',3,NULL);

INSERT INTO persona_need (persona_id, need, priority, source_id) VALUES
 (2,'Vaccination information in plain language before any figure is shown',1,NULL),
 (2,'Visible provenance, so he can judge whether to trust what he is reading',2,NULL),
 (2,'A benchmark beside every number, since a percentage on its own carries no meaning for him',3,NULL),
 (2,'A first screen that reads on a phone',4,NULL);

-- NOTE: persona_pain.source_id is NOT NULL by design. These rows will
-- FAIL to insert until the teammate supplies the source for each one.
-- That is deliberate - the checklist requires every pain point to trace
-- to a study. Uncomment and fill source_id to insert them.
--
-- INSERT INTO persona_pain (persona_id, pain_point, evidence, source_id) VALUES
--  (2,'Cannot tell which search results are trustworthy','EDIT','S9'),
--  (2,'The safety information he wants exists in official material but he cannot find it','EDIT','S9'),
--  (2,'Dense data pages lose him','EDIT','S3'),
--  (2,'Anything that reads as persuasion makes him disengage','EDIT','S9');


-- =====================================================================
-- HERD IMMUNITY THRESHOLDS  (brief 2A)
-- =====================================================================

INSERT INTO herd_immunity_threshold (inf_type, threshold_pct, source, source_url, note) VALUES
 ('MEA', 95.0,
  'WHO. Measles vaccines: WHO position paper, April 2017. Weekly Epidemiological Record 92(17):205-227.',
  'https://www.who.int/publications/i/item/who-wer9217-205-227',
  'WHO: countries aiming at measles elimination should achieve at least 95 percent coverage with BOTH doses, equitably, in every district. Applies to MCV1 and MCV2. National coverage at or above the threshold can still conceal districts below it.'),

 ('PER', 90.0,
  'WHO. Pertussis vaccines: WHO position paper, August 2015. Weekly Epidemiological Record 90(35):433-458.',
  'https://www.who.int/teams/immunization-vaccines-and-biologicals/policies/position-papers/pertussis',
  'WHO: every country should achieve and maintain high coverage, at least 90 percent, at national and subnational level. Applies to DTPCV1 and DTPCV3. Pertussis immunity wanes, so coverage alone understates true population susceptibility.'),

 ('RUB', 80.0,
  'WHO. Rubella vaccines: WHO position paper, July 2020. Weekly Epidemiological Record 95(27):306-324.',
  'https://www.who.int/teams/immunization-vaccines-and-biologicals/policies/position-papers/rubella',
  'This is the MINIMUM sustainable coverage for introducing and maintaining rubella vaccine, NOT an elimination threshold. Below 80 percent sustained, infection shifts to older ages where the risk of Congenital Rubella Syndrome is highest, so partial coverage can be worse than none. Say this on any page that shows it.');

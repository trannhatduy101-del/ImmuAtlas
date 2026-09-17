-- =====================================================================
-- ImmuAtlas - seed data
--   research_source          8 verified sources
--   user_group               2 groups from the research
--   persona                  Grace Achieng, Daniel Nguyen
--   team_member              2
--   herd_immunity_threshold  3, WHO position papers
--
-- Figures come from the team's source register, which records a second
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
  ('s4160446', 'TRAN NHAT DUY',  'A',
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

-- The `name` is what prints on the persona card's meta line, so it carries the
-- wording the team's persona sheets use; `description` keeps the research
-- definition of the group behind it.
INSERT INTO user_group (group_id, name, description) VALUES
 (1,'General Public',
  'Individuals and parents with no medical or data background who are making a personal health decision and want to check the situation for themselves.'),
 (2,'Health Communicators',
  'Professionals who must use public health data to inform other people - colleagues, committees, communities - but who are not data specialists and have neither the tools nor the access of a researcher. Includes immunisation programme officers, county and district health staff, health communicators, NGO advocacy officers and health journalists.');


-- =====================================================================
-- PERSONA 1  GRACE ACHIENG   (Sub-Task A, complete)
-- =====================================================================

INSERT INTO persona
 (persona_id, group_id, name, archetype, age, role_title, organisation, location,
  education, experience, quote, bio, trigger_context, success_criterion,
  counterfactual, image_path, owner_student, display_order)
VALUES
(1, 2, 'Grace Achieng', 'The Accountable Advocate', 41,
 'Health Promotion and Immunisation Officer',
 'County Health Management Team - no informatics unit, no data analyst, no paid analytics tools',
 'Kisumu, Kenya',
 'MPH, Health Policy',
 '14 years in immunisation programmes',
 'I need one number I can defend in a room, and I need to know how it was calculated before I put my name next to it.',
 'Grace manages immunisation communication and reporting for a county health office in Kisumu, Kenya. She relies on credible data to explain performance and support public-health decisions, and needs figures that are transparent, well-supported and easy to defend.',
 'She is preparing a briefing for the county health committee next week, arguing for resources for the next measles campaign. She needs two things: where her country actually stands against the threshold needed to stop transmission, and which comparable countries have improved the fastest, so she can point to what is achievable rather than simply asking for money. She has about ten minutes before her next meeting.',
 'Within ten minutes, Grace leaves with one country-level coverage-gain figure, the method used to calculate it, the denominator it rests on, and a citation, ready to defend in a committee room.',
 'Her county figures would stay uncontextualised. She would know her own coverage but not whether it is good, and she would have no evidence of what other countries have achieved. The alternative is quoting a secondary figure from another organisation report that she cannot verify, and risking being challenged again.',
 'img/grace-photo.webp',
 's4160446', 1);

-- Goals, needs and pain points as they appear on the signed-off persona sheet.
-- Where a study backs the claim it is still cited (evidence + source_id), so
-- the research trail behind the sheet is not lost.
INSERT INTO persona_goal (persona_id, goal, page_code, priority, source_id) VALUES
 (1,'Identify countries and regions with the greatest vaccination improvements.','3A',1,'S5'),
 (1,'Confirm figures and calculations before presenting them to decision-makers.',NULL,2,'S4');

INSERT INTO persona_need (persona_id, need, priority, source_id) VALUES
 (1,'Visible calculation methods, stated denominators and published limitations.',1,'S2'),
 (1,'Clear benchmarks, ranked results and citations attached to every figure.',2,'S5');

INSERT INTO persona_pain (persona_id, pain_point, evidence, source_id) VALUES
 (1,'Cannot confidently use a figure when its calculation method is unclear.',
    'Professionals distrusted figures they could not trace; the cause given was unfamiliarity with how they were produced. 23 participants across nine agencies.','S4'),
 (1,'Imperfect or missing data can make reported improvements difficult to trust.',
    'Anomalies in 47 percent of expected data points (26,390 of 55,836), involving all reporting countries but one.','S2');

-- 'personality' axes run between two opposing words: `label` is the left
-- anchor at 0, `label_right` the right anchor at 100, and `value` is where
-- this persona sits. 'motivation' and 'source_used' are one-ended, so
-- label_right stays NULL and the bar simply fills to `value`.
INSERT INTO persona_attribute (persona_id, category, label, label_right, value, anchor_note, source_id, display_order) VALUES
 (1,'personality','Analytical','Intuitive',22,NULL,'S1',1),
 (1,'personality','Cautious','Risk-taking',58,NULL,'S4',2),
 (1,'personality','Independent','Team-oriented',28,NULL,NULL,3),
 (1,'personality','Methodical','Spontaneous',42,NULL,NULL,4),
 (1,'personality','Accountable','Flexible',35,NULL,'S6',5),

 -- display_order ranks these strongest first, so the card reads as an order.
 (1,'motivation','Credible Communication',NULL,90,NULL,'S6',1),
 (1,'motivation','Time Efficiency',NULL,72,
   'Participation in data work was influenced by role, interest, workload, time, knowledge and willingness to change.','S1',2),
 (1,'motivation','Public Health Impact',NULL,40,NULL,NULL,3),
 (1,'motivation','Evidence-Based Decisions',NULL,20,NULL,'S4',4),
 (1,'motivation','Professional Accountability',NULL,16,NULL,'S6',5),

 (1,'source_used','Data Dashboards',NULL,75,NULL,'S3',1),
 (1,'source_used','Professional Email',NULL,68,NULL,NULL,2),
 (1,'source_used','Social Media',NULL,30,NULL,NULL,3),
 (1,'source_used','Research & Reports',NULL,16,NULL,'S6',4),
 (1,'source_used','Official Health Websites',NULL,12,NULL,'S2',5);

INSERT INTO persona_note (persona_id, category, note, source_id, display_order) VALUES
 (1,'skill_tag','14 years of experience in immunisation programmes.',NULL,1),
 (1,'skill_tag','Confident interpreting coverage rates, denominators and time series.','S1',2),
 (1,'skill_tag','Experienced with Excel but does not use SQL or Python.','S1',3);


-- =====================================================================
-- PERSONA 2  DANIEL NGUYEN   (Sub-Task B)
--
-- Group 1, the general public. Content follows the team's persona sheet;
-- what is still outstanding is the citation trail, not the copy.
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
  counterfactual, image_path, owner_student, display_order)
VALUES
(2, 1, 'Daniel Nguyen', 'The Curious Checker', 46,
 'Operations Coordinator', 'Household - general public', 'Melbourne, Australia',
 'Diploma-level; comfortable online but not a data specialist',
 'No formal background in public health or statistics',
 'I don''t need to be a health expert. I just want enough reliable evidence to understand what the numbers actually mean.',
 'Daniel is interested in understanding vaccination and preventable-disease trends. He checks reliable evidence and compares information before forming his own opinion, and prefers trustworthy sources with clear explanations of health data.',
 'A news headline or a conversation with a friend raises a question about whether a disease is coming back, or whether vaccination rates are falling in his own country. He wants to check it himself rather than take either side''s word for it.',
 'Within a few minutes, Daniel finds a plain-language answer backed by a real figure, understands roughly what the number means, and has a link he trusts enough to share.',
 'He falls back on the first search result or a social media post, with no way to judge whether it is accurate, dated or cherry-picked.',
 'img/daniel-photo.webp',
 's4138996', 2);

-- Goals, needs and pain points from the signed-off persona sheet. Group 1's
-- sources (Harmsen 2013; Frontiers in Public Health 2025) are not in
-- research_source yet, so these carry no source_id until the teammate adds
-- them as S9/S10 and says which claim rests on which paper.
INSERT INTO persona_goal (persona_id, goal, page_code, priority, source_id) VALUES
 (2,'Understand how vaccination and infection rates change over time.','1A',1,NULL),
 (2,'Compare countries and economic groups using reliable evidence.','2B',2,NULL);

INSERT INTO persona_need (persona_id, need, priority, source_id) VALUES
 (2,'Reliable evidence with clear context about countries, years and rates.',1,NULL),
 (2,'Easy comparison and independent exploration to answer his own questions.',2,NULL);

INSERT INTO persona_pain (persona_id, pain_point, evidence, source_id) VALUES
 (2,'Health statistics can be difficult to interpret without context.',NULL,NULL),
 (2,'Online health information can vary in reliability.',NULL,NULL);

-- Further pain points drawn from the Group 1 literature, held back until the
-- teammate adds S9/S10 to research_source and confirms which paper supports
-- which claim. Uncomment once the evidence column can be filled in honestly.
--
-- INSERT INTO persona_pain (persona_id, pain_point, evidence, source_id) VALUES
--  (2,'Cannot tell which search results are trustworthy','EDIT','S9'),
--  (2,'The safety information he wants exists in official material but he cannot find it','EDIT','S9'),
--  (2,'Dense data pages lose him','EDIT','S3'),
--  (2,'Anything that reads as persuasion makes him disengage','EDIT','S9');

-- Same shape as Grace's: two-ended personality axes, then one-ended
-- motivation and channel bars.
INSERT INTO persona_attribute (persona_id, category, label, label_right, value, anchor_note, source_id, display_order) VALUES
 (2,'personality','Analytical','Intuitive',20,NULL,NULL,1),
 (2,'personality','Cautious','Risk-taking',52,NULL,NULL,2),
 (2,'personality','Independent','Team-oriented',35,NULL,NULL,3),
 (2,'personality','Patient','Impatient',55,NULL,NULL,4),
 (2,'personality','Fact-driven','Emotion-driven',30,NULL,NULL,5),

 (2,'motivation','Helping Family & Community',NULL,72,NULL,NULL,1),
 (2,'motivation','Personal Curiosity',NULL,68,NULL,NULL,2),
 (2,'motivation','Staying Updated',NULL,40,NULL,NULL,3),
 (2,'motivation','Making Informed Decisions',NULL,30,NULL,NULL,4),
 (2,'motivation','Understanding & Learning',NULL,15,NULL,NULL,5),

 (2,'source_used','News & Online Articles',NULL,72,NULL,NULL,1),
 (2,'source_used','Email Newsletters',NULL,68,NULL,NULL,2),
 (2,'source_used','Social Media',NULL,45,NULL,NULL,3),
 (2,'source_used','Search Engines',NULL,20,NULL,NULL,4),
 (2,'source_used','Websites',NULL,10,NULL,NULL,5);

INSERT INTO persona_note (persona_id, category, note, source_id, display_order) VALUES
 (2,'skill_tag','Comfortable using websites and search engines.',NULL,1),
 (2,'skill_tag','Understands basic rates, percentages and comparisons.',NULL,2),
 (2,'skill_tag','Can evaluate information from different sources.',NULL,3);


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


-- =====================================================================
-- DISEASE INFORMATION  (landing "Vaccine information" cards)
-- Short factual blurbs and the WHO page for each disease. Verify the text
-- against the linked source before relying on it; these are summaries.
-- =====================================================================

DELETE FROM disease_info;
INSERT INTO disease_info (inf_type, vaccine_label, blurb, who_url) VALUES
 ('MEA', 'Measles-containing vaccine (MCV1, MCV2)',
  'Measles is a highly contagious airborne virus that can cause severe complications and death. Two doses of a measles-containing vaccine give lasting protection; WHO sets the elimination target at 95% coverage of both doses, reached equitably in every district.',
  'https://www.who.int/news-room/fact-sheets/detail/measles'),

 ('PER', 'DTP-containing vaccine (DTPCV1, DTPCV3)',
  'Pertussis, or whooping cough, is a respiratory infection caused by the bacterium Bordetella pertussis and is most dangerous to infants. Protection comes from the DTP-containing vaccine, but immunity wanes over time, so reported coverage alone understates how susceptible a population still is.',
  'https://www.who.int/health-topics/pertussis'),

 ('RUB', 'Rubella-containing vaccine (RCV1)',
  'Rubella is usually mild, but infection in early pregnancy can cause Congenital Rubella Syndrome in the baby. A rubella-containing vaccine prevents it. WHO warns that sustained coverage below 80% can shift infection to older ages and raise CRS risk, so partial coverage can be worse than none.',
  'https://www.who.int/news-room/fact-sheets/detail/rubella');

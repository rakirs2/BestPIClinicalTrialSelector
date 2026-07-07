Part 1: General Scraper of ClinicalTrials.gov.

Status: ✅ Local Python ingestion service is now available via `python -m scrapers.clinicaltrials.runner full-sync`, storing normalized data plus raw payloads in PostgreSQL with a 10 GB safety limit. Next steps focus on feeding this dataset into the .NET scoring + Blazor layers defined below.

## Long term
Product Plan: PI/Site Selection Tool + Clinical Trial Assistant Platform
1. Overall Vision
The goal is to build a clinical research platform for pharmaceutical sponsors, CROs, academic medical centers, and site teams that improves trial feasibility, site selection, recruitment, workflow creation, patient screening, consent workflows, co-enrollment planning, scheduling, data abstraction, and database buildout.
The platform should have two major products:
1.	PI/Site Selection Tool
o	Helps pharma companies identify which Principal Investigators and research sites are most likely to run a successful clinical trial.
o	Ranks investigators/sites based on research output, trial experience, patient population, disease volume, demographics of the population served, past enrollment performance, publication leadership, infrastructure, and trial fit.
2.	Clinical Trial Assistant Platform
o	Helps transform a trial idea or protocol concept into operational trial materials and workflows.
o	Supports protocol drafting, consent drafting, recruitment materials, study visit workflow creation, REDCap/database creation, EHR-based patient screening, enrollment prioritization, chart discrepancy flagging, e-consent workflows, automated outreach, co-enrollment opportunities, appointment scheduling, reminders, data abstraction, and quality control.
The platform should be designed as a human-in-the-loop clinical research operating system. It should assist research teams, but it should not independently determine final eligibility, independently contact patients without approval, or make clinical decisions without human review.
 
PART I: PI/SITE SELECTION TOOL
2. Goal of the PI/Site Selection Tool
The PI/Site Selection Tool should answer the following question:
“For this specific clinical trial, which Principal Investigators and sites are most likely to successfully activate, enroll, retain, generate high-quality data, represent the desired patient population, and produce strong research outputs?”
The tool should produce a ranked list of potential PIs and sites with transparent explanations for each recommendation.
The platform should allow a pharma sponsor or CRO to enter a trial concept, such as:
•	Disease area
•	Inclusion/exclusion criteria
•	Phase of trial
•	Intervention type
•	Required procedures
•	Target enrollment
•	Desired geography
•	Desired patient demographics
•	Required site capabilities
•	Timeline
•	Whether the sponsor prioritizes academic sites, community sites, diverse enrollment, high publication output, rapid startup, or high-volume recruitment
The system should then identify and rank investigators and sites.
 
3. Primary Users
3.1 Pharma/CRO Users
These users want to know:
•	Which PIs are best for the trial?
•	Which sites have the right patients?
•	Which sites can enroll quickly?
•	Which PIs have strong publication and trial leadership history?
•	Which sites serve diverse populations?
•	Which sites have experience with similar trials?
•	Which sites may be at risk for slow enrollment or poor data quality?
3.2 Academic Medical Center Users
These users want to know:
•	Which trials are a good fit for their patient population?
•	Which PIs are best suited for a sponsor opportunity?
•	Which departments have strong recruitment potential?
•	Which trials can be co-enrolled or operationally combined?
•	Which studies compete for the same patient population?
3.3 Research Operations Users
These users want to know:
•	Which site has the infrastructure to execute the protocol?
•	Which site has coordinators, imaging, labs, device expertise, regulatory support, and patient access?
•	Which sites have delays in contracting, IRB, budget negotiation, or activation?
•	Which sites have high screen fail rates or poor retention?
 
4. Inputs for PI/Site Selection
The PI/Site Selection Tool should allow the user to enter trial details manually or upload a draft protocol/synopsis.
4.1 Trial-Level Inputs
The platform should collect:
•	Trial title
•	Sponsor
•	Phase
•	Therapeutic area
•	Disease/condition
•	Intervention type
o	Drug
o	Device
o	Biologic
o	Procedure
o	Digital health
o	Behavioral intervention
o	Observational registry
•	Study design
o	Randomized
o	Single-arm
o	Blinded
o	Open-label
o	Sham-controlled
o	Registry
o	Prospective observational
•	Estimated target enrollment
•	Number of sites needed
•	Geographic preferences
•	Target patient population
•	Key inclusion criteria
•	Key exclusion criteria
•	Required procedures
o	Imaging
o	Echo
o	MRI
o	CT
o	PET
o	Right heart catheterization
o	Biopsy
o	Blood draws
o	Genetic testing
o	Exercise testing
o	Wearables
o	Remote monitoring
•	Follow-up schedule
•	Visit burden
•	Required specialist involvement
•	Desired population diversity
•	Sponsor priorities
o	Fast enrollment
o	Academic publication output
o	Diverse enrollment
o	Community representation
o	KOL involvement
o	Low operational risk
o	Trial-naive sites
o	High-volume sites
o	Sites with prior sponsor experience
 
5. Core PI/Site Selection Data Sources
The platform should combine public data, sponsor-provided data, institution-provided data, and optional EHR/CTMS data.
5.1 Public Investigator Data
For each PI, the platform should collect:
•	Full name
•	Degrees
•	Specialty
•	Subspecialty
•	Current institution
•	Current department/division
•	Prior institutions
•	City/state/country
•	Academic title
•	NPI, if available
•	ORCID, if available
•	PubMed author profile candidates
•	ClinicalTrials.gov investigator/site mentions
•	NIH grant history, if available
•	Industry payment/research relationship data, if available
•	Public leadership roles
•	Guideline committee membership, if available
•	Society leadership roles, if available
•	Editorial board roles, if available
5.2 Publication Data
The platform should collect publication information from PubMed and other publication databases.
For each PI, calculate:
•	Total publications
•	Publications in the past 5 years
•	Publications in the past 10 years
•	Number of clinical trial publications
•	Number of randomized trial publications
•	Number of phase 2/3 trial publications
•	Number of primary trial outcome publications
•	Number of first-author papers
•	Number of last-author papers
•	Number of corresponding-author papers
•	Number of first or last author papers in the past 5 years
•	Number of publications in high-impact journals
•	Number of publications in the exact disease area
•	Number of publications in adjacent disease areas
•	Number of pharma-sponsored trial publications
•	Number of device trial publications
•	Number of multicenter trial publications
•	Number of network/collaborative group publications
•	Citation metrics, if available
•	h-index or h-index proxy, if available
•	Co-author network strength
•	Frequency of collaboration with other high-performing trialists
•	Publications where the PI appears to be trial chair, steering committee member, or senior investigator
The system should classify the PI’s role in each publication:
•	First author
•	Co-first author
•	Last author
•	Co-senior author
•	Corresponding author
•	Middle author
•	Study group author
•	Committee author
•	Investigator group author
The system should specifically identify whether the PI was first, last, or corresponding author on:
•	Primary trial results papers
•	Secondary trial analyses
•	Substudies
•	Methods/design papers
•	Registry papers
•	Pooled analyses
•	Meta-analyses
•	Guideline documents
•	Consensus statements
5.3 Clinical Trial Experience Data
For each PI/site, the system should collect:
•	Number of active trials
•	Number of completed trials
•	Number of terminated trials
•	Number of suspended or withdrawn trials
•	Number of enrolling trials
•	Number of trials by phase
•	Number of trials by disease area
•	Number of pharma-sponsored trials
•	Number of device-sponsored trials
•	Number of NIH/federal trials
•	Number of investigator-initiated trials
•	Number of multicenter trials
•	Number of trials where the PI is listed as responsible party
•	Number of trials where the PI is listed as site investigator
•	Number of trials where the institution is a participating site
•	Similarity between prior trials and the proposed trial
•	Overlap between the PI’s prior trial criteria and the new trial criteria
•	Site history with the sponsor, if available
•	Site history with similar trial designs, if available
If sponsor-provided historical data is available, the platform should also calculate:
•	Time from CDA to feasibility completion
•	Time from feasibility to site selection
•	Time from site selection to contract execution
•	Time from contract to IRB approval
•	Time from IRB approval to site activation
•	Time from activation to first patient screened
•	Time from activation to first patient enrolled
•	Screened-to-enrolled ratio
•	Screen failure rate
•	Enrollment rate per month
•	Enrollment compared with target
•	Retention rate
•	Visit completion rate
•	Protocol deviation rate
•	Query rate
•	Time to query resolution
•	Data entry timeliness
•	Monitoring findings
•	Audit findings
•	Early termination risk
•	Staff turnover signals
5.4 Patient Population and Demographic Data
The tool should allow pharma companies to select sites based on the patient population served by the institution and surrounding catchment area.
For each site, the platform should estimate:
•	Total disease-relevant patient volume
•	Number of patients meeting broad disease criteria
•	Number of patients likely to meet key inclusion criteria
•	Number of patients likely excluded by major exclusion criteria
•	Age distribution
•	Sex distribution
•	Race/ethnicity distribution
•	Preferred language distribution
•	Insurance distribution, if available
•	ZIP code distribution
•	Distance-to-site distribution
•	Rural/urban distribution
•	Socioeconomic status indicators
•	Transportation access indicators
•	Area deprivation/social vulnerability indicators
•	Comorbidity burden
•	Prior hospitalization burden
•	Relevant medication use
•	Relevant procedure/imaging volume
For example, for a site like Northwestern, the platform should be able to estimate:
•	What patient population Northwestern serves
•	Which ZIP codes patients come from
•	Disease-specific patient volume
•	Race/ethnicity distribution of patients with the target disease
•	Age and sex distribution
•	Insurance and access-to-care patterns, where legally and institutionally allowed
•	Whether the site can support diverse enrollment goals for the proposed trial
Important: demographic data should be used to improve representativeness and access, not to exclude patients or unfairly prioritize based on protected characteristics.
5.5 Site Capability Data
For each site, collect:
•	Academic medical center vs community site
•	Specialty clinics available
•	Disease-specific clinic volume
•	Relevant subspecialists
•	Research coordinator availability
•	Research nurse availability
•	Regulatory support availability
•	Pharmacy support
•	Investigational drug service availability
•	Imaging capabilities
•	Core lab capabilities
•	Procedural capabilities
•	Device implantation capabilities
•	Lab processing capabilities
•	Biospecimen storage/freezer capacity
•	Weekend/evening visit capability
•	Remote visit capability
•	Telehealth capability
•	Transportation support
•	Multilingual staff
•	Translation services
•	eConsent capability
•	REDCap/EDC experience
•	Prior sponsor monitoring experience
•	IRB type
•	Single IRB experience
•	Contracting/budget speed
•	Competing trials in the same population
 
6. PI/Site Scoring Framework
The platform should generate an overall PI/Site Success Score from 0 to 100.
The score should be explainable, adjustable, and specific to the trial.
6.1 Suggested Score Components
A. Trial Fit Score — 20%
Measures how well the PI/site matches the scientific and clinical needs of the trial.
Inputs:
•	Disease-area expertise
•	Subspecialty match
•	Prior publications in disease area
•	Prior trials in same disease area
•	Required procedure capability
•	Required imaging/lab capability
•	Similarity between previous trials and current protocol
Example: A HFpEF trial requiring exercise right heart catheterization should rank sites higher if they have:
•	HFpEF publication history
•	Exercise hemodynamics expertise
•	Advanced heart failure clinic volume
•	Invasive cardiopulmonary testing capability
•	Prior HFpEF trial experience
B. Research Output Score — 20%
Measures the PI’s academic and publication productivity.
Inputs:
•	Total PubMed publications
•	Publications in past 5 years
•	Clinical trial publications
•	First-author trial papers
•	Last-author trial papers
•	Corresponding-author trial papers
•	Primary outcome papers
•	High-impact publications
•	Disease-specific publications
•	Multicenter trial publications
•	Guideline/consensus papers
•	Citation metrics
This score should not just count publications. It should weight leadership roles more heavily.
Suggested weighting:
•	Primary trial paper as first/last/corresponding author: highest weight
•	Disease-specific randomized clinical trial publication: high weight
•	First/last/corresponding author paper: high weight
•	Recent publication in past 5 years: moderate/high weight
•	Middle-author paper: lower weight
•	Non-disease-specific publication: lower weight
C. Trial Execution Score — 20%
Measures whether the site can operationally execute the trial.
Inputs:
•	Number of active trials
•	Number of completed similar trials
•	Enrollment rate, if available
•	Screen fail rate, if available
•	Retention rate, if available
•	Query rate, if available
•	Protocol deviation rate, if available
•	Site activation timeline
•	Contracting speed
•	IRB speed
•	Coordinator capacity
•	Prior sponsor experience
The platform should identify whether the site is:
•	High-performing and not overloaded
•	High-performing but overloaded
•	Scientifically excellent but operationally slow
•	Operationally fast but lower publication output
•	High volume but poor retention
•	Good diversity fit but limited research infrastructure
D. Patient Availability Score — 15%
Measures whether the site has enough potentially eligible patients.
Inputs:
•	Estimated number of patients with target condition
•	Estimated number meeting key inclusion criteria
•	Estimated number excluded by major exclusion criteria
•	Disease clinic volume
•	Procedure/imaging volume
•	Hospitalization volume
•	New patient volume
•	Follow-up patient volume
•	Referral network size
This should include confidence levels:
•	High confidence: EHR/claims/registry data available
•	Medium confidence: site-reported feasibility data
•	Low confidence: public/catchment estimates only
E. Diversity and Representativeness Score — 10%
Measures whether the site can help the sponsor enroll a representative population.
Inputs:
•	Race/ethnicity distribution of disease-specific patient population
•	Sex distribution
•	Age distribution
•	Language needs
•	Rural/urban representation
•	Socioeconomic vulnerability
•	Insurance status, if available
•	Community outreach infrastructure
•	Prior diverse enrollment performance, if available
This score should be designed carefully. It should support equitable recruitment planning and should not penalize sites that serve vulnerable populations.
F. Strategic/KOL Value Score — 5%
Measures the PI’s strategic value to the sponsor.
Inputs:
•	National/international reputation
•	Guideline involvement
•	Steering committee experience
•	Society leadership
•	Editorial roles
•	Speaker roles
•	Prior sponsor relationship
•	Influence in disease area
•	Ability to lead manuscripts or substudies
G. Risk Score — 10%
Measures operational, compliance, and feasibility risks.
Inputs:
•	Too many active competing trials
•	Overlapping patient population with other active trials
•	Prior slow activation
•	High screen fail rate
•	High protocol deviation rate
•	Poor data entry timeliness
•	High query burden
•	Limited coordinator capacity
•	Mismatch between protocol burden and site resources
•	Potential conflict of interest
•	Poor prior sponsor experience
•	Low confidence in public data matching
The overall score should subtract or flag major risk factors rather than hiding them.
 
7. Suggested PI/Site Success Score Formula
The initial version can use a transparent weighted model:
PI/Site Success Score =
•	Trial Fit Score × 0.20
•	Research Output Score × 0.20
•	Trial Execution Score × 0.20
•	Patient Availability Score × 0.15
•	Diversity/Representativeness Score × 0.10
•	Strategic/KOL Value Score × 0.05
•	Risk Adjustment × 0.10
Each score should be shown with:
•	Numeric score
•	Confidence level
•	Explanation
•	Data sources
•	Missing data
•	Recommended follow-up questions
Later, once enough sponsor/site outcome data is available, the platform can train predictive models for:
•	Probability of site activation within target timeline
•	Probability of meeting enrollment target
•	Probability of first patient enrolled within X days
•	Probability of high screen failure
•	Probability of high retention
•	Probability of publication/substudy productivity
•	Probability of operational delay
 
8. PI/Site Selection Output
For each PI/site, the system should generate a profile that includes:
8.1 PI Summary
•	Name
•	Institution
•	Department/division
•	Specialty
•	Location
•	Trial fit score
•	Research output score
•	Trial execution score
•	Patient availability score
•	Diversity/representativeness score
•	Risk score
•	Overall recommendation
Example labels:
•	Strongly recommend
•	Recommend
•	Consider with caveats
•	High scientific value but operational risk
•	High patient volume but limited research output
•	Not recommended for this protocol
•	Insufficient data
8.2 Evidence Summary
The platform should show:
•	Top relevant publications
•	Trial leadership publications
•	Primary trial result publications
•	First/last/corresponding author papers
•	Similar active/completed trials
•	Disease-specific patient volume estimate
•	Demographic/catchment profile
•	Operational feasibility signals
•	Competing trials
•	Key risks
•	Data gaps
8.3 Sponsor-Facing Recommendation
For each PI/site, generate a concise recommendation:
“This PI is a strong candidate because they have high disease-specific publication output, multiple prior phase 2/3 trial publications as senior author, active experience with similar trials, and the institution serves a large patient population matching the target demographic profile. Main risks include multiple active competing trials and unknown coordinator capacity.”
 
9. PI/Site Selection Filters
The user should be able to filter and sort by:
•	Disease area
•	Specialty
•	Geography
•	Institution type
•	Academic vs community
•	Patient demographics
•	Estimated eligible patient count
•	Race/ethnicity distribution of disease population
•	Age distribution
•	Sex distribution
•	Language needs
•	Prior trial experience
•	Active trials
•	Publication output
•	First/last/corresponding author count
•	Primary trial paper count
•	NIH funding history
•	Pharma trial history
•	Device trial history
•	Enrollment speed
•	Activation speed
•	Retention performance
•	Protocol deviation rate
•	Data quality
•	Site risk
•	KOL value
•	Sponsor relationship history
•	Co-enrollment opportunities
•	Competing trial burden

10. PI/Site Selection UI Implementation Plan
The front end should adopt the overall interaction model of CSRankings.com—dense filters, collapsible taxonomy sidebar, and sortable ranking tables—but render clinical trial, site, and investigator data.

10.1 Technology & Constraints
•	Blazor Server only (no WebAssembly for MVP) so the UI and data services live inside one ASP.NET Core host.
•	Native HTML/Blazor controls everywhere (select, checkbox, range inputs, `<details>/<summary>` accordions) to avoid third-party JavaScript packages; any advanced behavior (sliders, overlays) should be implemented with built-in Blazor plus minimal CSS.
•	All data requests must hit PostgreSQL directly through EF Core or Dapper queries; no caching, denormalized API snapshots, or offline files for now so every view reflects the current ingestion state.

10.2 Layout & UX Requirements
•	Sticky filter bar modeled after CSRankings with geography selector, timeline slider, disease/intervention toggles, and sponsor-focused quick actions (tour/export buttons).
•	Taxonomy sidebar that mirrors CSRankings area lists but uses therapeutic area groupings, intervention/drug types, and operational priorities; collapsible sections keep the footprint small on desktop and allow mobile reflow underneath the table.
•	Ranking table with virtualization, sortable headers, inline bar indicators for score components, and badges for interventions/geographies.
•	Detail drawer/modal that surfaces raw ClinicalTrials.gov excerpts, investigator history, locations, and aggregated stats without leaving the page.
•	Guided walkthrough overlay implemented natively (conditional Blazor components) to introduce controls, similar in spirit to CSRankings’ tour feature.

10.3 Execution Stages
1.	Scaffold Blazor Server host, global layout, theming, data access layer, and configuration for PostgreSQL.
2.	Implement filter panel + taxonomy sidebar with live bindings to an application-wide filter state service; wire controls to update query parameters.
3.	Build ranking table backed by server-side queries that fetch fresh scoring data on every change; include loading states and cancellation to handle rapid filter updates.
4.	Add investigator/site detail drawer plus evidence panels (publications, trials, demographics) loaded on demand, still querying the database directly.
5.	Layer in walkthrough overlay, sponsor/export CTAs, and documentation so teams can iterate on scoring logic and data sources without changing the UI contract.

Future enhancements (offline exports, auth, caching, UI polish) can layer on after the five stages above deliver a functioning, data-backed Blazor Server experience inspired by CSRankings.

# HIPAA & Data Privacy Design Notes

## Data Used
This project uses **fully synthetic** patient data generated programmatically. No real Protected Health Information (PHI) is used. The data generator creates clinically plausible distributions without referencing any actual patient records.

## Design Principles for Real PHI Deployment

If adapted for real EHR data under HIPAA:

**1. De-identification (Safe Harbor Method)**
Remove all 18 HIPAA identifiers: names, dates (retain year only for age calculation), geographic data below state level, phone numbers, SSNs, MRNs (replace with study IDs), device identifiers, URLs, IPs, biometric data, full-face photos, and any unique identifying numbers.

**2. Minimum Necessary Standard**
Analytical tables contain only the variables required for the specific analysis. Raw EHR tables are not exposed to the analytical layer. Only aggregated or de-identified data flows to dashboards.

**3. Role-Based Access Control**
Row-Level Security in Power BI ensures clinicians see only their department's patients. Researchers access only IRB-approved cohorts. Administrative users see aggregate metrics only.

**4. Audit Logging**
All queries against patient-level data are logged with user ID, timestamp, query text, and stated purpose. Logs are immutable and retained per institutional policy.

**5. Data Use Agreements**
Any cross-institutional data sharing requires a BAA (Business Associate Agreement) and DUA (Data Use Agreement) specifying permitted uses, retention periods, and destruction requirements.

**6. IRB Considerations**
Research use of patient data requires IRB approval or a determination of exemption (e.g., retrospective chart review with de-identified data). This project would qualify for exemption under 45 CFR 46.104(d)(4) as it uses de-identified data only.

## Applicable Regulations
- **HIPAA** Privacy Rule (45 CFR 160, 164) — PHI protection
- **HITECH Act** — Breach notification, meaningful use
- **21 CFR Part 11** — Electronic records (if FDA-regulated)
- **FERPA** — If student health data crosses into education records
- **Georgia HB 2020** — State health information privacy

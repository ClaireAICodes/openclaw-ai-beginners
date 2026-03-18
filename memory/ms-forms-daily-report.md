# MS Forms - Daily Org Report

**Form URL:** https://forms.cloud.microsoft/r/LsxLaEv13i  
**Form ID:** y4gQvsRJ0kSBTieaxXz5Ouhw_jegv2RBj77g1YxvQURUMFhYRzZQTFdSRUMzRlY5NVM5VVE1SEJKRSQlQCN0PWcu  
**Tenant ID:** be1088cb-49c4-44d2-814e-279ac57cf93a  
**Group ID:** 37fe70e8-bfa0-4164-8fbe-e0d58c6f4144  
**Retrieved:** 2026-03-18

---

## Questions

| # | Question | Type | Required | Question ID | Notes |
|---|----------|------|----------|-------------|-------|
| 1 | Date of Reporting | Date picker | ✅ | `r4920b5f203694c6aad4a6256d747d8a5` | Format: M/d/yyyy |
| 2 | Training Hours | Number (single line text) | ✅ | `rcd2a9123ac0545b098b5cec473f44ec0` | Hours teaching/assessment/webinars/KT. 0 if none. |
| 3 | Content Dev Hours | Number (single line text) | ✅ | `r65c9820bcced4c06857f7eaeafe632a0` | Hours on content development. 0 if not involved. |
| 4 | Content Dev Topic | Text | ✅ | `r6b219847cf374323bb5ae5abe164c8bd` | Course name + topics/modules completed. NA if not involved. |
| 5 | Learning Hours | Number (single line text) | ✅ | `rcccf5ae08f184b60bbb744c66ef3f940` | Hours on self-learning/upskilling (ACLP/KT/Webinar). 0 if N/A. |
| 6 | Learning Topic | Text | ✅ | `r4b0f3d4527134ad78aff24ec5c3b0c61` | What you learned. NA if N/A. |
| 7 | Other Items | Text | ❌ | `rafa8dc21a65a4e0f9aaa5e6919e7b5ee` | Other activities during working hours (duration + description). |
| 8 | Managing Team (Only for Leads) | Number (single line text) | ❌ | `r245865fa8a1347449143c43b2cbabb1f` | Hours on team tasks (quality review, content dev review, etc.). |
| 9 | Managing Team (Only for Leads) Description | Text | ❌ | `r65acc32b219d4cbdb3e41f1e930589ed` | Brief description of team tasks involved in. |

---

## API Endpoint (requires auth)
```
GET https://forms.cloud.microsoft/formapi/api/{tenantId}/groups/{groupId}/light/runtimeForms('{formId}')?$expand=questions($expand=choices)
```

## Notes
- All required fields: Q1-Q6
- Optional fields: Q7-Q9
- Q8 and Q9 are "Only for Leads" - may be skipped
- Form requires Microsoft 365 login to submit

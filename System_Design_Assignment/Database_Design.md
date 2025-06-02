# Sample Database Schema

Using SQL based or PostgreSQL, this sample database schema is designed to support the system architecture and functionalities described in the assignment. It includes tables for users, projects, floor plans, site visits, issues, action items, and decisions.

## Database Tables

### Users

Schema:
- id
- name
- email
- phone_number
- role (admin, engineer, designer, client, contractor)
- profile_image
- created_at
- updated_at

**Sample Data:**

| id | name | email | phone_number | role | profile_image |
|----|------|-------|-------------|------|--------------|
| 1 | Engineer A | engineer.a@example.com | +91987654321 | engineer | profiles/engineer_a.jpg |
| 2 | Designer B | designer.b@example.com | +91876543210 | designer | profiles/designer_b.jpg |
| 3 | Client C | client.c@example.com | +91765432109 | client | profiles/client_c.jpg |
| 4 | Contractor D | contractor.d@example.com | +91654321098 | contractor | profiles/contractor_d.jpg |

### Projects

Schema:
- id
- name
- address
- client_id (User)
- lead_designer_id (User)
- lead_engineer_id (User)
- status (planning, active, completed, on_hold)
- start_date
- estimated_completion_date
- actual_completion_date
- created_at
- updated_at

**Sample Data:**

| id | name | address | client_id | lead_designer_id | lead_engineer_id | status | start_date | estimated_completion_date |
|----|------|---------|-----------|------------------|------------------|--------|------------|--------------------------|
| 1 | Residential Project Alpha | 123 Main Street, Mumbai | 3 | 2 | 1 | active | 2024-12-15 | 2025-12-15 |

### Floor Plans

Schema:
- id
- project_id (Project)
- name
- file_path
- floor_number
- version
- created_at
- updated_at

**Sample Data:**

| id | project_id | name | file_path | floor_number | version |
|----|------------|------|-----------|-------------|---------|
| 1 | 1 | Ground Floor | floor_plans/project_1/ground_floor_v1.png | 0 | 1 |
| 2 | 1 | Second Floor | floor_plans/project_1/second_floor_v1.png | 2 | 1 |

### Site Visits

Schema:
- id
- project_id (Project)
- visit_date
- engineer_id (User)
- audio_recording_path
- recording_duration (seconds)
- language
- processing_status (pending, processing, completed, failed)
- transcript_text
- raw_transcript
- created_at
- updated_at

**Sample Data:**

| id | project_id | visit_date | engineer_id | audio_recording_path | recording_duration | language | processing_status |
|----|------------|------------|-------------|----------------------|---------------------|----------|-------------------|
| 1 | 1 | 2025-03-26 14:00:00 | 1 | recordings/visit_1.mp3 | 480 | english | completed |

### Visit Attendees

Schema:
- id
- site_visit_id (SiteVisit)
- name
- role
- user_id (User, optional)
- created_at

**Sample Data:**

| id | site_visit_id | name | role | user_id |
|----|---------------|------|------|---------|
| 1 | 1 | Engineer A | engineer | 1 |
| 2 | 1 | Client C | client | 3 |
| 3 | 1 | Client's Spouse | client_representative | NULL |

### Issues

Schema:
- id
- site_visit_id (SiteVisit)
- room
- floor_plan_id (FloorPlan)
- x_coordinate
- y_coordinate
- contractor
- problem
- solution
- remarks
- timestamp_start
- timestamp_end
- created_at
- updated_at

**Sample Data:**

| id | site_visit_id | room | floor_plan_id | x_coordinate | y_coordinate | contractor | problem | solution | timestamp_start | timestamp_end |
|----|---------------|------|---------------|-------------|-------------|------------|---------|----------|----------------|--------------|
| 1 | 1 | Master Bedroom | 2 | 450 | 320 | Civil / Mason | Wall chasing for conduits is rough and needs finishing | Needs proper finishing before plaster or final finishes | 35 | 55 |
| 2 | 1 | Master Bathroom | 2 | 520 | 345 | Plumber | Waterproofing needs checking, especially around the drain points | Re-check waterproofing integrity before tiling | 70 | 90 |

### Action Items

Schema:
- id
- site_visit_id (SiteVisit)
- issue_id (Issue)
- title
- description
- assignee_type (site_engineer, office_team, contractor, client)
- assigned_to_id (User)
- assigned_to_name
- due_date
- status (pending, in_progress, completed, blocked)
- priority (low, medium, high, critical)
- created_at
- updated_at

**Sample Data:**

| id | site_visit_id | issue_id | title | description | assignee_type | assigned_to_id | due_date | status | priority |
|----|---------------|----------|-------|-------------|--------------|---------------|----------|--------|----------|
| 1 | 1 | 1 | Fix wall chasing in Master Bedroom | Ensure proper finishing before plaster application | contractor | 4 | 2025-04-02 | pending | high |
| 2 | 1 | 2 | Waterproofing test in Master Bathroom | Conduct water test for 24 hours to ensure no leakage | site_engineer | 1 | 2025-04-05 | pending | critical |

### Decisions

Schema:
- id
- site_visit_id (SiteVisit)
- description
- decided_by_id (User)
- decided_by_role
- timestamp_start
- timestamp_end
- created_at

**Sample Data:**

| id | site_visit_id | description | decided_by_id | decided_by_role | timestamp_start | timestamp_end |
|----|---------------|-------------|--------------|----------------|-----------------|---------------|
| 1 | 1 | False ceiling height in living room to be increased by 3 inches | 3 | client | 125 | 145 |
| 2 | 1 | Kitchen platform material changed to granite from marble | 3 | client | 195 | 210 |

# AI-Powered Construction Site Visit System Architecture

## High-Level Component Overview

```
┌─────────────────────┐               ┌───────────────────────┐
│                     │  (1) Upload   │                       │
│   Mobile PWA        ├──────────────►│   API Gateway         │
│   (React + Vite)    │◄──────────────┤   (Django REST)       │
│                     │  (6) Reports  │                       │
└─────────────────────┘               └───────────┬───────────┘
                                                  │
        ┌──────────────────────────────────────────┘
        │
        │ (2) Process
        ▼
┌─────────────────────────┐          ┌───────────────────────┐
│                         │  (3) AI  │                       │
│   Celery Task Queue     ├─────────►│   AI Processing       │
│                         │          │   Pipeline            │
└─────────────────────────┘          │                       │
                                     └───────────┬───────────┘
                                                 │
        ┌──────────────────────────────────────────┘
        │ (4) Store
        ▼
┌─────────────────────┐               ┌───────────────────────┐
│                     │               │                       │
│   PostgreSQL DB     │◄─────────────►│   Admin Dashboard     │
│                     │               │   (Django Admin)      │
└─────────────────────┘               │                       │
                                      └───────────────────────┘
        │
        │ (5) Retrieve
        ▼
┌─────────────────────┐  
│                     │  
│   S3 Storage        │  
│                     │  
└─────────────────────┘  
```

### Data Flow Description

1. **Upload**: Site engineers upload audio recordings and floor plan images through the mobile PWA
2. **Process**: Django API schedules asynchronous processing tasks via Celery
3. **AI Processing**: Audio is transcribed, translated (if in Hindi), and analyzed with floor plan images
4. **Store**: Processed data is stored in PostgreSQL database and media files in S3
5. **Retrieve**: Media assets are retrieved from S3 when needed
6. **Reports**: Structured reports are delivered back to the mobile app and admin dashboard

## Technology Stack

### Frontend
- **Framework**: React with Vite for fast development and optimized production builds
- **UI Components**: Tailwind CSS with Shadcn/UI component library
- **PWA Features**: Service workers for offline functionality, push notifications
- **State Management**: React Context API or Redux for complex state

### Backend
- **Framework**: Django with Django REST Framework
- **Admin Interface**: Django Admin with custom dashboards
- **Authentication**: JWT with mobile OTP verification
- **Task Processing**: Celery with Redis for asynchronous job queue

### AI Services
- **Speech Processing**: OpenAI Whisper for audio transcription and Hindi-English translation
- **Text Analysis**: GPT-4.1/5 for structured data extraction from transcripts
- **Image Processing**: Custom computer vision system for floor plan annotation

### Infrastructure
- **Database**: PostgreSQL for relational data storage
- **File Storage**: Amazon S3 for audio, images, and generated reports
- **Hosting**: AWS ECS/EKS for containerized deployment
- **Monitoring**: Datadog for system monitoring and alerting

## API & Database Design

### Core API Endpoints

#### Authentication

| Endpoint | Method | Description | Parameters | Response |
|----------|--------|-------------|------------|----------|
| `/api/auth/register` | POST | Register a new user | `{phone_number, name, email, role}` | `{user_id, token}` |
| `/api/auth/verify-otp` | POST | Verify OTP for authentication | `{phone_number, otp}` | `{token, user}` |
| `/api/auth/refresh` | POST | Refresh authentication token | `{refresh_token}` | `{token}` |

#### Projects

| Endpoint | Method | Description | Parameters | Response |
|----------|--------|-------------|------------|----------|
| `/api/projects` | GET | List all projects for user | `{filters, pagination}` | `{projects[]}` |
| `/api/projects/:id` | GET | Get project details | `{project_id}` | `{project}` |
| `/api/projects/:id/floor-plans` | GET | Get floor plans for project | `{project_id}` | `{floor_plans[]}` |

#### Site Visits

| Endpoint | Method | Description | Parameters | Response |
|----------|--------|-------------|------------|----------|
| `/api/visits` | POST | Create new site visit | `{project_id, date, attendees}` | `{visit_id}` |
| `/api/visits/:id/upload` | POST | Upload audio recording | `{audio_file, floor_plan_id}` | `{task_id}` |
| `/api/visits/:id/status` | GET | Check processing status | `{visit_id}` | `{status, progress}` |
| `/api/visits/:id/report` | GET | Get generated report | `{visit_id}` | `{report}` |

#### Reports & Action Items

| Endpoint | Method | Description | Parameters | Response |
|----------|--------|-------------|------------|----------|
| `/api/reports/:id` | GET | Get detailed report | `{report_id}` | `{report_details}` |
| `/api/reports/:id/action-items` | GET | Get action items | `{report_id}` | `{action_items[]}` |
| `/api/action-items/:id/update` | PATCH | Update action item status | `{id, status, notes}` | `{action_item}` |

### Sample JSON Schemas

#### Site Visit Request
```json
{
  "project_id": "proj_123456",
  "visit_date": "2025-06-02T10:30:00Z",
  "engineer_id": "user_789012",
  "attendees": [
    {"name": "Client Name", "role": "client"},
    {"name": "Contractor Name", "role": "contractor"}
  ],
  "notes": "Regular weekly site visit"
}
```

#### Site Visit Report Response
```json
{
  "visit_id": "visit_345678",
  "project": {
    "id": "proj_123456",
    "name": "Residential Project Alpha",
    "address": "123 Main Street"
  },
  "date": "2025-06-02T10:30:00Z",
  "engineer": {
    "id": "user_789012",
    "name": "Engineer A"
  },
  "attendees": [...],
  "issues_observed": [
    {
      "room": "Master Bedroom",
      "floor_plan_coordinates": {"x": 450, "y": 320},
      "contractor": "Civil / Mason",
      "problem": "Wall chasing for conduits is rough and needs finishing",
      "solution": "Needs proper finishing before plaster or final finishes",
      "remarks": "Check if this affects concealed wiring or finishes",
      "timestamp_in_recording": "0:35-0:55"
    },
    // Additional issues...
  ],
  "decisions": [...],
  "action_items": [
    {
      "id": "action_901234",
      "title": "Fix wall chasing in Master Bedroom",
      "assignee": "Contractor Company",
      "assigned_to": "user_567890",
      "due_date": "2025-06-09T00:00:00Z",
      "status": "pending",
      "priority": "high"
    },
    // Additional action items...
  ],
  "next_visit_scheduled": "2025-06-09T10:30:00Z"
}
```

## Processing Pipeline

1. **Audio Preprocessing**:
   - Audio files are uploaded and stored in S3
   - Celery task is triggered for asynchronous processing

2. **Transcription & Translation**:
   - OpenAI Whisper API transcribes audio to text
   - If audio is in Hindi, translation to English is performed
   - Timestamps are preserved for reference

3. **Structured Data Extraction**:
   - GPT model processes transcript to extract:
     - Room references and issues
     - Action items and responsibilities
     - Decisions made during the visit

4. **Floor Plan Integration**:
   - Computer vision system marks issues on floor plan
   - Each observation is mapped to its location on the plan
   - Interactive visualization is generated

5. **Report Generation**:
   - Structured report is compiled from all extracted data
   - Notification is sent to relevant stakeholders
   - Data is stored in PostgreSQL for tracking and analysis

## Pydantic Model for Structured Report

The following Pydantic model is used to generate the structured site visit report from audio and floor plan input. The model ensures all key sections are captured in a standardized, machine-readable format:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class Attendee(BaseModel):
    name: str
    role: str
    present: bool

class IssueObservation(BaseModel):
    room: str
    contractor: str
    problem: str
    solution: str
    remarks: Optional[str]
    timestamps: List[str]

class Decision(BaseModel):
    room: str
    contractor: str
    problem: str
    solution_given: str
    remarks: Optional[str]
    timestamps: List[str]

class ActionItem(BaseModel):
    room: str
    contractor: str
    problem: str
    responsible_person: str
    remarks: Optional[str]
    timestamps: List[str]

class CommunicationResponsibility(BaseModel):
    contractor: str
    communication: str
    work_description: str
    remarks: Optional[str]
    timestamps: List[str]

class Responsibility(BaseModel):
    room: str
    contractor: str
    description: str
    remarks: Optional[str]
    timestamps: List[str]

class DesignTeamResponsibility(BaseModel):
    room: str
    description: str
    remarks: Optional[str]
    timestamps: List[str]

class SiteVisitReport(BaseModel):
    date: str
    project: str
    site_engineer: str
    designer: str
    client: str
    attendees: List[Attendee]
    issues_observations: List[IssueObservation]
    decisions: List[Decision]
    action_items: List[ActionItem]
    contractor_communications: List[CommunicationResponsibility]
    site_engineer_responsibilities: List[Responsibility]
    client_responsibilities: List[Responsibility]
    design_team_responsibilities: List[DesignTeamResponsibility]
```

**Input Mapping:**
- The fields `date`, `project`, `site_engineer`, `designer`, and `client` are extracted from the initial metadata section of the report (e.g., `**Date:** 26th March, 2025`).
- All subsequent sections (Issues, Decisions, Action Items, etc.) are parsed and mapped to their respective model fields, ensuring every observation and responsibility is structured for downstream use (dashboard, analytics, notifications, etc).

## Sample Data Processing Flow

Below is an example of how raw audio content is transformed into structured data:

### 1. Audio Recording
- Engineer records: "In the master bedroom, the wall chasing for conduits is rough and needs proper finishing before plaster or final finishes."

### 2. Whisper Transcription
```json
{
  "text": "In the master bedroom, the wall chasing for conduits is rough and needs proper finishing before plaster or final finishes.",
  "segments": [
    {
      "id": 0,
      "start": 35.0,
      "end": 55.0,
      "text": "In the master bedroom, the wall chasing for conduits is rough and needs proper finishing before plaster or final finishes."
    }
  ]
}
```

### 3. AI Structured Data Extraction
```json
{
  "room": "Master Bedroom",
  "contractor": "Civil / Mason",
  "problem": "Wall chasing for conduits is rough and needs finishing",
  "solution": "Needs proper finishing before plaster or final finishes",
  "remarks": "Check if this affects concealed wiring or finishes",
  "timestamp_range": [35.0, 55.0]
}
```

### 4. Database Storage
- Data is stored in relevant tables (issues, action_items)
- Floor plan location is identified and coordinates are stored
- Action items are created with appropriate assignments

### 5. Report Generation
- Data is compiled into structured report format
- Visualizations are created for the dashboard
- Notifications are sent to relevant stakeholders

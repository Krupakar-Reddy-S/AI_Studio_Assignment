# System Design Assignment Overview

This folder contains the complete system design files for the Assignment. The design focuses on creating an AI-powered system to transform audio recordings and floor plans into structured reports for construction site visits.

## Key Documents

- [System Architecture](./System_Architecture.md):
  - High-level component diagram, data flow, technology stack, API design, and the Pydantic model for structured site visit reports.
- [Database Design](./Database_Design.md):
  - Entity schemas and sample data for all core tables (users, projects, visits, issues, action items, etc.), presented in a simple, implementation-agnostic format.
- [Implementation Plan](./Implementation_Plan.md):
  - Stepwise roadmap for backend, frontend, and integration phases, with success criteria and risk mitigation strategies.

## Overview

This system design covers the end-to-end workflow for capturing, processing, and reporting on construction site visits using AI. It includes:
- A robust backend and AI pipeline for audio transcription, structured data extraction, and report generation.
- A mobile-first frontend for site engineers to record/upload data and for office/admin users to review and track progress.
- A clear, extensible data model and API contract to support future enhancements and integrations.

See the linked documents above for full details on architecture, data, and implementation strategy.

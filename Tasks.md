# Tasks - Meeting Transcription Tool

## Phase 1: Core Functionality (No Storage)

### 1. Streamlit UI
- [ ] Set up Streamlit app structure
- [ ] Implement audio file upload (.mp3, .wav)
- [ ] Implement audio recording via browser

### 2. Transcription Pipeline
- [ ] Integrate Whisper for speech-to-text transcription
- [ ] Display raw transcription in UI

### 3. Speaker Diarization and Vocabulary Correction
- [ ] Attempt speaker diarization using Whisper's capabilities
- [ ] Extract names/entities from transcription
- [ ] Build custom vocabulary for correcting names and important terms

### 4. Insight Extraction
- [ ] Integrate LLM (e.g., GPT-4.1) for:
    - [ ] Key discussion points
    - [ ] Action items
    - [ ] Important decisions
    - [ ] Meeting summary

### 5. Export Options
- [ ] Implement export as Markdown
- [ ] Implement export as PDF
- [ ] Implement export as JSON

---

## Phase 2: Storage Integration

### 6. Supabase Integration
- [ ] Set up Supabase project and tables
- [ ] Store audio files
- [ ] Store transcriptions and summaries
- [ ] Retrieve and display past meeting records

---

## Project Management

- [ ] Regularly update README with progress and decisions
- [ ] Document technical/design choices
- [ ] Prepare demo video and sample outputs
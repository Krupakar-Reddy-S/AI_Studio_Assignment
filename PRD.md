# PRD - Meeting Transcription Tool

---

### 1. Overview

The Meeting Transcription Tool is a robust application designed to transform meeting audio recordings into accurate, actionable, and organized documentation. It leverages state-of-the-art speech-to-text (Whisper) and large language models (LLMs) to provide transcriptions, extract key discussion points, identify action items, and generate executive summaries. The tool aims to streamline post-meeting workflows and enhance productivity by delivering outputs in multiple formats.

---

### 2. Goals & Objectives

- **Accurate Transcription:** Convert meeting audio into precise text using Whisper.
- **Insight Extraction:** Identify key discussion points, action items, and decisions using LLMs.
- **Speaker Diarization:** Attribute statements to individual speakers where possible.
- **Multi-format Export:** Support exporting results as PDF, Markdown, and JSON.
- **User-Friendly Interface:** Enable easy audio upload/recording and result review.
- **Scalable & Maintainable:** Ensure the solution is robust, modular, and easy to extend.

---

### 3. Features

#### Core Features
- **Audio Input**
  - Upload audio files (e.g., .mp3, .wav)
  - Record audio directly via browser (Streamlit UI)
- **Transcription**
  - Use Whisper for speech-to-text conversion
  - Support for English language (initially)
- **Speaker Diarization**
  - Attempt to distinguish and label speakers
  - Use heuristics or LLM post-processing if Whisper diarization is limited
- **Insight Extraction**
  - Use LLMs (e.g., GPT-4) to extract:
    - Key discussion points
    - Action items
    - Important decisions
    - Meeting summary
- **Vocabulary Correction**
  - Build a custom vocabulary from transcription for name/entity correction
- **Export Options**
  - Download results as PDF, Markdown, or JSON
- **Data Storage**
  - Store audio files, transcriptions, and summaries (e.g., Supabase)

#### Bonus/Nice-to-Have Features
- **Automatic Meeting Type Detection**
- **Integration with Calendar Tools**
- **Real-time Processing**
- **User Authentication & History**

---

### 4. User Stories

- **As a user,** I want to upload or record meeting audio so that I can generate a transcript.
- **As a user,** I want to receive a structured summary with action items and key points so I can quickly review meeting outcomes.
- **As a user,** I want to export the meeting documentation in my preferred format (PDF, Markdown, JSON).
- **As a user,** I want to see who said what during the meeting (speaker diarization).
- **As a user,** I want the tool to correct names and important terms for accuracy.

---

### 5. Technical Approach

- **Frontend:** Streamlit app for UI (audio upload/record, results display, export)
- **Backend:** Python for processing pipeline
  - Whisper for transcription
  - LLM (e.g., GPT-4.1) for analysis and structured output
  - Pydantic models for structured data
  - Libraries: pdfkit (PDF), markdown, json
- **Database:** Supabase for storing files and results
- **Deployment:** Streamlit Cloud

---

### 6. Assumptions & Limitations

- Audio input is in English and of reasonable quality.
- Real-time transcription is not required (batch processing only).
- Speaker diarization may be limited by Whisper's capabilities.
- Vocabulary correction is based on extracted context, not user input.
- No advanced state management in Streamlit; rely on backend/database.

---

### 7. Success Metrics

- **Transcription Accuracy:** >90% word accuracy on clear audio
- **Insight Extraction Quality:** Action items and summaries rated as useful by users
- **Export Reliability:** 100% successful export in all supported formats
- **User Satisfaction:** Positive feedback on ease of use and output quality

---

### 8. Out of Scope

- Multilingual support (initial version)
- Real-time meeting participation (joining live calls)
- Advanced user management and permissions

---

### 9. Milestones & Timeline

1. **Week 1:** Research, requirements, and initial setup
2. **Week 2:** Audio input & transcription pipeline
3. **Week 3:** LLM-based analysis & structured output
4. **Week 4:** Export features, UI polish, and documentation

---

### 10. References

- [OpenAI Whisper Speech-to-Text Guide](https://platform.openai.com/docs/guides/speech-to-text)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Supabase Documentation](https://supabase.com/docs)
- [Assignment Details](./Assignment_Development.md)
- [Project README](./README.md)

---
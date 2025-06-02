import os
import json
import streamlit as st
from openai import OpenAI
from datetime import datetime

from utils.report_model import MeetingReport
from utils.transcribe import simple_transcribe, advanced_transcribe
from utils.transcribe import MAX_UPLOAD_SIZE_MB, WHISPER_SIZE_LIMIT_MB
from utils.exports import clean_transcript, export_to_json, export_to_pdf, export_to_markdown

# Initialize session state
if 'audio_data' not in st.session_state:
    st.session_state.audio_data = None
if 'raw_transcript' not in st.session_state:
    st.session_state.raw_transcript = None
if 'cleaned_transcript' not in st.session_state:
    st.session_state.cleaned_transcript = None
if 'report' not in st.session_state:
    st.session_state.report = None

st.set_page_config(page_title="Meeting Transcription Tool", page_icon=":memo:")

# Load OpenAI API key from Streamlit secrets
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

st.title("Meeting Transcription Tool")
st.write(
    """
    Upload or record your meeting audio and get accurate transcriptions, summaries, and action items.
    """
)
st.markdown("---")

# --- 1. Audio Input Section ---
st.subheader("1. Audio Input")

input_method = st.radio(
    "Choose audio input method:",
    ("Upload audio file", "Record audio"),
    horizontal=True
)

if input_method == "Upload audio file":
    audio_file = st.file_uploader(
        "Upload an audio file (.mp3, .wav)", 
        type=["mp3", "wav"],
        accept_multiple_files=False
    )
    if audio_file is not None:
        st.audio(audio_file, format="audio/wav" if audio_file.type == "audio/wav" else "audio/mp3")
        st.session_state.audio_data = audio_file
        st.success("Audio file uploaded! Ready for transcription.")
    else:
        st.info("Please upload an audio file to proceed.")
else:
    audio_recorded = st.audio_input("Record your meeting audio")
    if audio_recorded:
        st.audio(audio_recorded)
        st.session_state.audio_data = audio_recorded
        st.success("Audio recorded! Ready for transcription.")
    else:
        st.info("Click the button above to record your audio.")


# --- 2.Transcription Section ---
if st.session_state.audio_data is not None:
    st.markdown("---")
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        st.subheader("2. Transcription")
    with col3:
        transcribe_clicked = st.button("Transcribe", use_container_width=True)
    
    # Always show transcription tabs if we have data
    if st.session_state.raw_transcript is not None:
        tab_full, tab_timestamps, tab_raw = st.tabs([
            "Full Transcript", 
            "Transcript with Timestamps", 
            "Raw Transcription Data"
        ])
        
        # Tab 1: Full transcript text
        with tab_full:
            if st.session_state.cleaned_transcript:
                with st.expander("Meeting Transcript", expanded=False):
                    st.write(st.session_state.cleaned_transcript["text"])
        
        # Tab 2: Segments with timestamps
        with tab_timestamps:
            if st.session_state.cleaned_transcript:
                with st.expander("Transcript with Timestamps", expanded=False):
                    for i, segment in enumerate(st.session_state.cleaned_transcript["segments"]):
                        # Format timestamps as minutes:seconds
                        start_time = f"{int(segment['start']//60)}:{int(segment['start']%60):02d}"
                        end_time = f"{int(segment['end']//60)}:{int(segment['end']%60):02d}"
                        st.markdown(f"**[{start_time} - {end_time}]** {segment['text']}")
        
        # Tab 3: Raw transcription data
        with tab_raw:
            with st.expander("Raw Transcription Data", expanded=False):
                st.json(st.session_state.raw_transcript)
    
    if transcribe_clicked:
        # Get file size to determine if we need chunking
        file_size = st.session_state.audio_data.size
        
        # Check if file is too large even for chunking (> MAX_UPLOAD_SIZE_MB)
        if file_size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            st.error(f"File is too large ({file_size/(1024*1024):.1f} MB). Maximum allowed size is {MAX_UPLOAD_SIZE_MB} MB.")
            st.stop()
        
        if file_size > WHISPER_SIZE_LIMIT_MB * 1024 * 1024:  # Larger than Whisper limit (25MB)
            
            with st.spinner("Processing large audio file... This may take several minutes."):
                try:
                    # Set up progress indicators
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Define progress callback function
                    def update_progress(step, message, percentage):
                        progress_bar.progress(percentage)
                        status_text.info(message)
                    
                    # Use advanced transcribe function with progress updates
                    transcription = advanced_transcribe(
                        client, 
                        st.session_state.audio_data, 
                        progress_callback=update_progress
                    )
                    
                    # Store both raw and cleaned transcripts
                    st.session_state.raw_transcript = transcription
                    st.session_state.cleaned_transcript = clean_transcript(transcription)
                    
                    # Verify the duration coverage for user feedback
                    audio_duration = file_size / (10 * 1024 * 1024) * 60
                    
                    processed_duration = 0
                    if st.session_state.cleaned_transcript["segments"]:
                        # Get the last end timestamp to determine processed duration
                        processed_duration = st.session_state.cleaned_transcript["segments"][-1]["end"]
                    
                    if processed_duration > 0:
                        coverage = (processed_duration / audio_duration) * 100
                        if coverage < 90:
                            status_text.warning(f"Transcription completed with {coverage:.1f}% coverage.")
                        else:
                            status_text.success(f"Transcription complete! Processed {processed_duration/60:.1f} minutes of audio.")
                    else:
                        status_text.success("Transcription complete!")
                        
                    st.rerun()
                except Exception as e:
                    st.error(f"Transcription failed: {e}")
        else:
            # Use simple_transcribe for files under 25MB            
            with st.spinner("Transcribing audio..."):
                try:
                    transcription = simple_transcribe(client, st.session_state.audio_data)
                    
                    st.session_state.raw_transcript = transcription
                    st.session_state.cleaned_transcript = clean_transcript(transcription)
                    
                    st.success("Transcription complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Transcription failed: {e}")

# --- 3. Report Generation Section ---
if st.session_state.raw_transcript is not None:
    st.markdown("---")
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        st.subheader("3. Generate Report")
    with col3:
        generate_report_clicked = st.button("Generate Report", use_container_width=True)
    
    # Always show report in a tab with expander if we have a report
    if st.session_state.report is not None:
        tab_report = st.tabs(["Structured Meeting Report"])
        with tab_report[0]:
            with st.expander("Meeting Report Details", expanded=True):
                st.write(st.session_state.report)
    
    if generate_report_clicked:
        with st.spinner("Generating structured meeting report..."):
            try:
                response = client.responses.parse(
                    model="gpt-4.1-mini-2025-04-14", # gpt-4.1 mini
                    input=[
                        {"role": "system", "content": "From the given transcript, extract a structured meeting report with meeting_name, purpose, takeaways, detailed_summary (as sections with title and points), action_items (with assignee, title, description). Use the MeetingReport pydantic model."},
                        {"role": "user", "content": json.dumps(st.session_state.cleaned_transcript, indent=2)},
                    ],
                    text_format=MeetingReport,
                )
                # Store the report in session state
                st.session_state.report = response.output_parsed.model_dump()
                st.success("Meeting report generated!")
                st.rerun()
            except Exception as e:
                st.error(f"Report generation failed: {e}")

# --- 4. Export Section ---
if st.session_state.report is not None:
    st.markdown("---")
    st.subheader("4. Export Report")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        export_format = st.selectbox(
            "Export format",
            ["JSON", "Markdown", "PDF"],
            index=0,
            label_visibility="collapsed"
        )
    
    # Generate the file based on selected format in memory and provide download button
    try:
        if export_format == "JSON":
            temp_json_path = export_to_json(st.session_state.report)
            with open(temp_json_path, "r", encoding="utf-8") as f:
                file_data = f.read()
            filename = f"meeting_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            mime = "application/json"
            try:
                os.remove(temp_json_path)
            except Exception:
                pass
        elif export_format == "Markdown":
            temp_md_path = export_to_markdown(st.session_state.report)
            with open(temp_md_path, "r", encoding="utf-8") as f:
                file_data = f.read()
            filename = f"meeting_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            mime = "text/markdown"
            try:
                os.remove(temp_md_path)
            except Exception:
                pass
        else:
            with st.spinner("Preparing PDF..."):
                temp_pdf_path = export_to_pdf(st.session_state.report)
                with open(temp_pdf_path, "rb") as file:
                    file_data = file.read()
                filename = f"meeting_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                mime = "application/pdf"
                try:
                    os.remove(temp_pdf_path)
                except:
                    pass
        
        # Show download button in the second column
        with col2:
            st.download_button(
                label=f"Download Report",
                data=file_data,
                file_name=filename,
                mime=mime,
                use_container_width=True
            )
    except Exception as e:
        st.error(f"Export failed: {str(e)}")

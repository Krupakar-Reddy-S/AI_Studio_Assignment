# AI Studio Assignment Development and System Design

Note: Both the assignements are in the same repo, the System Design is in the `System_Design_Assignment` folder and the Development one is at the root of the repo.

For the Development Assignement i have chosen the Meetinf Transcription Tool (Optiion 3) and coincidentaly the System Design Assignment is also about a similar topic.

Before moving on my whole process, first i will give the reasoing behind why i have not chosen the other options.

## Why not the other options?

1. MCP Server for API Integration
   - I have good understanding of MCP and have worked with it in the past, and also blogged on it [here](https://www.kubeblogs.com/supercharging-ai-ides-with-model-context-protocol/)
   - And the assignement boils down to integrating an API with MCP, which needs some ideas but i wanted to do try something new.

2. AI-Powered Voice Journaling App
    - Felt too mmodle specific solution where it needed speech and realtime response with a good system prompt with probably 4o-realtime
    - or i would have to use TTS then model response and then STT, and i figured it did not really make sense when i could just use a model whihc does this all in one go.

3. Prompt Engineering Playground
    - I have built this as part of a larger tools in my previous internship, where we had a prompt engineering playground for our internal articles.
    - So i did not want to do this again, and also it felt like a very niche tool which would not be used by many people.

## My Development Process (Initial research and brainstorming)

### Understanding the Problem
The problem is to build a meeting transcription tool that can handle audio input, transcribe it, and extract key insights like action items and summaries. The tool should be robust, accurate, and user-friendly.

And i instantly choose my stack, a streamlit app with Whisper for transcription and LLMs for analysis.

### Researching Existing Solutions
I remeber using a similar tool in my previous internship which used to join Team meetings, and record the audio and email every atendee with the transcription and summary of the meeting along with the action items.

First thought in my mind was why does a tool need to join the meeting as a Bot  when it can just get the audio recording of the meeting and then process it.

But i later understood this was done to help with the speaker diarization, which is a very important feature for meeting transcription tools.

### What tools to use?
Of course Whisper for transcription, but i needed to see what all parameters i could play with and i just googled it and found this page whihc answered my previouse question on how to do speaker diarization with Whisper.

[OpenAi Speech to Text Guide](https://platform.openai.com/docs/guides/speech-to-text), Since i realised that Whisper wont interpret names correctly, i had to build a pipeline where i could most of the words right.

### Building the Pipeline

- Step 1: Audio Input
  - Use Streamlit to create a simple UI for audio recording/uploading.
  - Allow users to upload audio files or record directly from their microphone.

- Step 2: Audio Transcription
  - Use Whisper to transcribe the audio input.
  - First we will not have a very good run and some words will be misinterpreted, so we will use a custom vocabulary to correct the names and other important words.

- Step 3: Building the Vocabulary
  - From the transcription, we will extract the names of the people in the meeting  and any other specific words based on the context of the audio.
  - We will use structured output from a model with huge context like GPT-4.1 to extract the names and other important words.

- Step 4: Structured Summary Generation
  - Use the same model to generate a structured summary of the meeting, including:
    - Key discussion points
    - Action items
    - Important decisions made
  - But now we also have the vocabulary to correct the names and other important words in the summary.

- Step 5: Various Output Formats
  - Our initial output will be a Pydantic model which will be used to generate the output in various formats like:
    - PDF
    - Markdown
    - JSON
  - Use libraries like `pdfkit` for PDF generation, `markdown` for Markdown, and `json` for JSON output.

### Assumptions and Limitations

I have made a few assumptions to make the implementation simpler and more focused:
- The audio input will be in English and of good quality.
- Not to manage state in the streamlit app as it is too hard and instead have a simple DB solution like Supabase to store the audio files and transcriptions and summaries.
- The tool will not handle real-time transcription but will process uploaded audio files.
- The vocabulary will be built from the transcription and will not be user-defined.
- The tool can handle large audio files up to 250MB by automatically chunking them into smaller segments that fit within the Whisper API's 25MB limit.

### Developing the Application

Then with my plan in place i just made a simple PRD with the above assumptions in mind for the project.
Also from the PRD generated a Tasks file to keep track of the tasks and their status.

### Decisions Made During Development

First after the base features where down i was going to proceed with supabase integration and have a page to see hiostory of the transcriptions and summaries.

But then i realised a better fature for this implementation would be to make th actual tool more useful by allowing files larger than 25MB to be processed by automatically chunking them into smaller segments that fit within the Whisper API's 25MB limit.
This would allow users to upload larger audio files without worrying about the size limit, making the tool more versatile and user-friendly.
So i added a feature to automatically chunk the audio files into smaller segments that fit within the Whisper API's 25MB limit, and then process each segment separately and combine the results.

Similarly with Step 3 from the pipeline mentioned above, it was not that useful from the audio itself as it is not very easy to find who said what from just the raw audio transcription.
So i have found the way that enterprises and other available tools solve this and have mentioned it at the last part under the `Further Enhancements` section.

### Benchmarks and Examples

I have tested the tool with two audio files, one of 5 minutes and another of 33 minutes, to see how well it performs with different audio lengths, file types and complexities.

For each audio file, all 3 formats of output (PDF, Markdown, and JSON) are generated. These can be found in the `examples` folder.

Timings

| Audio File  | Duration (min) | Transcription Time (sec) | Analysis Time (sec) |
|-------------|----------------|--------------------------|---------------------|
| Audio 1     | 5              | 25                       | 10                  |
| Audio 2     | 33             | 120                      | 15                  |

### Final Implementation Details

The Meeting Transcription Tool is designed as a modular, extensible Streamlit application for robust meeting audio transcription, summarization, and export. Here’s a breakdown of the architecture and logic:

#### Application Structure
- **main.py**: Orchestrates the UI and workflow. Handles audio input (upload/record), triggers transcription, displays results in a tabbed/collapsible interface, and manages report generation and export. It uses session state to manage user progress and data.
- **utils/transcribe.py**: Contains the core logic for audio processing and transcription. It provides:
  - `simple_transcribe`: For direct Whisper API transcription of small files.
  - `advanced_transcribe`: For large files, splits audio into optimal chunks (starting with 20 minutes, falling back as needed), converts to mono/16kHz/16-bit, and processes each chunk, synchronizing timestamps for a seamless transcript. Includes robust error handling and progress callbacks.
  - Helper functions for chunking, duration calculation, and chunk export.
- **utils/exports.py**: Handles cleaning and exporting of transcripts and reports. Provides:
  - `clean_transcript`: Standardizes transcript output for downstream processing.
  - `export_to_json`, `export_to_markdown`, `export_to_pdf`: Export the structured report to various formats using temporary files for safe, clean file handling.
- **utils/report_model.py**: Defines the Pydantic models (`MeetingReport`, `ActionItem`, `DetailedSection`) for structured meeting summaries, action items, and detailed discussion points.

#### Key Implementation Highlights
- **Audio Chunking & Optimization**: Large audio files are split into the largest possible chunks that fit within Whisper API limits, with fallback to smaller sizes if needed. Audio is always converted to mono, 16kHz, 16-bit for optimal size and compatibility.
- **Progress & Logging**: The app provides real-time progress updates and logs chunking/transcription steps for transparency and debugging.
- **Export & Cleanup**: All exports use Python’s `tempfile` for safe, automatic cleanup, avoiding clutter in the project root.
- **User Experience**: The UI uses tabs and expanders for organized viewing of transcripts and reports, and provides clear feedback at each step.

---

### Further Enhancements (To make a viable tool for enterprises)
To enhance the Meeting Transcription Tool into a more robust and reusable solution for enterprises, we can consider the following enhancements:

To make this tool more powerful and reusable across organizations and platforms, the following enhancements are recommended:

#### 1. API & MCP Server Backend
- Build a REST API or Model Context Protocol (MCP) server around the transcription logic.
- Allow asynchronous job submission: users or services upload audio, receive a job ID, and poll or receive a webhook when the transcript/report is ready.
- This enables integration with other AI tools, automation pipelines, and external UIs.

#### 2. Automated Meeting Integration (e.g., Microsoft Teams, Google Meet)
- Deploy a bot user that watches a Teams/Google calendar, joins meetings automatically, and records per-user or turn-based audio.
- Use the backend to transcribe, generate structured reports, and email summaries/action items to all attendees.
- This approach can be adapted for any meeting platform as needed.

#### 3. Scalability & Extensibility
- The backend can be reused for batch processing, analytics, or as a plug-in for enterprise tools.
- Add features like speaker diarization, real-time transcription, multi-language support, and compliance controls as needed.

By decoupling the UI from the core logic and exposing the backend as an API/MCP service, this solution can power a wide range of meeting productivity tools, bots, and integrations across platforms.

### AI Tools and Technologies Used
- **IDE**: Visual Studio Code + GitHub Copilot for code completion and Agent mode. (though only the reactive prompting matters and correct model selection)
- **Models in Copilot**: Claude 3.7 for generated code blocks or util functions from my descriptions, GPT-4.1 for all other works as Claude 3.7 does too much while GPT-4.1 is more focused and accurate.
- **Transcription and LLM**: OpenAI Whisper for audio transcription and GPT-4.1 for structured analysis and summary generation.
- **Miscellaneous**: ChatGPT for brainstorming, suggestions, and code reviews along with some Perplexity searches for additional information.

## Conclusion

I had a great experience working on the Meeting Transcription Tool project. It allowed me to explore various aspects of audio processing, natural language understanding, and user interface design. The modular architecture and use of modern AI tools made it a rewarding challenge, and I believe the final product has the potential to be built on and make a really good tool which can significantly enhance meeting productivity for users.

I hope this detailed overview provides a clear understanding of my development process, the decisions made, and the final implementation help you in understanding my entire process and the tool itself.
Thank you for reviewing my work, and I look forward to any feedback!

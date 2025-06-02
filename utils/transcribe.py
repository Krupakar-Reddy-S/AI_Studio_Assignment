import os
import math
import tempfile
from pydub import AudioSegment

# Constants for audio chunking
MAX_CHUNK_SIZE_MB = 15  # Maximum size for each chunk in MB (reduced to avoid 413 errors)
BYTES_PER_MB = 1024 * 1024  # Convert MB to bytes
MAX_UPLOAD_SIZE_MB = 250  # Maximum upload file size in MB
WHISPER_SIZE_LIMIT_MB = 25  # Maximum allowed size for Whisper API

def simple_transcribe(client, audio_data):
    """
    Transcribe audio files under 25MB using the Whisper API directly.
    
    Args:
        client: OpenAI client instance
        audio_data: The file-like audio data
        
    Returns:
        Transcription result in Whisper API format
    """
    # Create a temporary file to store the audio data
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
        tmp_audio.write(audio_data.read())
        audio_data.seek(0)  # Reset file pointer
        tmp_audio_path = tmp_audio.name
    
    try:
        # Call Whisper API directly
        with open(tmp_audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
        return transcription
    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_audio_path):
            os.remove(tmp_audio_path)

def advanced_transcribe(client, audio_data, progress_callback=None):
    """
    Transcribe large audio files (>25MB) by splitting into chunks and combining results.
    
    Args:
        client: OpenAI client instance
        audio_data: The file-like audio data
        progress_callback: Optional callback function to update progress
        
    Returns:
        Combined transcription result in Whisper API format
    """
    # Get file size
    audio_data.seek(0, 2)  # Go to end of file
    file_size = audio_data.tell()  # Get file size
    audio_data.seek(0)  # Reset file pointer
    
    # Get audio duration to calculate optimal chunk size
    audio_duration_ms = get_audio_duration(audio_data)
    audio_data.seek(0)  # Reset file pointer
    
    # Calculate optimal chunk duration
    chunk_duration_ms = calculate_chunk_duration(file_size, audio_duration_ms)
    
    # Show processing info if callback is available
    if progress_callback:
        progress_callback(0, "Splitting audio into chunks", 10)
    
    # Calculate estimated chunk size for logging
    bytes_per_ms = file_size / audio_duration_ms
    estimated_chunk_size_mb = (chunk_duration_ms * bytes_per_ms) / (1024 * 1024)
    print(f"Processing audio ({file_size/1024/1024:.1f} MB, {audio_duration_ms/60000:.1f} min)")
    print(f"Each chunk will be ~{estimated_chunk_size_mb:.1f} MB (max: {WHISPER_SIZE_LIMIT_MB} MB)")
    
    # Apply extra safety factor if we're very close to the limit
    # Be more generous with the threshold to allow for larger chunks
    if estimated_chunk_size_mb > WHISPER_SIZE_LIMIT_MB * 0.85:
        safety_factor = (WHISPER_SIZE_LIMIT_MB * 0.8) / estimated_chunk_size_mb
        chunk_duration_ms = int(chunk_duration_ms * safety_factor)
        estimated_chunk_size_mb = (chunk_duration_ms * bytes_per_ms) / (1024 * 1024)
        print(f"Chunk size adjusted for safety: {estimated_chunk_size_mb:.1f} MB")
        
    # Ensure we're getting chunks of at least 8-10 minutes when possible
    minute_ms = 60 * 1000
    if chunk_duration_ms < 8 * minute_ms and estimated_chunk_size_mb < WHISPER_SIZE_LIMIT_MB * 0.7:
        # If our chunks are small but we have room to make them bigger, increase size
        target_duration_ms = 10 * minute_ms  # Target 10-minute chunks
        target_size_mb = (target_duration_ms * bytes_per_ms) / (1024 * 1024)
        
        if target_size_mb < WHISPER_SIZE_LIMIT_MB * 0.8:
            chunk_duration_ms = target_duration_ms
            estimated_chunk_size_mb = target_size_mb
            print(f"Chunk size increased to 10 minutes: {estimated_chunk_size_mb:.1f} MB")
    
    # Try to split the audio file into chunks
    try:
        # We need to verify the entire duration is being processed
        # First get the total duration
        audio_data.seek(0)  # Make sure we're at the start
        original_audio_duration = get_audio_duration(audio_data) 
        audio_data.seek(0)  # Reset for further processing
        
        print(f"Original audio duration: {original_audio_duration/1000:.2f} seconds ({original_audio_duration/60000:.1f} minutes)")
        
        # Now chunk the audio
        chunk_files = chunk_audio(audio_data, chunk_duration_ms)
        
        if not chunk_files:
            print("Warning: No chunks were created by chunk_audio function.")
            # Try with a more conservative chunk size
            print("Retrying with a smaller chunk size...")
            # Half the chunk duration to get smaller chunks
            chunk_duration_ms = int(chunk_duration_ms * 0.5)
            audio_data.seek(0)  # Reset pointer before trying again
            chunk_files = chunk_audio(audio_data, chunk_duration_ms)
            
            if not chunk_files:
                raise ValueError("Failed to create valid audio chunks even with reduced chunk size")
    except Exception as e:
        print(f"Error in chunk_audio: {str(e)}")
        # Last resort - use a very conservative approach with fixed small chunks
        print("Using emergency chunking with fixed small chunks...")
        
        # Reset file pointer in case it was modified
        audio_data.seek(0)
        
        # Save the audio to a temporary file for manual processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(audio_data.read())
            audio_data.seek(0)  # Reset file pointer
            temp_path = temp_audio.name
        
        try:
            # Load audio
            audio = AudioSegment.from_file(temp_path)
            total_duration = len(audio)
            chunk_files = []
            
            # Display total duration for verification
            print(f"Emergency chunking - audio duration: {total_duration/1000:.2f} seconds ({total_duration/60000:.1f} minutes)")
            print(f"Emergency chunking - attempting to use 20-minute chunks first")
            
            # Try 20-minute chunks for emergency chunking, then fall back if needed
            chunk_durations_ms = [
                20 * 60 * 1000,  # 20 minutes
                15 * 60 * 1000,  # 15 minutes
                10 * 60 * 1000,  # 10 minutes
                5 * 60 * 1000,   # 5 minutes
            ]
            
            # Calculate approximate size for each duration
            bytes_per_ms = file_size / total_duration if total_duration > 0 else 10000
            
            # Find the largest viable chunk size
            fixed_chunk_ms = 5 * 60 * 1000  # Default to 5 minutes
            
            # Print emergency chunking details for each duration
            print("Emergency chunking - chunk size estimates:")
            for duration in chunk_durations_ms:
                size_mb = (duration * bytes_per_ms) / (1024 * 1024)
                print(f"- {duration/(60*1000):.0f} minutes: {size_mb:.1f}MB")
                
                # If this size is small enough, use it
                if size_mb <= WHISPER_SIZE_LIMIT_MB * 0.9:
                    fixed_chunk_ms = duration
                    print(f"Emergency chunking - using {fixed_chunk_ms/(60*1000):.0f}-minute chunks")
                    break
            
            # Process in 10-minute chunks (or 5-minute if we had to fall back)
            for position in range(0, total_duration, fixed_chunk_ms):
                end_position = min(position + fixed_chunk_ms, total_duration)
                chunk = audio[position:end_position]
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as chunk_file:
                    chunk.export(chunk_file.name, format="mp3", bitrate="64k", parameters=["-q:a", "4"])
                    chunk_files.append(chunk_file.name)
                    print(f"Created emergency chunk {len(chunk_files)}: {position/1000:.1f}s to {end_position/1000:.1f}s")
                    
            # Clean up original file
            os.unlink(temp_path)
            
            if not chunk_files:
                raise ValueError("Emergency chunking failed to create any valid chunks")
                
        except Exception as emergency_error:
            raise ValueError(f"All chunking methods failed: {str(emergency_error)}")
    
    # Update progress after successful chunking
    if progress_callback:
        progress_callback(1, f"Split into {len(chunk_files)} chunks", 20)
    
    print(f"Successfully created {len(chunk_files)} audio chunks")
    
    # Process each chunk and combine results
    combined_result = process_audio_chunks(client, chunk_files, progress_callback)
    
    # Verify we processed the full duration
    if hasattr(combined_result, 'segments') and combined_result.segments:
        total_processed_duration = 0
        if isinstance(combined_result.segments[-1], dict):
            total_processed_duration = combined_result.segments[-1].get('end', 0)
        else:
            total_processed_duration = getattr(combined_result.segments[-1], 'end', 0)
            
        print(f"Transcription summary:")
        print(f"- Original audio duration: {audio_duration_ms/1000:.2f} seconds ({audio_duration_ms/60000:.1f} minutes)")
        print(f"- Processed duration: {total_processed_duration:.2f} seconds ({total_processed_duration/60:.1f} minutes)")
        print(f"- Coverage: {(total_processed_duration*1000/audio_duration_ms)*100:.1f}%")
        print(f"- Total segments: {len(combined_result.segments)}\n")
    
    # Return the unified transcript that matches Whisper API format
    return combined_result

def process_audio_chunks(client, chunk_files, progress_callback=None):
    """
    Process multiple audio chunks and combine into a unified transcript.
    This function ensures timestamps are continuous across chunks.
    
    Args:
        client: OpenAI client instance
        chunk_files: List of file paths to audio chunks
        progress_callback: Optional callback function to update progress
        
    Returns:
        Combined transcription result in Whisper API format
    """
    # First get all chunk durations to calculate precise timestamp offsets
    chunk_durations = []
    total_audio_duration = 0
    print(f"Reading durations for {len(chunk_files)} audio chunks...")
    
    for i, chunk_path in enumerate(chunk_files):
        try:
            audio = AudioSegment.from_file(chunk_path)
            # Store duration in seconds for timestamp calculations
            duration_sec = len(audio) / 1000
            chunk_durations.append(duration_sec)
            total_audio_duration += duration_sec
            print(f"Chunk {i+1} duration: {duration_sec:.2f} seconds (running total: {total_audio_duration:.2f}s)")
        except Exception as e:
            print(f"Error reading chunk duration: {str(e)}")
            # Estimate duration based on file size - better than zero
            try:
                file_size = os.path.getsize(chunk_path)
                # Rough estimate: ~10MB per minute for WAV files
                estimated_duration = (file_size / (10 * BYTES_PER_MB)) * 60
                chunk_durations.append(estimated_duration)
                total_audio_duration += estimated_duration
                print(f"Using estimated duration for chunk {i+1}: {estimated_duration:.2f} seconds (running total: {total_audio_duration:.2f}s)")
            except:
                # Fallback to a reasonable default (5 minutes)
                chunk_durations.append(300)
                total_audio_duration += 300
                print(f"Using default 300 second duration for chunk {i+1} (running total: {total_audio_duration:.2f}s)")
    
    # Now process each chunk with accurate timestamp adjustments
    all_segments = []
    full_text = ""
    time_offset = 0  # Accumulate time offset for each chunk
    template = None  # Store first valid response structure as template
    completion_percentage_base = 20  # Start at 20% when chunk processing begins
    successful_chunks = 0  # Track how many chunks we process successfully
    
    for i, chunk_path in enumerate(chunk_files):
        # Update progress if callback provided
        if progress_callback:
            # Calculate progress as percentage (from 20% to 90%)
            progress_percentage = completion_percentage_base + int((i / len(chunk_files)) * 70)
            progress_callback(i, f"Transcribing chunk {i+1} of {len(chunk_files)}", progress_percentage)
        
        try:
            # Verify chunk size is within API limits
            file_size = os.path.getsize(chunk_path)
            if file_size > WHISPER_SIZE_LIMIT_MB * BYTES_PER_MB:
                print(f"Warning: Chunk {i+1} exceeds Whisper's limit ({file_size/BYTES_PER_MB:.2f} MB). Skipping.")
                continue
            
            # Transcribe this chunk with backup response handling
            try:
                with open(chunk_path, "rb") as audio_file:
                    # First attempt with verbose_json format
                    chunk_result = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",
                        timestamp_granularities=["segment"],
                    )
            except Exception as api_error:
                print(f"Error with verbose_json format: {str(api_error)}")
                print("Retrying with standard JSON format...")
                
                # Retry with standard JSON format if verbose_json fails
                with open(chunk_path, "rb") as audio_file:
                    chunk_result = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="json",
                    )
                    
                    # Convert simple response to our needed format
                    if isinstance(chunk_result, dict):
                        # Just extract text if we only get a simple response
                        chunk_text = chunk_result.get("text", "")
                        
                        # Create a minimal segment covering the whole chunk
                        chunk_segments = [{
                            "id": 0,
                            "start": 0,
                            "end": chunk_durations[i] if i < len(chunk_durations) else 0,
                            "text": chunk_text
                        }]
                        
                        # Create an object-like structure
                        class SimpleResponse:
                            def __init__(self, text, segments):
                                self.text = text
                                self.segments = segments
                        
                        chunk_result = SimpleResponse(chunk_text, chunk_segments)
            
            # Store template structure if this is the first successful transcription
            if template is None:
                template = chunk_result
            
            # Add this chunk's text to full text
            if hasattr(chunk_result, 'text'):
                full_text += chunk_result.text + " "
            elif isinstance(chunk_result, dict) and "text" in chunk_result:
                full_text += chunk_result["text"] + " "
            
            # Adjust timestamps and add to unified segments list
            adjusted_segments = []
            
            # Get segments from object or dictionary
            segments_to_process = []
            if hasattr(chunk_result, 'segments'):
                segments_to_process = chunk_result.segments
            elif isinstance(chunk_result, dict) and "segments" in chunk_result:
                segments_to_process = chunk_result["segments"]
            
            for segment in segments_to_process:
                try:
                    # Handle both object and dictionary segments
                    if isinstance(segment, dict):
                        # For dictionary segments
                        segment_dict = {
                            'id': segment.get('id', 0),
                            'start': segment.get('start', 0) + time_offset,
                            'end': segment.get('end', 0) + time_offset,
                            'text': segment.get('text', ""),
                            # Default values for required fields
                            'avg_logprob': segment.get('avg_logprob', 0.0),
                            'compression_ratio': segment.get('compression_ratio', 1.0),
                            'no_speech_prob': segment.get('no_speech_prob', 0.0),
                            'temperature': segment.get('temperature', 0.0),
                            'tokens': segment.get('tokens', [])
                        }
                        # Just add as dictionary rather than trying to create an object
                        all_segments.append(segment_dict)
                    else:
                        # For object segments
                        segment_dict = {
                            'id': getattr(segment, 'id', 0),
                            'seek': getattr(segment, 'seek', 0),
                            'start': getattr(segment, 'start', 0) + time_offset,
                            'end': getattr(segment, 'end', 0) + time_offset,
                            'text': getattr(segment, 'text', ""),
                            # Default values for required fields
                            'avg_logprob': getattr(segment, 'avg_logprob', 0.0),
                            'compression_ratio': getattr(segment, 'compression_ratio', 1.0),
                            'no_speech_prob': getattr(segment, 'no_speech_prob', 0.0),
                            'temperature': getattr(segment, 'temperature', 0.0),
                            'tokens': getattr(segment, 'tokens', [])
                        }
                        
                        try:
                            # Try to create a proper segment object
                            adj_segment = type(segment)(**segment_dict)
                            adjusted_segments.append(adj_segment)
                        except Exception as obj_error:
                            print(f"Error creating segment object: {obj_error}")
                            # Fallback to dictionary if object creation fails
                            all_segments.append(segment_dict)
                except Exception as e:
                    print(f"Error processing segment: {e}")
                    # Create minimal segment if everything else fails
                    minimal_segment = {
                        'id': 0,
                        'start': time_offset,
                        'end': time_offset + 1,  # 1 second default duration
                        'text': "..."  # Placeholder for missing text
                    }
                    all_segments.append(minimal_segment)
            
            # Add adjusted segments to our complete list if any were created
            if adjusted_segments:
                all_segments.extend(adjusted_segments)
                
            seg_count = len(adjusted_segments) if adjusted_segments else "dictionary-based segments"
            print(f"Chunk {i+1} processed: {seg_count}")
            
            # Count this as a successful chunk
            successful_chunks += 1
            
            # Update time offset for the next chunk
            time_offset += chunk_durations[i]
            
        except Exception as e:
            print(f"Error processing chunk {i+1}: {str(e)}")
            # Try to extract any useful information from the chunk if possible
            try:
                with open(chunk_path, "rb") as audio_file:
                    # Try with text-only format as last resort
                    simple_result = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )
                    
                    if simple_result:
                        print(f"Recovered text-only content from chunk {i+1}")
                        # Add to full text
                        full_text += str(simple_result) + " "
                        
                        # Create a simple segment
                        basic_segment = {
                            'id': len(all_segments),
                            'start': time_offset,
                            'end': time_offset + chunk_durations[i],
                            'text': str(simple_result)
                        }
                        all_segments.append(basic_segment)
            except Exception as recovery_error:
                print(f"Recovery attempt also failed: {recovery_error}")
        finally:
            # Clean up the temporary chunk file
            if os.path.exists(chunk_path):
                os.unlink(chunk_path)
    
    # Print summary of processing
    print(f"Processed {successful_chunks} of {len(chunk_files)} chunks successfully")
    print(f"Collected {len(all_segments)} segments in total")
    
    # If we have no segments but some text, create at least one segment
    if not all_segments and full_text:
        print("Creating fallback segment from collected text")
        all_segments = [{
            'id': 0,
            'start': 0,
            'end': sum(chunk_durations),  # Use total duration
            'text': full_text.strip()
        }]
    
    # Error if no segments were collected and no text was found
    if not all_segments and not full_text:
        raise ValueError("No transcription segments or text were collected from any chunk")
    
    # Handle the case where we don't have a valid template but have segments
    if template is None:
        print("No template structure found. Creating dictionary response.")
        # Create a simple dictionary response format
        combined_result = {
            "text": full_text.strip(),
            "segments": all_segments,
            "language": "en"  # Default language
        }
    else:
        # Use the template structure for the response format
        combined_result = template
        
        # Ensure text field is set
        if hasattr(combined_result, 'text'):
            combined_result.text = full_text.strip()
        
        # Handle segments based on whether they're objects or dictionaries
        all_dict_segments = all(isinstance(s, dict) for s in all_segments)
        
        if all_dict_segments and hasattr(combined_result, 'segments'):
            # If we're working with dictionary segments, ensure consistent format
            combined_result.segments = all_segments 
        elif not all_dict_segments and hasattr(combined_result, 'segments'):
            # Mix of objects and dictionaries - use only objects
            combined_result.segments = [s for s in all_segments if not isinstance(s, dict)]
        else:
            # Fallback - just attach segments as a property
            combined_result.segments = all_segments
    
    # Final progress update if callback provided
    if progress_callback:
        progress_callback(len(chunk_files), "Transcription complete", 100)
    
    return combined_result

def get_audio_duration(audio_data):
    """
    Get the duration of an audio segment in milliseconds.
    
    Args:
        audio_data: The file-like audio data
        
    Returns:
        Duration in milliseconds
    """
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(audio_data.read())
            temp_path = temp_audio.name
            
        audio_data.seek(0)  # Reset file pointer
        audio = AudioSegment.from_file(temp_path)
        return len(audio)
    except Exception as e:
        print(f"Error getting audio duration: {str(e)}")
        # Provide a fallback estimation based on file size
        # Assuming average quality audio (16-bit PCM stereo at 44.1kHz)
        # ~10MB per minute of audio
        audio_data.seek(0, 2)  # Seek to end
        file_size_bytes = audio_data.tell()
        audio_data.seek(0)  # Reset
        
        estimated_duration_ms = (file_size_bytes / (10 * 1024 * 1024)) * 60 * 1000
        print(f"Using estimated duration based on file size: {estimated_duration_ms/60000:.1f} minutes")
        return estimated_duration_ms
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

def chunk_audio(audio_data, segment_duration_ms):
    """
    Split audio into chunks of specified duration with stricter size control.
    Ensures the entire audio file is covered by creating sequential chunks.
    
    Args:
        audio_data: The file-like audio data
        segment_duration_ms: Duration of each segment in milliseconds
    
    Returns:
        List of temporary file paths containing audio chunks
    """
    # Save the audio to a temporary file, preserving original format
    content_type = getattr(audio_data, 'type', None)
    suffix = ".mp3"  # Default
    
    # Try to detect file format from content_type if available
    if content_type:
        if 'wav' in content_type.lower():
            suffix = ".wav"
        elif 'mp3' in content_type.lower():
            suffix = ".mp3"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
        temp_audio.write(audio_data.read())
        audio_data.seek(0)  # Reset file pointer
        temp_path = temp_audio.name
    
    # Load the audio file (pydub can auto-detect format)
    audio = AudioSegment.from_file(temp_path)
    total_duration = len(audio)
    chunk_files = []
    position = 0  # Current position in the audio in milliseconds
    
    # Print total duration for debugging
    print(f"Total audio duration: {total_duration/1000:.2f} seconds ({total_duration/60000:.1f} minutes)")
    
    # Calculate actual max chunk size in bytes (with margin for safety)
    max_chunk_size_bytes = int(WHISPER_SIZE_LIMIT_MB * 0.85 * BYTES_PER_MB)  # 85% of limit for safety
    
    # Calculate approximately how many chunks we'll need for continuous coverage
    estimated_chunks = math.ceil(total_duration / segment_duration_ms)
    print(f"Preparing to create approximately {estimated_chunks} chunks")
    print(f"Target chunk duration: {segment_duration_ms/1000:.1f} seconds ({segment_duration_ms/60000:.1f} minutes)")
    
    # Continue chunking until we've covered the entire file
    while position < total_duration:
        # Calculate end time for this chunk
        end_position = min(position + segment_duration_ms, total_duration)
        chunk_number = len(chunk_files) + 1
        
        # Extract chunk with exact timing
        chunk = audio[position:end_position]
        chunk_duration = len(chunk) / 1000  # Duration in seconds
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as chunk_file:
            chunk.export(chunk_file.name, format="mp3", bitrate="64k", parameters=["-q:a", "4"])
            chunk_size = os.path.getsize(chunk_file.name)
            
            # If the chunk is too large, reduce its duration
            if chunk_size > max_chunk_size_bytes:
                # Before reducing, log the actual vs. estimated size
                print(f"WARNING: Chunk {chunk_number} is {chunk_size/BYTES_PER_MB:.2f}MB, " +
                      f"larger than our estimate for {segment_duration_ms/1000:.1f}s")

                # Check a smaller sample to get more accurate size estimation
                test_duration = 1 * 60 * 1000  # 1 minute test
                test_chunk = audio[position:position + test_duration]
                with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as test_file:
                    test_chunk.export(test_file.name, format="mp3", bitrate="64k", parameters=["-q:a", "4"])
                    test_size = os.path.getsize(test_file.name)

                # Recalculate bytes per second based on this test
                actual_bytes_per_ms = test_size / test_duration
                print(f"Recalibrating size estimates: {actual_bytes_per_ms * 1000 / BYTES_PER_MB:.2f}MB per second")
                
                # Calculate safe duration based on actual size
                safe_duration = int(max_chunk_size_bytes / actual_bytes_per_ms * 0.9)  # 90% of safe limit
                
                # Ensure it's not too small
                min_duration = 2 * 60 * 1000  # 2 minutes minimum
                safe_duration = max(safe_duration, min_duration)
                
                print(f"Adjusting to {safe_duration/1000:.1f} seconds per chunk")
                
                # Create a smaller chunk with recalibrated size
                smaller_chunk = audio[position:position + safe_duration]
                smaller_duration = len(smaller_chunk) / 1000  # Duration in seconds
                
                # Save the smaller chunk
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as smaller_file:
                    smaller_chunk.export(smaller_file.name, format="mp3", bitrate="64k", parameters=["-q:a", "4"])
                    smaller_size = os.path.getsize(smaller_file.name)
                    
                    if smaller_size <= max_chunk_size_bytes:
                        # Delete the original chunk file
                        os.unlink(chunk_file.name)
                        # Use the smaller chunk instead
                        chunk_files.append(smaller_file.name)
                        print(f"Chunk {chunk_number}: Reduced size at {position/1000:.1f}s: " +
                              f"{smaller_size / BYTES_PER_MB:.2f} MB, duration: {smaller_duration:.1f}s")
                        # Update position by the actual processed duration
                        position += safe_duration
                    else:
                        # If still too large, try an even smaller chunk
                        os.unlink(smaller_file.name)
                        
                        # Fallback to 5-minute chunks and retry
                        fallback_duration = min(5 * 60 * 1000, safe_duration // 2)
                        final_attempt = audio[position:position + fallback_duration]
                        final_duration = len(final_attempt) / 1000

                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as final_file:
                            final_attempt.export(final_file.name, format="mp3", bitrate="64k", parameters=["-q:a", "4"])
                            if os.path.getsize(final_file.name) <= max_chunk_size_bytes:
                                os.unlink(chunk_file.name)
                                chunk_files.append(final_file.name)
                                print(f"Chunk {chunk_number}: Final reduced at {position/1000:.1f}s: " +
                                    f"{os.path.getsize(final_file.name) / BYTES_PER_MB:.2f} MB, " +
                                    f"duration: {final_duration:.1f}s")
                                position += fallback_duration
                            else:
                                os.unlink(final_file.name)
                                os.unlink(chunk_file.name)
                                print(f"Warning: Chunk at {position/1000:.1f}s still too large. " +
                                      "Falling back to 2-minute chunks.")
                                # Final fallback - use 2 minute chunks
                                small_fallback = 2 * 60 * 1000
                                last_attempt = audio[position:position + small_fallback]
                                
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as last_file:
                                    last_attempt.export(last_file.name, format="mp3", bitrate="64k", parameters=["-q:a", "4"])
                                    chunk_files.append(last_file.name)
                                    print(f"Emergency chunk: {os.path.getsize(last_file.name) / BYTES_PER_MB:.2f}MB, " +
                                          f"duration: {len(last_attempt)/1000:.1f}s")
                                position += small_fallback
            else:
                # If size is ok, add to our list
                chunk_files.append(chunk_file.name)
                print(f"Chunk {chunk_number}: Added at {position/1000:.1f}s: " +
                      f"{chunk_size / BYTES_PER_MB:.2f} MB, duration: {chunk_duration:.1f}s")
                # Update position to next segment
                position = end_position
    
    # Clean up original temp file
    os.unlink(temp_path)
    
    # Ensure we have at least one chunk
    if not chunk_files:
        raise ValueError("Could not create any valid audio chunks within size limits")
    
    # Verify chunking coverage 
    print(f"\nChunking completion summary:")
    print(f"- Original audio duration: {total_duration/1000:.2f} seconds ({total_duration/60000:.1f} minutes)")
    
    # Calculate and verify the total chunked duration
    total_chunked_duration = 0
    for i, chunk_path in enumerate(chunk_files):
        try:
            chunk_audio = AudioSegment.from_file(chunk_path)
            chunk_duration = len(chunk_audio) / 1000
            total_chunked_duration += chunk_duration
            print(f"- Chunk {i+1}: {chunk_duration:.2f} seconds")
        except Exception as e:
            print(f"- Error verifying chunk {i+1}: {str(e)}")
    
    coverage_percentage = (total_chunked_duration * 1000 / total_duration) * 100
    print(f"- Total chunked duration: {total_chunked_duration:.2f} seconds ({total_chunked_duration/60:.1f} minutes)")
    print(f"- Coverage: {coverage_percentage:.1f}%")
    
    # Warn if coverage is significantly under 100%
    if coverage_percentage < 95:
        print(f"WARNING: Audio chunking coverage is only {coverage_percentage:.1f}%. Some parts of the audio may not be transcribed.")
    
    return chunk_files

def calculate_chunk_duration(file_size_bytes, audio_duration_ms):
    """
    Calculate the optimal chunk duration based on file size and audio duration.
    Start with 20-minute chunks, then reduce by 5 minutes until reaching a viable size (min 5 minutes).
    
    Args:
        file_size_bytes: Size of the audio file in bytes
        audio_duration_ms: Duration of the audio file in milliseconds
        
    Returns:
        Duration for each chunk in milliseconds
    """
    # Calculate bytes per millisecond for this specific audio file
    bytes_per_ms = file_size_bytes / audio_duration_ms
    
    # Define common durations
    minute_in_ms = 60 * 1000
    twenty_min_ms = 20 * minute_in_ms
    fifteen_min_ms = 15 * minute_in_ms
    ten_min_ms = 10 * minute_in_ms
    five_min_ms = 5 * minute_in_ms
    
    # Start with 20-minute chunks and decrease if needed
    chunk_durations = [twenty_min_ms, fifteen_min_ms, ten_min_ms, five_min_ms]
    target_duration_ms = five_min_ms  # Default fallback
    
    # Print size estimates for different durations
    print("Calculating chunk size estimates:")
    for duration in chunk_durations:
        size_mb = (duration * bytes_per_ms) / BYTES_PER_MB
        print(f"- {duration/minute_in_ms:.0f}min: {size_mb:.1f}MB")
    
    print(f"API limit: {WHISPER_SIZE_LIMIT_MB}MB, Target size: {MAX_CHUNK_SIZE_MB}MB")
    
    # Find the largest viable chunk size, starting from largest
    for duration in chunk_durations:
        size_mb = (duration * bytes_per_ms) / BYTES_PER_MB
        
        # If this size is acceptably below the limit, use it
        if size_mb <= WHISPER_SIZE_LIMIT_MB * 0.9:
            target_duration_ms = duration
            break
    
    # If even 5-minute chunks are too large, calculate custom size
    if target_duration_ms == five_min_ms:
        five_min_size_mb = (five_min_ms * bytes_per_ms) / BYTES_PER_MB
        
        if five_min_size_mb > WHISPER_SIZE_LIMIT_MB * 0.9:
            # Calculate a more appropriate duration, aim for 80% of limit
            target_duration_ms = int((WHISPER_SIZE_LIMIT_MB * 0.8 * BYTES_PER_MB) / bytes_per_ms)
            # Round to nearest minute for cleaner splitting
            target_duration_ms = int(target_duration_ms / minute_in_ms) * minute_in_ms
            
            # Ensure at least 2 minutes per chunk
            min_chunk_duration_ms = 2 * minute_in_ms
            target_duration_ms = max(min_chunk_duration_ms, target_duration_ms)
    
    # Print the selected chunk duration for debugging
    print(f"Selected chunk duration: {target_duration_ms/minute_in_ms:.1f} minutes")
    
    return target_duration_ms

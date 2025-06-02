import json
import tempfile
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem

def clean_transcript(raw_transcript):
    """
    Clean the transcript format to only include essential information.
    Handles raw dictionary, TranscriptionVerbose object, mixed segment formats, 
    or combined chunks from the Whisper API.
    
    Returns a standardized dictionary with:
    - text: Full transcript text
    - segments: List of segments with start, end, and text fields
    """
    # Initialize cleaned dict with default values
    cleaned = {
        "text": "",
        "segments": []
    }
    
    # Extract text from transcript
    if isinstance(raw_transcript, dict):
        # Handle dictionary input
        cleaned["text"] = raw_transcript.get("text", "")
    else:
        # Handle object input (from OpenAI client)
        cleaned["text"] = raw_transcript.text if hasattr(raw_transcript, 'text') else ""
    
    # Process segments based on the input type
    segments_to_process = []
    
    if isinstance(raw_transcript, dict):
        # Get segments from dictionary
        segments_to_process = raw_transcript.get("segments", [])
    elif hasattr(raw_transcript, 'segments'):
        # Get segments from object
        segments_to_process = raw_transcript.segments
    
    # Process each segment to extract relevant fields
    for segment in segments_to_process:
        if isinstance(segment, dict):
            # Dictionary segment
            cleaned["segments"].append({
                "start": segment.get("start", 0),
                "end": segment.get("end", 0),
                "text": segment.get("text", "")
            })
        else:
            # Object segment
            segment_data = {
                "start": getattr(segment, 'start', 0),
                "end": getattr(segment, 'end', 0),
                "text": getattr(segment, 'text', "")
            }
            cleaned["segments"].append(segment_data)
    
    # Sort segments by start time to ensure chronological order
    # (important for chunked transcriptions where segments might be out of order)
    if cleaned["segments"]:
        cleaned["segments"] = sorted(cleaned["segments"], key=lambda x: x["start"])
    
    return cleaned


def export_to_json(report_data):
    """Export the report to a JSON file using a temporary file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json', mode='w', encoding='utf-8') as temp_file:
        json.dump(report_data, temp_file, indent=2)
        return temp_file.name

def convert_report_to_markdown(report_data):
    """Convert report data to markdown format"""
    md_content = []
    
    # Meeting Name
    md_content.append(f"# {report_data['meeting_name']}\n")
    
    # Purpose
    md_content.append("## Purpose")
    md_content.append(f"{report_data['purpose']}\n")
    
    # Key Takeaways
    md_content.append("## Key Takeaways")
    for takeaway in report_data['takeaways']:
        md_content.append(f"- {takeaway}")
    md_content.append("")
    
    # Detailed Summary
    md_content.append("## Detailed Summary\n")
    for section in report_data['detailed_summary']:
        md_content.append(f"### {section['section_title']}")
        for point in section['points']:
            md_content.append(f"- {point}")
        md_content.append("")
    
    # Action Items
    md_content.append("## Action Items\n")
    for item in report_data['action_items']:
        md_content.append(f"### {item['title']}")
        md_content.append(f"**Assignee:** {item['assignee']}")
        md_content.append(f"**Description:** {item['description']}\n")
    
    return "\n".join(md_content)

def export_to_markdown(report_data):
    """Export report to markdown file using a temporary file."""
    md_content = convert_report_to_markdown(report_data)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.md', mode='w', encoding='utf-8') as temp_file:
        temp_file.write(md_content)
        return temp_file.name

def export_to_pdf(report_data):
    """Export report to PDF file"""
    # Use a temporary file instead of saving to the root directory
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        filename = temp_file.name
        
    try:
        # Create the PDF document
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Create custom styles
        styles = getSampleStyleSheet()
        
        # Use a professional blue for headings
        heading_blue = colors.HexColor('#0066cc')
        
        custom_h1 = ParagraphStyle(
            name='CustomH1',
            parent=styles['Heading1'],
            textColor=heading_blue,
            fontSize=18,
            spaceAfter=20
        )
        custom_h2 = ParagraphStyle(
            name='CustomH2',
            parent=styles['Heading2'],
            textColor=heading_blue,
            fontSize=14,
            spaceAfter=15
        )
        custom_h3 = ParagraphStyle(
            name='CustomH3',
            parent=styles['Heading3'],
            textColor=heading_blue,  # Use the same blue color
            fontSize=12,
            spaceBefore=6,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )

        # Build the document content
        story = []
        
        # Title
        story.append(Paragraph(report_data['meeting_name'], custom_h1))
        story.append(Spacer(1, 12))
        
        # Purpose
        story.append(Paragraph('Purpose', custom_h2))
        story.append(Paragraph(report_data['purpose'], styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Create custom bullet style with more spacing
        bullet_style = ParagraphStyle(
            name='BulletStyle',
            parent=styles['Normal'],
            leftIndent=20,
            spaceBefore=2,
            spaceAfter=5
        )
        
        # Key Takeaways
        story.append(Paragraph('Key Takeaways', custom_h2))
        story.append(Spacer(1, 6))
        takeaway_items = [ListItem(Paragraph(item, styles['Normal'])) for item in report_data['takeaways']]
        story.append(ListFlowable(takeaway_items, bulletType='bullet', leftIndent=20))
        story.append(Spacer(1, 12))
        
        # Detailed Summary
        story.append(Paragraph('Detailed Summary', custom_h2))
        story.append(Spacer(1, 6))
        for section in report_data['detailed_summary']:
            story.append(Paragraph(section['section_title'], custom_h3))
            story.append(Spacer(1, 4))
            points = [ListItem(Paragraph(point, styles['Normal'])) for point in section['points']]
            story.append(ListFlowable(points, bulletType='bullet', leftIndent=20))
            story.append(Spacer(1, 12))
        
        # Action Items
        story.append(Paragraph('Action Items', custom_h2))
        story.append(Spacer(1, 6))
        for item in report_data['action_items']:
            story.append(Paragraph(item['title'], custom_h3))
            
            # Create a custom style for the action item details
            detail_style = ParagraphStyle(
                name='DetailStyle',
                parent=styles['Normal'],
                leftIndent=10,
                spaceBefore=2,
                spaceAfter=2
            )
            
            story.append(Paragraph(f"<b>Assignee:</b> {item['assignee']}", detail_style))
            story.append(Paragraph(f"<b>Description:</b> {item['description']}", detail_style))
            story.append(Spacer(1, 12))
        
        # Generate the PDF
        doc.build(story)
        return filename
    except Exception as e:
        raise Exception(f"Failed to export to PDF: {str(e)}")

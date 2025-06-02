from pydantic import BaseModel, Field
from typing import List

class ActionItem(BaseModel):
    """
    An action item assigned during the meeting.
    """
    assignee: str = Field(..., description="Name of the person responsible for the action item.")
    title: str = Field(..., description="Short title of the action item.")
    description: str = Field(..., description="Detailed description of the action item.")

class DetailedSection(BaseModel):
    """
    A section of the detailed summary, focused on a topic discussed in the meeting.
    """
    section_title: str = Field(..., description="Title or topic of this section.")
    points: List[str] = Field(..., description="List of detailed discussion points for this section.")

class MeetingReport(BaseModel):
    """
    Structured summary of a meeting, including meeting name, purpose, takeaways, detailed summary (with sections), action items, and the full transcript.
    """
    meeting_name: str = Field(..., description="The name or title of the meeting.")
    purpose: str = Field(..., description="The main purpose or topic of the meeting.")
    takeaways: List[str] = Field(..., description="Key points and decisions from the meeting.")
    detailed_summary: List[DetailedSection] = Field(..., description="Detailed breakdown of discussion topics, grouped by section.")
    action_items: List[ActionItem] = Field(..., description="List of action items with assignees, titles, and descriptions.")

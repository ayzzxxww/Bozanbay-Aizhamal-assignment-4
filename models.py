
class PostAnalysis(BaseModel):
    """LLM Call #1 — per-post classification"""

    topic: str = Field(
        description="Topic category: Politics / Tech / Business / Sports / Entertainment / Society / Other"
    )
    sentiment: str = Field(
        description="Sentiment: Positive / Negative / Neutral"
    )
    is_breaking: str = Field(
        description="Breaking news indicator: Yes / No"
    )
    emotion: str = Field(
        description="Dominant emotion: Fear / Anger / Joy / Sadness / Surprise / Neutral"
    )
    keywords: str = Field(
        description="2-4 key words from the post, comma-separated"
    )


class ChannelReport(BaseModel):
    """LLM Call #2 — per-channel aggregated analysis"""

    top_topic: str = Field(
        description="The most dominant topic in this channel"
    )
    overall_mood: str = Field(
        description="Overall mood of the channel: Positive / Negative / Neutral / Mixed"
    )
    mood_score: str = Field(
        description="Mood score from -10 (very negative) to +10 (very positive), as a string like '-3' or '+7'"
    )
    summary: str = Field(
        description="2-3 sentence summary of what this channel mostly talks about and its general tone"
    )
    content_style: str = Field(
        description="Content style: Breaking News / Analysis / Opinion / Entertainment / Mixed"
    )
    key_themes: str = Field(
        description="3-5 recurring themes or subjects, comma-separated"
    )


# ============================================================================
# Pipeline State
# ============================================================================

class PipelineState(BaseModel):
    """State for the LangGraph processing pipeline"""

    # Input
    channels_file: str = ""                        # Path to channels.txt

    # Node 1 output — raw posts per channel
    raw_posts: Dict[str, List[str]] = {}           # {channel_name: [post_text, ...]}

    # Node 2 output — per-post analysis
    post_analyses: Dict[str, List[Dict[str, Any]]] = {}  # {channel_name: [PostAnalysis.dict(), ...]}

    # Node 3 output — per-channel report
    channel_reports: Dict[str, Dict[str, Any]] = {}      # {channel_name: ChannelReport.dict()}

    # Node 4 output — final export path
    result_path: str = ""
    progress: int = 0

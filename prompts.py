
PROMPT_CLASSIFY_POST = """Analyze the following Telegram post and classify it.

Rules:
1. topic — write it
2. sentiment — choose ONE
3. is_breaking — "Yes" or "No"
4. emotion — choose ONE emotion
5. keywords — 2-4 key
6. Be objective. Ignore formatting, links, and emojis.
7. Return strictly valid JSON matching the PostAnalysis schema.

Post text:
{post_text}
"""


# ============================================================================
# Prompt for channel-level report (LLM Call #2)
# ============================================================================

PROMPT_CHANNEL_REPORT = """You are analyzing a Telegram news channel. 
Below is a statistical summary of {post_count} posts from the channel "{channel_name}".
Topic distribution:
{topic_distribution}
Sentiment distribution:
{sentiment_distribution}
Emotion distribution:
{emotion_distribution}

Breaking news posts: {breaking_count} out of {post_count}

Sample keywords (most frequent): {top_keywords}


Rules:
1. top_topic — what topic
2. overall_mood — your choice
3. mood_score — integer
4. summary — what it about
5. content_style — your choice
6. key_themes —  key words
7. Return schema
"""

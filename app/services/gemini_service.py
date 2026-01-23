"""
Gemini AI Service

Handles all interactions with Google's Gemini AI API.

Features:
- Content summarization
- Quality scoring
- Topic extraction
- Tag generation
- Content clustering

Uses the google-genai package.
"""

import os
import logging
from typing import List, Dict, Optional
from google import genai

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Service for interacting with Google Gemini AI.
    
    This service provides AI-powered content analysis including:
    - Summarization (long text → short summary)
    - Quality scoring (rate content 0-10)
    - Topic extraction (identify main topic)
    - Tag generation (extract relevant keywords)
    
    Example:
        gemini = GeminiService()
        summary = gemini.summarize("Long article text here...")
        quality = gemini.rate_quality("Article content...")
        topic = gemini.extract_topic("Article Title", "Summary...")
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini service.
        
        Args:
            api_key: Gemini API key. If not provided, reads from GEMINI_API_KEY env var.
        """
        # Get API key
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found! "
                "Set GEMINI_API_KEY environment variable or pass api_key parameter."
            )
        
        # Initialize client with new API
        self.client = genai.Client(api_key=self.api_key)
        
        # Model to use
        self.model_name = 'models/gemini-2.5-flash'
        
        logger.info("GeminiService initialized successfully")
    
    def summarize(
        self,
        content: str,
        max_words: int = 200,
        style: str = "concise"
    ) -> str:
        """
        Summarize content into a shorter version.
        
        Args:
            content: The text to summarize
            max_words: Maximum words in summary (default: 200)
            style: Summary style - "concise", "detailed", or "bullet" (default: "concise")
        
        Returns:
            str: Summarized text
        
        Example:
            summary = gemini.summarize(
                "Long article about GPT-5...",
                max_words=150,
                style="concise"
            )
        """
        if not content or not content.strip():
            logger.warning("Empty content provided for summarization")
            return ""
        
        # Build prompt based on style
        style_instructions = {
            "concise": "Write a concise, engaging summary",
            "detailed": "Write a comprehensive summary covering all key points",
            "bullet": "Write a summary in bullet point format"
        }
        
        instruction = style_instructions.get(style, style_instructions["concise"])
        
        prompt = f"""
{instruction} of the following content.

Requirements:
- Maximum {max_words} words
- Focus on the most important information
- Write in clear, engaging prose
- Maintain factual accuracy
- Do not add information not present in the original

Content:
{content}

Summary:
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            summary = response.text.strip()
            logger.info(f"Generated summary ({len(summary.split())} words)")
            return summary
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            # Return truncated version as fallback
            words = content.split()[:max_words]
            return ' '.join(words) + '...'
    
    def rate_quality(self, content: str) -> int:
        """
        Rate content quality on a scale of 0-10.
        
        Evaluates:
        - Relevance to AI/tech news
        - Information density
        - Clarity and coherence
        - Novelty and importance
        
        Args:
            content: The text to rate
        
        Returns:
            int: Quality score from 0-10
        
        Example:
            score = gemini.rate_quality("Article about new AI breakthrough...")
            # Returns: 8
        """
        if not content or not content.strip():
            logger.warning("Empty content provided for quality rating")
            return 0
        
        prompt = f"""
Rate the following content on a scale of 0-10 for its value in an AI/technology news digest.

Criteria:
- Relevance to AI, machine learning, or technology (0-3 points)
- Information quality and accuracy (0-3 points)
- Novelty and importance (0-2 points)
- Clarity and readability (0-2 points)

Content:
{content[:1000]}

Respond with ONLY a single number from 0-10, nothing else.
Score:
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            # Extract number from response
            score_text = response.text.strip()
            
            # Try to parse the number
            try:
                score = int(score_text)
                # Clamp to 0-10 range
                score = max(0, min(10, score))
                logger.info(f"Quality score: {score}/10")
                return score
            except ValueError:
                logger.warning(f"Could not parse score: {score_text}")
                return 5  # Default middle score
                
        except Exception as e:
            logger.error(f"Quality rating failed: {e}")
            return 5  # Default middle score on error
    
    def extract_topic(self, title: str, summary: str) -> str:
        """
        Extract main topic from content.
        
        Returns a short, hyphenated topic identifier like:
        - "gpt-5-release"
        - "ai-safety-research"
        - "llm-benchmark"
        
        Args:
            title: Article title
            summary: Article summary
        
        Returns:
            str: Topic identifier (lowercase, hyphenated, 2-4 words)
        
        Example:
            topic = gemini.extract_topic(
                "OpenAI Releases GPT-5",
                "OpenAI announced GPT-5 today..."
            )
            # Returns: "gpt-5-release"
        """
        if not title and not summary:
            logger.warning("Empty title and summary for topic extraction")
            return "general-ai-news"
        
        prompt = f"""
Extract the main topic from this article in 2-4 words.

Title: {title}
Summary: {summary}

Requirements:
- Return ONLY the topic, nothing else
- Use lowercase letters only
- Separate words with hyphens (-)
- Be specific and descriptive
- Focus on the core subject matter

Examples:
- "gpt-5-release"
- "ai-safety-regulation"
- "llm-benchmark-results"
- "robotics-breakthrough"

Topic:
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            topic = response.text.strip().lower()
            
            # Clean up the topic
            # Remove quotes, extra spaces, etc.
            topic = topic.replace('"', '').replace("'", '').strip()
            
            # Ensure it's hyphenated
            if ' ' in topic:
                topic = topic.replace(' ', '-')
            
            logger.info(f"Extracted topic: {topic}")
            return topic
            
        except Exception as e:
            logger.error(f"Topic extraction failed: {e}")
            return "ai-news"  # Default fallback
    
    def extract_tags(self, content: str, max_tags: int = 5) -> List[str]:
        """
        Extract relevant tags/keywords from content.
        
        Args:
            content: The text to analyze
            max_tags: Maximum number of tags to return (default: 5)
        
        Returns:
            list: List of relevant tags
        
        Example:
            tags = gemini.extract_tags("Article about GPT-5 and transformer models...")
            # Returns: ["gpt-5", "transformers", "language-models", "openai"]
        """
        if not content or not content.strip():
            logger.warning("Empty content for tag extraction")
            return []
        
        prompt = f"""
Extract {max_tags} relevant tags/keywords from this content.

Content:
{content[:1000]}

Requirements:
- Return ONLY the tags, one per line
- Use lowercase
- Use hyphens for multi-word tags
- Focus on specific, meaningful terms
- Prioritize technical terms and proper nouns

Tags:
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            # Parse tags from response
            tags_text = response.text.strip()
            tags = [
                tag.strip().lower().replace(' ', '-')
                for tag in tags_text.split('\n')
                if tag.strip()
            ]
            
            # Limit to max_tags
            tags = tags[:max_tags]
            
            logger.info(f"Extracted {len(tags)} tags")
            return tags
            
        except Exception as e:
            logger.error(f"Tag extraction failed: {e}")
            return []
    
    def generate_cluster_summary(self, articles_data: List[Dict]) -> str:
        """
        Generate unified summary from multiple articles on same topic.
        
        Args:
            articles_data: List of dicts with 'title' and 'summary' keys
        
        Returns:
            str: Unified summary covering all articles
        
        Example:
            articles = [
                {'title': 'GPT-5 Released', 'summary': 'OpenAI announced...'},
                {'title': 'GPT-5 Analysis', 'summary': 'Experts say...'},
            ]
            cluster_summary = gemini.generate_cluster_summary(articles)
        """
        if not articles_data:
            return ""
        
        # Build combined context
        articles_text = "\n\n".join([
            f"Source {i+1}: {article.get('title', 'Untitled')}\n{article.get('summary', '')}"
            for i, article in enumerate(articles_data)
        ])
        
        prompt = f"""
Multiple sources reported on the same topic. Create ONE comprehensive summary (200 words) that:

1. Synthesizes information from all sources
2. Highlights key points and main developments
3. Notes any different perspectives or additional details
4. Maintains factual accuracy
5. Writes in engaging, clear prose

Sources:
{articles_text}

Unified Summary:
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            cluster_summary = response.text.strip()
            logger.info(f"Generated cluster summary from {len(articles_data)} articles")
            return cluster_summary
            
        except Exception as e:
            logger.error(f"Cluster summary generation failed: {e}")
            # Fallback: return first article's summary
            return articles_data[0].get('summary', '') if articles_data else ''
    
    def test_connection(self) -> bool:
        """
        Test if Gemini API connection works.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents="Say 'OK' if you can read this."
            )
            
            result = 'ok' in response.text.lower()
            
            if result:
                logger.info("Gemini connection test: SUCCESS")
            else:
                logger.warning("Gemini connection test: UNEXPECTED RESPONSE")
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini connection test FAILED: {e}")
            return False
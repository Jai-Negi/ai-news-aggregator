"""
DigestGenerator Agent

Generates email digests from processed articles.

Responsibilities:
- Get high-quality articles from database
- Group articles by topic (optional)
- Generate beautiful HTML email
- Mark articles as included in digest

Example:
    generator = DigestGeneratorAgent()
    html = generator.generate_digest()
    # Returns: Beautiful HTML email ready to send
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, date

# Import models
from app.models import Article, db

logger = logging.getLogger(__name__)


class DigestGeneratorAgent:
    """
    Agent responsible for generating email digests.
    
    This agent:
    1. Gets high-quality unprocessed articles
    2. Groups them by topic (optional)
    3. Generates HTML email
    4. Marks articles as included
    
    Example:
        generator = DigestGeneratorAgent()
        html = generator.generate_digest(max_articles=10)
        print(html)  # Beautiful HTML email
    """
    
    def __init__(self):
        """Initialize the agent."""
        logger.info("DigestGeneratorAgent initialized")
    
    def generate_digest(
        self,
        max_articles: int = 10,
        min_quality: int = 7,
        digest_date: Optional[date] = None
    ) -> Optional[str]:
        """
        Generate HTML email digest.
        
        Args:
            max_articles: Maximum articles to include (default: 10)
            min_quality: Minimum quality score (default: 7)
            digest_date: Date for this digest (default: today)
        
        Returns:
            str: HTML email content, or None if no articles
        
        Example:
            generator = DigestGeneratorAgent()
            html = generator.generate_digest(max_articles=10, min_quality=7)
        """
        if digest_date is None:
            digest_date = date.today()
        
        logger.info(f"Generating digest for {digest_date}")
        
        # Get articles ready for digest
        articles = self._get_articles_for_digest(max_articles, min_quality)
        
        if not articles:
            logger.warning("No articles available for digest")
            return None
        
        logger.info(f"Found {len(articles)} articles for digest")
        
        # Generate HTML
        html = self._generate_html(articles, digest_date)
        
        # Mark articles as included
        self._mark_articles_included(articles, digest_date)
        
        logger.info(f"Digest generated successfully with {len(articles)} articles")
        
        return html
    
    def _get_articles_for_digest(
        self,
        max_articles: int,
        min_quality: int
    ) -> List[Article]:
        """
        Get articles ready for digest.
        
        Args:
            max_articles: Maximum number to return
            min_quality: Minimum quality score
        
        Returns:
            list: Article objects sorted by quality
        """
        try:
            articles = Article.query.filter(
                Article.included_in_digest == False,
                Article.quality_score >= min_quality
            ).order_by(
                Article.quality_score.desc(),
                Article.published_at.desc()
            ).limit(max_articles).all()
            
            return articles
            
        except Exception as e:
            logger.error(f"Error getting articles for digest: {e}")
            return []
    
    def _generate_html(
        self,
        articles: List[Article],
        digest_date: date
    ) -> str:
        """
        Generate HTML email from articles.
        
        Args:
            articles: List of Article objects
            digest_date: Date for this digest
        
        Returns:
            str: HTML email content
        """
        # Generate article HTML sections
        articles_html = []
        
        for i, article in enumerate(articles, 1):
            article_html = self._generate_article_html(article, i)
            articles_html.append(article_html)
        
        # Combine into full email
        full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News Digest - {digest_date.strftime('%B %d, %Y')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0 0 10px 0;
            font-size: 28px;
        }}
        .header .date {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        .article {{
            margin-bottom: 30px;
            padding-bottom: 30px;
            border-bottom: 1px solid #ecf0f1;
        }}
        .article:last-child {{
            border-bottom: none;
        }}
        .article-number {{
            display: inline-block;
            background-color: #4CAF50;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            text-align: center;
            line-height: 30px;
            font-weight: bold;
            margin-right: 10px;
        }}
        .article-title {{
            color: #2c3e50;
            font-size: 20px;
            font-weight: bold;
            margin: 10px 0;
            display: inline;
        }}
        .article-meta {{
            color: #7f8c8d;
            font-size: 13px;
            margin: 8px 0;
        }}
        .quality-badge {{
            display: inline-block;
            background-color: #4CAF50;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .article-summary {{
            color: #555;
            font-size: 15px;
            line-height: 1.6;
            margin: 15px 0;
        }}
        .article-link {{
            display: inline-block;
            color: #4CAF50;
            text-decoration: none;
            font-weight: 500;
            margin-top: 10px;
        }}
        .article-link:hover {{
            text-decoration: underline;
        }}
        .tags {{
            margin-top: 10px;
        }}
        .tag {{
            display: inline-block;
            background-color: #ecf0f1;
            color: #555;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 5px;
            margin-top: 5px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            color: #7f8c8d;
            font-size: 13px;
        }}
        .footer a {{
            color: #4CAF50;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI News Digest</h1>
            <div class="date">{digest_date.strftime('%A, %B %d, %Y')}</div>
            <div class="date" style="margin-top: 5px;">{len(articles)} articles curated for you</div>
        </div>
        
        {''.join(articles_html)}
        
        <div class="footer">
            <p>Generated with ❤️ by AI News Aggregator</p>
            <p>Powered by Gemini AI • Content from MIT Tech Review, Google AI, YouTube & more</p>
        </div>
    </div>
</body>
</html>
"""
        
        return full_html
    
    def _generate_article_html(self, article: Article, number: int) -> str:
        """
        Generate HTML for a single article.
        
        Args:
            article: Article object
            number: Article number in digest
        
        Returns:
            str: HTML for this article
        """
        # Get source info
        source_name = "Unknown"
        source_url = "#"
        
        if article.content_item and article.content_item.source:
            source_name = article.content_item.source.name
            source_url = article.content_item.url
        
        # Format tags
        tags_html = ""
        if article.relevance_tags:
            tags = article.relevance_tags[:5]  # Limit to 5 tags
            tags_html = '<div class="tags">'
            for tag in tags:
                tags_html += f'<span class="tag">#{tag}</span>'
            tags_html += '</div>'
        
        # Quality badge color
        quality = article.quality_score or 0
        badge_color = '#4CAF50' if quality >= 9 else '#FFA726' if quality >= 7 else '#999'
        
        article_html = f"""
        <div class="article">
            <div>
                <span class="article-number">{number}</span>
                <h2 class="article-title">{article.title}</h2>
                <span class="quality-badge" style="background-color: {badge_color};">
                    {quality}/10
                </span>
            </div>
            
            <div class="article-meta">
                📰 {source_name} • 
                📅 {article.published_at.strftime('%b %d, %Y') if article.published_at else 'Recently'}
                {f" • 📂 {article.topic_cluster}" if article.topic_cluster else ""}
            </div>
            
            <div class="article-summary">
                {article.summary}
            </div>
            
            {tags_html}
            
            <a href="{source_url}" class="article-link" target="_blank">
                Read full article →
            </a>
        </div>
        """
        
        return article_html
    
    def _mark_articles_included(
        self,
        articles: List[Article],
        digest_date: date
    ):
        """
        Mark articles as included in digest.
        
        Args:
            articles: List of Article objects
            digest_date: Date of this digest
        """
        try:
            for article in articles:
                article.included_in_digest = True
                article.digest_date = digest_date
            
            db.session.commit()
            logger.info(f"Marked {len(articles)} articles as included in digest")
            
        except Exception as e:
            logger.error(f"Error marking articles as included: {e}")
            db.session.rollback()
    
    def preview_digest(
        self,
        max_articles: int = 5,
        min_quality: int = 7
    ) -> Optional[str]:
        """
        Generate preview without marking articles as included.
        
        Useful for testing the digest layout.
        
        Args:
            max_articles: Maximum articles to include
            min_quality: Minimum quality score
        
        Returns:
            str: HTML email content
        """
        logger.info("Generating preview digest (articles not marked)")
        
        articles = self._get_articles_for_digest(max_articles, min_quality)
        
        if not articles:
            logger.warning("No articles available for preview")
            return None
        
        html = self._generate_html(articles, date.today())
        
        # Don't mark as included (preview only)
        logger.info(f"Preview generated with {len(articles)} articles")
        
        return html
    
    def get_stats(self) -> Dict:
        """
        Get digest statistics.
        
        Returns:
            dict: Statistics about digests
        """
        try:
            total_articles = Article.query.count()
            included = Article.query.filter_by(included_in_digest=True).count()
            available = Article.query.filter_by(included_in_digest=False).count()
            
            # Get average quality of available articles
            avg_quality = db.session.query(
                db.func.avg(Article.quality_score)
            ).filter_by(included_in_digest=False).scalar() or 0
            
            return {
                "total_articles": total_articles,
                "included_in_digest": included,
                "available_for_digest": available,
                "avg_quality_available": round(avg_quality, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
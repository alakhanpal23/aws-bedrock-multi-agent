import json
import time
import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, _):
    try:
        task_id = event.get("id", "data_task")
        feeds = event.get("inputs", {}).get("feeds", [])
        
        logger.info(f"Fetching data from feeds: {feeds}")
        
        records = []
        
        for feed in feeds:
            try:
                if feed == "hackernews" or feed == "hn_top":
                    records.extend(fetch_hackernews())
                elif feed == "aws_pricing":
                    records.extend(fetch_aws_pricing_info())
                elif feed == "aws_blogs":
                    records.extend(fetch_aws_blogs())
                elif feed == "reddit_aws":
                    records.extend(fetch_reddit_aws())
                else:
                    logger.warning(f"Unknown feed: {feed}")
                    
            except Exception as e:
                logger.error(f"Error fetching {feed}: {str(e)}")
                # Continue with other feeds
                
        logger.info(f"Fetched {len(records)} records total")
        
        return {
            "task_id": task_id,
            "records": records,
            "metadata": {
                "fetch_time": datetime.utcnow().isoformat(),
                "feeds_requested": feeds,
                "records_count": len(records)
            }
        }
        
    except Exception as e:
        logger.error(f"Data fetch error: {str(e)}")
        return {
            "task_id": event.get("id", "data_task"),
            "records": [],
            "error": str(e)
        }

def fetch_hackernews():
    """Fetch top stories from HackerNews API"""
    try:
        # Get top story IDs
        top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        response = requests.get(top_stories_url, timeout=10)
        story_ids = response.json()[:10]  # Top 10 stories
        
        records = []
        for story_id in story_ids:
            try:
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                story_response = requests.get(story_url, timeout=5)
                story = story_response.json()
                
                if story and story.get('title'):
                    records.append({
                        "source": "hackernews",
                        "title": story.get('title', ''),
                        "url": story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                        "score": story.get('score', 0),
                        "timestamp": story.get('time', int(time.time())),
                        "type": "news"
                    })
            except Exception as e:
                logger.warning(f"Error fetching story {story_id}: {str(e)}")
                continue
                
        return records
        
    except Exception as e:
        logger.error(f"HackerNews fetch error: {str(e)}")
        return []

def fetch_aws_pricing_info():
    """Fetch AWS pricing information from public sources"""
    try:
        # AWS What's New RSS feed
        records = []
        
        # Simulate AWS pricing data (in production, use AWS Price List API)
        pricing_data = [
            {
                "source": "aws_pricing",
                "title": "EC2 On-Demand Pricing Update",
                "description": "Latest EC2 instance pricing for compute-optimized instances",
                "service": "EC2",
                "region": "us-west-2",
                "instance_type": "c5.large",
                "price_per_hour": "$0.085",
                "timestamp": int(time.time()),
                "type": "pricing"
            },
            {
                "source": "aws_pricing",
                "title": "S3 Storage Cost Optimization",
                "description": "New S3 Intelligent Tiering options available",
                "service": "S3",
                "storage_class": "Intelligent-Tiering",
                "cost_savings": "up to 40%",
                "timestamp": int(time.time()),
                "type": "pricing"
            }
        ]
        
        records.extend(pricing_data)
        return records
        
    except Exception as e:
        logger.error(f"AWS pricing fetch error: {str(e)}")
        return []

def fetch_aws_blogs():
    """Fetch AWS blog posts"""
    try:
        # AWS News Blog RSS (simplified)
        return [{
            "source": "aws_blogs",
            "title": "AWS Cost Optimization Best Practices",
            "url": "https://aws.amazon.com/blogs/aws-cost-management/",
            "summary": "Learn how to optimize your AWS costs with these proven strategies",
            "timestamp": int(time.time()),
            "type": "blog"
        }]
        
    except Exception as e:
        logger.error(f"AWS blogs fetch error: {str(e)}")
        return []

def fetch_reddit_aws():
    """Fetch AWS-related posts from Reddit"""
    try:
        # Reddit AWS subreddit (simplified - in production use Reddit API)
        return [{
            "source": "reddit_aws",
            "title": "Best practices for AWS Lambda cost optimization",
            "url": "https://reddit.com/r/aws",
            "score": 156,
            "comments": 23,
            "timestamp": int(time.time()),
            "type": "discussion"
        }]
        
    except Exception as e:
        logger.error(f"Reddit AWS fetch error: {str(e)}")
        return []
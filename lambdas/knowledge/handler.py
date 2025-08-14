import json
import os
import logging
import requests
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inline retrieval functions
OS = f"https://{os.getenv('OS_ENDPOINT', 'your-opensearch-endpoint.region.es.amazonaws.com')}"
HEADERS = {"Content-Type":"application/json"}

def hybrid_search(query, k=8):
    try:
        # Simple text search for now
        search_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "body"]
                }
            },
            "size": k
        }
        
        response = requests.post(f"{OS}/documents_v1/_search", 
                               headers=HEADERS, 
                               json=search_query, 
                               auth=(os.getenv('OS_USERNAME', 'admin'), os.getenv('OS_PASSWORD', 'your-password')),
                               timeout=10)
        
        if response.status_code == 200:
            hits = response.json().get('hits', {}).get('hits', [])
            return [{
                "title": hit['_source'].get('title', 'Unknown'),
                "body": hit['_source'].get('body', ''),
                "url": hit['_source'].get('url', ''),
                "score": hit['_score']
            } for hit in hits]
        else:
            logger.error(f"Search failed: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return []

def handler(event, context):
    try:
        task_id = event.get("id", "knowledge_task")
        query = event.get("inputs", {}).get("query", "aws cloud cost")
        
        logger.info(f"Searching knowledge base for: {query}")
        
        passages = hybrid_search(query, k=6)
        
        citations = []
        for p in passages:
            if isinstance(p, dict):
                citations.append({
                    "title": p.get("title", "Unknown"),
                    "url": p.get("url", ""),
                    "source": "document"
                })
        
        logger.info(f"Found {len(passages)} relevant passages")
        
        return {
            "task_id": task_id,
            "passages": passages,
            "citations": citations,
            "query": query,
            "results_count": len(passages)
        }
        
    except Exception as e:
        logger.error(f"Knowledge search error: {str(e)}")
        return {
            "task_id": event.get("id", "knowledge_task"),
            "passages": [],
            "citations": [],
            "error": str(e)
        }
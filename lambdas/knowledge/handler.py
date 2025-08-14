import json
import sys
import os
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common.retrieval import hybrid_search
from common.error_handler import handle_lambda_errors, validate_required_fields, retry_with_backoff, opensearch_circuit_breaker

logger = logging.getLogger()
logger.setLevel(logging.INFO)

@handle_lambda_errors
def handler(event, context):
    # Validate required fields
    validate_required_fields(event, ['inputs.query'])
    
    task_id = event.get("id", "knowledge_task")
    query = event.get("inputs", {}).get("query", "aws cloud cost")
    
    logger.info(f"Searching knowledge base for: {query}")
    
    # Use circuit breaker for OpenSearch calls
    passages = opensearch_circuit_breaker.call(search_with_retry, query)
    
    citations = []
    for p in passages:
        if isinstance(p, dict):
            citations.append({
                "title": p.get("title", "Unknown"),
                "url": p.get("url", ""),
                "source": p.get("source_type", "document")
            })
    
    logger.info(f"Found {len(passages)} relevant passages")
    
    return {
        "task_id": task_id,
        "passages": passages,
        "citations": citations,
        "query": query,
        "results_count": len(passages)
    }

@retry_with_backoff(max_retries=3, base_delay=1.0)
def search_with_retry(query, k=6):
    """Search with retry logic"""
    try:
        return hybrid_search(query, k=k)
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        # Return empty results on failure rather than crashing
        return []
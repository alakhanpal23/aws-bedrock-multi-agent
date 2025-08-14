import sys
import os
import json
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common.bedrock_client import call_llm
from common.error_handler import handle_lambda_errors, retry_with_backoff, bedrock_circuit_breaker

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SYSTEM_PROMPT = """You are a synthesis agent that combines information from multiple sources into a coherent, well-cited response.

Given outputs from knowledge retrieval, data fetching, and action agents, create a comprehensive answer that:
1. Synthesizes the information logically
2. Includes proper citations
3. Highlights key insights
4. Provides actionable recommendations

Format your response in markdown with clear sections and bullet points where appropriate."""

@handle_lambda_errors
def handler(event, context):
    logger.info("Starting synthesis of agent outputs")
    
    # Extract results from previous agents
    fanout_results = event.get("FanOutResults", [])
    
    if not fanout_results:
        logger.warning("No fanout results to synthesize")
        return {
            "answer_md": "No information was retrieved to synthesize.",
            "citations": [],
            "status": "no_data"
        }
    
    # Prepare context for synthesis
    context = {
        "agent_outputs": fanout_results,
        "output_count": len(fanout_results)
    }
    
    # Use circuit breaker for Bedrock calls
    answer_md = bedrock_circuit_breaker.call(
        synthesize_with_retry,
        context,
        "Create a comprehensive answer based on the agent outputs"
    )
    
    # Extract citations from agent outputs
    citations = extract_citations(fanout_results)
    
    logger.info(f"Synthesis complete with {len(citations)} citations")
    
    return {
        "answer_md": answer_md,
        "citations": citations,
        "status": "success",
        "sources_used": len(citations)
    }

@retry_with_backoff(max_retries=2, base_delay=2.0)
def synthesize_with_retry(context, user_message):
    """Synthesize with retry logic"""
    return call_llm(
        system=SYSTEM_PROMPT,
        context_obj=context,
        user_msg=user_message,
        max_tokens=1000
    )

def extract_citations(fanout_results):
    """Extract citations from all agent outputs"""
    citations = []
    
    for result in fanout_results:
        if isinstance(result, dict):
            # From knowledge agent
            if 'citations' in result:
                citations.extend(result['citations'])
            
            # From data agent
            if 'records' in result:
                for record in result['records']:
                    if isinstance(record, dict) and record.get('url'):
                        citations.append({
                            "title": record.get('title', 'Data Source'),
                            "url": record.get('url', ''),
                            "source": record.get('source', 'external')
                        })
    
    # Remove duplicates
    seen = set()
    unique_citations = []
    for citation in citations:
        key = (citation.get('title', ''), citation.get('url', ''))
        if key not in seen:
            seen.add(key)
            unique_citations.append(citation)
    
    return unique_citations
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inline Bedrock client
bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')

def call_llm(system, context_obj, user_msg, max_tokens=1000):
    try:
        prompt = f"System: {system}\n\nContext: {json.dumps(context_obj)}\n\nUser: {user_msg}\n\nAssistant:"
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            })
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text']
        
    except Exception as e:
        logger.error(f"Bedrock error: {str(e)}")
        return f"Error generating response: {str(e)}"

SYSTEM_PROMPT = """You are a synthesis agent that combines information from multiple sources into a coherent, well-cited response.

Given outputs from knowledge retrieval, data fetching, and action agents, create a comprehensive answer that:
1. Synthesizes the information logically
2. Includes proper citations
3. Highlights key insights
4. Provides actionable recommendations

Format your response in markdown with clear sections and bullet points where appropriate."""

def handler(event, context):
    try:
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
        
        # Generate synthesis
        answer_md = call_llm(
            system=SYSTEM_PROMPT,
            context_obj=context,
            user_msg="Create a comprehensive answer based on the agent outputs",
            max_tokens=1000
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
        
    except Exception as e:
        logger.error(f"Synthesis error: {str(e)}")
        return {
            "answer_md": f"Error generating synthesis: {str(e)}",
            "citations": [],
            "status": "error"
        }

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
import json
import boto3
import os
import logging
import uuid
from datetime import datetime
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common.embeddings import embed
from common.retrieval import os_put

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
textract = boto3.client('textract')

def handler(event, context):
    """
    Triggered by S3 uploads to docs bucket
    Processes PDFs/text files and indexes them in OpenSearch
    """
    try:
        # Handle S3 event
        if 'Records' in event:
            for record in event['Records']:
                bucket = record['s3']['bucket']['name']
                key = record['s3']['object']['key']
                
                logger.info(f"Processing document: s3://{bucket}/{key}")
                
                # Skip if not a document
                if not is_document(key):
                    logger.info(f"Skipping non-document: {key}")
                    continue
                
                # Process the document
                process_document(bucket, key)
                
        # Handle direct invocation
        else:
            bucket = event.get('bucket')
            key = event.get('key')
            if bucket and key:
                process_document(bucket, key)
            else:
                return {"error": "Missing bucket or key"}
        
        return {"status": "success", "message": "Documents processed"}
        
    except Exception as e:
        logger.error(f"Document ingestion error: {str(e)}")
        return {"error": str(e)}

def process_document(bucket, key):
    """Process a single document"""
    try:
        # Get file extension
        file_ext = key.lower().split('.')[-1]
        
        if file_ext == 'pdf':
            text = extract_text_from_pdf(bucket, key)
        elif file_ext in ['txt', 'md']:
            text = extract_text_from_text_file(bucket, key)
        else:
            logger.warning(f"Unsupported file type: {file_ext}")
            return
        
        if not text or len(text.strip()) < 50:
            logger.warning(f"Insufficient text extracted from {key}")
            return
        
        # Chunk the text
        chunks = chunk_text(text, max_chunk_size=1000)
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            try:
                # Generate embedding
                embedding = embed(chunk)
                
                # Create document for OpenSearch
                doc_id = f"{key.replace('/', '_')}_{i}"
                document = {
                    "title": extract_title(key, chunk if i == 0 else ""),
                    "body": chunk,
                    "url": f"s3://{bucket}/{key}",
                    "source_type": "document",
                    "timestamp": datetime.utcnow().isoformat(),
                    "embedding_vector": embedding,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "file_path": key
                }
                
                # Index in OpenSearch
                os_put(f"/documents_v1/_doc/{doc_id}", document)
                logger.info(f"Indexed chunk {i+1}/{len(chunks)} for {key}")
                
            except Exception as e:
                logger.error(f"Error processing chunk {i} of {key}: {str(e)}")
                continue
        
        logger.info(f"Successfully processed {key} into {len(chunks)} chunks")
        
    except Exception as e:
        logger.error(f"Error processing document {key}: {str(e)}")
        raise

def extract_text_from_pdf(bucket, key):
    """Extract text from PDF using Textract"""
    try:
        # For small PDFs, use synchronous detection
        response = textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        
        # Extract text from blocks
        text_blocks = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_blocks.append(block['Text'])
        
        return '\n'.join(text_blocks)
        
    except Exception as e:
        logger.error(f"Textract error for {key}: {str(e)}")
        return ""

def extract_text_from_text_file(bucket, key):
    """Extract text from text files"""
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        return obj['Body'].read().decode('utf-8')
    except Exception as e:
        logger.error(f"Error reading text file {key}: {str(e)}")
        return ""

def chunk_text(text, max_chunk_size=1000, overlap=100):
    """Split text into overlapping chunks"""
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            for i in range(end, max(start + max_chunk_size//2, end - 200), -1):
                if text[i] in '.!?\n':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def extract_title(file_path, first_chunk):
    """Extract title from file path or first chunk"""
    # Use filename as base title
    filename = file_path.split('/')[-1]
    title = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
    
    # Try to get better title from first chunk
    if first_chunk:
        lines = first_chunk.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and len(line) < 100:  # Reasonable title length
                # If it looks like a title (short, no periods except at end)
                if line.count('.') <= 1 and not line.endswith(':'):
                    title = line
                    break
    
    return title[:200]  # Limit title length

def is_document(key):
    """Check if file is a supported document type"""
    supported_extensions = ['.pdf', '.txt', '.md', '.doc', '.docx']
    return any(key.lower().endswith(ext) for ext in supported_extensions)
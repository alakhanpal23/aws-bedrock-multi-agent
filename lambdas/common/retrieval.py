import os, requests, json
from .embeddings import embed

OS = f"https://{os.getenv('OS_ENDPOINT')}"
HEADERS = {"Content-Type":"application/json"}

def os_put(path, doc): return requests.put(OS+path, headers=HEADERS, data=json.dumps(doc), timeout=10)
def os_post(path, q):  return requests.post(OS+path, headers=HEADERS, data=json.dumps(q), timeout=10)

def hybrid_search(query, k=8):
    v = embed(query)
    knn = {
      "size": k*3,
      "query": { "knn": { "embedding_vector": { "vector": v, "k": k*3 } } }
    }
    bm25 = {
      "size": k*3,
      "query": { "multi_match": { "query": query, "fields": ["title^2","body"] } }
    }
    kv = os_post("/documents_v1/_search", knn).json()["hits"]["hits"]
    kb = os_post("/documents_v1/_search", bm25).json()["hits"]["hits"]
    # naive RRF
    scores, out = {}, []
    for i,h in enumerate(kv): scores[h["_id"]] = scores.get(h["_id"],0)+1/(60+i)
    for i,h in enumerate(kb): scores[h["_id"]] = scores.get(h["_id"],0)+1/(60+i)
    for doc_id in sorted(scores, key=scores.get, reverse=True)[:k]:
        # fetch source from whichever list contains it
        src = next((h["_source"] for h in kv if h["_id"]==doc_id), None) or next((h["_source"] for h in kb if h["_id"]==doc_id), None)
        out.append(src)
    return out
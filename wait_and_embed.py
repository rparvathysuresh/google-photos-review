import time
import sys
import subprocess

print("Waiting for chromadb to be available...")
started = time.time()
while time.time() - started < 300:
    try:
        import chromadb
        print("ChromaDB is now available!")
        break
    except ImportError:
        time.sleep(2)

print("Running bulk_embed.py...")
subprocess.run([r"backend\.venv\Scripts\python.exe", "bulk_embed.py"])

print("Fetching sample from ChromaDB...")
from backend.db.vector_store import vector_store
try:
    res = vector_store.episode_collection.peek(1)
    
    with open("embeddings_sample.md", "w") as f:
        f.write("# Embedding Sample from ChromaDB\n\n")
        f.write("Here is what an embedded retrieval episode looks like mathematically!\n\n")
        
        f.write("### The Source Semantic Text\n")
        f.write(f"```text\n{res['documents'][0]}\n```\n\n")
        
        f.write("### The Metadata\n")
        f.write(f"```json\n{res['metadatas'][0]}\n```\n\n")
        
        f.write("### The Mathematical Vector (First 15 of 1024 dimensions)\n")
        f.write(f"```json\n{res['embeddings'][0][:15]} ...\n```\n")
    print("Wrote embeddings_sample.md")
except Exception as e:
    print(f"Error fetching sample: {e}")

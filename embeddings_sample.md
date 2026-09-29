# Embedding Sample from ChromaDB

Here is what an embedded retrieval episode looks like mathematically!

### The Source Semantic Text
```text
Goal/Evidence: I searched 'Goa sunset' but got too many results spanning multiple trips. | Clues: location, event_trip, approximate_time, visual_appearance | Forgotten: exact_date | Methods: keyword_search | Failures: too_many_results
```

### The Metadata
```json
{'feedback_item_id': 'd8935370-9eb2-456d-a3d5-ad18f1c9b198', 'source': 'reddit', 'memory_type': 'photo'}
```

### The Mathematical Vector (First 15 of 1024 dimensions)
```json
[ 0.02253658 -0.00607934 -0.00655345  0.01965396 -0.03666401 -0.03057427
 -0.00137325  0.02370657  0.02583044  0.03985656  0.02318843 -0.00603519
  0.01038039 -0.01992396 -0.01365155] ...
```

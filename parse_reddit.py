import re
import csv
from datetime import datetime

# Input and output file paths
input_file = "data/sample/reddit_raw.txt"
output_file = "data/sample/reddit_manual_data.csv"

def parse_reviews(filepath):
    reviews = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Split the content by the numbered review pattern: "1. ", "2. ", etc.
    # The regex looks for a newline (or start of string), digits, a dot, and a space.
    # We use positive lookahead so we don't consume the number itself, or we can just split.
    # Let's split by the pattern `\n\d+\. ` and handle the first one.
    
    # Pre-process: ensure the first item has a newline if it starts right away
    if re.match(r'^\d+\. ', content):
        content = '\n' + content
        
    raw_blocks = re.split(r'\n\d+\. ', content)
    
    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue
            
        # The block should now contain:
        # Title
        # Flair (optional, often line 2)
        # Body (the rest)
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            continue
            
        title = lines[0]
        
        # Check if second line is a flair (usually short, has emojis)
        body_start_idx = 1
        if len(lines) > 1 and len(lines[1]) < 30 and any(flair in lines[1].lower() for flair in ['feedback', 'question', 'discussion', 'rant', 'bug']):
            body_start_idx = 2
            
        body = "\n".join(lines[body_start_idx:])
        
        # Combine title and body
        full_text = f"{title}\n\n{body}".strip()
        
        # We don't have URLs or authors, so we use placeholders
        review_data = {
            "source": "reddit",
            "source_url": "",
            "author_id": "anonymous_user",
            "date": datetime.now().strftime("%Y-%m-%d"), # Just use today's date since it's manual
            "text": full_text
        }
        reviews.append(review_data)
        
    return reviews

def main():
    print(f"Parsing {input_file}...")
    reviews = parse_reviews(input_file)
    print(f"Found {len(reviews)} reviews.")
    
    print(f"Writing to {output_file}...")
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['source', 'source_url', 'author_id', 'date', 'text']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for review in reviews:
            writer.writerow(review)
            
    print("Done!")

if __name__ == "__main__":
    main()

import json
from pathlib import Path

from datasets import load_dataset

KEYWORDS = ("Milano","Lombardia")
MAX_ARTICLES = 3000
OUTPUT = Path("data/articles.json1")

def main() -> None:
    OUTPUT.parent.mkdir(exist_ok=True)

    ds = load_dataset("Wikimedia/Wikipedia","20231101.it",split="train",streaming=True)

    n = 0

    with OUTPUT.open("w",encoding="utf-8") as f:
        for row in ds:
            if any(k in row["title"] or k in row["text"][:500] for k in KEYWORDS):
                record = {
                    "source_id": row["id"],
                    "title": row["title"],
                    "url": row["url"],
                    "content": row["text"],
                }
                f.write(json.dumps(record,ensure_ascii=False) + "\n")
                n += 1
                if n % 500 == 0:
                    print(f"{n} articoli salvati ...")
                if n >= MAX_ARTICLES:
                    break 
    print(f"Fatto: {n} articoli in {OUTPUT}")

if __name__ == "__main__":
    main()
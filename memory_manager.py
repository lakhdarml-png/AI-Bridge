#!/usr/bin/env python3
"""Search and list locally stored memories."""
from __future__ import annotations
import argparse
import core

def list_memories(query="", limit=50):
    if not 1 <= limit <= 200:
        raise ValueError("limit must be between 1 and 200")
    if query.strip():
        return core.recall(query, limit)
    with core.connect() as db:
        return db.execute("SELECT id,title,content,tags,created_at FROM memories ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

def main(argv=None):
    parser=argparse.ArgumentParser(description="Search local memories")
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--limit", type=int, default=20)
    args=parser.parse_args(argv)
    core.init_db()
    rows=list_memories(args.query,args.limit)
    for r in rows: print(f"#{r['id']} — {r['title']} [{r['tags']}]\n{r['content']}\n")
    if not rows: print("No matching memories.")
    return 0
if __name__=="__main__": raise SystemExit(main())

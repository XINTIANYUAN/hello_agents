"""把 Task5 课程资料用本地模型嵌入，再写入专用 Qdrant 集合。"""

import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import requests


COLLECTION = "hello_agents_task5"
QDRANT = "http://127.0.0.1:6335"
OLLAMA = "http://127.0.0.1:11434"
MODEL = "nomic-embed-text"


def main():
    root = Path(__file__).resolve().parents[2]
    documents = json.loads(Path(__file__).with_name("knowledge.json").read_text())
    session = requests.Session()
    session.trust_env = False
    response = session.post(
        OLLAMA + "/api/embed",
        json={"model": MODEL, "input": [item["content"] for item in documents]},
        timeout=120,
    )
    response.raise_for_status()
    embeddings = response.json()["embeddings"]
    assert len(embeddings) == len(documents)
    dimension = len(embeddings[0])
    assert all(len(vector) == dimension for vector in embeddings)
    collection_url = f"{QDRANT}/collections/{COLLECTION}"
    current = session.get(collection_url, timeout=15)
    if current.status_code == 404:
        created = session.put(collection_url, json={"vectors": {"size": dimension, "distance": "Cosine"}}, timeout=15)
        created.raise_for_status()
    else:
        current.raise_for_status()
        assert current.json()["result"]["config"]["params"]["vectors"]["size"] == dimension
    points = [{
        "id": str(uuid5(NAMESPACE_URL, "hello-agents/task5/" + item["doc_id"])),
        "vector": vector,
        "payload": {"content": item["content"], "metadata": {"doc_id": item["doc_id"], "source": item["source"]}},
    } for item, vector in zip(documents, embeddings)]
    stored = session.put(collection_url + "/points", params={"wait": "true"}, json={"points": points}, timeout=30)
    stored.raise_for_status()
    report = {
        "collection": COLLECTION, "embedding_model": MODEL, "dimension": dimension,
        "documents": len(points), "point_ids": [point["id"] for point in points],
        "storage": "Qdrant disk-backed collection",
    }
    (root / "docs/task5/knowledge-index.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

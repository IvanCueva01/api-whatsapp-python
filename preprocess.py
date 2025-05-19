import os
from dotenv import load_dotenv
import json
import numpy as np
import faiss
import openai
from docx import Document

load_dotenv()
# 1. Configura tu key de OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 2. Lee el .docx y extrae texto


def load_docx(path: str) -> str:
    doc = Document(path)
    full_text = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            full_text.append(text)
    return "\n\n".join(full_text)

# 3. Chunking: trocea en fragmentos de ~300-500 tokens (aquí palabras)


def chunk_text(text: str, max_words: int = 300):
    paragraphs = text.split("\n\n")
    chunks = []
    current = []
    count = 0
    for p in paragraphs:
        words = p.split()
        if count + len(words) > max_words:
            chunks.append(" ".join(current))
            current = words
            count = len(words)
        else:
            current.extend(words)
            count += len(words)
    if current:
        chunks.append(" ".join(current))
    return chunks

# 4. Calcula embeddings por lote


def compute_embeddings(chunks: list[str], model: str = "text-embedding-ada-002"):
    embeddings = []
    batch_size = 16
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        resp = client.embeddings.create(input=batch, model=model)
        embeddings.extend([d.embedding for d in resp.data])
    return embeddings

# 5. Guarda índice FAISS + metadatos


def build_and_save_index(chunks: list[str],
                         embeddings: list[list[float]],
                         index_path: str = "faiss.index",
                         meta_path: str = "chunks.json"):
    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    arr = np.array(embeddings, dtype="float32")
    index.add(arr)
    faiss.write_index(index, index_path)
    # metadatos: para cada vector, guardamos el texto del chunk
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # Ruta a tu documento de entrenamiento
    DOC_PATH = "Documento de Entrenamiento ChatGPT para WhatsApp M2M.docx"
    text = load_docx(DOC_PATH)
    chunks = chunk_text(text, max_words=350)
    print(f"Generados {len(chunks)} chunks.")
    embeddings = compute_embeddings(chunks)
    build_and_save_index(chunks, embeddings)
    print("Índice FAISS y metadatos guardados.")

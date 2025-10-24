from sentence_transformers import SentenceTransformer
import faiss
import os
import json

class PessoaRetriever:
    def __init__(self, data_dir="data/pessoa_poems", index_path="data/index.faiss"):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.data_dir = data_dir
        self.index_path = index_path
        self.texts = []
        self.embeddings = None
        self.index = None

    def load_texts(self):
        texts = []
        for file in os.listdir(self.data_dir):
            if file.endswith(".txt"):
                with open(os.path.join(self.data_dir, file), "r", encoding="utf-8") as f:
                    texts.append(f.read())
        self.texts = texts
        return texts

    def build_index(self):
        embeddings = self.model.encode(self.texts)
        self.embeddings = embeddings
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)
        self.index = index
        faiss.write_index(index, self.index_path)

    def load_index(self):
        self.index = faiss.read_index(self.index_path)

    def retrieve(self, query, top_k=3):
        query_emb = self.model.encode([query])
        D, I = self.index.search(query_emb, top_k)
        return [self.texts[i] for i in I[0]]

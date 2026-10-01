from __future__ import annotations

import hashlib
import json
import os

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Multilingual: the corpus is overwhelmingly Portuguese, so an English-only
# encoder (such as all-MiniLM-L6-v2) retrieves close to noise here.
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


class PessoaRetriever:
    def __init__(
        self,
        data_dir="data/pessoa_poems",
        index_path="data/index.faiss",
        embedding_model=EMBEDDING_MODEL,
    ):
        self.embedding_model_name = embedding_model
        self.model = SentenceTransformer(embedding_model)
        self.data_dir = data_dir
        self.index_path = index_path
        self.manifest_path = f"{os.path.splitext(index_path)[0]}.manifest.json"
        self.filenames = []
        self.texts = []
        self.index = None

    # --- corpus -----------------------------------------------------------

    def _corpus_files(self):
        # sorted(): os.listdir() order is arbitrary, and FAISS ids are
        # positional, so a stable order is what keeps id i pointing at
        # texts[i] across runs.
        return sorted(f for f in os.listdir(self.data_dir) if f.endswith(".txt"))

    def _read(self, name):
        with open(os.path.join(self.data_dir, name), "r", encoding="utf-8") as f:
            return f.read()

    def load_texts(self):
        self.filenames = self._corpus_files()
        self.texts = [self._read(name) for name in self.filenames]
        return self.texts

    def _fingerprint(self):
        h = hashlib.sha256()
        h.update(self.embedding_model_name.encode("utf-8"))
        for name in self.filenames:
            size = os.path.getsize(os.path.join(self.data_dir, name))
            h.update(f"{name}:{size}".encode("utf-8"))
        return h.hexdigest()

    # --- embeddings -------------------------------------------------------

    def _encode(self, texts, show_progress=False):
        emb = self.model.encode(
            texts, convert_to_numpy=True, show_progress_bar=show_progress
        )
        emb = np.asarray(emb, dtype="float32")
        # IndexFlatIP over L2-normalised vectors is cosine similarity, which is
        # the metric these embeddings are trained for; raw L2 is not.
        faiss.normalize_L2(emb)
        return emb

    # --- index ------------------------------------------------------------

    def build_index(self, show_progress=True):
        if not self.texts:
            self.load_texts()

        embeddings = self._encode(self.texts, show_progress=show_progress)
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        self.index = index

        os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
        faiss.write_index(index, self.index_path)
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "embedding_model": self.embedding_model_name,
                    "fingerprint": self._fingerprint(),
                    "filenames": self.filenames,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        return index

    def load_index(self):
        """Load the persisted index, or return None if it cannot be trusted.

        The index is only reusable together with the manifest that records the
        document order it was built from -- without it the positional ids mean
        nothing.
        """
        if not (
            os.path.exists(self.index_path) and os.path.exists(self.manifest_path)
        ):
            return None

        try:
            with open(self.manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

        if manifest.get("embedding_model") != self.embedding_model_name:
            return None

        self.filenames = manifest.get("filenames") or []
        if self.filenames != self._corpus_files():
            return None
        if manifest.get("fingerprint") != self._fingerprint():
            return None

        index = faiss.read_index(self.index_path)
        # Re-reading in manifest order is what guarantees texts[i] is the
        # document behind FAISS id i.
        self.texts = [self._read(name) for name in self.filenames]
        if index.ntotal != len(self.texts):
            return None

        self.index = index
        return index

    def load_or_build_index(self):
        if self.load_index() is not None:
            return self.index
        self.load_texts()
        return self.build_index()

    # --- search -----------------------------------------------------------

    def retrieve(self, query, top_k=3):
        if self.index is None:
            raise RuntimeError(
                "index not loaded; call load_or_build_index() first"
            )
        query_emb = self._encode([query])
        _scores, ids = self.index.search(query_emb, top_k)
        return [self.texts[i] for i in ids[0] if 0 <= i < len(self.texts)]

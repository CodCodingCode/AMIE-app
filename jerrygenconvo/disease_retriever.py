# disease_retriever.py
"""
Disease retrieval and embedding utilities for the medical diagnosis system.
"""

import openai
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class DiseaseRetriever:
    """Retrieves relevant diseases based on symptom embeddings"""
    
    def __init__(self, disease_db, openai_api_key, model="text-embedding-3-small", cache_path="disease_embeddings.json"):
        openai.api_key = openai_api_key
        self.disease_db = disease_db
        self.model = model
        self.cache_path = cache_path
        self.disease_embeddings = self._load_or_generate_embeddings()

    def _embed(self, text):
        """Generate embeddings for text"""
        response = openai.Embedding.create(input=[text], model=self.model)
        return response["data"][0]["embedding"]

    def _construct_embedding_text(self, info):
        """Construct text for embedding from disease info"""
        parts = []
        for field in ["symptoms", "causes", "risk_factors", "family_factors", "hereditary_factors"]:
            if field in info and info[field]:
                parts.extend(info[field])
        return " ".join(parts)

    def _load_or_generate_embeddings(self):
        """Load cached embeddings or generate new ones"""
        if os.path.exists(self.cache_path):
            with open(self.cache_path, "r") as f:
                cached = json.load(f)
        else:
            cached = {}

        updated = False
        for disease, info in self.disease_db.items():
            embed_text = self._construct_embedding_text(info)
            cache_key = f"{disease} | {embed_text}"

            if cache_key not in cached:
                embedding = self._embed(embed_text)
                cached[cache_key] = embedding
                updated = True

        if updated:
            with open(self.cache_path, "w") as f:
                json.dump(cached, f)

        # Final usable format: { disease_name: embedding_vector }
        disease_embeddings = {}
        for disease, info in self.disease_db.items():
            embed_text = self._construct_embedding_text(info)
            cache_key = f"{disease} | {embed_text}"
            disease_embeddings[disease] = cached[cache_key]

        return disease_embeddings

    def get_relevant_diseases(self, symptoms, causes=None, risk_factors=None, family_factors=None, hereditary_factors=None):
        """Get diseases relevant to given symptoms and factors"""
        input_parts = symptoms or []
        input_parts += causes or []
        input_parts += risk_factors or []
        input_parts += family_factors or []
        input_parts += hereditary_factors or []

        input_text = " ".join(input_parts)
        input_embedding = np.array(self._embed(input_text)).reshape(1, -1)

        similarities = []
        for disease, emb in self.disease_embeddings.items():
            emb = np.array(emb).reshape(1, -1)
            score = cosine_similarity(input_embedding, emb)[0][0]
            similarities.append((disease, score, self.disease_db[disease]))

        top_matches = sorted(similarities, key=lambda x: x[1], reverse=True)[:10]
        return [
            {
                "disease": disease,
                "relevance": float(score),
                "info": info
            }
            for disease, score, info in top_matches
        ]
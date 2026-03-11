from __future__ import annotations

from pathlib import Path
from typing import List

import chromadb
from llama_index.core import Settings, SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.schema import Document, NodeWithScore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore


class KnowledgeManager:
    def __init__(self, docs_path: Path, db_path: Path, collection_name: str = "project_hsa_knowledge") -> None:
        self.docs_path: Path = docs_path
        self.db_path: Path = db_path
        self.collection_name: str = collection_name
        self.index: VectorStoreIndex | None = None
        self.retriever: BaseRetriever | None = None

    def _load_documents(self) -> List[Document]:
        if not self.docs_path.exists():
            return []

        documents: List[Document] = []
        for subfolder in [p for p in self.docs_path.iterdir() if p.is_dir()]:
            reader = SimpleDirectoryReader(input_dir=str(subfolder), recursive=True)
            for doc in reader.load_data():
                doc.metadata["category"] = subfolder.name
                documents.append(doc)
        return documents

    def build_or_load_index(self) -> None:
        self.db_path.mkdir(parents=True, exist_ok=True)
        db_client = chromadb.PersistentClient(path=str(self.db_path))
        collection = db_client.get_or_create_collection(self.collection_name)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

        documents = self._load_documents()
        if documents:
            self.index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
        else:
            self.index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

        self.retriever = self.index.as_retriever(similarity_top_k=4)

    def retrieve_context(self, query: str) -> str:
        if self.retriever is None:
            raise RuntimeError("Knowledge index is not initialized. Call build_or_load_index first.")
        nodes: List[NodeWithScore] = self.retriever.retrieve(query)
        return "\n\n".join(f"[근거 {idx + 1}] {node.get_content()}" for idx, node in enumerate(nodes))

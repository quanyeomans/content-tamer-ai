"""
ML Refinement Layer

Provides selective machine learning enhancement for uncertain document classifications.
Only applies modern ML techniques when rule-based classification confidence is below threshold.
Uses state-of-the-art sentence transformers with simple clustering for reliable results.
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    # StandardScaler imported but not used - keeping for future ML enhancements
    from sklearn.preprocessing import StandardScaler  # pylint: disable=unused-import

    TRANSFORMERS_AVAILABLE = True
    SentenceTransformer_available = SentenceTransformer
    KMeans_available = KMeans
    silhouette_score_available = silhouette_score
except ImportError:
    logging.warning("ML dependencies not available - ML refinement will be skipped")
    TRANSFORMERS_AVAILABLE = False
    SentenceTransformer_available = None  # type: ignore
    KMeans_available = None  # type: ignore
    silhouette_score_available = None  # type: ignore


class SelectiveMLRefinement:
    """Selective ML enhancement for uncertain document classifications."""

    def __init__(self):
        """Initialize ML refinement with state-of-the-art models."""
        self.embedding_model = None
        self.confidence_threshold = 0.7  # Apply ML when rule confidence < 70%
        self.min_documents_for_ml = 3  # Skip ML for very small sets

        if TRANSFORMERS_AVAILABLE:
            try:
                # Use MTEB leaderboard winner for document classification
                if SentenceTransformer_available is not None:
                    self.embedding_model = SentenceTransformer_available("all-mpnet-base-v2")
                else:
                    self.embedding_model = None
                logging.info("ML refinement initialized with all-mpnet-base-v2")
            except Exception as e:
                logging.warning(f"Failed to load embedding model: {e}")
                self.embedding_model = None
        else:
            logging.info("ML refinement disabled - dependencies not available")

    def refine_uncertain_classifications(
        self,
        uncertain_docs: List[Dict[str, Any]],
        all_classified_docs: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Apply ML refinement to uncertain document classifications.

        Args:
            uncertain_docs: Documents with confidence < threshold
            all_classified_docs: All classified documents for context

        Returns:
            Dictionary mapping document filenames to refined classifications
        """
        if not self.embedding_model or not TRANSFORMERS_AVAILABLE:
            return {}

        if len(uncertain_docs) < self.min_documents_for_ml:
            logging.info(f"Skipping ML refinement - only {len(uncertain_docs)} uncertain documents")
            return {}

        logging.info(f"Applying ML refinement to {len(uncertain_docs)} uncertain documents")

        try:
            # Generate embeddings for uncertain documents
            embeddings = self._generate_embeddings(uncertain_docs)
            if embeddings is None:
                return {}

            # Apply intelligent clustering
            cluster_assignments = self._apply_smart_clustering(embeddings, uncertain_docs)

            # Interpret clusters semantically using high-confidence documents as reference
            refined_classifications = self._interpret_clusters_semantically(
                uncertain_docs, cluster_assignments, embeddings, all_classified_docs
            )

            return refined_classifications

        except Exception as e:
            logging.warning(f"ML refinement failed: {e}")
            return {}

    def _generate_embeddings(self, documents: List[Dict[str, Any]]) -> Optional[np.ndarray]:
        """Generate sentence embeddings for documents."""
        try:
            # Create document summaries for embedding
            document_texts = []
            for doc in documents:
                summary = self._create_document_summary(doc)
                document_texts.append(summary)

            # Generate embeddings
            if self.embedding_model is None:
                raise RuntimeError("Embedding model not available")
            embeddings = self.embedding_model.encode(document_texts, convert_to_numpy=True)
            return embeddings

        except Exception as e:
            logging.warning(f"Embedding generation failed: {e}")
            return None

    def _create_document_summary(self, doc: Dict[str, Any]) -> str:
        """Create a concise summary for embedding generation."""
        # Combine filename and content preview for rich context
        filename = doc.get("filename", "")
        content = doc.get("content_preview", "")
        metadata = doc.get("metadata", {})

        # Extract key information for embedding
        summary_parts = [filename]

        if content:
            summary_parts.append(content[:500])  # First 500 chars

        # Add metadata context if available
        if metadata.get("key_entities"):
            entities = metadata["key_entities"]
            for entity_type, entity_list in entities.items():
                if entity_list:
                    summary_parts.append(f"{entity_type}: {', '.join(entity_list[:3])}")

        return " ".join(summary_parts)

    def _apply_smart_clustering(
        self, embeddings: np.ndarray, documents: List[Dict[str, Any]]
    ) -> List[int]:
        """Apply intelligent clustering to embeddings."""
        n_docs = len(documents)

        if n_docs < 3:
            # Not enough documents for clustering
            return list(range(n_docs))

        # Determine optimal number of clusters
        optimal_k = self._determine_optimal_cluster_count(embeddings, n_docs)

        # Apply clustering with optimal parameters
        if optimal_k <= 1:
            # Single cluster - all documents similar
            return [0] * n_docs

        try:
            # Use KMeans for interpretable results
            if KMeans_available is None:
                raise RuntimeError("KMeans not available")
            clusterer = KMeans_available(n_clusters=optimal_k, random_state=42, n_init="auto")
            cluster_labels = clusterer.fit_predict(embeddings)

            return cluster_labels.tolist()

        except Exception as e:
            logging.warning(f"Clustering failed: {e}")
            return list(range(n_docs))  # Each doc in its own cluster

    def _determine_optimal_cluster_count(self, embeddings: np.ndarray, n_docs: int) -> int:
        """Determine optimal number of clusters using multiple methods."""
        max_k = min(8, n_docs // 2)  # Don't create too many small clusters
        if max_k < 2:
            return 1

        best_k = 2
        best_score = -1

        # Try different cluster counts and evaluate
        for k in range(2, max_k + 1):
            try:
                if KMeans_available is None:
                    continue
                clusterer = KMeans_available(n_clusters=k, random_state=42, n_init="auto")
                cluster_labels = clusterer.fit_predict(embeddings)

                # Use silhouette score to evaluate clustering quality
                if silhouette_score_available is None:
                    continue
                score = silhouette_score_available(embeddings, cluster_labels)

                if score > best_score:
                    best_score = score
                    best_k = k

            except Exception:
                continue

        return best_k

    def _interpret_clusters_semantically(
        self,
        uncertain_docs: List[Dict[str, Any]],
        cluster_labels: List[int],
        embeddings: np.ndarray,
        all_classified_docs: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """Interpret clusters semantically to assign document categories."""
        refined_classifications = {}

        # Group documents by cluster
        clusters = defaultdict(list)
        for i, label in enumerate(cluster_labels):
            clusters[label].append((i, uncertain_docs[i]))

        # Get high-confidence reference categories
        reference_categories = self._get_reference_categories(all_classified_docs)

        # Classify each cluster
        for cluster_id, cluster_docs in clusters.items():
            cluster_category = self._classify_cluster(
                cluster_docs, embeddings, reference_categories
            )

            # Assign refined classification to all documents in cluster
            for _doc_idx, doc in cluster_docs:
                refined_classifications[doc["filename"]] = {
                    "category": cluster_category["category"],
                    "confidence": cluster_category["confidence"],
                    "method": "ml_refinement",
                    "cluster_id": cluster_id,
                    "cluster_size": len(cluster_docs),
                }

        return refined_classifications

    def _get_reference_categories(
        self, all_classified_docs: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Extract reference patterns from high-confidence classifications."""
        reference_categories = defaultdict(list)

        for doc in all_classified_docs:
            confidence = doc.get("confidence", 0)
            if confidence >= self.confidence_threshold:  # High confidence documents
                category = doc.get("category", "other")

                # Extract representative text
                content_preview = doc.get("content_preview", "")
                filename = doc.get("filename", "")

                reference_text = f"{filename} {content_preview}"
                reference_categories[category].append(reference_text)

        return dict(reference_categories)

    def _classify_cluster(
        self,
        cluster_docs: List[Tuple[int, Dict[str, Any]]],
        embeddings: np.ndarray,
        reference_categories: Dict[str, List[str]],
    ) -> Dict[str, Any]:
        """Classify a cluster of documents using reference categories."""
        if not reference_categories:
            # No reference available - use pattern analysis
            return self._classify_cluster_by_patterns(cluster_docs)

        try:
            # Create cluster representative embedding (centroid)
            cluster_indices = [idx for idx, _ in cluster_docs]
            cluster_embeddings = embeddings[cluster_indices]
            cluster_centroid = np.mean(cluster_embeddings, axis=0)

            # Compare with reference category centroids
            best_category = "other"
            best_similarity = -1

            for category, reference_texts in reference_categories.items():
                if not reference_texts:
                    continue

                # Generate embeddings for reference texts
                try:
                    if self.embedding_model is None:
                        continue
                    ref_embeddings = self.embedding_model.encode(
                        reference_texts, convert_to_numpy=True
                    )
                    ref_centroid = np.mean(ref_embeddings, axis=0)

                    # Calculate cosine similarity
                    similarity = np.dot(cluster_centroid, ref_centroid) / (
                        np.linalg.norm(cluster_centroid) * np.linalg.norm(ref_centroid)
                    )

                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_category = category

                except Exception as e:
                    logging.debug(f"Failed to process reference category {category}: {e}")
                    continue

            # Convert similarity to confidence score
            confidence = max(0.4, min(0.9, best_similarity)) if best_similarity > 0.3 else 0.4

            return {"category": best_category, "confidence": confidence}

        except Exception as e:
            logging.warning(f"Cluster classification failed: {e}")
            return self._classify_cluster_by_patterns(cluster_docs)

    def _classify_cluster_by_patterns(
        self, cluster_docs: List[Tuple[int, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Fallback classification using simple pattern analysis."""
        # Extract common patterns from cluster documents
        filenames = []
        content_previews = []

        for _, doc in cluster_docs:
            filenames.append(doc.get("filename", "").lower())
            content_previews.append(doc.get("content_preview", "").lower())

        all_text = " ".join(filenames + content_previews)

        # Simple pattern matching for fallback classification
        if any(word in all_text for word in ["invoice", "bill", "payment", "$"]):
            return {"category": "invoices", "confidence": 0.6}
        elif any(word in all_text for word in ["contract", "agreement", "terms"]):
            return {"category": "contracts", "confidence": 0.6}
        elif any(word in all_text for word in ["report", "analysis", "summary"]):
            return {"category": "reports", "confidence": 0.6}
        elif any(word in all_text for word in ["email", "letter", "correspondence"]):
            return {"category": "correspondence", "confidence": 0.6}
        else:
            return {"category": "other", "confidence": 0.4}

    def is_ml_available(self) -> bool:
        """Check if ML refinement is available."""
        return self.embedding_model is not None and TRANSFORMERS_AVAILABLE

    def get_ml_stats(self) -> Dict[str, Any]:
        """Get statistics about ML refinement capabilities."""
        return {
            "ml_available": self.is_ml_available(),
            "model_name": "all-mpnet-base-v2" if self.embedding_model else None,
            "confidence_threshold": self.confidence_threshold,
            "min_documents_threshold": self.min_documents_for_ml,
            "transformers_available": TRANSFORMERS_AVAILABLE,
        }

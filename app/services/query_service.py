import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.core.logging import logger


class BaseQueryClassifier(ABC):
    """Abstract interface for natural language remote sensing query classifiers."""

    @abstractmethod
    def classify(self, query: str) -> Dict[str, Any]:
        pass


class RuleBasedQueryClassifier(BaseQueryClassifier):
    """
    High-precision rule-based intent classifier for remote sensing queries.
    Recognizes temporal change cues, semantic segmentation keywords,
    VQA questions, captioning requests, and optical/SAR fusion.
    """

    CHANGE_PATTERNS = [
        r"between\s+\d{4}\s+and\s+\d{4}",
        r"change[s]?",
        r"difference[s]?",
        r"expansion",
        r"loss",
        r"gain",
        r"deforestation",
        r"growth",
        r"temporal",
        r"before and after",
        r"compared to",
        r"over time"
    ]

    SEGMENTATION_PATTERNS = [
        r"segment",
        r"highlight",
        r"extract",
        r"delineate",
        r"classify land",
        r"land cover",
        r"flooded regions?",
        r"water bodies",
        r"vegetation zones?",
        r"urban footprint",
        r"mask",
        r"boundary of"
    ]

    OPTICAL_SAR_PATTERNS = [
        r"optical and sar",
        r"sar and optical",
        r"radar and optical",
        r"sentinel-1 and sentinel-2",
        r"sar",
        r"radar",
        r"backscatter",
        r"multimodal fusion",
        r"fuse optical",
        r"cloud-penetrating"
    ]

    CAPTIONING_PATTERNS = [
        r"describe this",
        r"generate caption",
        r"summarize this image",
        r"what is this image",
        r"overview of this scene",
        r"caption this"
    ]

    VQA_PATTERNS = [
        r"what objects",
        r"is there",
        r"are there",
        r"how many",
        r"where is",
        r"count the",
        r"does this image contain",
        r"identify the"
    ]

    def classify(self, query: str) -> Dict[str, Any]:
        text = query.strip().lower()

        # 1. Check Optical + SAR
        for pattern in self.OPTICAL_SAR_PATTERNS:
            if re.search(r"\b" + pattern + r"\b", text):
                return {
                    "intent": "optical_sar",
                    "confidence": 0.93,
                    "reason": f"Query mentions multimodal Optical and SAR keywords (matched '{pattern}').",
                    "selected_analysis": "optical_sar"
                }

        # 2. Check Change Detection
        for pattern in self.CHANGE_PATTERNS:
            if re.search(r"\b" + pattern + r"\b", text) or re.search(pattern, text):
                return {
                    "intent": "change_detection",
                    "confidence": 0.91,
                    "reason": f"The query asks for temporal differences or surface evolution (matched '{pattern}').",
                    "selected_analysis": "change_detection"
                }

        # 3. Check Segmentation
        for pattern in self.SEGMENTATION_PATTERNS:
            if re.search(r"\b" + pattern + r"\b", text):
                return {
                    "intent": "segmentation",
                    "confidence": 0.89,
                    "reason": f"The query requests feature boundary extraction or land cover segmentation (matched '{pattern}').",
                    "selected_analysis": "segmentation"
                }

        # 4. Check Captioning
        for pattern in self.CAPTIONING_PATTERNS:
            if re.search(pattern, text):
                return {
                    "intent": "captioning",
                    "confidence": 0.88,
                    "reason": f"The query requests an overall descriptive summary of the scene (matched '{pattern}').",
                    "selected_analysis": "captioning"
                }

        # 5. Check VQA
        for pattern in self.VQA_PATTERNS:
            if re.search(pattern, text):
                return {
                    "intent": "vqa",
                    "confidence": 0.85,
                    "reason": f"The query is a direct analytical question about scene features (matched '{pattern}').",
                    "selected_analysis": "vqa"
                }

        # Default fallback
        if "?" in text or text.startswith(("what", "who", "where", "which", "how", "can")):
            return {
                "intent": "vqa",
                "confidence": 0.70,
                "reason": "Query is structured as an interrogative sentence.",
                "selected_analysis": "vqa"
            }

        return {
            "intent": "unknown",
            "confidence": 0.50,
            "reason": "Could not conclusively map query to a specialist task. Defaulting to scene captioning.",
            "selected_analysis": "captioning"
        }


class QueryService:
    """Service facade for Query Understanding with extensible classifier backend."""

    def __init__(self, classifier: Optional[BaseQueryClassifier] = None):
        self.classifier = classifier or RuleBasedQueryClassifier()

    def understand_query(self, query: str) -> Dict[str, Any]:
        logger.info("Classifying query: '%s'", query)
        result = self.classifier.classify(query)
        logger.info("Query classification result: %s (confidence: %.2f)", result["intent"], result["confidence"])
        return result


query_service = QueryService()

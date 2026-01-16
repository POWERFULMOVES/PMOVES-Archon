"""
Keyword Extraction Utility

Simple and effective keyword extraction for improved search capabilities.
Uses lightweight Python string operations without heavy NLP dependencies.

Enhanced with optional Hi-RAG v2 semantic expansion for knowledge-aware search.
"""

import asyncio
import logging
import os
from typing import Optional

import httpx
import re

logger = logging.getLogger(__name__)

# Common stop words to filter out
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "by",
    "for",
    "from",
    "has",
    "have",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "will",
    "with",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "how",
    "can",
    "could",
    "should",
    "would",
    "may",
    "might",
    "must",
    "shall",
    "do",
    "does",
    "did",
    "done",
    "this",
    "these",
    "those",
    "there",
    "their",
    "them",
    "they",
    "we",
    "you",
    "your",
    "our",
    "us",
    "am",
    "im",
    "me",
    "my",
    "i",
    "if",
    "so",
    "or",
    "but",
    "not",
    "no",
    "yes",
}

# Technical stop words that are too common in code/docs to be useful
TECHNICAL_STOP_WORDS = {
    "get",
    "set",
    "use",
    "using",
    "used",
    "make",
    "made",
    "create",
    "created",
    "add",
    "added",
    "remove",
    "removed",
    "update",
    "updated",
    "delete",
    "deleted",
    "need",
    "needs",
    "want",
    "wants",
    "like",
    "example",
    "examples",
    "please",
    "help",
    "show",
    "find",
    "search",
    "look",
    "looking",
    "implement",
    "implementing",
    "implemented",
    "implementation",
}

# Common programming keywords to preserve (not filter out)
PRESERVE_KEYWORDS = {
    "api",
    "auth",
    "authentication",
    "authorization",
    "database",
    "db",
    "sql",
    "query",
    "queries",
    "function",
    "functions",
    "class",
    "classes",
    "method",
    "methods",
    "variable",
    "variables",
    "array",
    "arrays",
    "object",
    "objects",
    "type",
    "types",
    "interface",
    "interfaces",
    "component",
    "components",
    "module",
    "modules",
    "package",
    "packages",
    "library",
    "libraries",
    "framework",
    "frameworks",
    "server",
    "client",
    "request",
    "response",
    "http",
    "https",
    "rest",
    "graphql",
    "websocket",
    "async",
    "await",
    "promise",
    "callback",
    "event",
    "events",
    "error",
    "errors",
    "exception",
    "exceptions",
    "debug",
    "debugging",
    "test",
    "tests",
    "testing",
    "unit",
    "integration",
    "e2e",
    "docker",
    "kubernetes",
    "container",
    "containers",
    "deployment",
    "deploy",
    "git",
    "github",
    "gitlab",
    "version",
    "versions",
    "branch",
    "branches",
    "commit",
    "commits",
    "pull",
    "push",
    "merge",
    "rebase",
    "python",
    "javascript",
    "typescript",
    "java",
    "golang",
    "rust",
    "react",
    "vue",
    "angular",
    "next",
    "nuxt",
    "express",
    "django",
    "flask",
    "postgresql",
    "postgres",
    "mysql",
    "mongodb",
    "redis",
    "supabase",
    "aws",
    "azure",
    "gcp",
    "cloud",
    "serverless",
    "lambda",
    "jwt",
    "oauth",
    "token",
    "tokens",
    "session",
    "sessions",
    "cookie",
    "cookies",
}


class KeywordExtractor:
    """Simple keyword extraction for search queries.

    Enhanced with optional Hi-RAG v2 semantic expansion for knowledge-aware
    keyword discovery. When hirag_url is configured, the extractor can query
    the PMOVES knowledge graph to find semantically related terms.
    """

    def __init__(self, hirag_url: Optional[str] = None):
        """Initialize the keyword extractor.

        Args:
            hirag_url: Optional URL for Hi-RAG v2 service (e.g., "http://localhost:8086")
                When provided, enables semantic keyword expansion via knowledge graph.
        """
        self.stop_words = STOP_WORDS | TECHNICAL_STOP_WORDS
        self.preserve_keywords = PRESERVE_KEYWORDS
        self.hirag_url = hirag_url

    def extract_keywords(
        self, query: str, min_length: int = 2, max_keywords: int = 10
    ) -> list[str]:
        """
        Extract meaningful keywords from a search query.

        Args:
            query: The search query string
            min_length: Minimum keyword length (default: 2)
            max_keywords: Maximum number of keywords to return (default: 10)

        Returns:
            List of extracted keywords, ordered by importance
        """
        # Convert to lowercase for processing
        query_lower = query.lower()

        # Step 1: Extract potential keywords (alphanumeric + some special chars)
        # Keep dashes and underscores as they're common in tech terms
        tokens = re.findall(r"[a-z0-9_-]+", query_lower)

        # Step 2: Filter tokens
        keywords = []
        for token in tokens:
            # Skip if too short
            if len(token) < min_length:
                continue

            # Always keep if in preserve list
            if token in self.preserve_keywords:
                keywords.append(token)
            # Skip if in stop words
            elif token not in self.stop_words:
                keywords.append(token)

        # Step 3: Handle special cases and compound terms
        # Look for common patterns like "best practices", "how to", etc.
        compound_patterns = [
            (r"best\s+practice[s]?", "best_practices"),
            (r"how\s+to", "howto"),
            (r"step\s+by\s+step", "step_by_step"),
            (r"real\s+time", "realtime"),
            (r"full\s+text", "fulltext"),
            (r"full[\s-]?stack", "fullstack"),
            (r"back[\s-]?end", "backend"),
            (r"front[\s-]?end", "frontend"),
            (r"data[\s-]?base", "database"),
            (r"web[\s-]?socket", "websocket"),
        ]

        for pattern, replacement in compound_patterns:
            if re.search(pattern, query_lower):
                keywords.append(replacement)

        # Step 4: Deduplicate while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)

        # Step 5: Prioritize keywords
        # - Original case-sensitive matches get priority
        # - Technical terms get priority
        # - Longer terms often more specific
        prioritized = self._prioritize_keywords(unique_keywords, query)

        # Return top N keywords
        return prioritized[:max_keywords]

    def _prioritize_keywords(self, keywords: list[str], original_query: str) -> list[str]:
        """
        Prioritize keywords based on various factors.

        Args:
            keywords: List of extracted keywords
            original_query: The original search query

        Returns:
            Keywords sorted by priority
        """
        keyword_scores = []

        for keyword in keywords:
            score = 0

            # Bonus for exact case match in original
            if keyword in original_query:
                score += 3

            # Bonus for being a known technical term
            if keyword in self.preserve_keywords:
                score += 2

            # Bonus for longer terms (more specific)
            if len(keyword) > 5:
                score += 1

            # Bonus for containing numbers (versions, etc.)
            if any(c.isdigit() for c in keyword):
                score += 1

            # Check if it appears multiple times (important term)
            count = original_query.lower().count(keyword)
            if count > 1:
                score += (count - 1) * 2  # Give more weight to repeated terms

            keyword_scores.append((keyword, score))

        # Sort by score (descending) then by original order
        keyword_scores.sort(key=lambda x: (-x[1], keywords.index(x[0])))

        return [kw for kw, _ in keyword_scores]

    def build_search_terms(self, keywords: list[str]) -> list[str]:
        """
        Build search terms from keywords, including variations.

        Args:
            keywords: List of keywords

        Returns:
            List of search terms including variations
        """
        search_terms = []

        for keyword in keywords:
            # Add the keyword itself
            search_terms.append(keyword)

            # Add plural/singular variations for common patterns
            if keyword.endswith("s") and len(keyword) > 3 and not keyword.endswith("ss"):
                # Possible plural -> add singular (but not for words ending in ss)
                search_terms.append(keyword[:-1])
            elif not keyword.endswith("s") or keyword.endswith("ss"):
                # Possible singular -> add plural
                # Handle special cases
                if keyword.endswith("ss"):
                    search_terms.append(keyword + "es")  # e.g., "class" -> "classes"
                elif keyword.endswith("s"):
                    search_terms.append(keyword + "es")  # Other words ending in s
                else:
                    search_terms.append(keyword + "s")

            # Add common variations
            if keyword.endswith("ing"):
                # Remove -ing
                base = keyword[:-3]
                if len(base) > 2:
                    search_terms.append(base)
                    search_terms.append(base + "e")  # e.g., "coding" -> "code"

            if keyword.endswith("ed"):
                # Remove -ed
                base = keyword[:-2]
                if len(base) > 2:
                    search_terms.append(base)
                    search_terms.append(base + "e")  # e.g., "created" -> "create"

        # Deduplicate
        seen = set()
        unique_terms = []
        for term in search_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)

        return unique_terms

    async def extract_keywords_with_semantic_expansion(
        self,
        query: str,
        min_length: int = 2,
        max_keywords: int = 10,
        hirag_top_k: int = 3,
        hirag_timeout: float = 3.0,
    ) -> list[str]:
        """Extract keywords with optional semantic expansion via Hi-RAG v2.

        This method combines heuristic keyword extraction with semantic expansion
        from the PMOVES knowledge graph. When Hi-RAG v2 is available, it queries
        the knowledge graph for semantically related entities and terms.

        Args:
            query: The search query string
            min_length: Minimum keyword length (default: 2)
            max_keywords: Maximum number of keywords to return (default: 10)
            hirag_top_k: Number of semantic results to request from Hi-RAG (default: 3)
            hirag_timeout: Timeout in seconds for Hi-RAG request (default: 3.0)

        Returns:
            List of extracted keywords with semantic expansion, ordered by importance
        """
        # Start with heuristic extraction
        keywords = self.extract_keywords(query, min_length, max_keywords)

        # Skip semantic expansion if Hi-RAG is not configured
        if not self.hirag_url:
            return keywords

        try:
            # Query Hi-RAG v2 for semantically related content
            async with httpx.AsyncClient(timeout=hirag_timeout) as client:
                response = await client.post(
                    f"{self.hirag_url}/hirag/query",
                    json={
                        "query": query,
                        "top_k": hirag_top_k,
                        "rerank": True,
                    },
                )

                if response.status_code == 200:
                    data = response.json()

                    # Extract entities/keywords from Hi-RAG response
                    # Hi-RAG returns results with 'content' and optional 'entities'
                    semantic_keywords = self._extract_semantic_keywords(data)

                    # Merge semantic keywords with heuristic ones
                    # Prioritize keywords that appear in both sets
                    for sem_kw in semantic_keywords:
                        if sem_kw.lower() not in [k.lower() for k in keywords]:
                            keywords.append(sem_kw)

                    # Re-prioritize combined set
                    keywords = self._prioritize_keywords(keywords, query)

                    logger.debug(
                        f"Semantic expansion: {len(keywords)} keywords "
                        f"(added {len(semantic_keywords)} semantic)"
                    )
                else:
                    logger.warning(
                        f"Hi-RAG request failed: {response.status_code}, "
                        f"using heuristic keywords only"
                    )

        except asyncio.TimeoutError:
            logger.warning("Hi-RAG request timed out, using heuristic keywords only")
        except Exception as e:
            logger.warning(f"Hi-RAG semantic expansion failed: {e}, using heuristic keywords")

        return keywords[:max_keywords]

    def _extract_semantic_keywords(self, hirag_response: dict) -> list[str]:
        """Extract semantic keywords from Hi-RAG v2 response.

        Args:
            hirag_response: JSON response from Hi-RAG v2 /hirag/query endpoint

        Returns:
            List of semantically related keywords/entities
        """
        keywords = []

        # Handle different response formats from Hi-RAG
        results = hirag_response.get("results", [])
        if not results and "data" in hirag_response:
            results = hirag_response["data"]

        for result in results:
            # Extract from content field
            content = result.get("content", "")
            if content:
                # Extract named entities if available (Hi-RAG may include entities)
                entities = result.get("entities", [])
                if entities:
                    for entity in entities:
                        if isinstance(entity, dict):
                            entity_text = entity.get("text", entity.get("name", ""))
                            if entity_text and len(entity_text) >= 2:
                                keywords.append(entity_text)
                        elif isinstance(entity, str) and len(entity) >= 2:
                            keywords.append(entity)

                # Extract key terms from content using heuristics
                # Look for capitalized terms (potential named entities)
                content_keywords = re.findall(r"\b[A-Z][a-z0-9_]{2,}\b", content)
                keywords.extend(content_keywords[:2])  # Limit to avoid noise

        # Deduplicate while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen and kw_lower not in self.stop_words:
                seen.add(kw_lower)
                unique_keywords.append(kw)

        return unique_keywords[:5]  # Limit semantic keywords to avoid overwhelming


# Global instance for easy access
# Note: To enable semantic expansion, set HIRAG_URL environment variable
# before importing this module, or create a new instance with hirag_url parameter
_hirag_url = os.environ.get("HIRAG_URL", "http://localhost:8086")
keyword_extractor = KeywordExtractor(hirag_url=_hirag_url)


def extract_keywords(query: str, min_length: int = 2, max_keywords: int = 10) -> list[str]:
    """
    Convenience function to extract keywords from a query.

    Args:
        query: The search query string
        min_length: Minimum keyword length
        max_keywords: Maximum number of keywords to return

    Returns:
        List of extracted keywords
    """
    return keyword_extractor.extract_keywords(query, min_length, max_keywords)


async def extract_keywords_semantic(
    query: str,
    min_length: int = 2,
    max_keywords: int = 10,
    hirag_top_k: int = 3,
    hirag_timeout: float = 3.0,
) -> list[str]:
    """
    Convenience function to extract keywords with Hi-RAG v2 semantic expansion.

    This async function combines heuristic keyword extraction with semantic
    expansion from the PMOVES knowledge graph when Hi-RAG v2 is available.

    Args:
        query: The search query string
        min_length: Minimum keyword length
        max_keywords: Maximum number of keywords to return
        hirag_top_k: Number of semantic results from Hi-RAG
        hirag_timeout: Timeout in seconds for Hi-RAG request

    Returns:
        List of extracted keywords with semantic expansion
    """
    return await keyword_extractor.extract_keywords_with_semantic_expansion(
        query, min_length, max_keywords, hirag_top_k, hirag_timeout
    )


def build_search_terms(keywords: list[str]) -> list[str]:
    """
    Convenience function to build search terms from keywords.

    Args:
        keywords: List of keywords

    Returns:
        List of search terms including variations
    """
    return keyword_extractor.build_search_terms(keywords)

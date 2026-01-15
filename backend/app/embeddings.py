"""
Simple text matching for mapping resume bullets to job description.
Uses basic keyword matching instead of embeddings (no external dependencies).
"""
from typing import List, Tuple
import re


def _calculate_simple_relevance(bullet: str, jd_text: str) -> float:
    """
    Calculate a simple relevance score based on keyword overlap.
    Returns a score between 0.0 and 1.0.
    """
    # Extract words from bullet and JD (lowercase, alphanumeric only)
    bullet_words = set(re.findall(r'\b\w+\b', bullet.lower()))
    jd_words = set(re.findall(r'\b\w+\b', jd_text.lower()))
    
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can'}
    bullet_words = bullet_words - stop_words
    jd_words = jd_words - stop_words
    
    if not bullet_words or not jd_words:
        return 0.5  # Default relevance if no meaningful words
    
    # Calculate Jaccard similarity (intersection over union)
    intersection = len(bullet_words & jd_words)
    union = len(bullet_words | jd_words)
    
    if union == 0:
        return 0.5
    
    similarity = intersection / union
    return min(similarity * 2, 1.0)  # Scale up to make it more useful (0-1 range)


def map_bullets_to_jd(
    resume_bullets: List[str],
    job_description: str,
    top_k: int = 3
) -> List[Tuple[str, float, str]]:
    """
    Map resume bullets to relevant sections of the job description.
    Uses simple keyword matching instead of embeddings.
    
    Returns:
        List of tuples: (bullet, relevance_score, matched_jd_snippet)
    """
    if not resume_bullets:
        return []
    
    # Split job description into chunks (sentences)
    jd_chunks = _extract_jd_chunks(job_description)
    
    if not jd_chunks:
        # If no chunks, match against full JD
        mappings = [
            (bullet, _calculate_simple_relevance(bullet, job_description), job_description[:200])
            for bullet in resume_bullets
        ]
    else:
        # For each bullet, find the most relevant JD chunk
        mappings = []
        for bullet in resume_bullets:
            best_score = 0.0
            best_chunk = jd_chunks[0] if jd_chunks else job_description[:200]
            
            for chunk in jd_chunks:
                score = _calculate_simple_relevance(bullet, chunk)
                if score > best_score:
                    best_score = score
                    best_chunk = chunk
            
            mappings.append((bullet, best_score, best_chunk))
    
    # Sort by relevance score (descending)
    mappings.sort(key=lambda x: x[1], reverse=True)
    
    return mappings[:top_k] if top_k else mappings


def _extract_jd_chunks(job_description: str) -> List[str]:
    """
    Extract meaningful chunks from job description.
    Splits by sentences and filters for key sections.
    """
    chunks = []
    
    # Split by sentences
    sentences = job_description.replace('\n', ' ').split('.')
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 20:  # Filter very short sentences
            chunks.append(sentence)
    
    # Also extract key sections (Requirements, Responsibilities, etc.)
    sections = job_description.split('\n\n')
    for section in sections:
        section = section.strip()
        if len(section) > 30:
            chunks.append(section)
    
    return chunks[:50]  # Limit to top 50 chunks

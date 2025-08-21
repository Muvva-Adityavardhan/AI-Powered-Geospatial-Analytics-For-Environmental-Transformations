# utils.py
"""
Utility functions for parsing user queries (states, years, metrics)
and cleaning API responses.
"""
import re
from config import state_corpus_files, DYNAMIC_WORLD_CLASSES

def extract_states_from_query(query):
    return [state for state in state_corpus_files.keys() if re.search(rf"\b{state}\b", query, re.IGNORECASE)]

def extract_year(query):
    year_dict = {}
    states = extract_states_from_query(query)
    if not states:
        states = ["default"]
    
    for state in states:
        year_dict[state] = []

    last_n_years_match = re.search(r"last\s+(\d+)\s+years?", query, re.IGNORECASE)
    if last_n_years_match:
        n_years = int(last_n_years_match.group(1))
        current_year = 2024
        start_year = max(2015, current_year - n_years + 1)
        for state in states:
            year_dict[state] = [str(y) for y in range(start_year, current_year + 1)]
        return year_dict

    range_match = re.search(r"(\d{4})\s*(?:to|-)\s*(\d{4})", query, re.IGNORECASE)
    if range_match:
        start_year, end_year = map(int, range_match.groups())
        start_year = max(2015, start_year)
        end_year = min(2024, end_year)
        if start_year <= end_year:
            for state in states:
                year_dict[state] = [str(y) for y in range(start_year, end_year + 1)]
    
    multiple_years = re.findall(r"\b(\d{4})\b", query)
    if multiple_years and not range_match:
        valid_years = [y for y in multiple_years if 2015 <= int(y) <= 2024]
        if valid_years:
            for state in states:
                year_dict[state] = sorted(set(valid_years))
    
    for state in states:
        state_pattern = rf"\b{re.escape(state)}\s*(\d{{4}})?\b"
        match = re.search(state_pattern, query, re.IGNORECASE)
        if match and match.group(1) and not year_dict[state]:
            year_dict[state] = [match.group(1)] if 2015 <= int(match.group(1)) <= 2024 else []
    
    for state in states:
        if not year_dict[state]:
            year_dict[state] = ["2024"]
    
    # Ensure no None values in year_dict
    for state in year_dict:
        year_dict[state] = [y for y in year_dict[state] if y is not None and y.strip()]
        if not year_dict[state]:
            year_dict[state] = ["2024"]
    
    return year_dict

def extract_metrics_from_query(query):
    query_lower = query.lower()
    if "land cover" in query_lower:
        return DYNAMIC_WORLD_CLASSES
    if "ndvi" in query_lower and not any(m in query_lower for m in ["nbr", "evi", "ndmi", "mndwi", "land cover"]):
        return ["NDVI"]
    if "nbr" in query_lower and not any(m in query_lower for m in ["ndvi", "evi", "ndmi", "mndwi", "land cover"]):
        return ["NBR"]
    if "evi" in query_lower and not any(m in query_lower for m in ["ndvi", "nbr", "ndmi", "mndwi", "land cover"]):
        return ["EVI"]
    if "ndmi" in query_lower and not any(m in query_lower for m in ["ndvi", "nbr", "evi", "mndwi", "land cover"]):
        return ["NDMI"]
    if "mndwi" in query_lower and not any(m in query_lower for m in ["ndvi", "nbr", "evi", "ndmi", "land cover"]):
        return ["MNDWI"]
    return ["NDVI"]

def clean_response(response):
    response = re.sub(r"DynamicWorld\s+([a-z_]+)\s*:\s*([\d.]+)", r"\1: \2", response)
    patterns = [
        r"Sentinel2\s+([A-Za-z0-9]+)\s*(?:at|is|:)?\s*([\d.]+)"
    ]
    for pattern in patterns:
        response = re.sub(pattern, r"\1: \2", response)
    return response.strip()

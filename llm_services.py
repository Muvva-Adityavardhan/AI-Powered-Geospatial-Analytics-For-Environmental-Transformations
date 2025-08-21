# llm_services.py
"""
Functions for interacting with external language model APIs (Mistral, Gemini).
"""
import time
import requests
import google.generativeai as genai

from utils import extract_year, clean_response

def call_mistral_saba(api_url, api_key, corpus, query, states, metrics=None):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    instruction = (
        "Provide a response using only numerical values from the corpus. "
        "List metrics and values (e.g., '2023 NDVI: 0.415 Kerala' or '2023 water: 0.2 Kerala') with corresponding years and states. "
        "For land cover, include requested Dynamic World classes (water, trees, grass, flooded_vegetation, crops, shrub_and_scrub, built, bare, snow_and_ice) with values summing to 1.0 per year and state, prefixed with 'DynamicWorld' (e.g., 'DynamicWorld water: 0.1'). "
        "If metrics are specified, only include those; otherwise, include all requested data. "
        "If multiple states or years are requested, provide data for each state-year combination separately. "
        "If no data, return 'No relevant data'. "
        "End with: 'Data sourced from Sentinel-2 and Dynamic World.'"
    )
    year_dict = extract_year(query)
    year_str = ""
    for state in states:
        years = year_dict.get(state, ["2024"])
        year_str += f"{state}: {', '.join(years)}; "
    
    metric_instruction = f"Metrics requested: {', '.join(metrics)}" if metrics else "All available metrics"
    payload = {
        "model": "mistral-saba-2502",
        "messages": [
            {"role": "system", "content": f"You are an AI trained on environmental data. {instruction}\n{metric_instruction}"},
            {"role": "user", "content": f"Context: {corpus}\nQuery: {query} for {', '.join(states)}"}
        ]
    }
    try:
        for attempt in range(3):
            try:
                response = requests.post(api_url, json=payload, headers=headers, timeout=30)
                response.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                if attempt == 2:
                    return f"API Error: {str(e)}"
                time.sleep(1)
        raw_response = response.json()
        print(f"Raw API Response: {raw_response}")
        return raw_response.get("choices", [{}])[0].get("message", {}).get("content", "No response")
    except requests.exceptions.RequestException as e:
        return f"API Error: {str(e)}"

def call_gemini(api_key, context, query, states, mistral_values):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    instruction = (
        "Provide a detailed response using only the specific numerical values provided in the context (mistral_values). "
        "List metric names and their exact values (e.g., 'NDVI: 0.415', 'trees: 0.654') from the dataset. Don't mention Sentinel or Dynamic World anywhere."
        "For each metric, include a paragraph (at least 50 words) explaining its significance, what the value indicates about the state's environment, and how it compares to typical ranges or other states if multiple are provided. "
        "Do not provide theoretical answers or values not present in the mistral_values. "
        "If multiple states are mentioned_TOKEN_PLACEHOLDER_ structure the response with clear headings for each state and compare their metrics. "
        "If no relevant data is found, respond only with 'No relevant data'. "
        "End the response with: 'Data sourced from Sentinel-2 and Dynamic World.'"
    )
    context_with_values = f"Context: {context}\nMistral Values: {mistral_values}\nQuery: {query} for {', '.join(states)}\n{instruction}"
    response = model.generate_content(context_with_values)
    return clean_response(response.text) if hasattr(response, "text") else "Error generating response"

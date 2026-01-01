# Used to make HTTP requests to the Perplexity API
import requests
import os
# Used to safely parse JSON strings returned by the API
import json


# =========================
# PERPLEXITY API CONFIG
# =========================

# ✅ Put your Perplexity API key directly here
# Example: PPLX_API_KEY = "pplx-xxxxxxxxxxxxxxxx"
PPLX_API_KEY =os.getenv("PPLX_API_KEY")

# Perplexity Chat Completion endpoint
PPLX_URL = "https://api.perplexity.ai/chat/completions"


# =========================
# MAIN FACT-CHECK FUNCTION
# =========================
def classify_news_transformer(text: str) -> dict:
    """
    Uses Perplexity AI to classify news credibility.

    Returns a dictionary with:
    - label: Real / Fake / Unclear
    - score: confidence score (0.0–1.0)
    - mode: always 'perplexity'
    - reason: short explanation

    ⚠️ Function name is kept unchanged so existing app.py code works.
    """

    # If input text is empty or whitespace, return early
    if not text.strip():
        return {
            "label": "Empty input",
            "score": 0.0,
            "mode": "perplexity"
        }

    # Prompt sent to Perplexity AI
    # Instructs the model to return STRICT JSON (important!)
    prompt = f"""
You are a news fact-checking assistant.
Classify the news into ONE of these:
1) Likely Real
2) Likely Fake / Misleading
3) Unclear / Needs Verification

Return ONLY JSON like:
{{
  "label": "...",
  "confidence": 0.0,
  "reason": "short explanation"
}}

News Text: {text}
"""

    # HTTP headers for authentication and content type
    headers = {
        "Authorization": f"Bearer {PPLX_API_KEY}",
        "Content-Type": "application/json"
    }

    # Request payload sent to Perplexity
    payload = {
        "model": "sonar-pro",  # Perplexity model used for reasoning
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1     # Low temperature = more deterministic output
    }

    try:
        # Send POST request to Perplexity API
        res = requests.post(
            PPLX_URL,
            headers=headers,
            json=payload,
            timeout=25
        )

        # Handle non-success HTTP responses
        if res.status_code != 200:
            return {
                "label": "Error",
                "score": 0.0,
                "mode": "perplexity",
                "reason": f"API error {res.status_code}: {res.text}"
            }

        # Extract the AI-generated message content
        output = res.json()["choices"][0]["message"]["content"].strip()

        # Parse JSON returned by the AI
        data = json.loads(output)

        # Return normalized result
        return {
            "label": data.get("label", "Unclear / Needs Verification"),
            "score": float(data.get("confidence", 0.5)),
            "mode": "perplexity",
            "reason": data.get("reason", "")
        }

    except Exception as e:
        # Catch network errors, JSON parsing errors, etc.
        return {
            "label": "Error",
            "score": 0.0,
            "mode": "perplexity",
            "reason": str(e)
        }

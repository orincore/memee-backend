import os
import google.generativeai as genai
from typing import List, Dict
from app.services.supabase_service import get_supabase

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

PROMPT_MEMES = (
    "Find the top 20 most popular Indian memes posted on Reddit in the last 24 hours. "
    "For each, return:\n"
    "- The direct image or video URL\n"
    "- The Reddit post title\n"
    "- The Reddit post URL\n"
    "- The subreddit name\n"
    "Only include posts that are actual memes (not text posts or unrelated content). "
    "Return the result as a JSON array with keys: 'image_url', 'title', 'post_url', 'subreddit'."
)

PROMPT_SUBREDDITS = (
    "List the top 20 most active Indian meme subreddits. "
    "Return only the subreddit names as a JSON array of strings."
)

def list_gemini_models():
    models = genai.list_models()
    print("Available Gemini models:")
    for m in models:
        print(f"- {m.name} (methods: {m.supported_generation_methods})")
    return models

# Call this once at import to print available models
list_gemini_models()

# Use the first available model that supports 'generateContent'
def get_first_supported_model():
    models = genai.list_models()
    for m in models:
        if 'generateContent' in getattr(m, 'supported_generation_methods', []):
            return m.name
    raise RuntimeError("No Gemini model with generateContent support found.")


def search_indian_memes_on_reddit() -> List[Dict]:
    model_name = get_first_supported_model()
    print(f"Using Gemini model: {model_name}")
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(PROMPT_MEMES)
    # Try to extract JSON from the response
    import json
    import re
    # Find the first JSON array in the response
    match = re.search(r'\[.*\]', response.text, re.DOTALL)
    if not match:
        raise ValueError("No JSON array found in Gemini response")
    memes_json = match.group(0)
    try:
        memes = json.loads(memes_json)
    except Exception as e:
        raise ValueError(f"Failed to parse memes JSON: {e}")
    # Filter out memes that already exist in the database
    unique_memes = []
    for meme in memes:
        post_url = meme.get("post_url")
        if not post_url:
            continue
        existing = get_supabase().table("memes").select("id").eq("reddit_post_url", post_url).execute()
        if existing.data and len(existing.data) > 0:
            continue  # Duplicate, skip
        unique_memes.append(meme)
    return unique_memes


def search_active_indian_meme_subreddits() -> List[str]:
    model_name = get_first_supported_model()
    print(f"Using Gemini model for subreddits: {model_name}")
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(PROMPT_SUBREDDITS)
    import json
    import re
    match = re.search(r'\[.*\]', response.text, re.DOTALL)
    if not match:
        raise ValueError("No JSON array found in Gemini subreddit response")
    subreddits_json = match.group(0)
    try:
        subreddits = json.loads(subreddits_json)
    except Exception as e:
        raise ValueError(f"Failed to parse subreddits JSON: {e}")
    return [s.strip() for s in subreddits if isinstance(s, str)] 
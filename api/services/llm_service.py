import os
from datetime import datetime, timezone
from typing import Optional
import dotenv
import boto3
import logging
from models.entry import AnalysisResponse, LlmResponse
import json
import re

logger = logging.getLogger("llm-service")

dotenv.load_dotenv()
os.environ['AWS_BEARER_TOKEN_BEDROCK'] = os.getenv("API_TOKEN")


def extract_json(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


async def analyze_journal_entry(entry_id: str, entry_text: str) -> dict:
    """
    Analyze a journal entry using your chosen LLM API.

    Args:
        entry_id: The ID of the journal entry being analyzed
        entry_text: The combined text of the journal entry (work + struggle + intention)

    Returns:
        dict with keys:
            - entry_id: ID of the analyzed entry
            - sentiment: "positive" | "negative" | "neutral"
            - summary: 2 sentence summary of the entry
            - topics: list of 2-4 key topics mentioned
            - created_at: timestamp when the analysis was created
    """
    client = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1"
    )

    prompt = f"""Analyze the sentiment of this journal entry and respond in JSON format. 
                Return ONLY valid JSON that conforms exactly to this schema:

                {{
                "sentiment": "positive | negative | neutral",
                "summary": "string (2 sentences)",
                "topics": ["string", "string"],
                }}

                Rules:
                - Do not include any extra keys
                - Do not include explanations or markdown
                - Use 2-4 topics 
                
                Journal entry: {entry_text}"""

    model_id = "amazon.nova-lite-v1:0"
    messages = [{"role": "user", "content": [{"text": prompt}]}]

    try:
        response = client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(
                {"messages": messages})
        )
        raw_body = response["body"].read().decode("utf-8")
        model_output = json.loads(raw_body)
        llm_text = model_output["output"]["message"]["content"][0]["text"]
        analysis = LlmResponse.model_validate_json(
            extract_json(llm_text))
        return AnalysisResponse(entry_id=entry_id, **analysis.model_dump())
    except Exception as e:
        logger.error(str(e))
        raise

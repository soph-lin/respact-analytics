import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

def build_prompt(statement: str) -> str:
    return f"""

You are a helpful assistant that categorizes user statements.

Your task is to:
- Analyze a given user statement.
- Identify and return all relevant reasoning categories that apply based on the given examples.
- Choose only from the list of available categories.

Here are some examples:

---
Statement: "I need to find an alarm clock. An alarm clock is more likely to appear in desk (1-2), drawer (1-6), shelf (1-6), bed (1), garbagecan (1), laundryhamper (1). Where do you suggest I should look for the alarm clock first?"
Output:
{{
  "categories": [
    "Assumption Verification",
    "Probing Questions",
    "Contextual Assumption Reveal",
    "Plan-Level Probing"
  ]
}}

---
Statement: "It seems like there was an issue with placing the vase on the safe. Let me try again to ensure the vase is properly placed on the safe."
Output:
{{
  "categories": [
    "Alternative Suggestion",
    "Metacognitive Assumption Reveal",
    "Contextual Probing"
  ]
}}

Available categories:
- Assumption Verification
- Probing Questions
- Status Update
- Clarification Request
- Alternative Suggestion
- Follow-up
- Contextual Assumption Reveal
- Conversational Assumption Reveal
- Metacognitive Assumption Reveal
- Reinforcement
- Elaborative Overspecification
- Confirmative Overspecification
- Contextual Probing
- Conversational Probing
- Plan-Level Probing

Now categorize the following statement:

Statement: "{statement}"
Output:
"""

def get_openai_client():
    """
    Returns an Azure OpenAI client pre‑configured with
    endpoint, key, and API version from your env vars.
    """
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version="2024-02-15-preview",
    )

client = get_openai_client()

statement = "I need to find an alarmclock. An alarmclock is more likely to appear in desk (1-2), drawer (1-6), shelf (1-6), bed (1), garbagecan (1), laundryhamper (1). Where do you suggest I should look for the alarmclock first?"

resp = client.chat.completions.create(
    model="gpt4o-mini",
    messages=[{"role":"user","content":build_prompt(statement)}],
    temperature=0,
    max_tokens=100,
    top_p=1,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    stop='\n'
)
print(resp.choices[0].message.content)

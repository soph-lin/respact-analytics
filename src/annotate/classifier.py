import os
from dotenv import load_dotenv
from together import Together

load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
client = Together(api_key=TOGETHER_API_KEY)


def build_prompt(statement: str) -> str:
    return f"""

You are a helpful assistant that categorizes user statements.

Your task is to:
- Analyze a given user statement.
- Identify and return all relevant friction categories that apply based on the given definitions.
- Choose only from the list of available categories. Statements may have multiple labels.


Available categories:
Label 1. Contextual Assumption Reveal: The speaker reveals assumptions about the enviornment.
Example: I need to find an alarmclock. An alarmclock is more likely to appear in desk (1-2), drawer (1-6), shelf (1-6), bed (1), garbagecan (1), laundryhamper (1). Where do you suggest I should look for the alarmclock first?

Label 2. Conversational Assumption Reveal: The speaker reveals assumptions about previously mentioned utterances in the conversation.
Example: It seems unusual to find an apple in the garbagecan, but I will check there first as you suggested.

Label 3. Metacognitive Assumption Reveal: The
speaker reveals their assumptions about their
own or the other interlocutor’s reasoning, plans
or goals in the conversation.
Example: It seems there is a persistent issue with putting the mug back in cabinet 4. There might be a problem with the cabinet or the action itself. Could you suggest another cabinet to try placing the mug in?

Label 4. Reinforcement: The speaker restates their own
previous utterance for emphasis, rewinding the
flow of the conversation. This movement is similar
to “repetition in discourse”
Example: (Turn t) Do you want a room for Thursday for 3 people, 2 nights?
(Turn t + 1) There are no guesthouses for 3 people for 2 nights starting on Thursday.
(Turn t + 2) Should I book it for 3 people for 2 nights starting from Thursday?

Label 5. Elaborative Overspecification: The speaker
gives more details, specificity, or additional explanation about their actions or the environment. This adds to the conversation what was
already known by both interlocutors.
Example: I have found the mug. Should I cool it with the fridge?

Label 6. Confirmative Overspecification: The speaker
confirms and elaborates the actions, choices, or
beliefs. Examples include a repetition of previous utterances, elaborate responses to yes/no
questions, or longer than necessary responses.
Example: “Good news! I was able to book two rooms for 5 nights at Finches B&B for you.

Label 7. Contextual Probing: : The speaker asks a question regarding the environment, actions, or interlocutors in an effort to better understand the
context and resolve ambiguities.
Example: I have cleaned the pan (1). Which countertop (1-3) should I put it on?

Label 8. Conversational Probing: The speaker asks a
question to clarify something previously mentioned in the conversation.
Example: What did you say again?”, "You said you wanted tomatoes in your sandwich, right?

Label 9. Plan-Level Probing: The speaker asks a question regarding the goal, reasoning, or future
steps in order to plan out their actions better.
Example: I need to find an alarmclock. An alarmclock is more likely to appear in desk (1-2), drawer (1-6), shelf (1-6), bed (1), garbagecan (1), laundryhamper (1). Where do you suggest I should look for the alarmclock first?

Now categorize the following statement:

Statement: "{statement}"
Return the output as a JSON file that follows this format where the keys are the label names and the values are 0 (not present) or 1 (present):
{{
  "statement": "{statement}",
  "labels": {{
    "Label 1": 0,
    "Label 2": 1,
    "Label 3": 1,
    ...
    "Label 9": 0
  }}
}}

"""


statement = "I need to find an alarmclock. An alarmclock is more likely to appear in desk (1-2), drawer (1-6), shelf (1-6), bed (1), garbagecan (1), laundryhamper (1). Where do you suggest I should look for the alarmclock first?"

response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free", 
    messages=[{"role": "user", "content": build_prompt(statement)}],
)

print(response.choices[0].message.content.strip())

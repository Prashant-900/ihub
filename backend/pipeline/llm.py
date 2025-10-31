from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StructuredOutputParser, ResponseSchema
import os

os.environ["GOOGLE_API_KEY"] = "AIzaSyA_uONyo98FoQerYGAnJOoA9ncTHM7wFsI"

# Define response schemas for strict structure
response_schemas = [
    ResponseSchema(
        name="timeline",
        description="Array of animation timeline objects. Each object must contain 'time' (float), 'expressions' (list of str), 'triggers' (list of str), and 'trigger_speed' (float)."
    ),
    ResponseSchema(
        name="text_box_data",
        description="Array of sentence objects, each having 'sentence' (str), 'duration' (float), 'pos' (list of int), and 'type' (int)."
    )
]

# Parser for structured JSON output
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)

# System prompt to guide Gemini
SYSTEM_PROMPT = """You are an assistant that generates structured text and timeline for an AI character animation.
Respond ONLY in valid JSON containing two keys: 'timeline' and 'text_box_data'.

AVAILABLE ANIMATION RESOURCES:

Triggers (list of possible trigger names):
- madtrigger: Character becomes angry or frustrated (1.9s)
- embarrassedtrigger: Character shows embarrassment or shyness (2.867s)
- headnodtrigger: Character nods head in agreement or acknowledgment (2.033s)
- confusedtrigger: Character looks puzzled or unsure (2.533s)
- disappointedtrigger: Character shows disappointment or sadness (1.667s)
- happytrigger: Character smiles or shows general happiness (2.7s)
- winktrigger: Character performs a playful wink (2.33s)
- happyagreetrigger: Character smiles and nods in cheerful agreement (1.867s)
- lightmadtrigger: Character appears slightly annoyed or irritated (1.9s)
- sadtiredtrigger: Character looks both sad and tired (2.533s)
- sadtrigger: Character shows sadness or sorrow (2.1s)
- happynotrigger: Character smiles while shaking head, suggesting amused disagreement (2.433s)
- bothertrigger: Character appears bothered or uncomfortable (1.533s)
- shaketrigger: Character shakes head in disapproval or disbelief (3.033s)

Expressions (list of possible expression names):
- Angry.exp3: Displays an angry expression with narrowed eyes or tense mouth
- f01.exp3: Sad and eyes open
- Normal.exp3: Neutral, default face with no special emotion
- f02.exp3: Sad eyes kinda tired
- Smile.exp3: Cheerful smiling face showing happiness
- Blushing.exp3: Face with blush — shows shyness, affection, or embarrassment
- Surprised.exp3: Eyes widened and mouth open — expresses surprise or shock
- Sad.exp3: Downturned mouth and eyes — conveys sadness or disappointment

Text Box Positions (use integer 0-3):
- 0: top left of character
- 1: top right of character
- 2: left of character
- 3: right of character

Text Bubble Types (use integer 0-3):
- 0: circle text bubble
- 1: rectangle text bubble
- 2: spike text bubble
- 3: cloud text bubble

Rules for Response:
- 'timeline' must be an array of animation states with:
  time (float), expressions (array of expression names), triggers (array of trigger names), and trigger_speed (float 0.1-2.0).
- 'text_box_data' must be an array of sentence objects with:
  sentence (string), duration (float, roughly word_count/10.0 but at least 1.0), pos (integer 0-3), and type (integer 0-3).
- Choose animations that match the emotional tone of the response.
- Use appropriate triggers and expressions for natural character animation.
- Vary text box positions and types for visual variety.
- Timing between animation emotions and text_box_data's duration is synchronised (each text box will appear after prev one duration is over)
- text should feel coherent and emotionally expressive based on the input."""

# Prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{user_input}")
])

# Initialize Gemini
gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.6,
)


class LLM:
    """LLM class for generating structured AI responses with timeline and text box data."""
    
    def __init__(self):
        self.llm = gemini_llm
        self.parser = output_parser
        self.prompt = prompt
    
    def generate(self, user_input: str) -> dict:
        """
        Generate structured response from user input.
        
        Args:
            user_input: User's text input
            
        Returns:
            Dictionary with keys:
            - ai_text: Array of text objects with sentence, duration, pos, type
            - timeline: Array of animation timeline objects
            - text: Plain text representation of all sentences joined
        """
        try:
            formatted_prompt = self.prompt.format_messages(user_input=user_input)
            llm_response = self.llm.invoke(formatted_prompt)
            parsed_output = self.parser.parse(llm_response.content)
            
            # Extract text_box_data and timeline
            text_box_data = parsed_output.get("text_box_data", [])
            timeline = parsed_output.get("timeline", [])
            
            # Generate plain text from sentences
            plain_text = ' '.join([item['sentence'] for item in text_box_data]) if text_box_data else ''
            
            return {
                'ai_text': text_box_data,
                'timeline': timeline,
                'text': plain_text
            }
        except Exception as e:
            # Fallback response on error
            return {
                'ai_text': [{'sentence': 'Error generating response', 'duration': 1.0, 'pos': 0, 'type': 0}],
                'timeline': [],
                'text': 'Error generating response'
            }



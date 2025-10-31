from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import os
import json
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

"""
LLM response generation module using Google Gemini API.

Generates structured AI responses with animation timelines and text formatting,
with support for expression-aware context to create emotionally-aware character responses.
"""

# Load environment variables from .env file
load_dotenv()

# Initialize Gemini API key from environment variable
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError(
        "GOOGLE_API_KEY environment variable not set. "
        "Please configure it in your .env file or environment."
    )
os.environ["GOOGLE_API_KEY"] = api_key


# Pydantic models for structured output
class TextBoxData(BaseModel):
    """Text box data for character animation display."""
    text: str = Field(..., description="The text text to display")
    duration: float = Field(..., description="Duration in seconds to display the text")
    pos: int = Field(..., description="Position 0-3: 0=top left, 1=top right, 2=left, 3=right")
    type: int = Field(..., description="Text bubble type 0-3: 0=circle, 1=rectangle, 2=spike, 3=cloud")


class TimelineEvent(BaseModel):
    """Animation timeline event."""
    time: float = Field(..., description="Time in seconds")
    expressions: List[str] = Field(..., description="List of expression names to apply")
    triggers: List[str] = Field(..., description="List of animation trigger names")
    trigger_speed: float = Field(..., description="Speed multiplier for triggers (0.1-2.0)")


class LLMResponse(BaseModel):
    """Structured LLM response for character animation and dialogue."""
    timeline: List[TimelineEvent] = Field(..., description="Array of animation timeline events")
    text_box_data: List[TextBoxData] = Field(..., description="Array of text boxes with dialogue")

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
- 'text_box_data' must be an array of text objects with:
  text (string), duration (float, roughly word_count/10.0 but at least 1.0), pos (integer 0-3), and type (integer 0-3).
- Choose animations that match the emotional tone of the response.
- Use appropriate triggers and expressions for natural character animation.
- Vary text box positions and types for visual variety, but don't use each position twice.
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
).with_structured_output(LLMResponse)


class LLM:
    """AI character response generator with animation and expression awareness.
    
    Uses Google Gemini API to generate structured responses with animation
    timelines and text formatting. Supports expression-aware responses that
    consider the user's detected emotional state.
    """
    
    def __init__(self):
        """Initialize LLM service with Gemini model and prompt template."""
        self.llm = gemini_llm
        self.prompt = prompt
    
    def generate(
        self,
        user_input: str,
        user_expression: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate structured response from user input with optional expression context.
        
        Generates a response that includes:
        - Animation timeline with triggers and expressions
        - Formatted text boxes with position and styling
        - Plain text representation
        
        Args:
            user_input: User's text message
            user_expression: Optional user's detected emotion (e.g., "happy", "sad")
            
        Returns:
            Dictionary with keys:
                - 'ai_text': Array of text box objects with text, duration, pos, type
                - 'timeline': Array of animation events with timing and triggers
                - 'text': Plain text of all texts joined together
                
        Raises:
            Returns fallback error response if generation fails
        """
        try:
            # Enhance input with expression context if available
            input_with_context = user_input
            if user_expression:
                input_with_context = f"User Expression: {user_expression}\n\nUser Message: {user_input}"
            
            formatted_prompt = self.prompt.format_messages(user_input=input_with_context)
            llm_response = self.llm.invoke(formatted_prompt)
            
            # Parse structured output
            text_box_data = [box.model_dump() for box in llm_response.text_box_data]
            timeline = [event.model_dump() for event in llm_response.timeline]
            
            # Generate plain text representation
            plain_text = ' '.join([item['text'] for item in text_box_data]) if text_box_data else ''
            
            return {
                'ai_text': text_box_data,
                'timeline': timeline,
                'text': plain_text
            }
        except Exception as e:
            # Return fallback response on error
            return {
                'ai_text': [{'text': 'Error generating response', 'duration': 1.0, 'pos': 0, 'type': 0}],
                'timeline': [],
                'text': 'Error generating response'
            }



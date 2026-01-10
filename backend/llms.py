
import os
from typing import List  # library to interact with operating system
import openai  # Library for interacting with the OpenAI API
import json  # Library for working with JSON data

#schema for structured output
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

import base64
from loguru import logger  # Custom logger for logging messages

# API keys
from dotenv import load_dotenv # Load environment variables from a .env file
load_dotenv()  # Load environment variables from .env file
openai_api_key = os.getenv("OPENAI_API_KEY")  # Get OpenAI API key from environment variable    
if not openai_api_key:
    raise ValueError("De OPENAI_API_KEY omgevingsvariabele is niet ingesteld.")

#AI libraries
from openai import OpenAI  # Class for creating OpenAI clients
client = OpenAI(api_key=openai_api_key)  # Create OpenAI client


# Helper function for image encoding (for vision API)
def encode_image(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


class LLMClient:
    
    ROLE_INSTRUCTOR = "developer"  
    ROLE_ME = "user"
    ROLE_AI = "assistant"
    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002"
    #alternatives "text-embedding-3-small" #text-embedding-3-small and text-embedding-3-large
    
    def __init__(self, model=DEFAULT_MODEL):
        self.model = model
        self.last_response_id = None  # Houd het laatste response_id bij

    def prompt_llm(self, input_messages, image=None):
        """
        Prompt the responses endpoint of the OpenAI API with messages
        and/or images. This API maintains stage!
        """
        input = list(input_messages)
        image_content = {}
        if image:
            image_content = LLMClient._prepare_image_content(image)
            input.append(image_content)

        #logger.debug(input)    
                  
        try:
            response = client.responses.create(
                model=self.model,
                previous_response_id=self.last_response_id,  # keep track of the last reponse
                input=input, #can be text and(!) images
            )
            # update reponse id state
            self.last_response_id = response.id
            return response
        except openai.OpenAIError as e:
            logger.error(f"OpenAI API-fout: {e}")
            return None

    """
    def _prepare_image_content(image_path):
        logger.debug(image_path)                    
        base64_image = encode_image(image_path)
        image_encoded = "data:image/jpeg;base64,{}".format(base64_image)

        img_content = {
            "type": "input_image", 
            "image_url": {
                "url": image_encoded,
                "detail": "high"
            }
        }
        
        return img_content"
    """

    @staticmethod
    def convert_to_structured_output(caption, pydantic_model):
        """
        Convert the caption to a structured output format.
        """
        #class FabritiusModel(BaseModel):
        #    description: str = Field(..., description="Concise but complete summary of the painting (200-300 words)")
        #    objects: List[str] = Field(..., description="List of objects such as tools, toys, instruments, etc. in the painting")

        schema_json = pydantic_model.model_json_schema()
        schema_json["additionalProperties"] = False #required parameter!
        #logger.debug(f"Generated JSON schema: {json.dumps(schema_json, indent=4)}")

        instruction = "Convert the caption to a structured output format. Caption: {}".format(caption)
        response = client.responses.create(
            model=LLMClient.DEFAULT_MODEL,
            input = LLMClient.create_llm_message(msg=instruction),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "CMS_schema",
                    "schema": schema_json,
                    "strict": True
                }
            },
        )
        #pydantic_model.model_json_schema(),
        logger.debug("convert to structured output: ".format(response.output_text))
        return json.loads(response.output_text)
            
        
    def get_embedding(self, text: str, model: str = DEFAULT_EMBEDDING_MODEL) -> list:
        """Get embedding vector for text using OpenAI's embedding model.
        
        Args:
            text: The text to generate embeddings for
            model: The embedding model to use (default: text-embedding-ada-002)
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None


    @staticmethod
    def create_llm_message(role=ROLE_ME, msg=""):   
        return [{
            "role": role, 
            "content": msg
        }]
    
    @staticmethod
    def create_llm_message_with_image(role=ROLE_ME, msg="", image_path=None):                                        
        base64_image = encode_image(image_path)
        image_encoded = f"data:image/jpeg;base64,{base64_image}"
    
        return [
            {
                "role": role, 
                "content": [
                    {
                        "type": "input_text",
                        "text": msg
                    },
                    {
                        "type": "input_image", 
                        "image_url": image_encoded,
                        
                    }

                ]
            }
        ]
        
    @staticmethod
    def create_llm_message_with_image_url(role=ROLE_ME, msg="", image_url=None):
        """Create a message for GPT-4V with an image URL."""
        return [
            {
                "role": role, 
                "content": [
                    {
                        "type": "input_text",
                        "text": msg
                    },
                    {
                        "type": "input_image", 
                        "image_url": image_url,
                    }
                ]
            }
        ]

    def generate_labels_with_examples(self, caption: str, field_type: str,
    examples: List[Dict], num_examples: int = 20) -> str:
        """Generate iconographic labels using examples from database.
        
        Args:
            caption: GPT Vision caption of current artwork
            field_type: One of 'subject', 'terms', 'conceptual'
            examples: List of example records with captions and labels
            num_examples: Maximum number of examples to use
        """
        # Filter for valid examples
        valid_examples = []
        iconography_field = f'iconografie_{field_type}'
        
        for example in examples:
            has_caption = example.get('gpt_vision_caption')
            has_label = example.get(iconography_field)
            
            if has_caption and has_label:
                valid_examples.append(example)
                
            if len(valid_examples) >= num_examples:
                break
        
        if not valid_examples:
            logger.warning(f"No valid examples found for {field_type}")
            return ""
        
        # Build few-shot prompt
        example_text = "\n\n".join([
            f"""Caption: {ex['gpt_vision_caption']}
            {field_type.title()}: {ex[iconography_field]}"""
            for ex in valid_examples
        ])
        
        # Create and send prompt
        prompt = f"""
        Given these example artwork descriptions and their {field_type} labels:
        
        {example_text}
        
        Now generate a similar {field_type} label for this artwork:
        Caption: {caption}
        
        Generate only the {field_type} label, nothing else.
        Make sure the style matches the examples shown.
        Use Dutch language for consistency.
        """
        
        try:
            response = self.prompt_llm(self.create_llm_message(msg=prompt))
            return response.output_text.strip() if response else ""
        except Exception as e:
            logger.error(f"Error generating {field_type} labels: {e}")
            return ""
            
    




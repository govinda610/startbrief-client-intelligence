import os
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv
import time
import random
from typing import List, Optional, Type, TypeVar, Union
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

load_dotenv()

# Primary: OpenRouter free models (curated for reliability and JSON support)
OPENROUTER_MODELS = [
    "upstage/solar-pro-3:free",
    "arcee-ai/trinity-large-preview:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "tngtech/tng-r1t-chimera:free",
]

# Fallback: ZAI GLM-4.7 (Anthropic-compatible API - Coding Plan credits)
# ZAI Coding Plan: 120 requests per 5-hour window
ZAI_CONFIG = {
    "api_key": os.getenv("ZAI_API_KEY"),
    "base_url": "https://api.z.ai/api/anthropic",
    "model": "glm-4.7"
}

class LLMRotator:
    """Rotate through free models with rate limiting and ZAI fallback"""
    
    def __init__(self):
        self.current_model_idx = 0
        self.last_request_time = 0
        self.min_delay = 2.0  # seconds between requests to avoid burst limits
        self.use_zai_fallback = False
        self.zai_request_count = 0
        self.zai_limit_reset_time = time.time() + (5 * 3600)  # 5 hours window
        self.max_retries_per_request = 3
        
        # OpenRouter client
        self.openrouter_client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        
        # ZAI client - Using Anthropic SDK for Coding Plan credits
        self.zai_client = Anthropic(
            api_key=ZAI_CONFIG["api_key"],
            base_url=ZAI_CONFIG["base_url"]
        )
    
    def generate(self, prompt: str, system_prompt: str = "You are a helpful assistant.", max_tokens: int = 4000) -> str:
        """Central generation method with rotation and fallback"""
        return self._execute_request(prompt, system_prompt, max_tokens, response_model=None)

    def generate_structured(self, prompt: str, response_model: Type[T], system_prompt: str = "You are a helpful assistant.", max_tokens: int = 4000) -> T:
        """Generation method that returns a validated Pydantic model"""
        return self._execute_request(prompt, system_prompt, max_tokens, response_model=response_model)

    def _execute_request(self, prompt: str, system_prompt: str, max_tokens: int, response_model: Optional[Type[T]]) -> Union[str, T]:
        # Apply rate limiting delay
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        
        # Check ZAI window reset
        if time.time() > self.zai_limit_reset_time:
            self.zai_request_count = 0
            self.zai_limit_reset_time = time.time() + (5 * 3600)

        # Implementation with retries
        for attempt in range(self.max_retries_per_request):
            # Try OpenRouter unless we are in forced fallback mode
            if not self.use_zai_fallback:
                try:
                    result = self._call_openrouter(prompt, system_prompt, max_tokens, response_model)
                    self.last_request_time = time.time()
                    return result
                except Exception as e:
                    print(f"OpenRouter attempt {attempt+1} error: {e}. Trying ZAI fallback...")
                    self.use_zai_fallback = True
            
            # Fallback to ZAI (Anthropic SDK)
            try:
                if self.zai_request_count >= 120:
                    print("ZAI limit reached (120 req/5hr). Resetting rotation to OpenRouter...")
                    self.use_zai_fallback = False
                    continue # Retry with next OpenRouter model
                
                result = self._call_zai(prompt, system_prompt, max_tokens, response_model)
                self.zai_request_count += 1
                self.last_request_time = time.time()
                return result
            except Exception as e:
                print(f"ZAI attempt {attempt+1} error: {e}. Resetting OpenRouter rotation...")
                self.use_zai_fallback = False
                self.current_model_idx = (self.current_model_idx + 1) % len(OPENROUTER_MODELS)
                time.sleep(1) # Brief pause before retry
        
        raise Exception(f"All models failed after {self.max_retries_per_request} attempts.")

    def _call_openrouter(self, prompt: str, system_prompt: str, max_tokens: int, response_model: Optional[Type[T]]) -> Union[str, T]:
        model = OPENROUTER_MODELS[self.current_model_idx]
        print(f"Using OpenRouter model: {model}")
        self.current_model_idx = (self.current_model_idx + 1) % len(OPENROUTER_MODELS)
        
        return self._call_with_openai_client(self.openrouter_client, model, prompt, system_prompt, max_tokens, response_model)

    def _call_zai(self, prompt: str, system_prompt: str, max_tokens: int, response_model: Optional[Type[T]]) -> Union[str, T]:
        print(f"Using ZAI model: {ZAI_CONFIG['model']} (Count: {self.zai_request_count}/120)")
        
        # Anthropic SDK call
        try:
            message = self.zai_client.messages.create(
                model=ZAI_CONFIG["model"],
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": f"{system_prompt}\n\n{prompt}"}
                ]
            )
            content = message.content[0].text
            
            if response_model:
                # Parse and validate JSON response
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                content = content.strip()
                if not content.startswith("{"):
                    start = content.find("{")
                    end = content.rfind("}")
                    if start != -1 and end != -1:
                        content = content[start:end+1]
                
                return response_model.model_validate_json(content)
            
            return content
        except Exception as e:
            raise Exception(f"ZAI Anthropic call failed: {e}")

    def _call_with_openai_client(self, client: OpenAI, model: str, prompt: str, system_prompt: str, max_tokens: int, response_model: Optional[Type[T]]) -> Union[str, T]:
        def _make_request(use_json_mode: bool):
            msgs = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            args = {"max_tokens": max_tokens}
            if response_model:
                schema = response_model.model_json_schema()
                if use_json_mode:
                    args["response_format"] = {"type": "json_object"}
                    msgs[0]["content"] += f"\nReturn ONLY a JSON object matching this schema: {schema}"
                else:
                    msgs[0]["content"] += f"\nReturn ONLY a valid JSON object matching this schema (no markdown, no preamble): {schema}"
            
            return client.chat.completions.create(
                model=model,
                messages=msgs,
                **args
            ).choices[0].message.content

        try:
            content =_make_request(use_json_mode=bool(response_model))
        except Exception as e:
            if response_model and "json_object" in str(e).lower():
                print(f"Model {model} does not support json_mode. Falling back to plain text JSON request...")
                content = _make_request(use_json_mode=False)
            else:
                raise e
        
        if response_model:
            # Extract JSON in case LLM added padding or markdown backticks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Clean up potential leading/trailing non-JSON characters
            content = content.strip()
            if not content.startswith("{"):
                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end != -1:
                    content = content[start:end+1]
            
            return response_model.model_validate_json(content)
        
        return content

# Singleton instance
llm_rotator = LLMRotator()

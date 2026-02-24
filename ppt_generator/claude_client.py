"""
Unified AI Client Module - Compatible with OpenAI and Claude API formats
"""

import os
import json
from typing import Dict, List, Optional, Union, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class UnifiedAIClient:
    """Unified AI Client - Supports OpenAI and Claude API formats"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 provider: Optional[str] = None):
        """
        Initialize unified AI client
        
        Args:
            api_key: API key, if None read from environment
            base_url: API base URL (for OpenAI-compatible APIs)
            provider: Provider ('openai', 'claude', 'auto')
        """
        self.provider = provider or 'auto'
        self.base_url = base_url
        self.api_key = api_key
        
        # Initialize clients
        self._init_clients()
        
    def _init_clients(self):
        """Initialize API clients"""
        self.openai_client = None
        self.claude_client = None
        
        if self.provider == 'claude':
            try:
                from anthropic import Anthropic
                claude_key = self.api_key or os.getenv('ANTHROPIC_API_KEY')
                claude_base_url = self.base_url or os.getenv('ANTHROPIC_BASE_URL')
                if claude_key:
                    kwargs = {"api_key": claude_key}
                    if claude_base_url:
                        kwargs["base_url"] = claude_base_url
                    self.claude_client = Anthropic(**kwargs)
            except ImportError:
                print("Anthropic library not installed, skipping Claude support")
            except Exception as e:
                print(f"Failed to initialize Claude client: {e}")
        else:
            try:
                import openai
                openai_key = self.api_key or os.getenv('OPENAI_API_KEY')
                if openai_key:
                    if self.base_url:
                        self.openai_client = openai.OpenAI(
                            api_key=openai_key,
                            base_url=self.base_url
                        )
                    else:
                        self.openai_client = openai.OpenAI(api_key=openai_key)
            except ImportError:
                print("OpenAI library not installed, skipping OpenAI support")
            except Exception as e:
                print(f"Failed to initialize OpenAI client: {e}")
    
    def _detect_provider(self, model: str) -> str:
        """
        Detect provider from model name
        
        Args:
            model: Model name
            
        Returns:
            str: Provider name
        """
        if 'claude' in model.lower():
            return 'claude'
        elif any(name in model.lower() for name in ['gpt', 'o1', 'davinci', 'curie', 'babbage', 'ada']):
            return 'openai'
        elif self.openai_client:
            return 'openai'
        elif self.claude_client:
            return 'claude'
        else:
            raise ValueError("Cannot detect provider, ensure at least one API is configured")
    
    def chat_completions_create(self,
                              model: str,
                              messages: List[Dict[str, str]],
                              temperature: float = 0.7,
                              max_tokens: Optional[int] = None,
                              stream: bool = False,
                              **kwargs) -> Dict[str, Any]:
        """
        OpenAI-compatible chat completions interface
        
        Args:
            model: Model name
            messages: Message list, format [{"role": "user|assistant|system", "content": "..."}]
            temperature: Temperature parameter
            max_tokens: Max tokens
            stream: Whether to stream output
            **kwargs: Other parameters
            
        Returns:
            Dict: OpenAI format response
        """
        provider = self._detect_provider(model)
        
        if provider == 'openai' and self.openai_client:
            return self._call_openai(model, messages, temperature, max_tokens, stream, **kwargs)
        elif provider == 'claude' and self.claude_client:
            return self._call_claude_as_openai(model, messages, temperature, max_tokens, **kwargs)
        else:
            # raise ValueError(f"Unsupported provider: {provider} or client not initialized")
            return self._call_openai(model, messages, temperature, max_tokens, stream, **kwargs)
    
    def _call_openai(self, model: str, messages: List[Dict], temperature: float, 
                    max_tokens: Optional[int], stream: bool, **kwargs) -> Dict:
        """Call OpenAI API"""
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                timeout=120,
                **kwargs
            )
            
            if stream:
                return response
            
            return {
                "id": response.id,
                "object": "chat.completion",
                "created": response.created,
                "model": response.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response.choices[0].message.content
                    },
                    "finish_reason": response.choices[0].finish_reason
                }],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {e}")
    
    def _call_claude_as_openai(self, model: str, messages: List[Dict], 
                              temperature: float, max_tokens: Optional[int], **kwargs) -> Dict:
        """Convert Claude API call to OpenAI format response"""
        try:
            # Convert message format
            system_message = None
            claude_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    claude_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Call Claude API
            default_model = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-5-global')
            claude_kwargs = {
                "model": model if 'claude' in model else default_model,
                "max_tokens": max_tokens or 4000,
                "temperature": temperature,
                "messages": claude_messages
            }
            
            if system_message:
                claude_kwargs["system"] = system_message
            
            response = self.claude_client.messages.create(**claude_kwargs)
            
            # Convert to OpenAI format
            return {
                "id": response.id,
                "object": "chat.completion",
                "created": int(response.created.timestamp()) if hasattr(response, 'created') else 0,
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response.content[0].text
                    },
                    "finish_reason": response.stop_reason or "stop"
                }],
                "usage": {
                    "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                    "completion_tokens": response.usage.output_tokens if response.usage else 0,
                    "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0
                }
            }
        except Exception as e:
            raise Exception(f"Claude API call failed: {e}")
    
    def generate_response(self, 
                         system_prompt: str, 
                         user_prompt: str, 
                         model: str = "gpt-3.5-turbo",
                         max_tokens: int = 4000,
                         temperature: float = 0.7) -> str:
        """
        Generate AI response (backward compatible method)
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            model: Model name
            max_tokens: Max tokens
            temperature: Temperature parameter
            
        Returns:
            str: AI response
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        
        response = self.chat_completions_create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response["choices"][0]["message"]["content"]
    
    def generate_structured_response(self,
                                   system_prompt: str,
                                   user_prompt: str,
                                   model: str = "gpt-3.5-turbo",
                                   expected_structure: str = "json",
                                   max_tokens: int = 4000) -> Dict:
        """
        Generate structured response
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            model: Model name
            expected_structure: Expected response structure format
            max_tokens: Max tokens
            
        Returns:
            Dict: Parsed structured data
        """
        # Explicitly request structured output in user prompt
        structured_prompt = f"{user_prompt}\n\nPlease return the result in {expected_structure} format."
        
        response = self.generate_response(
            system_prompt=system_prompt,
            user_prompt=structured_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=0.3          # Lower temperature for more stable structured output
        )
        
        # Try to parse JSON response
        if expected_structure.lower() == "json":
            try:
                # First try to clean markdown code blocks
                cleaned_response = response.strip()
                
                # Remove markdown code block markers
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                elif cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]   # Remove ```
                
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # Remove trailing ```
                
                cleaned_response = cleaned_response.strip()
                
                # Extract JSON portion
                start_idx = cleaned_response.find('{')
                end_idx = cleaned_response.rfind('}') + 1
                
                if start_idx != -1 and end_idx != 0:
                    json_str = cleaned_response[start_idx:end_idx]
                    
                    # Fix common JSON issues: replace curly/smart quotes
                    json_str = json_str.replace('"', '"').replace('"', '"')
                    json_str = json_str.replace(''', "'").replace(''', "'")
                    
                    # Try direct parse first
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        # If failed, try to fix quote issues
                        # 2. Handle unescaped quotes
                        lines = json_str.split('\n')
                        fixed_lines = []
                        
                        for line in lines:
                            # Check if JSON string value line
                            if '": "' in line and line.count('"') > 4:
                                    # Try to fix unescaped quotes
                                value_start = line.find('": "') + 4
                                value_end = line.rfind('"')
                                
                                if value_start < value_end:
                                    value = line[value_start:value_end]
                                    # Count inner quotes
                                    inner_quotes = value.count('"')
                                    
                                    if inner_quotes > 0:
                                        # Escape inner quotes
                                        fixed_value = value.replace('"', '\\"')
                                        fixed_line = line[:value_start] + fixed_value + line[value_end:]
                                        fixed_lines.append(fixed_line)
                                        continue
                            
                            fixed_lines.append(line)
                        
                        fixed_json = '\n'.join(fixed_lines)
                        return json.loads(fixed_json)
                else:
                    # If no JSON found, try entire response
                    return json.loads(cleaned_response)
                    
            except json.JSONDecodeError as e:
                print(f"JSON parse failed: {e}")
                print(f"Raw response length: {len(response)} chars")
                print(f"Raw response first 200 chars: {response[:200]}...")
                
                # Try to find specific error position
                try:
                    error_position = e.pos
                    if error_position:
                        print(f"Content near error position: {cleaned_response[max(0, error_position-50):error_position+50]}")
                except:
                    pass
                    
                return {
                    "error": "JSON parse failed",
                    "raw_response": response
                }
        
        return {"response": response}


# For backward compatibility, keep original ClaudeClient class
class ClaudeClient(UnifiedAIClient):
    """Claude client (backward compatible)"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key, provider='claude')


class OpenaiClient(UnifiedAIClient):
    """OpenAI client - For OpenAI API calls"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key, if None read from OPENAI_API_KEY env
            base_url: Custom API endpoint URL, supports OpenAI-compatible APIs
        """
        super().__init__(api_key=api_key, base_url=base_url, provider='openai')
    
    def completions_create(self, 
                          model: str = "gpt-3.5-turbo",
                          messages: Optional[List[Dict[str, str]]] = None,
                          prompt: Optional[str] = None,
                          system_prompt: Optional[str] = None,
                          temperature: float = 0.7,
                          max_tokens: Optional[int] = None,
                          stream: bool = False,
                          **kwargs) -> Dict[str, Any]:
        """
        OpenAI-style completions create method
        
        Args:
            model: Model name, default gpt-3.5-turbo
            messages: Message list (OpenAI format)
            prompt: Single prompt text (simplified usage)
            system_prompt: System prompt (simplified usage)
            temperature: Temperature parameter
            max_tokens: Max tokens
            stream: Whether to stream output
            **kwargs: Other parameters
            
        Returns:
            Dict: OpenAI format response
        """
        # If prompt provided, build messages
        if messages is None:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            if prompt:
                messages.append({"role": "user", "content": prompt})
            elif not messages:
                raise ValueError("Must provide messages or prompt parameter")
        
        return self.chat_completions_create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs
        )
    
    def simple_chat(self, 
                   prompt: str,
                   model: str = "gpt-3.5-turbo",
                   system_prompt: Optional[str] = None,
                   temperature: float = 0.7,
                   max_tokens: Optional[int] = None) -> str:
        """
        Simplified chat interface
        
        Args:
            prompt: User input
            model: Model name
            system_prompt: System prompt
            temperature: Temperature parameter
            max_tokens: Max tokens
            
        Returns:
            str: AI response content
        """
        response = self.completions_create(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response["choices"][0]["message"]["content"]


# Convenience factory functions
def create_openai_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> UnifiedAIClient:
    """Create OpenAI client"""
    return UnifiedAIClient(api_key=api_key, base_url=base_url, provider='openai')


def create_claude_client(api_key: Optional[str] = None) -> UnifiedAIClient:
    """Create Claude client"""
    return UnifiedAIClient(api_key=api_key, provider='claude')


def create_auto_client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> UnifiedAIClient:
    """Create auto-detect client"""
    return UnifiedAIClient(api_key=api_key, base_url=base_url, provider='auto') 
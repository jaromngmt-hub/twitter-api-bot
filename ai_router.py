#!/usr/bin/env python3
"""AI Router - Use the BEST model for each task via OpenRouter.

Supported models:
- anthropic/claude-3.5-sonnet (Best overall code)
- openai/gpt-4o (Good general purpose)
- qwen/qwen3-coder-next (BEST value - cheap + great code)
- deepseek/deepseek-coder (Another great cheap option)
- google/gemini-2.0-flash (Fast)

OpenRouter: https://openrouter.ai
"""

import os
from typing import Optional
from dataclasses import dataclass

import httpx
from loguru import logger


@dataclass
class ModelConfig:
    """Configuration for an AI model."""
    id: str  # OpenRouter model ID
    name: str
    strength: str  # What it's best at
    input_price: float  # per million tokens
    output_price: float  # per million tokens
    context: int  # context window


# Model registry - optimized for specific tasks
CODING_MODELS = {
    # 🧠 REASONING MODELS (Analysis, Planning, Architecture)
    "kimi-k2.5": ModelConfig(
        id="moonshotai/kimi-k2.5",
        name="Kimi K2.5",
        strength="LATEST Kimi - Enhanced reasoning and analysis",
        input_price=0.50,
        output_price=2.00,
        context=256000
    ),
    "kimi-k2": ModelConfig(
        id="moonshotai/kimi-k2",
        name="Kimi K2",
        strength="EXCELLENT reasoning and analysis, great for requirements & architecture",
        input_price=0.50,
        output_price=2.00,
        context=256000
    ),
    "claude-sonnet": ModelConfig(
        id="anthropic/claude-3.5-sonnet",
        name="Claude 3.5 Sonnet",
        strength="Best overall reasoning and code quality",
        input_price=3.00,
        output_price=15.00,
        context=200000
    ),
    
    # 💻 CODING MODELS (Implementation, Tests)
    "qwen-coder-32b": ModelConfig(
        id="qwen/qwen-2.5-coder-32b-instruct",
        name="Qwen Coder 32B",
        strength="LATEST 32B model - Best code generation, 40x cheaper than Claude",
        input_price=0.10,
        output_price=0.40,
        context=131072
    ),
    "qwen-coder": ModelConfig(
        id="qwen/qwen3-coder-next",
        name="Qwen3 Coder Next",
        strength="EXCELLENT code generation, 40x cheaper than Claude, huge context",
        input_price=0.07,
        output_price=0.30,
        context=262144
    ),
    "deepseek-coder": ModelConfig(
        id="deepseek/deepseek-chat",
        name="DeepSeek V3",
        strength="Great coding, very cheap, good for long contexts",
        input_price=0.14,
        output_price=0.28,
        context=64000
    ),
    
    # 🔄 FALLBACK MODELS
    "gpt-4o": ModelConfig(
        id="openai/gpt-4o",
        name="GPT-4o",
        strength="Good general purpose, fast",
        input_price=2.50,
        output_price=10.00,
        context=128000
    ),
    "gemini-flash": ModelConfig(
        id="google/gemini-2.0-flash-exp",
        name="Gemini 2.0 Flash",
        strength="Very fast, cheap, good for simple tasks",
        input_price=0.075,
        output_price=0.30,
        context=1000000
    ),
}


class AIRouter:
    """
    Routes requests to the best AI model for each task.
    
    Uses OpenRouter for unified access to all models.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.client = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://twitter-monitor-bot.com",
                "X-Title": "Twitter Monitor Build Agent"
            } if self.api_key else {}
        )
        
        # OPTIMIZED: Kimi K2.5 for thinking, DeepSeek Coder for coding (FAST!)
        self.defaults = {
            "requirements": "kimi-k2.5",      # 🧠 Kimi K2.5: Latest enhanced reasoning
            "architecture": "kimi-k2.5",      # 🧠 Kimi K2.5: Best for complex architecture
            "design": "kimi-k2.5",            # 🧠 Kimi K2.5: Great for design systems
            "code": "deepseek-coder",         # 💻 DeepSeek: FAST + CHEAP + GOOD!
            "review": "kimi-k2.5",            # 🧠 Kimi K2.5: Critical analysis
            "analysis": "kimi-k2.5",          # 🧠 Kimi K2.5: Content analysis (Discord verifier)
            "docs": "deepseek-coder",         # 💻 DeepSeek: Fast for docs
        }
    
    async def generate(
        self,
        prompt: str,
        task_type: str = "code",
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000
    ) -> str:
        """
        Generate text using the best model for the task.
        
        Args:
            prompt: The prompt to send
            task_type: requirements|architecture|design|code|review|docs
            model: Override default model
            temperature: Creativity (0=deterministic, 1=creative)
            max_tokens: Max response length
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        
        # Select model
        model_key = model or self.defaults.get(task_type, "deepseek-coder")
        model_config = CODING_MODELS.get(model_key, CODING_MODELS["deepseek-coder"])
        
        logger.info(f"Using {model_config.name} for {task_type} (${model_config.input_price}/M tokens)")
        
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": model_config.id,
                    "messages": [
                        {"role": "system", "content": self._get_system_prompt(task_type)},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=120.0
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Log usage
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            cost = (input_tokens / 1_000_000 * model_config.input_price + 
                   output_tokens / 1_000_000 * model_config.output_price)
            
            logger.info(f"Used {input_tokens} in, {output_tokens} out tokens (${cost:.4f})")
            
            return data["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            # Fallback to next best model
            if model_key != "gpt-4o":
                logger.info("Falling back to GPT-4o")
                return await self.generate(prompt, task_type, "gpt-4o", temperature, max_tokens)
            raise
    
    def _get_system_prompt(self, task_type: str) -> str:
        """Get appropriate system prompt for task type."""
        prompts = {
            "requirements": "You are a senior product manager. Extract clear, actionable requirements.",
            "architecture": "You are a staff software architect. Design pragmatic, scalable systems.",
            "design": "You are a UX engineer. Create beautiful, accessible designs.",
            "code": "You are a senior software engineer. Write clean, production-ready code with tests.",
            "review": "You are a staff engineer doing code review. Be thorough but constructive.",
            "docs": "You are a technical writer. Create clear, helpful documentation.",
        }
        return prompts.get(task_type, "You are a helpful AI assistant.")
    
    def get_model_info(self, model_key: str) -> Optional[ModelConfig]:
        """Get info about a specific model."""
        return CODING_MODELS.get(model_key)
    
    def list_models(self) -> dict:
        """List all available models."""
        return {
            key: {
                "name": config.name,
                "strength": config.strength,
                "price_per_million": f"${config.input_price} in / ${config.output_price} out",
                "context": f"{config.context:,} tokens"
            }
            for key, config in CODING_MODELS.items()
        }


# Singleton
ai_router = AIRouter()

#!/usr/bin/env python3
"""Vercel AI SDK Skills for building modern AI-powered applications.

Vercel AI SDK provides:
- Streaming AI responses
- Tool/Function calling
- Structured outputs (JSON mode)
- RAG (Retrieval-Augmented Generation)
- AI UI components
- Multi-step agents

Source: https://github.com/vercel/ai
"""

from typing import Dict, List, Optional, Any


class VercelAISkill:
    """
    Vercel AI SDK patterns for building AI-native applications.
    
    Repo: vercel/ai (10k+ stars)
    Docs: sdk.vercel.ai
    """
    
    # ═══════════════════════════════════════════════════════════════
    # STREAMING PATTERNS
    # ═══════════════════════════════════════════════════════════════
    
    STREAMING_PATTERNS = """
    Vercel AI SDK Streaming Patterns:
    
    1. REAL-TIME UI UPDATES
       - Stream tokens as they're generated
       - Show typing indicator
       - Progressive rendering for better UX
       
    2. STREAMING WITH TOOLS
       - Stream tool calls in real-time
       - Show "thinking" states
       - Progressive UI updates as tools execute
       
    3. MULTI-MODAL STREAMING
       - Text + Images + Audio streaming
       - Progressive loading for large outputs
    
    Code Pattern:
    ```typescript
    const { messages, input, handleInputChange, handleSubmit } = useChat({
      api: '/api/chat',
      streamProtocol: 'text', // or 'data' for complex streams
    });
    ```
    """
    
    # ═══════════════════════════════════════════════════════════════
    # TOOL CALLING (FUNCTION CALLING)
    # ═══════════════════════════════════════════════════════════════
    
    TOOL_CALLING_PATTERNS = """
    Vercel AI SDK Tool Calling:
    
    1. DEFINING TOOLS
       ```typescript
       const tools = {
         getWeather: {
           description: 'Get weather for a location',
           parameters: z.object({
             location: z.string(),
             unit: z.enum(['celsius', 'fahrenheit'])
           }),
           execute: async ({ location, unit }) => {
             // Call weather API
             return { temperature: 72, unit };
           }
         }
       };
       ```
    
    2. MULTI-TOOL WORKFLOWS
       - AI can call multiple tools in sequence
       - Tools can depend on each other
       - Parallel tool execution for speed
       
    3. TOOL UI COMPONENTS
       - Render tool calls as interactive UI
       - Show loading states
       - Allow user to confirm/modify tool inputs
    
    Best Practices:
    - Keep tool descriptions clear
    - Validate inputs with Zod
    - Handle tool errors gracefully
    - Show tool execution status in UI
    """
    
    # ═══════════════════════════════════════════════════════════════
    # STRUCTURED OUTPUTS
    # ═══════════════════════════════════════════════════════════════
    
    STRUCTURED_OUTPUTS = """
    Vercel AI SDK Structured Outputs:
    
    1. OBJECT GENERATION
       ```typescript
       const { object } = useObject({
         api: '/api/analyze',
         schema: z.object({
           sentiment: z.enum(['positive', 'negative', 'neutral']),
           confidence: z.number(),
           keywords: z.array(z.string())
         })
       });
       ```
    
    2. JSON MODE
       - Force AI to return valid JSON
       - Schema validation with Zod
       - Type-safe responses
       
    3. ARRAY GENERATION
       - Generate lists of structured items
       - Pagination support
       - Streaming arrays item by item
    
    Use Cases:
    - Form filling
    - Data extraction
    - Analysis results
    - Report generation
    """
    
    # ═══════════════════════════════════════════════════════════════
    # RAG (RETRIEVAL-AUGMENTED GENERATION)
    # ═══════════════════════════════════════════════════════════════
    
    RAG_PATTERNS = """
    Vercel AI SDK RAG Patterns:
    
    1. VECTOR STORE INTEGRATION
       - Pinecone, Chroma, Supabase pgvector
       - Embedding with OpenAI, Voyage, etc.
       - Semantic search
       
    2. MULTI-QUERY RAG
       - Generate multiple search queries
       - Retrieve from multiple sources
       - Rerank and combine results
       
    3. CONVERSATIONAL RAG
       - Maintain context across turns
       - Cite sources in responses
       - Follow-up question handling
    
    4. RAG WITH TOOLS
       ```typescript
       const tools = {
         searchDocuments: {
           description: 'Search knowledge base',
           execute: async ({ query }) => {
             const embedding = await embed(query);
             const results = await vectorStore.similaritySearch(embedding);
             return results;
           }
         }
       };
       ```
    
    Best Practices:
    - Chunk documents appropriately
    - Add metadata for filtering
    - Show sources to users
    - Cache embeddings
    """
    
    # ═══════════════════════════════════════════════════════════════
    # AI UI COMPONENTS
    # ═══════════════════════════════════════════════════════════════
    
    AI_UI_PATTERNS = """
    Vercel AI SDK UI Components:
    
    1. CHAT INTERFACE
       ```tsx
       import { useChat } from 'ai/react';
       
       function Chat() {
         const { messages, input, handleInputChange, handleSubmit } = useChat();
         return (
           <div>
             {messages.map(m => (
               <div key={m.id}>
                 {m.role}: {m.content}
               </div>
             ))}
             <form onSubmit={handleSubmit}>
               <input value={input} onChange={handleInputChange} />
             </form>
           </div>
         );
       }
       ```
    
    2. COMPLETION INTERFACE
       - Autocomplete inputs
       - Inline suggestions
       - Ghost text
       
    3. ASSISTANT UI
       - Message threading
       - File attachments
       - Tool call visualization
       - Loading states
       
    4. REACT SERVER COMPONENTS (RSC)
       - Stream AI responses from server
       - Progressive enhancement
       - Reduced client JS
    
    Styling Patterns:
    - Markdown rendering
    - Code syntax highlighting
    - Mermaid diagram support
    - LaTeX math rendering
    """
    
    # ═══════════════════════════════════════════════════════════════
    # MULTI-STEP AGENTS
    # ═══════════════════════════════════════════════════════════════
    
    AGENT_PATTERNS = """
    Vercel AI SDK Agent Patterns:
    
    1. REACT PATTERN (Reasoning + Acting)
       - Think about what to do
       - Act (call tools)
       - Observe results
       - Repeat until done
       
    2. PLANNING AGENTS
       - Break complex tasks into steps
       - Execute steps sequentially
       - Handle failures and retry
       
    3. MULTI-AGENT SYSTEMS
       - Specialized agents for different tasks
       - Agent router delegates to right agent
       - Share context between agents
    
    4. HUMAN-IN-THE-LOOP
       - Pause for user confirmation
       - Show proposed actions
       - Allow editing tool inputs
       - Approve/reject workflows
    
    Implementation:
    ```typescript
    const agent = createAgent({
      model: openai('gpt-4o'),
      tools: { search, calculate, save },
      maxSteps: 10, // Prevent infinite loops
    });
    ```
    """
    
    # ═══════════════════════════════════════════════════════════════
    # PROVIDER PATTERNS
    # ═══════════════════════════════════════════════════════════════
    
    PROVIDER_SETUP = """
    Vercel AI SDK Provider Setup:
    
    Supported Providers:
    - OpenAI (gpt-4, gpt-3.5, dall-e)
    - Anthropic (claude-3, claude-2)
    - Google (gemini, palm)
    - Mistral
    - Groq (fast inference)
    - Ollama (local models)
    
    Universal Interface:
    ```typescript
    import { generateText } from 'ai';
    import { openai } from '@ai-sdk/openai';
    import { anthropic } from '@ai-sdk/anthropic';
    
    // Same code, different providers
    const result = await generateText({
      model: openai('gpt-4o'), // or anthropic('claude-3-opus')
      prompt: 'Hello world',
    });
    ```
    
    Provider Routing:
    - Route by task type (fast vs quality)
    - Fallback providers
    - Cost optimization
    """
    
    @staticmethod
    def should_use_ai_sdk(project_description: str, features: List[str]) -> bool:
        """
        Determine if a project should use Vercel AI SDK.
        
        Returns True if project involves:
        - Chat interfaces
        - AI-generated content
        - Tool use / function calling
        - Streaming responses
        - RAG / knowledge bases
        """
        ai_keywords = [
            'ai', 'chat', 'gpt', 'llm', 'openai', 'claude',
            'assistant', 'bot', 'generate', 'summarize',
            'analyze', 'semantic', 'embedding', 'vector',
            'rag', 'retrieval', 'agent', 'automation',
            'content', 'writing', 'creative'
        ]
        
        text = (project_description + ' ' + ' '.join(features)).lower()
        matches = [kw for kw in ai_keywords if kw in text]
        
        return len(matches) >= 2  # If 2+ AI keywords, likely AI project
    
    @staticmethod
    def get_recommended_stack(project_type: str) -> Dict[str, str]:
        """Get AI SDK stack recommendation for project type."""
        
        stacks = {
            "chat_app": {
                "framework": "Next.js 14",
                "ai_sdk": "ai (React hooks)",
                "ui": "shadcn/ui + Tailwind",
                "backend": "Next.js API routes",
                "database": "Vercel Postgres + Vercel KV",
                "streaming": "Vercel AI SDK streaming",
                "deployment": "Vercel"
            },
            "ai_api": {
                "framework": "FastAPI",
                "ai_sdk": "Vercel AI SDK Core (Python)",
                "streaming": "Server-Sent Events (SSE)",
                "deployment": "Render / Railway",
                "database": "PostgreSQL"
            },
            "rag_knowledge_base": {
                "framework": "Next.js",
                "ai_sdk": "ai + @ai-sdk/openai",
                "vector_store": "Pinecone / Supabase pgvector",
                "embedding": "OpenAI text-embedding-3-small",
                "ui": "Streaming chat with sources"
            },
            "ai_agent": {
                "framework": "Python (FastAPI/Express)",
                "ai_sdk": "Vercel AI SDK Core",
                "pattern": "ReAct with tools",
                "tools": "Custom tool definitions",
                "state": "Redis / Upstash"
            }
        }
        
        return stacks.get(project_type, stacks["chat_app"])
    
    @staticmethod
    def generate_ai_component_prompt(component_type: str, description: str) -> str:
        """Generate prompt for AI-powered UI component."""
        
        prompts = {
            "chat_interface": f"""Create a chat interface using Vercel AI SDK:

Requirements: {description}

Use:
- useChat hook from 'ai/react'
- Streaming messages
- Loading states
- Error handling
- Message history
- Tool call visualization (if tools used)

Include:
- TypeScript types
- Styled with Tailwind
- Responsive design
""",
            "completion_input": f"""Create an autocomplete/completion input:

Requirements: {description}

Use:
- useCompletion hook
- Ghost text suggestions
- Keyboard navigation (Tab to accept)
- Debounced requests

Include:
- TypeScript
- Accessibility (ARIA labels)
- Loading indicator
""",
            "object_generation": f"""Create a form that uses AI to generate structured data:

Requirements: {description}

Use:
- useObject hook
- Zod schema validation
- Real-time preview
- Error handling

Include:
- Form UI
- Generated object display
- Copy to clipboard
"""
        }
        
        return prompts.get(component_type, prompts["chat_interface"])


# Pre-built templates for common AI patterns
VERCEL_AI_TEMPLATES = {
    "streaming_chat_api": """
// app/api/chat/route.ts
import { openai } from '@ai-sdk/openai';
import { streamText } from 'ai';

export async function POST(req: Request) {
  const { messages } = await req.json();
  
  const result = streamText({
    model: openai('gpt-4o'),
    messages,
    tools: { /* define tools */ },
  });
  
  return result.toDataStreamResponse();
}
""",
    
    "chat_component": """
// components/chat.tsx
'use client';

import { useChat } from 'ai/react';

export function Chat() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat();
  
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        {messages.map(m => (
          <div key={m.id} className={`p-4 ${m.role === 'user' ? 'bg-blue-50' : 'bg-gray-50'}`}>
            <strong>{m.role}:</strong> {m.content}
          </div>
        ))}
      </div>
      
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <input
          value={input}
          onChange={handleInputChange}
          disabled={isLoading}
          className="w-full p-2 border rounded"
          placeholder="Type a message..."
        />
      </form>
    </div>
  );
}
""",
    
    "tool_definition": """
// lib/tools.ts
import { z } from 'zod';

export const tools = {
  getWeather: {
    description: 'Get current weather',
    parameters: z.object({
      location: z.string(),
      unit: z.enum(['celsius', 'fahrenheit']).optional()
    }),
    execute: async ({{ location, unit = 'celsius' }}) => {
      // Implementation
      return {{ temperature: 22, unit }};
    }
  }
};
"""
}


def get_vercel_ai_skill():
    """Get the Vercel AI SDK skill."""
    return VercelAISkill

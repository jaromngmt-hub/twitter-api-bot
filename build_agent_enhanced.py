#!/usr/bin/env python3
"""Enhanced Build Agent with famous GitHub skills.

Skills integrated from top GitHub repos:
1. ANALYZE - Shape Up (Basecamp) - Requirements Engineering
2. PLAN - System Design Primer (270k stars) - Architecture patterns
3. DESIGN - Google Technical Writing Course - Documentation
4. IMPLEMENT - Awesome Testing + Jest/Pytest best practices - TDD
5. REVIEW - Google Engineering Practices (40k stars) - Code review
6. DEPLOY - GitHub Actions Awesome (30k stars) - CI/CD, Docker

Pipeline stages:
1. ANALYZE - Extract requirements using Shape Up methodology
2. PLAN - Architecture using System Design Primer patterns
3. DESIGN - API/docs using Google Technical Writing standards
4. IMPLEMENT - TDD with tests first (Awesome Testing patterns)
5. REVIEW - Code review using Google & OWASP checklists
6. DEPLOY - CI/CD using GitHub Actions best practices
"""

import asyncio
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

import httpx
from loguru import logger
from openai import AsyncOpenAI

from config import settings
from build_skills import (
    RequirementsEngineeringSkill,
    SystemArchitectureSkill,
    TechnicalWritingSkill,
    TDDSkill,
    CodeReviewSkill,
    DevOpsSkill,
    VercelAISkill,
    VERCEL_AI_TEMPLATES,
)


class BuildStage(Enum):
    """Build pipeline stages."""
    ANALYZE = "analyze"
    PLAN = "plan"
    DESIGN = "design"
    IMPLEMENT = "implement"
    REVIEW = "review"
    DEPLOY = "deploy"
    COMPLETE = "complete"


@dataclass
class ProjectRequirements:
    """Extracted requirements from tweet analysis."""
    name: str
    description: str
    problem_statement: str
    target_users: str
    core_features: List[str]
    constraints: List[str]
    success_criteria: List[str]
    tweet_source: str


@dataclass
class TechStack:
    """Selected technology stack."""
    language: str
    framework: str
    database: Optional[str]
    frontend: Optional[str]
    deployment: str
    testing: str
    ci_cd: str
    reasoning: str


@dataclass
class Component:
    """System component definition."""
    name: str
    type: str  # api, database, frontend, worker, etc.
    description: str
    responsibilities: List[str]
    dependencies: List[str]
    files: List[str]


@dataclass
class ProjectPlan:
    """Complete project plan."""
    requirements: ProjectRequirements
    tech_stack: TechStack
    components: List[Component]
    api_endpoints: List[Dict]
    data_models: List[Dict]
    file_structure: Dict[str, Any]
    estimated_hours: int
    risks: List[str]


@dataclass
class CodeFile:
    """Generated code file."""
    path: str
    content: str
    language: str
    purpose: str
    tests: Optional[str] = None


@dataclass
class ReviewResult:
    """Code review results."""
    score: int  # 1-10
    issues: List[Dict]
    suggestions: List[str]
    security_concerns: List[str]
    passed: bool


class EnhancedBuildAgent:
    """
    Production-grade build agent with multi-stage pipeline.
    
    Skills integrated:
    - Requirements engineering
    - Architecture design patterns
    - Test-driven development (TDD)
    - Code review best practices
    - Security scanning
    - CI/CD pipeline creation
    """
    
    def __init__(self):
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.github_token = settings.GITHUB_TOKEN
        self.github_username = settings.GITHUB_USERNAME
        self.projects_dir = "./projects"
        os.makedirs(self.projects_dir, exist_ok=True)
    
    # ═══════════════════════════════════════════════════════════════
    # STAGE 1: ANALYZE - Extract structured requirements from tweet
    # ═══════════════════════════════════════════════════════════════
    
    async def analyze_tweet(self, tweet_text: str, username: str) -> Optional[ProjectRequirements]:
        """
        Stage 1: ANALYZE using Shape Up methodology (from Basecamp).
        
        Skill: RequirementsEngineeringSkill
        Source: basecamp/shape_up, Joel on Software
        """
        logger.info(f"Stage 1/6: ANALYZE - Extracting requirements using Shape Up methodology")
        
        prompt = RequirementsEngineeringSkill.extract_requirements_prompt(tweet_text, username)

        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": f"You are a senior product manager using Shape Up methodology (from Basecamp). {RequirementsEngineeringSkill.SHAPE_UP_PRINCIPLES}"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            content = self._extract_json(content)
            data = json.loads(content)
            
            if not data.get("is_buildable"):
                logger.info(f"Tweet from @{username} not buildable: {data.get('reason')}")
                return None
            
            logger.info(f"✅ Analysis complete: {data['project_name']} (appetite: {data.get('appetite', 'unknown')})")
            
            return ProjectRequirements(
                name=data["project_name"],
                description=data["description"],
                problem_statement=data["problem_statement"],
                target_users=data["target_users"],
                core_features=data["core_features"],
                constraints=data.get("constraints", []),
                success_criteria=data.get("success_criteria", []),
                tweet_source=f"https://twitter.com/{username}"
            )
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════
    # STAGE 2: PLAN - Architecture & Tech Stack Selection
    # ═══════════════════════════════════════════════════════════════
    
    async def create_architecture_plan(self, requirements: ProjectRequirements) -> ProjectPlan:
        """
        Stage 2: PLAN using System Design Primer patterns + Vercel AI SDK for AI projects.
        
        Skills: 
        - SystemArchitectureSkill (System Design Primer)
        - VercelAISkill (Vercel AI SDK - 10k stars)
        """
        logger.info(f"Stage 2/6: PLAN - Designing architecture")
        
        # Check if this is an AI project
        is_ai_project = VercelAISkill.should_use_ai_sdk(
            requirements.description,
            requirements.core_features
        )
        
        if is_ai_project:
            logger.info(f"🤖 AI project detected! Using Vercel AI SDK patterns")
            return await self._create_ai_architecture_plan(requirements)
        
        prompt = SystemArchitectureSkill.design_architecture_prompt({
            "name": requirements.name,
            "appetite": getattr(requirements, 'appetite', 'unknown'),
            "features": requirements.core_features
        })

        response = await self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are a staff software architect. Apply patterns from System Design Primer. {SystemArchitectureSkill.SCALABILITY_PATTERNS}"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=2500
        )
        
        content = response.choices[0].message.content
        content = self._extract_json(content)
        data = json.loads(content)
        
        tech_stack = TechStack(**data["tech_stack"])
        components = [Component(**c) for c in data["components"]]
        
        logger.info(f"✅ Architecture planned: {data.get('architecture_pattern')} with {len(components)} components")
        
        return ProjectPlan(
            requirements=requirements,
            tech_stack=tech_stack,
            components=components,
            api_endpoints=data["api_endpoints"],
            data_models=data["data_models"],
            file_structure=data["file_structure"],
            estimated_hours=data["estimated_hours"],
            risks=data.get("risks", [])
        )
    
    async def _create_ai_architecture_plan(self, requirements: ProjectRequirements) -> ProjectPlan:
        """
        Create architecture plan specifically for AI projects using Vercel AI SDK.
        
        Skill: VercelAISkill
        Source: vercel/ai (10k+ stars)
        """
        # Determine project type
        features_text = ' '.join(requirements.core_features).lower()
        
        if 'chat' in features_text or 'conversation' in features_text:
            project_type = "chat_app"
        elif 'rag' in features_text or 'knowledge' in features_text or 'search' in features_text:
            project_type = "rag_knowledge_base"
        elif 'agent' in features_text or 'automation' in features_text or 'tool' in features_text:
            project_type = "ai_agent"
        else:
            project_type = "chat_app"  # Default
        
        stack = VercelAISkill.get_recommended_stack(project_type)
        
        prompt = f"""Design an AI-powered application using Vercel AI SDK patterns.

Project: {requirements.name}
Description: {requirements.description}
Features: {', '.join(requirements.core_features)}
Project Type: {project_type}

Recommended Stack from Vercel AI SDK:
{json.dumps(stack, indent=2)}

Vercel AI SDK Patterns to apply:
{VercelAISkill.STREAMING_PATTERNS}

{VercelAISkill.TOOL_CALLING_PATTERNS}

{VercelAISkill.AGENT_PATTERNS if project_type == "ai_agent" else VercelAISkill.RAG_PATTERNS if project_type == "rag_knowledge_base" else ""}

Design:
1. ARCHITECTURE: Next.js 14 with App Router, API routes for AI
2. AI SDK SETUP: Provider (OpenAI/Anthropic), streaming, tools
3. COMPONENTS: Chat UI, message handling, tool visualization
4. STATE: Message history, conversation context
5. API ROUTES: /api/chat (streaming), /api/tools (executions)

Respond in JSON with tech_stack, components, api_endpoints, etc."""

        response = await self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI engineer specializing in Vercel AI SDK. Design modern AI applications with streaming, tool calling, and great UX."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=2500
        )
        
        content = response.choices[0].message.content
        content = self._extract_json(content)
        data = json.loads(content)
        
        # Add Vercel AI SDK to tech stack
        tech_stack = TechStack(**data["tech_stack"])
        components = [Component(**c) for c in data["components"]]
        
        logger.info(f"✅ AI Architecture planned: {project_type} with Vercel AI SDK ({len(components)} components)")
        
        return ProjectPlan(
            requirements=requirements,
            tech_stack=tech_stack,
            components=components,
            api_endpoints=data["api_endpoints"],
            data_models=data["data_models"],
            file_structure=data["file_structure"],
            estimated_hours=data["estimated_hours"],
            risks=data.get("risks", [])
        )
            requirements=requirements,
            tech_stack=tech_stack,
            components=components,
            api_endpoints=data["api_endpoints"],
            data_models=data["data_models"],
            file_structure=data["file_structure"],
            estimated_hours=data["estimated_hours"],
            risks=data.get("risks", [])
        )
    
    # ═══════════════════════════════════════════════════════════════
    # STAGE 3: DESIGN - Detailed Design Documents
    # ═══════════════════════════════════════════════════════════════
    
    async def create_design_docs(self, plan: ProjectPlan) -> Dict[str, str]:
        """
        Stage 3: DESIGN using Google Technical Writing standards.
        
        Skill: TechnicalWritingSkill
        Source: Google Technical Writing Course (10k stars)
        """
        logger.info(f"Stage 3/6: DESIGN - Creating docs using Google Technical Writing standards")
        
        # API Specification
        if plan.api_endpoints:
            api_doc = f"# API Specification: {plan.requirements.name}\n\n"
            api_doc += "## Endpoints\n\n"
            for endpoint in plan.api_endpoints:
                api_doc += f"### {endpoint['method']} {endpoint['path']}\n"
                api_doc += f"{endpoint['description']}\n\n"
                if 'request' in endpoint:
                    api_doc += f"**Request:**\n```json\n{json.dumps(endpoint['request'], indent=2)}\n```\n\n"
                if 'response' in endpoint:
                    api_doc += f"**Response:**\n```json\n{json.dumps(endpoint['response'], indent=2)}\n```\n\n"
            docs["API_SPEC.md"] = api_doc
        
        # Architecture Decision Record (ADR)
        adr = f"# Architecture Decision Record: {plan.requirements.name}\n\n"
        adr += f"## Context\n\n{plan.requirements.problem_statement}\n\n"
        adr += f"## Decision\n\n"
        adr += f"We will build a {plan.tech_stack.language} application using {plan.tech_stack.framework}.\n\n"
        adr += f"**Rationale:** {plan.tech_stack.reasoning}\n\n"
        adr += f"## Components\n\n"
        for comp in plan.components:
            adr += f"- **{comp.name}** ({comp.type}): {comp.description}\n"
        adr += f"\n## Risks\n\n"
        for risk in plan.risks:
            adr += f"- {risk}\n"
        docs["ADR.md"] = adr
        
        return docs
    
    # ═══════════════════════════════════════════════════════════════
    # STAGE 4: IMPLEMENT - Test-Driven Development
    # ═══════════════════════════════════════════════════════════════
    
    async def generate_code(self, plan: ProjectPlan, component: Component) -> List[CodeFile]:
        """
        Stage 4: IMPLEMENT using Test-Driven Development (TDD).
        
        Skill: TDDSkill
        Source: Awesome Testing, Jest/Pytest best practices
        
        Follows Red-Green-Refactor cycle:
        1. Write failing test (Red)
        2. Write code to pass test (Green)
        3. Refactor while keeping tests passing
        """
        files = []
        
        for file_path in component.files:
            # Generate tests first (TDD)
            test_content = await self._generate_tests(file_path, component, plan)
            
            # Generate implementation
            impl_content = await self._generate_implementation(file_path, component, plan, test_content)
            
            # Detect language
            language = self._detect_language(file_path)
            
            files.append(CodeFile(
                path=file_path,
                content=impl_content,
                language=language,
                purpose=f"{component.name} implementation",
                tests=test_content
            ))
        
        return files
    
    async def _generate_tests(self, file_path: str, component: Component, plan: ProjectPlan) -> str:
        """
        Stage 4a: Write tests FIRST (TDD - Red phase).
        
        Skill: TDDSkill
        Source: Awesome Testing, Jest/Pytest best practices
        """
        prompt = f"""Write comprehensive unit tests for {file_path}.

Component: {component.name}
Type: {component.type}
Description: {component.description}
Responsibilities: {', '.join(component.responsibilities)}
Tech Stack: {plan.tech_stack.language}, {plan.tech_stack.testing}

Apply TDD principles:
{TDDSkill.TDD_CYCLE}

Apply testing best practices:
{TDDSkill.BEST_PRACTICES}

Write tests using AAA pattern (Arrange, Act, Assert).
Tests should FAIL initially (we haven't written the code yet).

Only output the test code."""

        response = await self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are a TDD expert. Apply patterns from Awesome Testing. {TDDSkill.BEST_PRACTICES}"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        return self._clean_code(response.choices[0].message.content)
    
    async def _generate_implementation(self, file_path: str, component: Component, plan: ProjectPlan, tests: str) -> str:
        """Generate implementation to pass the tests."""
        prompt = f"""Write implementation for {file_path} that passes these tests.

Component: {component.name}
Type: {component.type}
Description: {component.description}
Responsibilities: {', '.join(component.responsibilities)}
Dependencies: {', '.join(component.dependencies)}
Tech Stack: {plan.tech_stack.language}, {plan.tech_stack.framework}

Tests to pass:
```
{tests}
```

Requirements:
- Clean, readable code
- Follow {plan.tech_stack.language} best practices
- Include docstrings/comments
- Handle errors gracefully
- Use dependency injection where appropriate

Only output the implementation code."""

        response = await self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a senior software engineer writing production-quality code. Follow clean code principles and SOLID design."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2500
        )
        
        return self._clean_code(response.choices[0].message.content)
    
    # ═══════════════════════════════════════════════════════════════
    # STAGE 5: REVIEW - Code Review & Security Scan
    # ═══════════════════════════════════════════════════════════════
    
    async def review_code(self, files: List[CodeFile], plan: ProjectPlan) -> ReviewResult:
        """
        Stage 5: REVIEW using Google Engineering Practices + OWASP.
        
        Skill: CodeReviewSkill
        Source: google/eng-practices (40k stars), OWASP Secure Code Review
        """
        logger.info(f"Stage 5/6: REVIEW - Code review using Google & OWASP standards")
        
        all_code = "\n\n".join([f"=== {f.path} ===\n{f.content}" for f in files])
        
        prompt = CodeReviewSkill.review_prompt(all_code, plan.tech_stack.language)

        response = await self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are a staff engineer performing code review. Apply Google Engineering Practices. {CodeReviewSkill.GOOGLE_REVIEW_CHECKLIST}"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        content = self._extract_json(content)
        data = json.loads(content)
        
        logger.info(f"✅ Code review complete: Score {data['score']}/10, Passed: {data['passed']}")
        
        return ReviewResult(
            score=data["score"],
            issues=data.get("issues", []),
            suggestions=data.get("suggestions", []),
            security_concerns=data.get("security_concerns", []),
            passed=data["passed"]
        )
    
    # ═══════════════════════════════════════════════════════════════
    # STAGE 6: DEPLOY - CI/CD Pipeline
    # ═══════════════════════════════════════════════════════════════
    
    async def generate_ai_sdk_files(self, plan: ProjectPlan) -> Dict[str, str]:
        """
        Generate Vercel AI SDK specific files for AI projects.
        
        Skill: VercelAISkill
        Source: vercel/ai (10k stars)
        """
        files = {}
        
        # Check if this is an AI project
        is_ai = 'ai' in plan.tech_stack.framework.lower() or 'vercel' in plan.tech_stack.deployment.lower()
        if not is_ai:
            return files
        
        logger.info(f"🤖 Generating Vercel AI SDK files")
        
        # 1. AI API Route (streaming)
        files["app/api/chat/route.ts"] = '''import { openai } from '@ai-sdk/openai';
import { streamText } from 'ai';

export async function POST(req: Request) {
  const { messages } = await req.json();
  
  const result = streamText({
    model: openai('gpt-4o'),
    messages,
    onChunk: async ({ chunk }) => {
      // Optional: Log or process chunks
    },
  });
  
  return result.toDataStreamResponse();
}
'''
        
        # 2. Chat Component
        files["components/chat.tsx"] = ''''use client';

import { useChat } from 'ai/react';
import { Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';

export function Chat() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat();
  
  return (
    <div className="flex flex-col h-[600px] border rounded-lg">
      <ScrollArea className="flex-1 p-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-10">
            <p className="text-lg font-medium">Welcome! 👋</p>
            <p className="text-sm">Start a conversation...</p>
          </div>
        ) : (
          messages.map((m) => (
            <div
              key={m.id}
              className={`mb-4 flex ${
                m.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  m.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <p className="text-sm">{m.content}</p>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}
      </ScrollArea>
      
      <form onSubmit={handleSubmit} className="p-4 border-t flex gap-2">
        <Input
          value={input}
          onChange={handleInputChange}
          placeholder="Type your message..."
          disabled={isLoading}
          className="flex-1"
        />
        <Button type="submit" disabled={isLoading || !input.trim()}>
          <Send className="w-4 h-4" />
        </Button>
      </form>
    </div>
  );
}
'''
        
        # 3. Environment variables template
        files[".env.example"] = '''# Vercel AI SDK
OPENAI_API_KEY=sk-...
# Or use Anthropic
# ANTHROPIC_API_KEY=sk-ant-...

# Optional: Other providers
# GROQ_API_KEY=...
# MISTRAL_API_KEY=...
'''
        
        # 4. Vercel config
        files["vercel.json"] = '''{
  "functions": {
    "app/api/**/*.ts": {
      "maxDuration": 30
    }
  }
}
'''
        
        logger.info(f"✅ Generated {len(files)} Vercel AI SDK files")
        return files
    
    async def generate_cicd_files(self, plan: ProjectPlan) -> Dict[str, str]:
        """
        Stage 6: DEPLOY using GitHub Actions & Docker/Vercel best practices.
        
        Skill: DevOpsSkill + VercelAISkill
        Source: Awesome GitHub Actions (30k stars), Vercel deployment patterns
        """
        logger.info(f"Stage 6/6: DEPLOY - Generating CI/CD")
        
        # Check if Vercel deployment
        is_vercel = 'vercel' in plan.tech_stack.deployment.lower()
        
        files = {}
        
        # For Vercel deployments, use Vercel-specific workflow
        if is_vercel:
            workflow = '''name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Lint
        run: npm run lint
      
      - name: Type check
        run: npm run type-check
      
      - name: Test
        run: npm test
      
      - name: Build
        run: npm run build
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Vercel
        uses: vercel/action-deploy@v1
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
'''
            files[".github/workflows/ci.yml"] = workflow
            
        else:
            # Standard GitHub Actions for other platforms
            prompt = DevOpsSkill.generate_cicd_prompt(
                {
                    "language": plan.tech_stack.language,
                    "framework": plan.tech_stack.framework,
                    "testing": plan.tech_stack.testing
                },
                plan.tech_stack.deployment
            )

        response = await self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"Generate production-ready CI/CD. Apply patterns from GitHub Actions Awesome. {DevOpsSkill.GITHUB_ACTIONS_PATTERNS}"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2500
        )
        
        cicd_content = response.choices[0].message.content
        cicd_content = self._clean_code(cicd_content)
        files[".github/workflows/ci.yml"] = cicd_content
        
        # Dockerfile using best practices
        if "docker" in plan.tech_stack.deployment.lower() or "container" in plan.tech_stack.deployment.lower():
            dockerfile_prompt = f"""Generate a Dockerfile for {plan.tech_stack.language} application.

Apply Docker best practices:
{DevOpsSkill.DOCKER_BEST_PRACTICES}

Requirements:
- Use specific base image (not :latest)
- Minimize layers
- Run as non-root user
- Include .dockerignore recommendations
"""
            response = await self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a DevOps engineer specializing in Docker."},
                    {"role": "user", "content": dockerfile_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            dockerfile = self._clean_code(response.choices[0].message.content)
            files["Dockerfile"] = dockerfile
            files[".dockerignore"] = "__pycache__\n*.pyc\n.env\n.git\n.gitignore\n.pytest_cache\n"
        
        # README with setup instructions
        readme = await self._generate_readme(plan)
        files["README.md"] = readme
        
        logger.info(f"✅ CI/CD generated: GitHub Actions workflow + {'Dockerfile' if 'Dockerfile' in files else 'deployment config'}")
        
        return files
    
    # ═══════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def _extract_json(self, content: str) -> str:
        """Extract JSON from markdown code blocks."""
        if "```json" in content:
            return content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            return content.split("```")[1].split("```")[0].strip()
        return content.strip()
    
    def _clean_code(self, content: str) -> str:
        """Clean code from markdown formatting."""
        if content.startswith("```"):
            lines = content.split("\n")
            if len(lines) > 1:
                # Remove first line (```language)
                content = "\n".join(lines[1:])
                # Remove last line (```)
                if content.endswith("```"):
                    content = content[:-3].strip()
        return content
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".rb": "ruby",
            ".php": "php",
            ".html": "html",
            ".css": "css",
            ".sql": "sql",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".json": "json",
            ".md": "markdown",
        }
        return mapping.get(ext, "text")
    
    async def _generate_readme(self, plan: ProjectPlan) -> str:
        """Generate comprehensive README."""
        readme = f"""# {plan.requirements.name}

{plan.requirements.description}

## 🎯 Problem Statement

{plan.requirements.problem_statement}

## 👥 Target Users

{plan.requirements.target_users}

## 🛠️ Tech Stack

- **Language:** {plan.tech_stack.language}
- **Framework:** {plan.tech_stack.framework}
- **Database:** {plan.tech_stack.database or 'None'}
- **Frontend:** {plan.tech_stack.frontend or 'None'}
- **Deployment:** {plan.tech_stack.deployment}
- **Testing:** {plan.tech_stack.testing}
- **CI/CD:** {plan.tech_stack.ci_cd}

## 🏗️ Architecture

### Components

"""
        for comp in plan.components:
            readme += f"#### {comp.name} ({comp.type})\n\n"
            readme += f"{comp.description}\n\n"
            readme += "**Responsibilities:**\n"
            for resp in comp.responsibilities:
                readme += f"- {resp}\n"
            readme += "\n"
        
        readme += f"""## 🚀 Getting Started

### Prerequisites

- {plan.tech_stack.language} installed
- {plan.tech_stack.database or 'No database required'}

### Installation

```bash
git clone https://github.com/{self.github_username}/{plan.requirements.name}.git
cd {plan.requirements.name}
{'pip install -r requirements.txt' if 'python' in plan.tech_stack.language.lower() else 'npm install'}
```

### Running Tests

```bash
{'pytest' if 'python' in plan.tech_stack.language.lower() else 'npm test'}
```

### Running Locally

```bash
{'python main.py' if 'python' in plan.tech_stack.language.lower() else 'npm start'}
```

## 📊 Project Stats

- **Estimated Hours:** {plan.estimated_hours}
- **Generated:** {datetime.now().strftime("%Y-%m-%d")}
- **Source Tweet:** {plan.requirements.tweet_source}

## 📝 ADR

See [ADR.md](ADR.md) for architecture decisions.

## 🔒 Security

See [API_SPEC.md](API_SPEC.md) for API documentation.

---
Built with 🤖 Enhanced Build Agent
"""
        return readme


    # ═══════════════════════════════════════════════════════════════
    # MAIN BUILD ORCHESTRATION
    # ═══════════════════════════════════════════════════════════════
    
    async def build_project(self, tweet_text: str, username: str) -> Dict[str, Any]:
        """
        Execute full 6-stage build pipeline.
        
        Returns build result with repo URL or error.
        """
        logger.info(f"🏗️ Starting full build pipeline for @{username}")
        logger.info(f"Tweet: {tweet_text[:100]}...")
        
        build_log = []
        
        # Stage 1: ANALYZE
        logger.info("\n" + "="*60)
        logger.info("STAGE 1/6: ANALYZE")
        logger.info("="*60)
        requirements = await self.analyze_tweet(tweet_text, username)
        if not requirements:
            return {"success": False, "error": "Could not extract buildable requirements from tweet"}
        build_log.append(f"✅ Analyzed: {requirements.name}")
        
        # Stage 2: PLAN
        logger.info("\n" + "="*60)
        logger.info("STAGE 2/6: PLAN")
        logger.info("="*60)
        plan = await self.create_architecture_plan(requirements)
        build_log.append(f"✅ Planned: {plan.tech_stack.language} + {plan.tech_stack.framework}")
        
        # Stage 3: DESIGN
        logger.info("\n" + "="*60)
        logger.info("STAGE 3/6: DESIGN")
        logger.info("="*60)
        docs = await self.create_design_docs(plan)
        build_log.append(f"✅ Designed: {len(docs)} documentation files")
        
        # Stage 4: IMPLEMENT
        logger.info("\n" + "="*60)
        logger.info("STAGE 4/6: IMPLEMENT")
        logger.info("="*60)
        all_files = []
        for component in plan.components[:3]:  # Limit to 3 components for speed
            files = await self.generate_code(plan, component)
            all_files.extend(files)
        build_log.append(f"✅ Implemented: {len(all_files)} files with tests")
        
        # Stage 5: REVIEW
        logger.info("\n" + "="*60)
        logger.info("STAGE 5/6: REVIEW")
        logger.info("="*60)
        review = await self.review_code(all_files, plan)
        build_log.append(f"✅ Reviewed: Score {review.score}/10, Passed: {review.passed}")
        
        # Stage 6: DEPLOY
        logger.info("\n" + "="*60)
        logger.info("STAGE 6/6: DEPLOY")
        logger.info("="*60)
        cicd_files = await self.generate_cicd_files(plan)
        ai_sdk_files = await self.generate_ai_sdk_files(plan)
        build_log.append(f"✅ Deploy config: {len(cicd_files) + len(ai_sdk_files)} CI/CD files")
        
        # Create local project structure
        project_path = await self._create_local_project(
            plan, all_files, docs, cicd_files, ai_sdk_files
        )
        
        logger.info("\n" + "="*60)
        logger.info("BUILD COMPLETE!")
        logger.info("="*60)
        
        return {
            "success": True,
            "project_name": requirements.name,
            "project_path": project_path,
            "tech_stack": {
                "language": plan.tech_stack.language,
                "framework": plan.tech_stack.framework,
                "deployment": plan.tech_stack.deployment
            },
            "stats": {
                "files_generated": len(all_files),
                "tests_generated": sum(1 for f in all_files if f.tests),
                "docs_generated": len(docs),
                "review_score": review.score,
                "estimated_hours": plan.estimated_hours
            },
            "build_log": build_log,
            "next_steps": [
                f"cd {project_path}",
                "git init && git add .",
                "git commit -m 'Initial commit'",
                f"gh repo create {requirements.name} --public --source=. --push" if self.github_token else "Create GitHub repo manually",
                "Deploy to " + plan.tech_stack.deployment
            ]
        }
    
    async def _create_local_project(
        self,
        plan: ProjectPlan,
        code_files: List[CodeFile],
        docs: Dict[str, str],
        cicd_files: Dict[str, str],
        ai_sdk_files: Dict[str, str]
    ) -> str:
        """Create local project directory with all files."""
        import os
        
        project_path = os.path.join(self.projects_dir, plan.requirements.name)
        os.makedirs(project_path, exist_ok=True)
        
        # Write code files
        for file in code_files:
            file_path = os.path.join(project_path, file.path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(file.content)
            # Write tests if present
            if file.tests:
                test_path = os.path.join(project_path, "tests", f"test_{os.path.basename(file.path)}")
                os.makedirs(os.path.dirname(test_path), exist_ok=True)
                with open(test_path, 'w') as f:
                    f.write(file.tests)
        
        # Write docs
        for name, content in docs.items():
            with open(os.path.join(project_path, name), 'w') as f:
                f.write(content)
        
        # Write CI/CD files
        for name, content in cicd_files.items():
            file_path = os.path.join(project_path, name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
        
        # Write AI SDK files (Vercel projects)
        for name, content in ai_sdk_files.items():
            file_path = os.path.join(project_path, name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
        
        logger.info(f"📁 Project created at: {project_path}")
        return project_path


# Singleton
enhanced_build_agent = EnhancedBuildAgent()

#!/usr/bin/env python3
"""Enhanced Build Agent with industry best practices and skills.

Pipeline stages:
1. ANALYZE - Extract requirements from tweet
2. PLAN - Architecture & tech stack selection  
3. DESIGN - API design, data models, UI mockups
4. IMPLEMENT - Code generation with tests
5. REVIEW - Code review & security check
6. DEPLOY - CI/CD setup & deployment
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
        Use Requirements Engineering skills to extract structured requirements.
        
        Prompt engineering technique: Chain-of-Thought + Structured Output
        """
        prompt = f"""Analyze this tweet and extract structured project requirements using software engineering best practices.

Tweet from @{username}:
"{tweet_text}"

Extract the following using requirements engineering principles:

1. **Problem Statement**: What problem does this solve?
2. **Target Users**: Who would use this?
3. **Core Features**: What are the must-have features? (3-5 features)
4. **Constraints**: Technical, time, or resource limitations
5. **Success Criteria**: How do we know this works?

Respond in JSON:
{{
    "is_buildable": true/false,
    "project_name": "kebab-case-name",
    "description": "One sentence pitch",
    "problem_statement": "The problem...",
    "target_users": "Who uses this",
    "core_features": ["feature 1", "feature 2", "feature 3"],
    "constraints": ["constraint 1"],
    "success_criteria": ["criteria 1"]
}}

If not buildable: {{"is_buildable": false, "reason": "..."}}"""

        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a senior product manager and requirements engineer. Extract clear, actionable requirements from vague descriptions."},
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
        Use Architecture Design Patterns to create a solid technical plan.
        
        Skills: System design, technology selection, microservices patterns
        """
        prompt = f"""Design a technical architecture for this project:

Project: {requirements.name}
Description: {requirements.description}
Problem: {requirements.problem_statement}
Target Users: {requirements.target_users}
Features: {', '.join(requirements.core_features)}
Constraints: {', '.join(requirements.constraints)}

Design decisions to make:
1. **Tech Stack**: Choose language, framework, database, deployment platform
2. **Architecture Pattern**: Monolith, microservices, serverless, or modular
3. **Components**: Break into logical components/services
4. **Data Model**: Key entities and relationships
5. **API Design**: Main endpoints needed

Use these principles:
- Choose proven, well-documented technologies
- Prefer simplicity over complexity
- Consider the constraints
- Design for the features needed, not hypothetical future needs

Respond in JSON:
{{
    "tech_stack": {{
        "language": "...",
        "framework": "...",
        "database": "... or null",
        "frontend": "... or null",
        "deployment": "...",
        "testing": "...",
        "ci_cd": "GitHub Actions",
        "reasoning": "Why these choices..."
    }},
    "architecture_pattern": "monolith/microservices/serverless",
    "components": [
        {{
            "name": "...",
            "type": "api/database/frontend/worker",
            "description": "...",
            "responsibilities": ["..."],
            "dependencies": ["..."],
            "files": ["..."]
        }}
    ],
    "api_endpoints": [
        {{"method": "GET", "path": "/...", "description": "..."}}
    ],
    "data_models": [
        {{"name": "...", "fields": ["..."], "relationships": ["..."]}}
    ],
    "file_structure": {{
        "root": ["file1", "file2"],
        "src/": ["..."]
    }},
    "estimated_hours": 5,
    "risks": ["risk 1", "risk 2"]
}}"""

        response = await self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a staff software architect with 15 years experience. Design pragmatic, scalable architectures. Prefer boring technology that works."},
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
    
    # ═══════════════════════════════════════════════════════════════
    # STAGE 3: DESIGN - Detailed Design Documents
    # ═══════════════════════════════════════════════════════════════
    
    async def create_design_docs(self, plan: ProjectPlan) -> Dict[str, str]:
        """
        Create detailed design documents.
        
        Skills: Technical specification writing, API documentation
        """
        docs = {}
        
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
        Generate code using TDD principles.
        
        Skills: TDD, clean code, SOLID principles, design patterns
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
        """Generate tests first (TDD approach)."""
        prompt = f"""Write comprehensive unit tests for {file_path}.

Component: {component.name}
Type: {component.type}
Description: {component.description}
Responsibilities: {', '.join(component.responsibilities)}
Tech Stack: {plan.tech_stack.language}, {plan.tech_stack.testing}

Write tests that:
1. Test happy path
2. Test edge cases
3. Test error handling
4. Use mocking for dependencies

Only output the test code."""

        response = await self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are a TDD expert writing {plan.tech_stack.testing} tests. Write thorough, realistic tests."},
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
        Perform code review using best practices.
        
        Skills: Code review, security scanning, performance analysis
        """
        all_code = "\n\n".join([f"=== {f.path} ===\n{f.content}" for f in files])
        
        prompt = f"""Perform a thorough code review of this codebase.

Tech Stack: {plan.tech_stack.language}, {plan.tech_stack.framework}

Code to review:
{all_code}

Review checklist:
1. **Code Quality**: Readability, naming, structure
2. **Security**: SQL injection, XSS, secrets handling, input validation
3. **Error Handling**: Try/catch, error messages, recovery
4. **Performance**: Efficiency, unnecessary operations
5. **Best Practices**: Following language/framework conventions
6. **Testing**: Test coverage, edge cases

Respond in JSON:
{{
    "score": 8,
    "passed": true,
    "issues": [
        {{
            "severity": "high/medium/low",
            "file": "...",
            "line": "...",
            "issue": "...",
            "fix": "..."
        }}
    ],
    "suggestions": ["suggestion 1", "suggestion 2"],
    "security_concerns": ["concern 1"]
}}"""

        response = await self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a staff engineer performing code review. Be thorough but constructive. Focus on real issues, not nitpicks."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        content = self._extract_json(content)
        data = json.loads(content)
        
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
    
    async def generate_cicd_files(self, plan: ProjectPlan) -> Dict[str, str]:
        """
        Generate CI/CD configuration.
        
        Skills: DevOps, GitHub Actions, Docker, deployment automation
        """
        files = {}
        
        # GitHub Actions workflow
        workflow = f"""name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up {plan.tech_stack.language}
      uses: actions/setup-{plan.tech_stack.language}@v3
      with:
        {'python-version' if 'python' in plan.tech_stack.language.lower() else 'node-version'}: '{'3.11' if 'python' in plan.tech_stack.language.lower() else '18'}'
    
    - name: Install dependencies
      run: {'pip install -r requirements.txt' if 'python' in plan.tech_stack.language.lower() else 'npm install'}
    
    - name: Run tests
      run: {'pytest --cov' if 'python' in plan.tech_stack.language.lower() else 'npm test'}
    
    - name: Run linter
      run: {'flake8' if 'python' in plan.tech_stack.language.lower() else 'eslint .'}
    
    - name: Security scan
      run: {'bandit -r .' if 'python' in plan.tech_stack.language.lower() else 'npm audit'}

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to {plan.tech_stack.deployment}
      run: echo "Deploying..."
"""
        files[".github/workflows/ci.yml"] = workflow
        
        # Dockerfile
        if "docker" in plan.tech_stack.deployment.lower():
            dockerfile = f"""FROM {'python:3.11-slim' if 'python' in plan.tech_stack.language.lower() else 'node:18-alpine'}

WORKDIR /app

COPY requirements.txt .
RUN {'pip install -r requirements.txt' if 'python' in plan.tech_stack.language.lower() else 'npm install'}

COPY . .

EXPOSE 8000

CMD {'["python", "main.py"]' if 'python' in plan.tech_stack.language.lower() else '["npm", "start"]'}
"""
            files["Dockerfile"] = dockerfile
        
        # README with setup instructions
        readme = await self._generate_readme(plan)
        files["README.md"] = readme
        
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


# Singleton
enhanced_build_agent = EnhancedBuildAgent()

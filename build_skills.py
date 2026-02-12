#!/usr/bin/env python3
"""Industry-standard skills for the build pipeline.

Each skill is based on famous GitHub repos with 1000+ stars.
These define best practices for software engineering.
"""

from typing import Dict, List


class RequirementsEngineeringSkill:
    """
    Based on:
    - Basecamp's "Shape Up" (basecamp/shape_up)
    - Thoughtbot's Playbook
    - Joel on Software principles
    """
    
    SHAPE_UP_PRINCIPLES = """
    Shape Up Principles (from Basecamp):
    1. APPETITE: How much time are we willing to spend? (2 weeks? 6 weeks?)
    2. BOUNDARIES: What's explicitly OUT of scope?
    3. RABBIT HOLES: What problems might trap us?
    4. NO COMMITMENTS: Define the problem, not the solution
    
    Key Questions:
    - What is the PROBLEM we're solving?
    - Who are the USERS?
    - What does SUCCESS look like?
    - What are CONSTRAINTS (time, tech, budget)?
    """
    
    @staticmethod
    def extract_requirements_prompt(tweet: str, username: str) -> str:
        return f"""Using Shape Up methodology, analyze this tweet:

Tweet from @{username}:
"{tweet}"

Apply these principles:
{RequirementsEngineeringSkill.SHAPE_UP_PRINCIPLES}

Extract:
1. PROBLEM STATEMENT (1 sentence)
2. APPETITE (estimated time: 2weeks/1month/unknown)
3. TARGET USERS (who benefits?)
4. CORE FEATURES (3-5 must-haves)
5. BOUNDARIES (what's NOT included?)
6. CONSTRAINTS (technical limitations)
7. SUCCESS CRITERIA (how do we know it works?)

Response format: JSON with these fields."""


class SystemArchitectureSkill:
    """
    Based on:
    - donnemartin/system-design-primer (270k stars)
    - binhnguyennus/awesome-scalability (60k stars)
    - Clean Architecture by Uncle Bob
    """
    
    SCALABILITY_PATTERNS = """
    From System Design Primer:
    
    Architecture Patterns:
    - Monolith: Simple, single deploy, good for MVPs
    - Microservices: Distributed, scalable, complex
    - Serverless: Event-driven, pay-per-use, good for sporadic workloads
    - Modular Monolith: Middle ground - monolith with clear boundaries
    
    Tech Stack Selection (from Awesome Scalability):
    - Language: Choose based on ecosystem, not hype
    - Database: Match data model (SQL for relational, NoSQL for flexible)
    - Caching: Redis for hot data
    - Queue: RabbitMQ/Redis for background jobs
    - CDN: CloudFlare for static assets
    
    Decision Factors:
    - Team expertise
    - Time to market
    - Expected scale
    - Maintenance burden
    """
    
    @staticmethod
    def design_architecture_prompt(requirements: dict) -> str:
        return f"""Design architecture using System Design Primer patterns:

Project: {requirements.get('name')}
Appetite: {requirements.get('appetite')}
Features: {requirements.get('features')}

Apply these principles:
{SystemArchitectureSkill.SCALABILITY_PATTERNS}

Design:
1. ARCHITECTURE PATTERN (monolith/microservices/serverless/modular)
   - Why this pattern fits the appetite?
   
2. TECH STACK
   - Language: (Python/TypeScript/Go/Rust)
   - Framework: (FastAPI/Express/Django)
   - Database: (PostgreSQL/MongoDB/None)
   - Why these choices?
   
3. COMPONENT BREAKDOWN
   - What are the logical components?
   - How do they communicate?
   
4. DATA FLOW
   - How does data move through the system?
   
5. SCALABILITY CONSIDERATIONS
   - What if this grows 10x?
"""


class TechnicalWritingSkill:
    """
    Based on:
    - Google Technical Writing Course
    - Write the Docs community
    - Docs Like Code methodology
    """
    
    GOOGLE_WRITING_PRINCIPLES = """
    From Google's Technical Writing Course:
    
    1. AUDIENCE: Who is reading this?
       - Developers (API docs)
       - End users (README)
       - Operators (deployment guides)
    
    2. CLARITY: One idea per sentence
       - Use active voice
       - Remove unnecessary words
       - Use lists for complex info
    
    3. STRUCTURE:
       - Title: What is this?
       - Overview: Why should I care?
       - Quickstart: How do I try it?
       - Details: How does it work?
       - Reference: What are all the options?
    
    4. CODE EXAMPLES:
       - Always include working examples
       - Show expected output
       - Include error handling
    """
    
    DOCUMENTATION_TYPES = {
        "README": {
            "sections": ["Title", "Overview", "Installation", "Usage", "Contributing"],
            "audience": "end_users"
        },
        "API_SPEC": {
            "sections": ["Base URL", "Authentication", "Endpoints", "Error Codes"],
            "audience": "developers",
            "format": "OpenAPI/Swagger"
        },
        "ADR": {
            "sections": ["Context", "Decision", "Consequences", "Alternatives"],
            "audience": "maintainers"
        }
    }


class TDDSkill:
    """
    Based on:
    - Kent Beck's TDD by Example
    - Awesome Testing collection
    - Jest/Pytest best practices
    """
    
    TDD_CYCLE = """
    Test-Driven Development Cycle:
    
    1. RED: Write a failing test
       - Start with the simplest case
       - Test one thing at a time
       - Name tests descriptively: test_should_do_something()
    
    2. GREEN: Write minimal code to pass
       - Don't over-engineer
       - Hardcode if needed (refactor later)
       - Just make the test green
    
    3. REFACTOR: Clean up
       - Remove duplication
       - Improve names
       - Keep tests green
    
    Testing Pyramid:
    - Unit tests: 70% (fast, isolated)
    - Integration tests: 20% (component interaction)
    - E2E tests: 10% (full flow)
    """
    
    BEST_PRACTICES = """
    From Awesome Testing & Jest/Pytest:
    
    GOOD TESTS:
    - Fast (< 100ms each)
    - Independent (no shared state)
    - Repeatable (same result every time)
    - Self-validating (pass/fail clear)
    - Timely (written with code)
    
    TEST STRUCTURE (AAA):
    - Arrange: Set up test data
    - Act: Call the function
    - Assert: Verify the result
    
    MOCKING:
    - Mock external dependencies (APIs, DB)
    - Don't mock what you don't own
    - Use dependency injection
    """


class CodeReviewSkill:
    """
    Based on:
    - Google Engineering Practices (40k stars)
    - Awesome Code Review (5k stars)
    - OWASP Secure Code Review
    """
    
    GOOGLE_REVIEW_CHECKLIST = """
    From Google's Engineering Practices:
    
    DESIGN:
    - Does this change belong in the codebase?
    - Is it well-integrated with existing code?
    - Is it the right level of abstraction?
    
    FUNCTIONALITY:
    - Does it do what the developer intended?
    - Does it handle edge cases?
    - Are there potential bugs?
    
    COMPLEXITY:
    - Can this code be simplified?
    - Will it be hard to maintain?
    - Are there unnecessary abstractions?
    
    TESTS:
    - Are there unit tests?
    - Do tests cover edge cases?
    - Are tests readable?
    
    NAMING:
    - Are names descriptive?
    - Do they follow conventions?
    
    COMMENTS:
    - Are comments necessary?
    - Do they explain WHY not WHAT?
    """
    
    SECURITY_CHECKLIST = """
    From OWASP Secure Code Review:
    
    INJECTION:
    - SQL injection vulnerabilities
    - Command injection
    - NoSQL injection
    
    AUTHENTICATION:
    - Hardcoded credentials
    - Weak password policies
    - Session management
    
    DATA:
    - Sensitive data exposure
    - Encryption in transit
    - Encryption at rest
    
    INPUT:
    - Input validation
    - Output encoding
    - File upload validation
    
    DEPENDENCIES:
    - Known vulnerabilities (CVEs)
    - Outdated packages
    - License compliance
    """
    
    @staticmethod
    def review_prompt(code: str, language: str) -> str:
        return f"""Review this {language} code using Google and OWASP standards:

{CodeReviewSkill.GOOGLE_REVIEW_CHECKLIST}

{CodeReviewSkill.SECURITY_CHECKLIST}

Code to review:
```
{code}
```

Provide:
1. OVERALL SCORE (1-10)
2. CRITICAL ISSUES (must fix)
3. WARNINGS (should fix)
4. SUGGESTIONS (nice to have)
5. SECURITY CONCERNS
6. SHOULD PASS REVIEW? (yes/no with reasoning)
"""


class DevOpsSkill:
    """
    Based on:
    - Awesome DevOps (10k stars)
    - GitHub Actions Awesome (30k stars)
    - Docker Best Practices (30k stars)
    """
    
    GITHUB_ACTIONS_PATTERNS = """
    From Awesome GitHub Actions:
    
    CI PIPELINE:
    1. Checkout code
    2. Setup environment (language version)
    3. Install dependencies
    4. Lint (code style check)
    5. Test (unit + integration)
    6. Security scan
    7. Build artifact
    8. Deploy (if on main branch)
    
    BEST PRACTICES:
    - Use matrix builds for multiple versions
    - Cache dependencies for speed
    - Run security scans on every PR
    - Use secrets for API keys
    - Pin action versions (@v3, not @main)
    """
    
    DOCKER_BEST_PRACTICES = """
    From Docker Awesome:
    
    DOCKERFILE:
    - Use specific base images (python:3.11-slim, not python:latest)
    - Minimize layers (combine RUN commands)
    - Use .dockerignore
    - Don't run as root
    - Use multi-stage builds for smaller images
    
    SECURITY:
    - Scan images for vulnerabilities (Trivy, Snyk)
    - Don't embed secrets
    - Use read-only filesystems where possible
    """
    
    DEPLOYMENT_PATTERNS = {
        "render": {
            "platform": "PaaS",
            "best_for": "Simple apps, quick deploy",
            "needs": "render.yaml or Dockerfile"
        },
        "vercel": {
            "platform": "Serverless",
            "best_for": "Frontend, Next.js",
            "needs": "vercel.json"
        },
        "fly.io": {
            "platform": "Edge deployment",
            "best_for": "Global apps",
            "needs": "fly.toml"
        },
        "aws": {
            "platform": "IaaS",
            "best_for": "Enterprise scale",
            "needs": "Terraform/CloudFormation"
        }
    }
    
    @staticmethod
    def generate_cicd_prompt(tech_stack: dict, deployment: str) -> str:
        return f"""Generate CI/CD pipeline using GitHub Actions best practices:

Tech Stack: {tech_stack}
Deployment Target: {deployment}

Apply these patterns:
{DevOpsSkill.GITHUB_ACTIONS_PATTERNS}

Generate:
1. .github/workflows/ci.yml (test, lint, security scan)
2. Dockerfile (if containerized)
3. Deployment config for {deployment}
4. README section on deployment

Include:
- Matrix testing (Python 3.10, 3.11 or Node 18, 20)
- Caching for dependencies
- Security scanning (bandit/npm audit)
- Auto-deploy on main branch
"""


# Skill Registry - for easy access
SKILLS = {
    "requirements": RequirementsEngineeringSkill,
    "architecture": SystemArchitectureSkill,
    "technical_writing": TechnicalWritingSkill,
    "tdd": TDDSkill,
    "code_review": CodeReviewSkill,
    "devops": DevOpsSkill,
}


def get_skill(skill_name: str):
    """Get a skill by name."""
    return SKILLS.get(skill_name)

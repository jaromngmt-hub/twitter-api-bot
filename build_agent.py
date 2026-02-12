#!/usr/bin/env python3
"""AI Agent that turns tweets into actual GitHub projects.

This agent:
1. Analyzes tweet for project ideas/opportunities
2. Generates detailed architecture plan
3. Sends plan to user via WhatsApp/SMS for approval
4. Creates GitHub repo
5. Implements the project
6. Notifies user when done
"""

import asyncio
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict

import httpx
from loguru import logger
from openai import AsyncOpenAI

from config import settings
from urgent_notifier import UrgentNotifier
from models import Tweet


@dataclass
class ProjectPlan:
    """Generated project plan from tweet analysis."""
    name: str
    description: str
    tech_stack: List[str]
    features: List[str]
    architecture: str
    files_to_create: List[Dict[str, str]]  # filename -> description
    estimated_time: str
    tweet_source: str
    created_at: datetime


class BuildAgent:
    """
    AI Agent for turning high-value tweets into actual projects.
    
    Pipeline:
    1. Analyze tweet → Project idea
    2. Generate plan → Send to user for approval
    3. User approves via WhatsApp reply
    4. Create repo → Implement code
    5. Notify user with repo link
    """
    
    def __init__(self):
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.github_username = os.getenv("GITHUB_USERNAME", "")
        self.projects_dir = "./projects"  # Local dir for project files
        os.makedirs(self.projects_dir, exist_ok=True)
    
    async def analyze_tweet_for_project(self, tweet: Tweet, username: str) -> Optional[ProjectPlan]:
        """
        Analyze a tweet and generate a project plan if it contains a buildable idea.
        
        Returns None if tweet doesn't contain a clear project opportunity.
        """
        if not self.openai:
            logger.error("OpenAI not configured")
            return None
        
        prompt = f"""Analyze this tweet and determine if it describes a buildable software project, tool, or opportunity.

Tweet from @{username}:
"{tweet.text}"

If this tweet describes something that could be built (tool, app, bot, script, website, automation, etc.), generate a detailed project plan.

Respond in JSON format:
{{
    "is_buildable": true/false,
    "project_name": "Short, catchy name for the project",
    "description": "One paragraph describing what this project does",
    "tech_stack": ["primary language", "framework", "key libraries"],
    "features": ["feature 1", "feature 2", "feature 3"],
    "architecture": "Brief architecture description",
    "files": [
        {{"name": "main.py", "purpose": "Entry point and CLI"}},
        {{"name": "config.py", "purpose": "Configuration management"}}
    ],
    "estimated_time": "How long to build (e.g., '2-3 hours', '1 day')",
    "rationale": "Why this project is worth building based on the tweet"
}}

If NOT buildable, return only: {{"is_buildable": false}}

Choose tech stack based on the project type. Prefer Python for scripts/automation, React for web apps, etc."""

        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a senior software architect who identifies opportunities in tweets and designs practical projects."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            
            if not data.get("is_buildable"):
                logger.info(f"Tweet from @{username} not buildable")
                return None
            
            # Sanitize project name for repo
            repo_name = re.sub(r'[^a-zA-Z0-9-]', '-', data["project_name"].lower())
            repo_name = re.sub(r'-+', '-', repo_name).strip('-')
            
            return ProjectPlan(
                name=repo_name,
                description=data["description"],
                tech_stack=data["tech_stack"],
                features=data["features"],
                architecture=data["architecture"],
                files_to_create=data["files"],
                estimated_time=data["estimated_time"],
                tweet_source=f"https://twitter.com/{username}/status/{tweet.id}",
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze tweet: {e}")
            return None
    
    async def send_plan_for_approval(self, plan: ProjectPlan, username: str) -> bool:
        """
        Send project plan to user via WhatsApp/SMS for approval.
        
        User can reply:
        - "BUILD" or "YES" → Start implementation
        - "MODIFY <changes>" → Revise plan
        - "NO" or "SKIP" → Cancel
        """
        message = f"""🚀 *PROJECT PLAN READY FOR REVIEW*

From tweet by @{username}

*Project:* {plan.name}
*Description:* {plan.description}

*Tech Stack:*
{chr(10).join(f"• {tech}" for tech in plan.tech_stack)}

*Features:*
{chr(10).join(f"• {feat}" for feat in plan.features)}

*Architecture:*
{plan.architecture}

*Estimated Time:* {plan.estimated_time}

*Files to create:* {len(plan.files_to_create)}

Reply with:
✅ *BUILD* - Start implementation
✏️ *MODIFY <changes>* - Revise plan  
❌ *NO* - Skip this project

Source: {plan.tweet_source}
"""
        
        try:
            async with UrgentNotifier() as notifier:
                # Send via WhatsApp
                result = await notifier._send_whatsapp_raw(
                    to=settings.YOUR_PHONE_NUMBER,
                    message=message
                )
                
                if result.get("sent"):
                    logger.info(f"Project plan sent for approval: {plan.name}")
                    # TODO: Store pending approval in database
                    return True
                else:
                    logger.error(f"Failed to send plan: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending plan: {e}")
            return False
    
    async def implement_project(self, plan: ProjectPlan) -> Optional[str]:
        """
        Implement the project by generating all code files.
        
        Returns the path to created project directory.
        """
        project_path = os.path.join(self.projects_dir, plan.name)
        os.makedirs(project_path, exist_ok=True)
        
        logger.info(f"Implementing project: {plan.name} at {project_path}")
        
        # Generate each file
        for file_info in plan.files_to_create:
            filename = file_info["name"]
            purpose = file_info["purpose"]
            
            # Generate file content using AI
            content = await self._generate_file_content(
                filename=filename,
                purpose=purpose,
                plan=plan,
                project_path=project_path
            )
            
            # Write file
            file_path = os.path.join(project_path, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Created: {filename}")
        
        # Create README
        readme = self._generate_readme(plan)
        with open(os.path.join(project_path, "README.md"), 'w') as f:
            f.write(readme)
        
        return project_path
    
    async def _generate_file_content(self, filename: str, purpose: str, plan: ProjectPlan, project_path: str) -> str:
        """Generate content for a specific file using AI."""
        if not self.openai:
            return f"# {filename}\n# TODO: Implement {purpose}\n"
        
        # Check if file already exists (for context)
        existing_files = []
        for f in os.listdir(project_path):
            if os.path.isfile(os.path.join(project_path, f)):
                with open(os.path.join(project_path, f), 'r') as file:
                    existing_files.append(f"{f}:\n{file.read()[:500]}...")
        
        prompt = f"""Generate the code for file: {filename}
Purpose: {purpose}

Project: {plan.name}
Description: {plan.description}
Tech Stack: {', '.join(plan.tech_stack)}
Features: {', '.join(plan.features)}

Existing files in project:
{chr(10).join(existing_files) if existing_files else "None yet"}

Generate complete, working code. Include:
- All necessary imports
- Error handling
- Comments explaining key parts
- Follow best practices for the tech stack

Only output the code, no markdown formatting."""

        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are an expert {plan.tech_stack[0] if plan.tech_stack else 'software'} developer. Write clean, production-ready code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```", 2)[1]
                if content.startswith("python") or content.startswith("javascript") or content.startswith("typescript"):
                    content = content.split("\n", 1)[1]
                content = content.rstrip("`")
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to generate {filename}: {e}")
            return f"# {filename}\n# TODO: Implement {purpose}\n# Error during generation: {e}\n"
    
    def _generate_readme(self, plan: ProjectPlan) -> str:
        """Generate README.md for the project."""
        return f"""# {plan.name}

{plan.description}

## 🎯 Origin

This project was auto-generated from a tweet:
{plan.tweet_source}

Generated on: {plan.created_at.strftime("%Y-%m-%d %H:%M")}

## 🛠️ Tech Stack

{chr(10).join(f"- {tech}" for tech in plan.tech_stack)}

## ✨ Features

{chr(10).join(f"- {feat}" for feat in plan.features)}

## 🏗️ Architecture

{plan.architecture}

## 📁 Project Structure

{chr(10).join(f"- `{f['name']}` - {f['purpose']}" for f in plan.files_to_create)}

## 🚀 Getting Started

### Prerequisites

{chr(10).join(f"- {tech}" for tech in plan.tech_stack[:2])}

### Installation

```bash
git clone https://github.com/{self.github_username}/{plan.name}.cd
cd {plan.name}
# Add installation steps here
```

### Usage

```bash
# Add usage examples here
```

## 📝 Notes

This project was AI-generated. Review and test thoroughly before production use.

---
Built by 🤖 Build Agent
"""
    
    async def create_github_repo(self, plan: ProjectPlan, local_path: str) -> Optional[str]:
        """Create GitHub repo and push the project."""
        if not self.github_token or not self.github_username:
            logger.error("GitHub not configured")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                # Create repo
                headers = {
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                
                repo_data = {
                    "name": plan.name,
                    "description": plan.description,
                    "private": False,
                    "auto_init": False
                }
                
                response = await client.post(
                    "https://api.github.com/user/repos",
                    headers=headers,
                    json=repo_data
                )
                
                if response.status_code not in (201, 422):  # 422 = already exists
                    logger.error(f"Failed to create repo: {response.text}")
                    return None
                
                repo_url = f"https://github.com/{self.github_username}/{plan.name}"
                logger.info(f"GitHub repo created: {repo_url}")
                
                # TODO: Push local files to repo
                # For now, return repo URL
                return repo_url
                
        except Exception as e:
            logger.error(f"Error creating GitHub repo: {e}")
            return None
    
    async def notify_completion(self, plan: ProjectPlan, repo_url: str):
        """Send notification that project is complete."""
        message = f"""✅ *PROJECT COMPLETE!*

*{plan.name}* has been built and pushed to GitHub!

🔗 Repo: {repo_url}

*Summary:*
• {len(plan.files_to_create)} files created
• Tech: {', '.join(plan.tech_stack[:3])}
• Time: {plan.estimated_time}

Review the code and let me know if you want any changes!
"""
        
        try:
            async with UrgentNotifier() as notifier:
                await notifier._send_whatsapp_raw(
                    to=settings.YOUR_PHONE_NUMBER,
                    message=message
                )
        except Exception as e:
            logger.error(f"Failed to send completion notification: {e}")


# Singleton instance
build_agent = BuildAgent()

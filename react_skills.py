#!/usr/bin/env python3
"""React & Next.js Best Practices from Vercel and the React community.

Sources:
- Vercel React Best Practices
- React Server Components (RSC) patterns
- Next.js 14 App Router patterns
- Epic React (Kent C. Dodds)
"""

from typing import Dict, List, Optional


class VercelReactSkill:
    """
    React best practices from Vercel and React core team.
    """
    
    REACT_BEST_PRACTICES = """
    React Best Practices (Vercel & Core Team):
    
    1. SERVER COMPONENTS BY DEFAULT
       - Use Server Components for data fetching
       - Zero client-side JavaScript for static content
       - Direct backend access (no API layer needed)
       - Can be async!
       
    2. CLIENT COMPONENTS ONLY WHEN NEEDED
       - 'use client' directive at top
       - Use for: interactivity, browser APIs, React hooks
       - Keep as small as possible
       - Compose with Server Components
       
    3. COMPOSITION PATTERN
       - Pass Server Components as children to Client Components
       - Best of both worlds: interactivity + zero JS
       
    4. DATA FETCHING PATTERNS
       - Fetch in Server Components
       - Use React's cache() for deduplication
       - Parallel fetching with Promise.all
       - Loading UI with React Suspense
       
    5. STREAMING & SUSPENSE
       - Wrap slow components in <Suspense>
       - Show loading states immediately
       - Progressive enhancement
       
    6. ERROR HANDLING
       - error.tsx for error boundaries
       - not-found.tsx for 404s
       - Graceful degradation
       
    7. FORMS & MUTATIONS
       - Server Actions for form submissions
       - Progressive enhancement (works without JS)
       - Automatic revalidation
       
    8. CACHING STRATEGIES
       - fetch with revalidate
       - Route Segment Config
       - Dynamic vs Static
    """
    
    COMPONENT_PATTERNS = {
        "server_component": {
            "use_for": [
                "Data fetching",
                "Backend resource access",
                "Static content",
                "SEO-critical content"
            ],
            "benefits": [
                "Zero client JS",
                "Direct backend access",
                "Can be async",
                "Better SEO"
            ]
        },
        
        "client_component": {
            "use_for": [
                "Interactivity",
                "Browser APIs",
                "React hooks (useState, useEffect)",
                "Event handlers"
            ],
            "best_practices": [
                "Keep small and focused",
                "Compose with Server Components",
                "Use 'use client' at top",
                "Avoid unnecessary client components"
            ]
        },
        
        "composition_pattern": {
            "description": "Pass Server Components as children to Client Components",
            "benefits": [
                "Interactive wrapper around static content",
                "Minimal client JS",
                "Best performance"
            ]
        },
        
        "loading_ui": {
            "pattern": "Use loading.tsx for instant loading states"
        },
        
        "error_handling": {
            "pattern": "Use error.tsx for error boundaries"
        }
    }
    
    FILE_ORGANIZATION = """
    Next.js 14 App Router File Organization:
    
    app/
    ├── layout.tsx              # Root layout (Server Component)
    ├── page.tsx                # Home page
    ├── loading.tsx             # Loading UI
    ├── error.tsx               # Error boundary
    ├── not-found.tsx           # 404 page
    ├── globals.css             # Global styles
    ├── (marketing)/            # Route groups
    │   ├── layout.tsx
    │   ├── page.tsx
    │   └── about/
    ├── dashboard/              # /dashboard
    │   ├── layout.tsx
    │   ├── page.tsx
    │   ├── loading.tsx
    │   └── settings/
    └── api/                    # API routes
        └── route.ts
    
    components/
    ├── ui/                     # shadcn/ui components
    ├── layout/                 # Layout components
    ├── providers/              # Context providers
    └── features/               # Feature components
    
    lib/
    ├── utils.ts                # Utilities
    ├── db.ts                   # Database
    └── api.ts                  # API helpers
    
    hooks/                      # Custom hooks
    types/                      # TypeScript types
    """
    
    PERFORMANCE_PATTERNS = """
    Performance Best Practices:
    
    1. IMAGE OPTIMIZATION
       - Use next/image
       - Automatic WebP conversion
       - Responsive images
       - Lazy loading
       
    2. FONT OPTIMIZATION
       - Use next/font
       - Automatic self-hosting
       - Zero layout shift
       
    3. SCRIPT OPTIMIZATION
       - Use next/script
       - Control loading priority
       
    4. DYNAMIC IMPORTS
       - Lazy load heavy components
       - Reduce initial bundle size
       
    5. ROUTE PREFETCHING
       - Automatic on hover
       - Instant navigation
    """
    
    @staticmethod
    def should_use_app_router(project_type: str, features: List[str]) -> bool:
        """Determine if App Router is appropriate."""
        modern_features = [
            'react', 'next', 'modern', 'app', 'dashboard',
            'streaming', 'server', 'rsc'
        ]
        
        text = ' '.join(features + [project_type]).lower()
        return any(f in text for f in modern_features)
    
    @staticmethod
    def generate_component_prompt(component_type: str, description: str, is_server: bool = True) -> str:
        """Generate prompt for React component with best practices."""
        
        return f"""Create a React component using Vercel/Next.js best practices.

Component Type: {component_type}
Description: {description}
Component Mode: {'Server Component' if is_server else 'Client Component'}

Apply these principles:
{VercelReactSkill.REACT_BEST_PRACTICES}

Requirements:
- {'No "use client" - Server Component' if is_server else "'use client' at top"}
- TypeScript with proper types
- {'Async/await allowed' if is_server else 'React hooks for state'}
- Composition-friendly
- Error handling
- Accessible

Include:
- Main component
- Props interface
- Usage example
"""


class EpicReactSkill:
    """Patterns from Epic React by Kent C. Dodds."""
    
    TESTING_PATTERNS = """
    Testing Best Practices (Epic React):
    
    1. TESTING PHILOSOPHY
       - Test behavior, not implementation
       - Users don't care about your state
       - Test what the user sees and does
    
    2. REACT TESTING LIBRARY
       - render, screen, fireEvent
       - Prefer user-event over fireEvent
       - Queries: getBy, findBy, queryBy
    
    3. MOCKING
       - Mock at module level
       - Restore mocks between tests
       - Don't mock what you don't own
    
    4. HOOKS TESTING
       - renderHook for custom hooks
       - act for state updates
    """
    
    ADVANCED_PATTERNS = """
    Advanced React Patterns:
    
    1. COMPOUND COMPONENTS
       - Components that work together
       - Shared state via context
       - Flexible composition
    
    2. CONTROLLED PROPS PATTERN
       - Lift state or control internally
       - Inversion of control
    
    3. CUSTOM HOOKS
       - Extract reusable logic
       - Name starts with 'use'
       - Can call other hooks
    """


class TotalTypeScriptSkill:
    """TypeScript best practices from Matt Pocock."""
    
    TYPE_PATTERNS = """
    TypeScript Best Practices:
    
    1. AVOID 'any'
       - Use 'unknown' when type unknown
       - Type assertions as last resort
       - Let inference work
    
    2. GENERIC PATTERNS
       - Function createSet<T>(items: T[])
       - Constraints: T extends Record<string, any>
    
    3. UTILITY TYPES
       - Partial<T>, Required<T>
       - Pick<T, K>, Omit<T, K>
       - ReturnType<T>, Parameters<T>
    
    4. DISCRIMINATED UNIONS
       - Type Action = { type: 'inc' } | { type: 'dec' }
       - Switch on type property
    
    5. TYPE INFERENCE
       - Let TS infer when possible
       - Explicit for API contracts
    """


# Registry
REACT_SKILLS = {
    "vercel_react": VercelReactSkill,
    "epic_react": EpicReactSkill,
    "total_typescript": TotalTypeScriptSkill,
}


def get_react_skill(skill_name: str):
    return REACT_SKILLS.get(skill_name)

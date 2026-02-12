#!/usr/bin/env python3
"""Frontend Design Skills from famous GitHub repos.

Sources:
- shadcn/ui (50k+ stars) - Beautiful component patterns
- Tailwind CSS (80k+ stars) - Utility-first CSS
- Radix UI (12k+ stars) - Accessible primitives
- Storybook (80k+ stars) - Component-driven design
"""

from typing import Dict, List, Optional


class ShadcnUISkill:
    """
    shadcn/ui design patterns for beautiful, accessible components.
    
    Repo: shadcn-ui/ui (50k+ stars)
    Philosophy: Copy-paste, not library. Own your components.
    Stack: React + TypeScript + Tailwind CSS + Radix UI
    """
    
    DESIGN_PRINCIPLES = """
    shadcn/ui Design Philosophy:
    
    1. ACCESSIBILITY FIRST
       - Built on Radix UI primitives (WAI-ARIA compliant)
       - Keyboard navigation support
       - Screen reader optimized
       - Focus management
    
    2. COMPOSITION PATTERN
       - Small, composable components
       - Mix and match primitives
       - Build complex UIs from simple pieces
       
    3. STYLE WITH TAILWIND
       - Utility-first CSS
       - Consistent spacing (4px grid)
       - Color system with CSS variables
       - Dark mode support out-of-box
    
    4. COPY-PASTE PHILOSOPHY
       - Own your code
       - Customize freely
       - No dependency lock-in
       - Full source control
    
    5. THINKING IN COMPONENTS
       - One component = One responsibility
       - Props for configuration
       - Slots for flexibility
       - Variants for styles
    """
    
    COMPONENT_PATTERNS = {
        "button": {
            "variants": ["default", "destructive", "outline", "secondary", "ghost", "link"],
            "sizes": ["default", "sm", "lg", "icon"],
            "composition": "Can contain icons, text, or both"
        },
        "card": {
            "parts": ["Card", "CardHeader", "CardTitle", "CardDescription", "CardContent", "CardFooter"],
            "use_case": "Content containers with clear hierarchy"
        },
        "dialog": {
            "parts": ["Dialog", "DialogTrigger", "DialogContent", "DialogHeader", "DialogTitle", "DialogDescription"],
            "accessibility": "Focus trap, escape to close, click outside"
        },
        "form": {
            "integration": "React Hook Form + Zod",
            "parts": ["Form", "FormField", "FormItem", "FormLabel", "FormControl", "FormMessage"],
            "validation": "Real-time with clear error messages"
        },
        "data_table": {
            "features": ["Sorting", "Filtering", "Pagination", "Row selection"],
            "tanstack": "Uses @tanstack/react-table"
        }
    }
    
    TAILWIND_PATTERNS = """
    Tailwind CSS Patterns (from shadcn/ui):
    
    SPACING:
    - Use 4px grid: p-4 (16px), m-2 (8px), gap-6 (24px)
    - Consistent rhythm throughout
    
    COLORS:
    - Primary: action buttons, links
    - Secondary: less prominent actions
    - Muted: backgrounds, disabled states
    - Accent: highlights, badges
    - Destructive: errors, delete actions
    
    TYPOGRAPHY:
    - text-sm: secondary text, labels
    - text-base: body text
    - text-lg: section headers
    - text-xl: page titles
    - font-medium: emphasis
    - font-semibold: strong emphasis
    
    LAYOUT:
    - flex for 1D layouts
    - grid for 2D layouts
    - container for max-width
    - Stack pattern: flex-col gap-4
    
    INTERACTIVE STATES:
    - hover: mouse over
    - focus: keyboard focused
    - active: being clicked
    - disabled: not interactive
    - data-[state]: Radix UI states
    """
    
    @staticmethod
    def generate_component_prompt(component_type: str, description: str) -> str:
        """Generate prompt for shadcn/ui style component."""
        
        base_prompt = f"""Create a {component_type} component using shadcn/ui patterns:

Requirements: {description}

Apply these principles:
{ShadcnUISkill.DESIGN_PRINCIPLES}

Styling with Tailwind:
{ShadcnUISkill.TAILWIND_PATTERNS}

Requirements:
- TypeScript with proper types
- Accessible (keyboard nav, ARIA labels)
- Responsive design
- Dark mode compatible (use CSS variables)
- Composition-friendly (accept children)
- Variant support (size, style variants)

Include:
- Main component file
- Variants using class-variance-authority (cva)
- Usage examples
- Props documentation
"""
        
        specific_patterns = {
            "button": """
Button-specific:
- Variants: default, outline, ghost, destructive
- Sizes: default, sm, lg, icon
- Can contain icons (left/right)
- Loading state with spinner
- Disabled state styling
""",
            "card": """
Card-specific:
- Parts: Header, Title, Description, Content, Footer
- Shadow on hover (optional)
- Clear visual hierarchy
- Padding consistent with design system
""",
            "input": """
Input-specific:
- Label association
- Error state with red border
- Focus ring (blue)
- Placeholder styling
- Icon support (left/right)
""",
            "dialog": """
Dialog-specific:
- Overlay backdrop
- Centered content
- Close button (X)
- Escape key to close
- Click outside to close
- Focus trap inside
- Animation: fade in, scale up
""",
            "form": """
Form-specific:
- Integration with React Hook Form
- Zod schema validation
- Real-time error display
- Label + Input pairs
- Submit button with loading state
""",
            "dashboard": """
Dashboard-specific:
- Sidebar navigation
- Header with user menu
- Grid layout for widgets
- Responsive (sidebar collapses)
- Cards for data display
- Charts integration ready
""",
            "chat": """
Chat-specific:
- Message bubbles (user vs assistant)
- Input area at bottom
- Scrollable message history
- Typing indicator
- Avatar support
- Timestamp display
"""
        }
        
        return base_prompt + specific_patterns.get(component_type, "")
    
    @staticmethod
    def get_component_template(component: str) -> str:
        """Get shadcn/ui style template for common components."""
        
        templates = {
            "button": '''"use client"

import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
''',
            "card": '''import * as React from "react"
import { cn } from "@/lib/utils"

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-lg border bg-card text-card-foreground shadow-sm",
      className
    )}
    {...props}
  />
))
Card.displayName = "Card"

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-2xl font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
'''
        }
        
        return templates.get(component, "")


class TailwindCSSSkill:
    """
    Tailwind CSS utility-first patterns.
    
    Repo: tailwindlabs/tailwindcss (80k+ stars)
    """
    
    UTILITY_PATTERNS = """
    Tailwind CSS Best Practices:
    
    LAYOUT:
    - flex flex-col gap-4 (stack pattern)
    - grid grid-cols-3 gap-6 (grid pattern)
    - container mx-auto px-4 (centered container)
    - min-h-screen (full height)
    
    SPACING:
    - Use multiples of 4: p-4, m-2, gap-6
    - Consistent vertical rhythm: space-y-4
    - Component padding: p-6 for cards
    
    RESPONSIVE:
    - Mobile-first: sm:, md:, lg:, xl:
    - Example: grid-cols-1 md:grid-cols-2 lg:grid-cols-3
    
    INTERACTIVE:
    - hover:bg-primary/90 (opacity modifier)
    - focus-visible:ring-2 (keyboard focus)
    - active:scale-95 (press effect)
    - disabled:opacity-50
    
    DARK MODE:
    - Use CSS variables: bg-background text-foreground
    - Define in :root and .dark
    """


class StorybookSkill:
    """
    Component-driven development with Storybook.
    
    Repo: storybookjs/storybook (80k+ stars)
    """
    
    STORY_PATTERNS = """
    Storybook Patterns:
    
    1. COMPONENT STORIES
       - Default story (primary use case)
       - Variant stories (all variants)
       - Edge cases (empty, loading, error)
       
    2. ARGS & CONTROLS
       - Make components interactive
       - Test all prop combinations
       - Document prop types
       
    3. DOCUMENTATION
       - MDX for rich docs
       - Usage examples
       - Design tokens
       
    4. TESTING
       - Visual regression testing
       - Interaction testing
       - Accessibility testing
    """


# Skill registry
FRONTEND_SKILLS = {
    "shadcn_ui": ShadcnUISkill,
    "tailwind": TailwindCSSSkill,
    "storybook": StorybookSkill,
}


def get_frontend_skill(skill_name: str):
    """Get a frontend design skill."""
    return FRONTEND_SKILLS.get(skill_name)

"""
Robust component parsing utilities to handle AI model output variations.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from loguru import logger


@dataclass 
class Component:
    """System component definition with validation."""
    name: str
    type: str  # api, database, frontend, worker, etc.
    description: str
    responsibilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Component':
        """Create Component from dict with safe defaults."""
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict, got {type(data).__name__}")
        
        # Required fields
        name = data.get('name', 'unnamed_component')
        if not isinstance(name, str):
            name = str(name)
        
        comp_type = data.get('type', 'module')
        if not isinstance(comp_type, str):
            comp_type = 'module'
        
        description = data.get('description', f"Component: {name}")
        if not isinstance(description, str):
            description = str(description)
        
        # List fields with safe conversion
        responsibilities = cls._to_string_list(data.get('responsibilities', []))
        dependencies = cls._to_string_list(data.get('dependencies', []))
        files = cls._to_string_list(data.get('files', []))
        
        return cls(
            name=name,
            type=comp_type,
            description=description,
            responsibilities=responsibilities,
            dependencies=dependencies,
            files=files
        )
    
    @classmethod
    def from_string(cls, name: str) -> 'Component':
        """Create Component from just a name string."""
        if not isinstance(name, str):
            name = str(name) if name else 'unnamed_component'
        
        return cls(
            name=name,
            type='module',
            description=f"Component: {name}",
            responsibilities=[],
            dependencies=[],
            files=[]
        )
    
    @staticmethod
    def _to_string_list(value: Any) -> List[str]:
        """Safely convert any value to list of strings."""
        if value is None:
            return []
        
        if isinstance(value, str):
            return [value]
        
        if isinstance(value, (list, tuple)):
            result = []
            for item in value:
                if isinstance(item, str):
                    result.append(item)
                elif isinstance(item, (int, float)):
                    result.append(str(item))
                elif isinstance(item, dict) and 'name' in item:
                    result.append(str(item['name']))
                else:
                    result.append(str(item))
            return result
        
        return [str(value)]
    
    @classmethod
    def parse_list(cls, data: Any) -> List['Component']:
        """
        Parse a list of components from various AI output formats.
        Handles: list of dicts, list of strings, nested dicts, single items, None
        """
        components = []
        
        if data is None:
            logger.warning("Components data is None, returning empty list")
            return components
        
        # If it's a dict with 'components' key, extract it
        if isinstance(data, dict):
            if 'components' in data:
                data = data['components']
            else:
                try:
                    components.append(cls.from_dict(data))
                    return components
                except Exception as e:
                    logger.warning(f"Failed to parse single component dict: {e}")
                    return components
        
        # If it's a string, treat as component name
        if isinstance(data, str):
            components.append(cls.from_string(data))
            return components
        
        if not isinstance(data, (list, tuple)):
            logger.warning(f"Unexpected components type: {type(data).__name__}")
            return components
        
        # Parse each item in list
        for i, item in enumerate(data):
            try:
                if isinstance(item, dict):
                    components.append(cls.from_dict(item))
                elif isinstance(item, str):
                    components.append(cls.from_string(item))
                else:
                    logger.warning(f"Skipping component {i}: unexpected type {type(item).__name__}")
            except Exception as e:
                logger.warning(f"Failed to parse component {i}: {e}")
                continue
        
        return components


def safe_parse_components(data: Any) -> List[Component]:
    """Safely parse components from AI output with extensive error handling."""
    try:
        return Component.parse_list(data)
    except Exception as e:
        logger.error(f"Critical error parsing components: {e}")
        return []

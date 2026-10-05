from dataclasses import dataclass
from typing import Callable, Optional, Type
from pydantic import BaseModel

@dataclass
class Tool:
    name:str
    description:str
    parameters: dict
    handler: Optional[Callable[[dict], object]] = None
    response_model: Optional[Type[BaseModel]] = None

    def to_openai_tool(self) -> dict:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

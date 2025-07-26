import yaml
from dataclasses import dataclass, field
from typing import Annotated, Optional

from livekit.agents import (Agent, AgentSession)

@dataclass
class UserData:
    customer_first_name: Optional[str] = None
    customer_last_name: Optional[str] = None
    customer_phone: Optional[str] = None
    questionnaire_answers: dict[str, str] = field(default_factory=dict)
    recording_id: Optional[str] = None 
    
    agents: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    session: Optional[AgentSession] = None
    

    def summarize(self) -> str:
        data = {
            "customer_first_name": self.customer_first_name or "unknown",
            "customer_last_name": self.customer_last_name or "unknown",
            "customer_phone": self.customer_phone or "unknown",
            "questionnaire_answers": self.questionnaire_answers or "unknown",
            "recording_id": self.recording_id or "unknown",
        }
        return yaml.dump(data)
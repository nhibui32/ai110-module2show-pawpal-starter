from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Owner:
    name: str
    contact: str

@dataclass  
class Pet:
    name: str
    species: str
    owner: Owner

@dataclass
class Task:
    title: str
    category: str        # walk, eat, drink, other
    duration_minutes: int
    priority: str        # high, medium, low
    notes: str = ""
    completed: bool = False
    completed_at: Optional[datetime] = None
    
    def mark_complete(self):
        pass
    
    def priority_value(self):
        pass

class Scheduler:
    def __init__(self, pet: Pet):
        pass
    
    def add_task(self, task: Task):
        pass
    
    def remove_task(self, title: str):
        pass
    
    def complete_task(self, title: str):
        pass
    
    def get_schedule(self):
        pass
    
    def summary(self):
        pass
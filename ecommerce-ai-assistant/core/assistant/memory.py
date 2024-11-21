# ecommerce-ai-assistant/core/assistant/memory.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from collections import defaultdict

from utils.logger import get_logger

class ConversationMemory:
    """
    Manages conversation history and context for the AI Assistant.
    """
    
    def __init__(self, max_history: int = 10):
        self.logger = get_logger(__name__)
        self.max_history = max_history
        self.conversations: Dict[str, List[Dict]] = defaultdict(list)
        self.context: Dict[str, Dict] = defaultdict(dict)
        
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            conversation_id: Unique conversation identifier
            role: Message sender role (user/assistant)
            content: Message content
            metadata: Additional message metadata
        """
        try:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            self.conversations[conversation_id].append(message)
            
            # Trim history if needed
            if len(self.conversations[conversation_id]) > self.max_history:
                self.conversations[conversation_id] = self.conversations[conversation_id][-self.max_history:]
            
            self.logger.debug(
                "Added message to conversation",
                conversation_id=conversation_id,
                role=role,
                content_length=len(content)
            )
            
        except Exception as e:
            self.logger.error(
                "Error adding message to memory",
                error=str(e),
                exc_info=True
            )
    
    def get_history(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Get conversation history."""
        history = self.conversations.get(conversation_id, [])
        if limit:
            history = history[-limit:]
        return history
    
    def get_last_message(
        self,
        conversation_id: str,
        role: Optional[str] = None
    ) -> Optional[Dict]:
        """Get the last message from the conversation."""
        history = self.conversations.get(conversation_id, [])
        
        if not history:
            return None
            
        if role:
            # Find last message with specified role
            for message in reversed(history):
                if message["role"] == role:
                    return message
            return None
            
        return history[-1]
    
    def set_context(
        self,
        conversation_id: str,
        key: str,
        value: any
    ) -> None:
        """Set context value for a conversation."""
        self.context[conversation_id][key] = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_context(
        self,
        conversation_id: str,
        key: Optional[str] = None
    ) -> Dict:
        """Get conversation context."""
        if key:
            return self.context.get(conversation_id, {}).get(key, {}).get("value")
        return {
            k: v.get("value")
            for k, v in self.context.get(conversation_id, {}).items()
        }
    
    def clear_history(
        self,
        conversation_id: str,
        older_than: Optional[timedelta] = None
    ) -> None:
        """Clear conversation history."""
        if older_than:
            cutoff = datetime.utcnow() - older_than
            self.conversations[conversation_id] = [
                msg for msg in self.conversations.get(conversation_id, [])
                if datetime.fromisoformat(msg["timestamp"]) > cutoff
            ]
        else:
            self.conversations.pop(conversation_id, None)
    
    def clear_context(
        self,
        conversation_id: str,
        keys: Optional[List[str]] = None
    ) -> None:
        """Clear conversation context."""
        if keys:
            for key in keys:
                self.context[conversation_id].pop(key, None)
        else:
            self.context.pop(conversation_id, None)
    
    def get_summary(self, conversation_id: str) -> Dict:
        """Get conversation summary."""
        history = self.conversations.get(conversation_id, [])
        
        if not history:
            return {
                "message_count": 0,
                "duration": None,
                "last_message": None
            }
        
        first_msg = datetime.fromisoformat(history[0]["timestamp"])
        last_msg = datetime.fromisoformat(history[-1]["timestamp"])
        
        return {
            "message_count": len(history),
            "duration": (last_msg - first_msg).total_seconds(),
            "last_message": last_msg.isoformat(),
            "context_keys": list(self.context.get(conversation_id, {}).keys())
        }
    
    def save_state(self, file_path: str) -> None:
        """Save conversation state to file."""
        try:
            state = {
                "conversations": self.conversations,
                "context": self.context,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            with open(file_path, 'w') as f:
                json.dump(state, f)
                
            self.logger.info("Saved conversation state", file_path=file_path)
            
        except Exception as e:
            self.logger.error(
                "Error saving conversation state",
                error=str(e),
                exc_info=True
            )
    
    def load_state(self, file_path: str) -> None:
        """Load conversation state from file."""
        try:
            with open(file_path, 'r') as f:
                state = json.load(f)
            
            self.conversations = defaultdict(list, state["conversations"])
            self.context = defaultdict(dict, state["context"])
            
            self.logger.info(
                "Loaded conversation state",
                file_path=file_path,
                conversations=len(self.conversations),
                contexts=len(self.context)
            )
            
        except Exception as e:
            self.logger.error(
                "Error loading conversation state",
                error=str(e),
                exc_info=True
            )
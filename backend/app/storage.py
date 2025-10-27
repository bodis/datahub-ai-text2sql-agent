from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional
import uuid


class StorageInterface(ABC):
    """Abstract storage interface for chat threads and messages"""

    @abstractmethod
    def create_thread(self, name: str) -> Dict:
        """Create a new chat thread"""
        pass

    @abstractmethod
    def get_thread(self, thread_id: str) -> Optional[Dict]:
        """Get a thread by ID"""
        pass

    @abstractmethod
    def get_all_threads(self) -> List[Dict]:
        """Get all threads"""
        pass

    @abstractmethod
    def add_message(self, thread_id: str, content: str, sender: str) -> Dict:
        """Add a message to a thread"""
        pass

    @abstractmethod
    def get_messages(self, thread_id: str) -> List[Dict]:
        """Get all messages for a thread"""
        pass


class InMemoryStorage(StorageInterface):
    """In-memory implementation of storage interface"""

    def __init__(self):
        self.threads: Dict[str, Dict] = {}
        self.messages: Dict[str, List[Dict]] = {}

    def create_thread(self, name: str) -> Dict:
        thread_id = str(uuid.uuid4())
        thread = {
            "id": thread_id,
            "name": name,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.threads[thread_id] = thread
        self.messages[thread_id] = []
        return thread

    def get_thread(self, thread_id: str) -> Optional[Dict]:
        return self.threads.get(thread_id)

    def get_all_threads(self) -> List[Dict]:
        return sorted(
            self.threads.values(),
            key=lambda x: x["created_at"],
            reverse=True
        )

    def add_message(self, thread_id: str, content: str, sender: str) -> Dict:
        if thread_id not in self.threads:
            raise ValueError(f"Thread {thread_id} not found")

        message = {
            "id": str(uuid.uuid4()),
            "thread_id": thread_id,
            "content": content,
            "sender": sender,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.messages[thread_id].append(message)
        return message

    def get_messages(self, thread_id: str) -> List[Dict]:
        return self.messages.get(thread_id, [])


# Global storage instance
storage = InMemoryStorage()

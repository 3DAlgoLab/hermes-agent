"""
Session Linker - Share conversation context across platforms.

This module enables session linking between different platforms (CLI, Telegram, etc.)
by creating parent-child relationships and copying conversation history.
"""

import logging
from typing import Optional
from gateway.session import SessionStore, SessionSource

logger = logging.getLogger(__name__)


class SessionLinker:
    """Manages cross-platform session sharing."""
    
    def __init__(self, session_store: SessionStore):
        self.session_store = session_store
        self.linked_platforms = {"cli", "telegram"}  # Platforms to link
    
    def should_link(self, source: SessionSource) -> bool:
        """Check if this platform should be linked."""
        platform_name = source.platform.value if hasattr(source.platform, "value") else str(source.platform)
        return platform_name in self.linked_platforms
    
    def get_primary_session_id(self, source: SessionSource) -> Optional[str]:
        """
        Get the primary session ID from another linked platform.
        Returns None if no primary session exists.
        """
        # For now, use CLI as primary (most active)
        primary_platform = "cli"
        
        # Generate session key for primary platform
        primary_source = SessionSource(
            platform=primary_platform,
            chat_id=source.user_id or "default",
            user_id=source.user_id,
            chat_type="dm",
            chat_name=source.chat_name,
        )
        
        primary_key = self.session_store._generate_session_key(primary_source)
        
        with self.session_store._lock:
            self.session_store._ensure_loaded_locked()
            primary_entry = self.session_store._entries.get(primary_key)
        
        if primary_entry:
            return primary_entry.session_id
        return None
    
    def link_to_primary(self, source: SessionSource, new_session_id: str) -> bool:
        """
        Link a new session to the primary session by copying history.
        Returns True if linking was successful.
        """
        primary_session_id = self.get_primary_session_id(source)
        
        if not primary_session_id:
            logger.info(f"[SessionLinker] No primary session found for {source.platform}")
            return False
        
        try:
            # Load primary session history
            primary_history = self.session_store.load_transcript(primary_session_id)
            
            if not primary_history:
                logger.info(f"[SessionLinker] Primary session {primary_session_id} has no history")
                return False
            
            # Rewrite new session with primary history
            self.session_store.rewrite_transcript(new_session_id, primary_history)
            
            logger.info(
                f"[SessionLinker] Linked {new_session_id} to {primary_session_id} "
                f"with {len(primary_history)} messages"
            )
            return True
            
        except Exception as e:
            logger.error(f"[SessionLinker] Failed to link sessions: {e}")
            return False


def create_session_linker(session_store: SessionStore) -> SessionLinker:
    """Factory function to create a SessionLinker instance."""
    return SessionLinker(session_store)

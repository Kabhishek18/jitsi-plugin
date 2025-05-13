"""
Poll controller for managing polls and Q&A functionality.
"""

import logging
import uuid
import time
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

class PollController:
    """
    Controller for managing polls and Q&A functionality.
    Handles poll creation, voting, and results.
    """
    
    def __init__(self, signaling_server):
        """
        Initialize the poll controller.
        
        Args:
            signaling_server: Signaling server instance.
        """
        self.signaling = signaling_server
        self.active_polls = {}
    
    def create_poll(self, room_id: str, question: str, options: List[str], 
                   creator_id: str, anonymous: bool = False) -> Dict[str, Any]:
        """
        Create a new poll.
        
        Args:
            room_id (str): ID of the room.
            question (str): Poll question.
            options (List[str]): Poll options.
            creator_id (str): ID of the poll creator.
            anonymous (bool): Whether votes are anonymous.
            
        Returns:
            Dict[str, Any]: Poll information.
        """
        # Generate poll ID
        poll_id = str(uuid.uuid4())
        
        poll_info = {
            "id": poll_id,
            "room_id": room_id,
            "question": question,
            "options": options,
            "creator_id": creator_id,
            "created_at": time.time(),
            "active": True,
            "anonymous": anonymous,
            "votes": {},
            "results": None
        }
        
        self.active_polls[poll_id] = poll_info
        
        # Send poll event through signaling server
        if self.signaling and hasattr(self.signaling, "_handle_poll_event"):
            import asyncio
            asyncio.create_task(self.signaling._handle_poll_event(
                creator_id, room_id, "create", {
                    "question": question,
                    "options": options,
                    "pollId": poll_id,
                    "anonymous": anonymous
                }
            ))
        
        logger.info(f"Created poll {poll_id} in room {room_id}: {question}")
        return poll_info
    
    def vote(self, poll_id: str, user_id: str, option_index: int) -> bool:
        """
        Vote in a poll.
        
        Args:
            poll_id (str): ID of the poll.
            user_id (str): ID of the user voting.
            option_index (int): Index of the selected option.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if poll_id not in self.active_polls:
            logger.warning(f"Poll not found: {poll_id}")
            return False
        
        poll_info = self.active_polls[poll_id]
        
        # Check if poll is active
        if not poll_info["active"]:
            logger.warning(f"Poll is closed: {poll_id}")
            return False
        
        # Check if option index is valid
        if option_index < 0 or option_index >= len(poll_info["options"]):
            logger.warning(f"Invalid option index: {option_index}")
            return False
        
        # Record vote
        poll_info["votes"][user_id] = option_index
        
        # Send poll event through signaling server
        if self.signaling and hasattr(self.signaling, "_handle_poll_event"):
            import asyncio
            asyncio.create_task(self.signaling._handle_poll_event(
                user_id, poll_info["room_id"], "vote", {
                    "pollId": poll_id,
                    "optionIndex": option_index
                }
            ))
        
        logger.info(f"User {user_id} voted in poll {poll_id}: option {option_index}")
        return True
    
    def end_poll(self, poll_id: str, user_id: str) -> Dict[str, Any]:
        """
        End a poll and compute results.
        
        Args:
            poll_id (str): ID of the poll.
            user_id (str): ID of the user ending the poll.
            
        Returns:
            Dict[str, Any]: Poll results.
        """
        if poll_id not in self.active_polls:
            logger.warning(f"Poll not found: {poll_id}")
            return None
        
        poll_info = self.active_polls[poll_id]
        
        # Check if poll is active
        if not poll_info["active"]:
            logger.warning(f"Poll is already closed: {poll_id}")
            return poll_info["results"]
        
        # Only creator or admin can end poll
        if user_id != poll_info["creator_id"] and not self._is_admin(user_id, poll_info["room_id"]):
            logger.warning(f"User {user_id} not authorized to end poll {poll_id}")
            return None
        
        # End the poll
        poll_info["active"] = False
        poll_info["ended_at"] = time.time()
        
        # Compute results
        results = [0] * len(poll_info["options"])
        for option_index in poll_info["votes"].values():
            results[option_index] += 1
        
        poll_info["results"] = {
            "counts": results,
            "total_votes": len(poll_info["votes"]),
            "percentages": [count / len(poll_info["votes"]) * 100 if len(poll_info["votes"]) > 0 else 0 
                           for count in results]
        }
        
        # Send poll event through signaling server
        if self.signaling and hasattr(self.signaling, "_handle_poll_event"):
            import asyncio
            asyncio.create_task(self.signaling._handle_poll_event(
                user_id, poll_info["room_id"], "end", {
                    "pollId": poll_id,
                    "results": poll_info["results"]
                }
            ))
        
        logger.info(f"Ended poll {poll_id}")
        return poll_info["results"]
    
    def get_poll_info(self, poll_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Get information about a poll.
        
        Args:
            poll_id (str): ID of the poll.
            user_id (str, optional): ID of the requesting user.
            
        Returns:
            Optional[Dict[str, Any]]: Poll information or None if not found.
        """
        if poll_id not in self.active_polls:
            return None
        
        poll_info = self.active_polls[poll_id]
        
        # If anonymous, remove voter identities for non-creators
        if poll_info["anonymous"] and user_id and user_id != poll_info["creator_id"] and not self._is_admin(user_id, poll_info["room_id"]):
            # Create a copy without identifiable vote information
            poll_copy = poll_info.copy()
            if "votes" in poll_copy:
                # Replace with counts only
                vote_counts = {}
                for option_index in poll_copy["votes"].values():
                    vote_counts[option_index] = vote_counts.get(option_index, 0) + 1
                poll_copy["vote_counts"] = vote_counts
                del poll_copy["votes"]
            return poll_copy
        
        return poll_info
    
    def list_active_polls(self, room_id: str) -> List[Dict[str, Any]]:
        """
        List all active polls in a room.
        
        Args:
            room_id (str): ID of the room.
            
        Returns:
            List[Dict[str, Any]]: List of active poll information.
        """
        return [poll for poll in self.active_polls.values() 
                if poll["room_id"] == room_id and poll["active"]]
    
    def list_all_polls(self, room_id: str) -> List[Dict[str, Any]]:
        """
        List all polls in a room.
        
        Args:
            room_id (str): ID of the room.
            
        Returns:
            List[Dict[str, Any]]: List of all poll information.
        """
        return [poll for poll in self.active_polls.values() 
                if poll["room_id"] == room_id]
    
    def delete_poll(self, poll_id: str, user_id: str) -> bool:
        """
        Delete a poll.
        
        Args:
            poll_id (str): ID of the poll.
            user_id (str): ID of the user deleting the poll.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if poll_id not in self.active_polls:
            logger.warning(f"Poll not found: {poll_id}")
            return False
        
        poll_info = self.active_polls[poll_id]
        
        # Only creator or admin can delete poll
        if user_id != poll_info["creator_id"] and not self._is_admin(user_id, poll_info["room_id"]):
            logger.warning(f"User {user_id} not authorized to delete poll {poll_id}")
            return False
        
        # Delete the poll
        del self.active_polls[poll_id]
        
        # Send poll event through signaling server
        if self.signaling and hasattr(self.signaling, "_handle_poll_event"):
            import asyncio
            asyncio.create_task(self.signaling._handle_poll_event(
                user_id, poll_info["room_id"], "delete", {
                    "pollId": poll_id
                }
            ))
        
        logger.info(f"Deleted poll {poll_id}")
        return True
    
    def _is_admin(self, user_id: str, room_id: str) -> bool:
        """
        Check if a user is an admin in a room.
        
        Args:
            user_id (str): ID of the user.
            room_id (str): ID of the room.
            
        Returns:
            bool: True if the user is an admin, False otherwise.
        """
        # This would need to be implemented based on your permission system
        # For now, just return False
        return False
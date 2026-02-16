from dataclasses import dataclass


@dataclass
class TutorContext:
    """Context schema shared across all tutor agents.

    Attributes:
        user_id: Unique identifier for the learner.
        session_id: Unique identifier for the current session/conversation.
    """

    user_id: str
    session_id: str

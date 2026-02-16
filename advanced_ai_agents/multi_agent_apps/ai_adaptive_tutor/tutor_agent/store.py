from langgraph.store.memory import InMemoryStore

# Shared in-memory store for long-term memory across all agents and sessions.
# Namespaces used:
#   ("learner_profiles",)  key=user_id  -> learner profile data
#   ("topic_maps",)        key=user_id  -> researched topic map
#   ("learning_plans",)    key=user_id  -> learning roadmap
#   ("progress",)          key=user_id  -> progress tracking (covered topics, scores, etc.)
#   ("current_quiz",)      key=user_id  -> current quiz data
store = InMemoryStore()

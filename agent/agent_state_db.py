import json
import os
import time

class AgentStateDB:
    """
    Simple persistent state for agent memory and last intel timestamp.
    Stores state in a JSON file.
    """
    def __init__(self, path="agent_state.db"):
        self.path = path
        self._state = self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"memory": {}, "last_intel_ts": {}}

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self._state, f)

    @property
    def memory(self):
        return self._state.get("memory", {})

    @memory.setter
    def memory(self, value):
        self._state["memory"] = value
        self.save()

    def get_last_intel_ts(self, node_id):
        return self._state.get("last_intel_ts", {}).get(node_id)

    def set_last_intel_ts(self, node_id, ts):
        if "last_intel_ts" not in self._state:
            self._state["last_intel_ts"] = {}
        self._state["last_intel_ts"][node_id] = ts
        self.save()

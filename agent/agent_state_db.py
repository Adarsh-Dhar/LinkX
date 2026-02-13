import sqlite3
import os
from datetime import datetime

class AgentStateDB:
    def __init__(self, db_path="dev.db"):
        # Absolute path fix for Docker/Local compatibility
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, db_path)

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_performance_context(self):
        """Fetches recent trade outcomes to inform risk appetite."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            # Fetch last 10 trades from TradeDecision table
            cursor.execute("""
                SELECT type, status, pnl 
                FROM TradeDecision 
                ORDER BY createdAt DESC 
                LIMIT 10
            """)
            trades = cursor.fetchall()
            conn.close()

            if not trades:
                return "No recent trade history. Starting fresh."

            wins = len([t for t in trades if t[1] == 'WIN' or (t[2] and t[2] > 0)])
            return f"Recent Performance: {wins}/{len(trades)} wins. Last 3 trades: {[t[0] for t in trades[:3]]}"
        except Exception as e:
            return f"DB Error (Performance): {str(e)}"

    def get_active_nodes_catalog(self):
        """Fetches a catalog of active nodes for the Scout to analyze, including lastPurchaseTime."""
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Fetch lastPurchaseTime so the AI knows if it's recently updated
            cursor.execute("""
                SELECT name, category, reliabilityScore, description, lastPurchaseTime
                FROM AlphaNode WHERE status = 'ACTIVE'
            """)
            nodes = cursor.fetchall()
            conn.close()

            catalog = []
            for node in nodes:
                catalog.append({
                    "name": node['name'],
                    "specialty": node['category'],
                    "description": node['description'],
                    "last_bought_at": node['lastPurchaseTime'] # <--- CRITICAL FOR AI
                })
            return catalog
        except Exception as e:
            return []

    def record_node_purchase(self, node_name):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute("UPDATE AlphaNode SET lastPurchaseTime = ? WHERE name = ?", (now, node_name))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def update_node_score(self, node_name, score_delta):
        """Updates node reliability based on utility."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE AlphaNode 
                SET reliabilityScore = reliabilityScore + ? 
                WHERE name = ?
            """, (score_delta, node_name))
            conn.commit()
            conn.close()
        except Exception:
            pass

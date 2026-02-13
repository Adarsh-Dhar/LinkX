import sqlite3
import os
from datetime import datetime

class AgentStateDB:
    def __init__(self, db_path="prisma/dev.db"):
        # This correctly points to the subfolder where Prisma stores the SQLite file
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(project_root, "frontend/prisma/dev.db")
            print(f"   📂 [DB Connection] Looking for DB at: {self.db_path}")

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
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Fetch ALL nodes regardless of status to ensure the AI sees 'something'
            cursor.execute("SELECT title, category, reliabilityScore, description, lastPurchaseTime FROM AlphaNode")
            nodes = cursor.fetchall()
            conn.close()

            catalog = []
            for n in nodes:
                catalog.append({
                    "title": n['title'],
                    "specialty": n['category'],
                    "description": n['description'] or "Market data provider",
                    "last_bought_at": n['lastPurchaseTime']
                })
            print(f"   📡 [DB Catalog] Found {len(catalog)} nodes in database.")
            return catalog
        except Exception as e:
            print(f"   ❌ [DB Error] {e}")
            return []

    def record_node_purchase(self, node_title):
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute("UPDATE AlphaNode SET lastPurchaseTime = ? WHERE title = ?", (now, node_title))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def update_node_score(self, node_title, score_delta):
        """Updates node reliability based on utility."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE AlphaNode 
                SET reliabilityScore = reliabilityScore + ? 
                WHERE title = ?
            """, (score_delta, node_title))
            conn.commit()
            conn.close()
        except Exception:
            pass

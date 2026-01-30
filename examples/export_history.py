import sqlite3
import json
import os
import sys
import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "hourly_simulation.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "ghost_kg", "templates")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "simulation_history.json")


def export_history():
    print(f"📂 Working Directory: {BASE_DIR}")

    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    logs = conn.execute("SELECT * FROM logs ORDER BY timestamp ASC").fetchall()
    all_nodes = conn.execute("SELECT * FROM nodes").fetchall()
    all_edges = conn.execute("SELECT * FROM edges").fetchall()

    if not logs:
        print("⚠️ Warning: Database is empty.")
        return

    history = {
        "metadata": {"topic": "Robust Heatmap", "date": "Reconstructed"},
        "agents": ["Alice", "Bob"],
        "steps": [],
    }

    # Step 0: Init
    history["steps"].append(
        {
            "step": 0,
            "round": 0,
            "action": "Init",
            "graphs": {
                "Alice": {"nodes": [], "links": []},
                "Bob": {"nodes": [], "links": []},
            },
        }
    )

    for i, log in enumerate(logs):
        current_time_str = log["timestamp"]
        try:
            current_time = datetime.datetime.fromisoformat(current_time_str)
        except:
            current_time = datetime.datetime.now(datetime.timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=datetime.timezone.utc)

        step_data = {
            "step": i + 1,
            "round": i + 1,
            "action": f"{log['agent_name']} {log['action_type']} ({current_time.strftime('%H:%M')})",
            "graphs": {},
        }

        for agent in ["Alice", "Bob"]:

            # --- STEP 1: Gather ALL Valid Nodes for this Time ---
            potential_nodes = {}  # id -> node_data

            for n in all_nodes:
                created_at = n["created_at"]
                try:
                    created_at = datetime.datetime.fromisoformat(created_at)
                except:
                    created_at = current_time
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=datetime.timezone.utc)

                if n["owner_id"] == agent and created_at <= current_time:
                    is_self = n["id"] == "I"

                    # FSRS Calculation
                    stability = n["stability"]
                    last_review = n["last_review"]
                    try:
                        last_review = datetime.datetime.fromisoformat(last_review)
                    except:
                        last_review = current_time
                    if last_review.tzinfo is None:
                        last_review = last_review.replace(tzinfo=datetime.timezone.utc)

                    elapsed_days = (current_time - last_review).total_seconds() / 86400
                    if elapsed_days < 0:
                        elapsed_days = 0
                    retrievability = (
                        (1 + elapsed_days / (9 * stability)) ** -1
                        if stability > 0
                        else 0
                    )

                    # Force "I" to be visible and active
                    if is_self:
                        retrievability = 1.0

                    potential_nodes[n["id"]] = {
                        "id": n["id"],
                        "group": 0 if is_self else 1,
                        "radius": 25 if is_self else 10 + (stability * 0.5),
                        "retrievability": round(retrievability, 3),
                        "stability": round(stability, 2),
                    }

            # --- STEP 2: Gather Edges (STRICT FILTER) ---
            valid_edges = []
            touched_node_ids = set()
            touched_node_ids.add("I")  # Always save the Self node

            for e in all_edges:
                e_created = e["created_at"]
                try:
                    e_created = datetime.datetime.fromisoformat(e_created)
                except:
                    e_created = current_time
                if e_created.tzinfo is None:
                    e_created = e_created.replace(tzinfo=datetime.timezone.utc)

                if e["owner_id"] == agent and e_created <= current_time:
                    # CRITICAL: Do not include edges if the node is missing
                    if (
                        e["source"] in potential_nodes
                        and e["target"] in potential_nodes
                    ):
                        valid_edges.append(
                            {
                                "source": e["source"],
                                "target": e["target"],
                                "label": e["relation"],
                                "value": 1,
                                "dashed": False,
                            }
                        )
                        touched_node_ids.add(e["source"])
                        touched_node_ids.add(e["target"])

            # --- STEP 3: Final Node List (Prune Orphans) ---
            final_nodes = []
            for nid, ndata in potential_nodes.items():
                if nid in touched_node_ids:
                    final_nodes.append(ndata)

            step_data["graphs"][agent] = {"nodes": final_nodes, "links": valid_edges}

        history["steps"].append(step_data)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(history, f, indent=2)

    print(f"✅ History exported to {OUTPUT_FILE}")


if __name__ == "__main__":
    export_history()

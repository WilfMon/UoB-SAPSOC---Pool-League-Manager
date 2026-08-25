import sqlite3
conn = sqlite3.connect(":memory:")
for name in ("set_update_hook", "set_authorizer", "set_progress_handler", "set_trace_callback"):
    print(name, hasattr(conn, name))
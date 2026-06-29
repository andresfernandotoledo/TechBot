import json
import os
import fcntl
import uuid
from datetime import datetime

TOPOLOGY_DB_FILE = os.path.join(os.path.dirname(__file__), "topology_db.json")

EMPTY_DB = {
    "topologies": [],
    "metadata": {
        "created": datetime.now().isoformat(),
        "version": "1.0",
    }
}

def _lock_db(archivo, modo="r"):
    try:
        fcntl.flock(archivo, fcntl.LOCK_EX if modo == "w" else fcntl.LOCK_SH)
    except (IOError, AttributeError):
        pass

def _unlock_db(archivo):
    try:
        fcntl.flock(archivo, fcntl.LOCK_UN)
    except (IOError, AttributeError):
        pass

def _load_db():
    """Carga la base de datos de topologías con lock compartido."""
    if os.path.exists(TOPOLOGY_DB_FILE):
        try:
            with open(TOPOLOGY_DB_FILE, "r") as f:
                _lock_db(f, "r")
                data = json.load(f)
                _unlock_db(f)
                return data
        except (json.JSONDecodeError, IOError):
            return dict(EMPTY_DB)
    return dict(EMPTY_DB)

def _save_db(db):
    """Guarda la base de datos de topologías con lock exclusivo."""
    with open(TOPOLOGY_DB_FILE, "w") as f:
        _lock_db(f, "w")
        json.dump(db, f, indent=2)
        _unlock_db(f)
    return True

# ─── OPERACIONES ──────────────────────────────────────────────

def list_topologies():
    """Retorna la lista de todas las topologías."""
    db = _load_db()
    return db["topologies"]

def get_topology(topo_id):
    """Retorna una topología específica por ID."""
    db = _load_db()
    for topo in db["topologies"]:
        if topo["id"] == topo_id:
            return topo
    return None

def save_topology(topo_data):
    """Guarda o actualiza una topología."""
    db = _load_db()
    topo_id = topo_data.get("id")
    
    if not topo_id:
        topo_id = str(uuid.uuid4())
        topo_data["id"] = topo_id
        topo_data["created_at"] = datetime.now().isoformat()
    
    topo_data["updated_at"] = datetime.now().isoformat()
    
    # Buscar si ya existe para actualizar
    updated = False
    for i, topo in enumerate(db["topologies"]):
        if topo["id"] == topo_id:
            db["topologies"][i] = topo_data
            updated = True
            break
    
    if not updated:
        db["topologies"].append(topo_data)
        
    _save_db(db)
    return topo_data

def delete_topology(topo_id):
    """Elimina una topología por ID."""
    db = _load_db()
    original_count = len(db["topologies"])
    db["topologies"] = [t for t in db["topologies"] if t["id"] != topo_id]
    
    if len(db["topologies"]) < original_count:
        _save_db(db)
        return True
    return False

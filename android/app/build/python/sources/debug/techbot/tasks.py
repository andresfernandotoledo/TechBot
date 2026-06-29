import threading
import uuid
import time

_tasks = {}
_lock = threading.Lock()


def start_task(func, *args, **kwargs):
    task_id = uuid.uuid4().hex[:12]
    task = {
        "id": task_id,
        "status": "running",
        "result": None,
        "error": None,
        "progress": "",
        "started": time.time(),
    }
    with _lock:
        _tasks[task_id] = task

    def _run():
        try:
            task["progress"] = "Iniciando..."
            result = func(*args, **kwargs)
            with _lock:
                task["status"] = "done"
                task["result"] = result
                task["progress"] = "Completado"
        except Exception as e:
            with _lock:
                task["status"] = "error"
                task["error"] = str(e)
                task["progress"] = f"Error: {e}"

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return task_id


def get_task(task_id):
    with _lock:
        task = _tasks.get(task_id)
        if task is None:
            return {"status": "not_found", "error": "Tarea no encontrada"}
        return dict(task)


def list_tasks():
    with _lock:
        return {tid: {"status": t["status"], "progress": t["progress"]}
                for tid, t in sorted(_tasks.items(),
                                     key=lambda x: x[1]["started"], reverse=True)[:20]}

import multiprocessing

def worker_threads():
    return multiprocessing.cpu_count()

def worker_count():
    return multiprocessing.cpu_count() * 2 + 1

workers = worker_count()
threads = worker_threads()
worker_class = "gthread"
bind = "0.0.0.0:8545"
loglevel = "info"
accesslog = "-"

print(f"⚙️ Gunicorn starting with {workers} workers × {threads} threads (I/O heavy mode)")

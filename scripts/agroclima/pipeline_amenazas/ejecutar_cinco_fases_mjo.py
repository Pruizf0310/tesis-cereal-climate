"""Run the five remaining global maize ONI/MJO phases detached on this laptop."""
import argparse
import ctypes
import json
import msvcrt
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

PHASES = ['VEG', 'FLO', 'REP', 'FIL', 'MAT']


def stamp():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('C:/Users/paola/Tesis'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers-per-phase', type=int, default=2)
    args = parser.parse_args()
    if args.workers_per_phase not in (1, 2):
        parser.error('Use 1 or 2 workers per phase; five phases run concurrently')
    args.output.mkdir(parents=True, exist_ok=True)
    # One orchestrator per dataset. Windows releases the lock on process exit.
    lock_path = Path(__file__).with_name('cinco_fases_mjo.lock')
    lock = lock_path.open('a+b')
    lock.seek(0)
    if lock.read(1) == b'':
        lock.write(b'0'); lock.flush()
    lock.seek(0)
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        raise RuntimeError('Ya hay una ejecución de las cinco fases; no se inicia otra')
    script = Path(__file__).with_name('maize_probabilidades_una_fase.py')
    state = dict(started_utc=stamp(), pid=os.getpid(), status='RUNNING',
                 root=str(args.root), output=str(args.output), phases={},
                 workers_per_phase=args.workers_per_phase, estimated_total_hours=None,
                 note='ERA5-Land calculation uses GEE. Native cache and pixel checkpoints survive interruption.')
    children = {}
    handles = []
    keep_awake = ctypes.windll.kernel32.SetThreadExecutionState
    keep_awake(0x80000001)  # Prevent system idle sleep; display can switch off.
    try:
        for phase in PHASES:
            command = [sys.executable, '-u', '-X', 'utf8', str(script), '--root', str(args.root),
                       '--phase', phase, '--workers', str(args.workers_per_phase)]
            log = (args.output/f'{phase}.log').open('ab', buffering=0)
            handles.append(log)
            child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                     creationflags=subprocess.CREATE_NO_WINDOW,
                                     cwd=str(script.parent))
            children[phase] = child
            state['phases'][phase] = dict(status='RUNNING', pid=child.pid, started_utc=stamp(),
                                         command=command, log=str(args.output/f'{phase}.log'))
        while True:
            stopping = (args.output/'DETENER.txt').exists()
            for phase, child in children.items():
                item = state['phases'][phase]
                if stopping and child.poll() is None:
                    child.terminate()
                code = child.poll()
                if code is not None and item['status'] == 'RUNNING':
                    item.update(status='COMPLETED' if code == 0 else 'STOPPED' if stopping else 'FAILED',
                                exit_code=code, finished_utc=stamp())
                # Keep compact real progress, without repeatedly reading entire logs.
                log_path = args.output/f'{phase}.log'
                if log_path.exists():
                    with log_path.open('rb') as source:
                        source.seek(max(0, log_path.stat().st_size-5000))
                        lines = source.read().decode('utf-8', errors='replace').splitlines()
                    if lines:
                        item['last_message'] = lines[-1]
                    progress = [v for v in lines if v.startswith('Píxeles ') or v.startswith('TERMINADO:')]
                    if progress:
                        item['progress'] = progress[-1]
            state['updated_utc'] = stamp()
            active = any(c.poll() is None for c in children.values())
            if not active:
                state['status'] = 'COMPLETED' if all(v['status']=='COMPLETED' for v in state['phases'].values()) else 'NEEDS_ATTENTION'
                state['finished_utc'] = stamp()
            save(args.output/'estado.json', state)
            if not active:
                break
            time.sleep(30)
    finally:
        keep_awake(0x80000000)
        for handle in handles:
            handle.close()
        lock.close()


if __name__ == '__main__':
    main()

"""Allocator peaks plus sampled process VRAM; measurements include model load."""
import os
import subprocess
import threading
import time


class GpuUsage:
    def __init__(self, limit_mib=12288):
        self.limit_mib = limit_mib
        self.samples = []
        self.stop = threading.Event()

    def sample(self):
        result = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory",
                                 "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            values = []
            for line in result.stdout.splitlines():
                fields = [p.strip() for p in line.split(",")]
                if len(fields) == 2 and fields[0] == str(os.getpid()) and fields[1].isdigit():
                    values.append(int(fields[1]))
            if values:
                self.samples.append({"elapsed_seconds": time.monotonic() - self.started,
                                     "process_vram_mib": sum(values)})

    def poll(self):
        while not self.stop.wait(0.5):
            try:
                self.sample()
            except (OSError, subprocess.TimeoutExpired):
                pass

    def __enter__(self):
        import torch
        self.started = time.monotonic()
        torch.cuda.init()
        torch.cuda.reset_peak_memory_stats()
        self.thread = threading.Thread(target=self.poll, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        import torch
        torch.cuda.synchronize()
        self.stop.set()
        self.thread.join(timeout=12)
        self.sample()
        allocated = torch.cuda.max_memory_allocated() / 1024**2
        reserved = torch.cuda.max_memory_reserved() / 1024**2
        process = max((s['process_vram_mib'] for s in self.samples), default=None)
        self.result = {"gpu": torch.cuda.get_device_name(0), "elapsed_seconds": time.monotonic() - self.started,
                       "peak_allocated_mib": allocated, "peak_reserved_mib": reserved,
                       "sampled_process_peak_mib": process, "process_sample_interval_seconds": 0.5,
                       "memory_limit_mib": self.limit_mib,
                       "within_limit": process is not None and max(allocated, reserved, process) <= self.limit_mib,
                       "note": "Process VRAM is sampled, allocator values are peaks; this measures only tested inputs."}

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from loguru import logger


@dataclass
class ImageJob:
    job_id: str
    owner: str
    prompt: str
    created_at: float = field(default_factory=time.time)
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None
    completed_at: Optional[float] = None
    done: threading.Event = field(default_factory=threading.Event, repr=False)


class ImageJobManager:
    """Run image generation outside Gradio callbacks and signal completion once."""

    def __init__(self, max_workers=4, retention_seconds=3600, max_jobs=256):
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="image-generation",
        )
        self._retention_seconds = retention_seconds
        self._max_jobs = max_jobs
        self._jobs = {}
        self._lock = threading.RLock()

    def submit(self, *, owner: str, prompt: str, work: Callable[[], Any]) -> ImageJob:
        with self._lock:
            self._prune_locked()
            if len(self._jobs) >= self._max_jobs:
                raise RuntimeError("后台图片任务过多，请稍后再试。")
            job = ImageJob(
                job_id=uuid.uuid4().hex,
                owner=owner,
                prompt=prompt,
            )
            self._jobs[job.job_id] = job
        self._executor.submit(self._run_job, job.job_id, work)
        return job

    def get(self, job_id: str, *, owner: Optional[str] = None) -> Optional[ImageJob]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or (owner is not None and job.owner != owner):
                return None
            return job

    def wait(self, job_id: str, *, owner: Optional[str] = None) -> Optional[ImageJob]:
        job = self.get(job_id, owner=owner)
        if job is None:
            return None
        job.done.wait()
        return self.get(job_id, owner=owner)

    def _run_job(self, job_id: str, work: Callable[[], Any]):
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job.status = "running"
        try:
            result = work()
        except Exception as exc:
            logger.exception("Background image job failed: job_id={}", job_id)
            with self._lock:
                job.status = "failed"
                job.error = str(exc)
                job.completed_at = time.time()
                job.done.set()
            return
        with self._lock:
            job.status = "completed"
            job.result = result
            job.completed_at = time.time()
            job.done.set()

    def _prune_locked(self):
        cutoff = time.time() - self._retention_seconds
        expired = [
            job_id
            for job_id, job in self._jobs.items()
            if job.done.is_set() and (job.completed_at or job.created_at) < cutoff
        ]
        for job_id in expired:
            self._jobs.pop(job_id, None)


image_job_manager = ImageJobManager()

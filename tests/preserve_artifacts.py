"""Opt-in pytest plugin: retain files otherwise removed during fixture exercises.

Run with -p tests.preserve_artifacts and SEO_TEST_RETAIN_DIR set to a new run's
retained/ folder. Deletions outside the test's owned paths are refused.
"""
import os
from pathlib import Path
import shutil
import uuid
import pytest

@pytest.fixture(autouse=True)
def retain_removed_artifacts(monkeypatch, tmp_path_factory, request):
    destination = os.environ.get('SEO_TEST_RETAIN_DIR')
    if not destination:
        return
    retained = Path(destination).resolve()
    retained.mkdir(parents=True, exist_ok=True)
    owned = tmp_path_factory.getbasetemp().resolve()
    monkeypatch.setenv('CLAUDE_SEO_RUN_DIR', str(owned))
    if request.module.__name__.endswith('test_commoncrawl_graph'):
        monkeypatch.setenv('CODEX_SEO_CACHE_DIR', str(owned / 'commoncrawl-cache'))

    def retain(path, *args, **kwargs):
        if kwargs.get('dir_fd') is not None or isinstance(path, int):
            raise RuntimeError('Unsupported descriptor-relative deletion in preserved test run')
        path = Path(path).absolute()
        if not path.exists() and not path.is_symlink():
            if kwargs.get('ignore_errors') or kwargs.get('missing_ok'):
                return
            raise FileNotFoundError(path)
        # The path itself (including a symlink) must be owned by this test run.
        if not path.parent.resolve().is_relative_to(owned):
            raise RuntimeError('Refusing cleanup outside the versioned test directory: ' + str(path))
        target = retained / (uuid.uuid4().hex + '-' + path.name)
        path.rename(target)

    monkeypatch.setattr(os, 'unlink', retain)
    monkeypatch.setattr(os, 'remove', retain)
    monkeypatch.setattr(os, 'rmdir', retain)
    monkeypatch.setattr(shutil, 'rmtree', retain)

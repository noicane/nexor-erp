# -*- coding: utf-8 -*-
"""
NEXOR ERP - Database Worker
DB sorgularini arka plan thread'inde calistirir, UI donmasini onler.
"""
import logging
from PySide6.QtCore import QObject, QThread, Signal

logger = logging.getLogger(__name__)


class _Worker(QObject):
    """Arka plan thread'inde calisan isci"""
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, func):
        super().__init__()
        self._func = func

    def run(self):
        try:
            result = self._func()
            self.finished.emit(result)
        except Exception as e:
            logger.error("DB worker hatasi: %s", e)
            self.error.emit(str(e))


def run_in_background(query_func, on_success=None, on_error=None):
    """
    query_func'i arka plan thread'inde calistir.

    Args:
        query_func: Parametre almayan, sonuc donduren fonksiyon
        on_success: Basarili olursa cagrilan callback (result)
        on_error: Hata olursa cagrilan callback (error_str)

    Returns:
        (thread, worker) tuple - caller'in referans tutmasi icin
    """
    thread = QThread()
    worker = _Worker(query_func)
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.error.connect(thread.quit)

    if on_success:
        worker.finished.connect(on_success)
    if on_error:
        worker.error.connect(on_error)

    # Temizlik
    thread.finished.connect(thread.deleteLater)
    worker.finished.connect(worker.deleteLater)
    worker.error.connect(worker.deleteLater)

    thread.start()
    return thread, worker

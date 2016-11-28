import time
import subprocess

from celery.contrib.abortable import AbortableTask

from kostyor.rpc.app import app


@app.task(bind=True, base=AbortableTask)
def execute(self, args, cwd=None, ignore_errors=False):
    """Execute an arbitrary process and terminate it if abort() is sent.

    In case when process ended with return code non-equal to zero, the
    exception is raised in order to mark celery task as failed.

    :param args: process with arguments to be executed
    :param cwd: path to current working directory to be set
    :param ignore_errors: do not raise exception for '!=0' return codes if True
    :return: process' return code, or 'None' if it was aborted
    """
    process = subprocess.Popen(args, cwd=cwd)

    # Unfortunately, 'timeout' parameter of 'wait' method has been added in
    # Python 3.3, so we can't use to do a periodic check for 'is_aborted()'
    # value and that's why 'poll()' and 'sleep()' are used.
    while process.poll() is None:
        if self.is_aborted():
            process.terminate()
            break

        time.sleep(1)

    # Celery treats exceptions from task as way to mark it failed. So let's
    # throw one to do so in case return code is not zero.
    if all([not ignore_errors,
            process.returncode is not None,
            process.returncode != 0]):
        raise subprocess.CalledProcessError(process.returncode, ' '.join(args))

    return process.returncode

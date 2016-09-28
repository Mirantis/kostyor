

Consider using Celery to distribute the tasks.

For the ansible driver, a task may be a playbook that is to be
executed for a specific node.

Job control
-----------

Cancellation:

http://docs.celeryproject.org/en/latest/userguide/workers.html#revoke-revoking-tasks

http://docs.celeryproject.org/en/latest/reference/celery.app.control.html#celery.app.control.Control.discard_all

http://stackoverflow.com/a/15642110/705245


Pause:

http://docs.celeryproject.org/en/latest/reference/celery.app.control.html#celery.app.control.Control.cancel_consumer


Resume:

http://docs.celeryproject.org/en/latest/reference/celery.app.control.html#celery.app.control.Control.add_consumer

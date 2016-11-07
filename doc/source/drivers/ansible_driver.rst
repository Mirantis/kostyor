##############
Ansible driver
##############

Driver for run ansible playbook.

Python API for running playbook
===============================

Here is an example of using Python API:

::

    import os
    import sys
    from collections import namedtuple

    from ansible.parsing.dataloader import DataLoader
    from ansible.vars import VariableManager
    from ansible.inventory import Inventory
    from ansible.executor.playbook_executor import PlaybookExecutor

    from threading import Thread
    import time

    variable_manager = VariableManager()
    loader = DataLoader()

    inventory = Inventory(loader=loader, variable_manager=variable_manager)
    playbook_path = '/home/user/site.yml'

    if not os.path.exists(playbook_path):
        print '[INFO] The playbook does not exist'
        sys.exit()

    Options = namedtuple('Options', ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection','module_path', 'forks', 'remote_user', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check'])
    options = Options(listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh', module_path=None, forks=100, remote_user='user', private_key_file=None, ssh_common_args=None, ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None, become=True, become_method=None, become_user='user', verbosity=None, check=False)

    passwords = {}

    pbex = PlaybookExecutor(playbooks=[playbook_path], inventory=inventory, variable_manager=variable_manager, loader=loader, options=options, passwords=passwords)

    results = pbex.run()


Interrupt playbook run
======================

For interrupting playbook somewhere in the middle you can call "terminate()" on TaskQueueManager object.
Take into account that "terminate()" don't interrupt ansible work immediately.
After "terminate()" is calling, current task will keep running, and no more tasks will run.

Here is an example of terminating:

::

    pbex = PlaybookExecutor(playbooks=[playbook_path], inventory=inventory, variable_manager=variable_manager, loader=loader, options=options, passwords=passwords)

    p = Thread(target=pbex.run)
    p.start()
    time.sleep(5)
    pbex._tqm.terminate()
    p.join()


In case when we have multiple servers flow will be the following.
Ansible iterates by tasks and for each task iterates by servers.
That means when we interrupt playbook we will have servers in almost the same conditions.

Resume interrupted playbook
=============================

Implementation
--------------

Current state is contained in PlayIterator.
The iterator is a local variable inside "TaskQueueManager.run()" function.
For interruct with it we need to change variable scope.

::

    --- a/lib/ansible/executor/task_queue_manager.py
    +++ b/lib/ansible/executor/task_queue_manager.py
    @@ -76,6 +76,7 @@ class TaskQueueManager:
             self._stdout_callback  = stdout_callback
             self._run_additional_callbacks = run_additional_callbacks
             self._run_tree         = run_tree
    +        self._iterator         = None

             self._callbacks_loaded = False
             self._callback_plugins = []
    @@ -252,14 +253,18 @@ class TaskQueueManager:
                 raise AnsibleError("Invalid play strategy specified: %s" % new_play.strategy, obj=play._ds)

             # build the iterator
    -        iterator = PlayIterator(
    -            inventory=self._inventory,
    -            play=new_play,
    -            play_context=play_context,
    -            variable_manager=self._variable_manager,
    -            all_vars=all_vars,
    -            start_at_done = self._start_at_done,
    -        )
    +        if self._iterator:
    +            iterator = self._iterator
    +        else:
    +            iterator = PlayIterator(
    +                inventory=self._inventory,
    +                play=new_play,
    +                play_context=play_context,
    +                variable_manager=self._variable_manager,
    +                all_vars=all_vars,
    +                start_at_done = self._start_at_done,
    +            )
    +            self._iterator = iterator

             # Because the TQM may survive multiple play runs, we start by marking
             # any hosts as failed in the iterator here which may have been marked

After this we can use iterator for our needs. The following example demonstrates how playbook can be resumed after terminating.

::

    pbex = PlaybookExecutor(playbooks=[playbook_path], inventory=inventory, variable_manager=variable_manager, loader=loader, options=options, passwords=passwords)

    p = Thread(target=pbex.run)
    p.start()
    time.sleep(5)
    pbex._tqm.terminate()
    p.join()

    iterator = pbex._tqm._iterator
    pbex = PlaybookExecutor(playbooks=[playbook_path], inventory=inventory, variable_manager=variable_manager, loader=loader, options=options, passwords=passwords)
    pbex._tqm._iterator = iterator
    pbex.run()

Advantages
----------

* resuming playbook run from any point
* PlayIterator can be serialised and saved in persistence store

Disadvantages
-------------

* ansible core code must be changed

Conclusion
----------

Taking into account ansible task idenpotency we can run whole playbook from the beginning after interrupting it in the middle.
In this way resume interrupted playbook is meaningless.

OpenStack ansible upgrade
=========================

For running upgrade you must execute `scripts/run-upgrade.sh`.

This script consists of two parts:

* run `scripts/bootstrap-ansible.sh` for install required tools, packages, etc.
* run sequence of 20 ansible playbooks

Each playbook runs independently, they don't have shared namespace with variables.

That means that we can split whole upgrade at least on 20 pieces.
Also if the piece was done successfully we don't need to repeat it when try to resume upgrade.


Testing the Ansible Driver
==========================

* `Use an AIO instance`_ - based off Ubuntu 14.04

* Check out the stable/mitaka branch of OpenStack-Ansible 

* Run `scripts/boostrap-ansible.sh`

* Run `scripts/bootstraip-aio.sh`

* Edit `/etc/openstack_deploy/user_variables.yml` and change the
  `affinity`_ for `galera_container` and `rabbit_mq_container` to `3`

  This works around https://bugs.launchpad.net/openstack-ansible/+bug/1595143

* Run `scripts/run-playbooks.sh`

This will create the base environment where Mitaka is installed.

.. _Use an AIO instance: http://docs.openstack.org/developer/openstack-ansible/developer-docs/quickstart-aio.html#rebooting-an-aio

.. _affinity: https://github.com/openstack/openstack-ansible/blob/eol-kilo/etc/openstack_deploy/openstack_user_config.yml.aio#L71-L77

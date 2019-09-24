from __future__ import absolute_import

import sys

from ..api import BaseWebSocketHandler
from ..app import Flower


class EventsApiHandler(BaseWebSocketHandler):
    def open(self, task_id=None):
        BaseWebSocketHandler.open(self)
        self.task_id = task_id
    
    @classmethod
    def send_message(cls, event):
        for l in cls.listeners:
            if not l.task_id or l.task_id == event['uuid']:
                event["actives"] = cls.get_events_state()
                l.write_message(event)
    
    @classmethod
    def get_events_state(cls):
        state = Flower.events.state
        # workers = OrderedDict()
        actives = []
        for name, worker in sorted(state.workers.items()):
            counter = state.counter[name]
            started = counter.get('task-started', 0)
            processed = counter.get('task-received', 0)
            failed = counter.get('task-failed', 0)
            succeeded = counter.get('task-succeeded', 0)
            retried = counter.get('task-retried', 0)
            active = started - succeeded - failed - retried
            # if active < 0:
            #     active = 'N/A'
            actives.append(active)
            #workers[name] = dict(
            #    name=name,
            #    status=worker.alive,
            #    active=active,
            #    processed=processed,
            #    failed=failed,
            #    succeeded=succeeded,
            #    retried=retried,
            #    loadavg=getattr(worker, 'loadavg', None))
        return sum(actives)
        


EVENTS = ('task-sent', 'task-received', 'task-started', 'task-succeeded',
          'task-failed', 'task-revoked', 'task-retried', 'task-custom')


def getClassName(eventname):
    return ''.join(map(lambda x: x[0].upper() + x[1:], eventname.split('-')))


# Dynamically generates handler classes
thismodule = sys.modules[__name__]
for event in EVENTS:
    classname = getClassName(event)
    setattr(thismodule, classname,
            type(classname, (EventsApiHandler, ), {'listeners': []}))


__all__ = list(map(getClassName, EVENTS))
__all__.append(getClassName)

#!/usr/bin/env python
from cortexutils.responder import Responder

class ReporterResponder(Responder):
    def __init__(self):
        Responder.__init__(self)

    def _simpletemplate(self, case_id, title):
        return '# #{}: {}'.format(case_id, title)

    def run(self):


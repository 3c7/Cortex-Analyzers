#!/usr/bin/env python
import pypandoc
import tempfile
import base64
import io
from cortexutils.responder import Responder


class ReporterResponder(Responder):
    def __init__(self):
        Responder.__init__(self)

    def _simpletemplate(self, case_id, title):
        return '# #{}: {}'.format(case_id, title)

    def run(self):
        case_id = self.get_param('caseId')
        title = self.get_param('title')

        fd, path = tempfile.mkstemp()
        pypandoc.convert_text(self._simpletemplate(case_id, title), 'pdf', format='md', outputfile=path)
        fd.close()

        with io.open(path, 'rb') as fd:
            b64 = base64.encodebytes(fd.read())

        self.report({
            'report': base64
        })

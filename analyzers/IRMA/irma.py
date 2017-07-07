#!/usr/bin/env python
# encoding: utf-8

import time
import hashlib
import requests
import urlparse
from requests.auth import HTTPBasicAuth

from cortexutils.analyzer import Analyzer


class IRMAAnalyzer(Analyzer):

    def __init__(self):
        Analyzer.__init__(self)
        self.service = self.get_param('config.service', None, 'Service parameter is missing')
        self.url = self.get_param('config.url', None, 'IRMA URL parameter is missing')
        self.timeout = self.get_param('config.timeout', 60)
        self.scan = self.get_param('config.scan', 1)
        self.force = self.get_param('config.force', 1)
        self.verify = self.get_param('config.verify', True)
        self.time_start = time.time()
        self.username = self.get_param('config.username', None)
        self.password = self.get_param('config.password', None)

        if self.username is None:
            self.auth = None
        else:
            self.auth = HTTPBasicAuth(self.username, self.password)

    def summary(self, raw):
        total = 0
        findings = 0
        if 'probe_results' in raw:
            antiviruses = filter(lambda analysis: analysis["type"] == 'antivirus', raw["probe_results"])
            total = len(antiviruses)

            malicious = filter(lambda analysis: analysis["status"] == 1, antiviruses)
            findings = len(malicious)

        return {
            'taxonomies': [self.build_taxonomy(
                'safe' if findings == 0 else 'malicious',
                'IRMA',
                'Scan',
                '0' if total == 0 else '{}/{}'.format(findings, total)
            )]
        }

        return result

    """Gets antivirus signatures from IRMA for various results.
       Currently obtains IRMA results for the target sample.
       """
    # IRMA statuses https://github.com/quarkslab/irma-cli/blob/master/irma/apiclient.py
    IRMA_FINISHED_STATUS = 50

    def _request_json(self, url, **kwargs):
        """Wrapper around doing a request and parsing its JSON output."""
        try:
            r = requests.get(url, timeout=self.timeout, verify=self.verify, auth=self.auth, **kwargs)
            return r.json() if r.status_code == 200 else {}
        except (requests.ConnectionError, ValueError) as e:
            self.unexpectedError(e)

    def _post_json(self, url, **kwargs):
        """Wrapper around doing a post and parsing its JSON output."""
        try:
            r = requests.post(url, timeout=self.timeout, verify=self.verify, auth=self.auth, **kwargs)
            return r.json() if r.status_code == 200 else {}
        except (requests.ConnectionError, ValueError) as e:
            self.unexpectedError(e)

    def _scan_file(self, filepath, force):
        # Initialize scan in IRMA.
        init = self._post_json(urlparse.urljoin(self.url, "/api/v1.1/scans"))

        # Post file for scanning.
        files = {
            "files": open(filepath, "rb"),
        }
        url = urlparse.urljoin(
            self.url, "/api/v1.1/scans/%s/files" % init.get("id")
        )
        self._post_json(url, files=files, )

        # launch posted file scan
        params = {
            "force": force,
        }
        url = urlparse.urljoin(
            self.url, "/api/v1.1/scans/%s/launch" % init.get("id")
        )
        requests.post(url, json=params, verify=self.verify, auth=self.auth)

        result = None

        while result is None or result.get(
                "status") != self.IRMA_FINISHED_STATUS or time.time() < self.time_start + self.timeout:
            url = urlparse.urljoin(
                self.url, "/api/v1.1/scans/%s" % init.get("id")
            )
            result = self._request_json(url)
            time.sleep(10)

        return

    def _get_results(self, sha256):
        # Fetch list of scan IDs.
        results = self._request_json(
            urlparse.urljoin(self.url, "/api/v1.1/files/%s" % sha256)
        )

        if not results.get("items"):
            return

        result_id = results["items"][-1]["result_id"]
        return self._request_json(
            urlparse.urljoin(self.url, "/api/v1.1/results/%s" % result_id)
        )

    def run(self):
        if self.service == 'scan':
            if self.data_type == 'file':
                filename = self.get_param('attachment.name', 'noname.ext')
                filepath = self.get_param('file', None, 'File is missing')
                hashes = self.get_param('attachment.hashes', None)
                if hashes is None:
                    hash = hashlib.sha256(open(filepath, 'r').read()).hexdigest()
                else:
                    # find SHA256 hash
                    hash = next(h for h in hashes if len(h) == 64)

                # Fetch the result from IRMA using the file's hash
                results = self._get_results(hash)

                if not self.force and not self.scan and not results:
                    # Not existing result is found, force is false, scan is false
                    #self.error('No report found for this file')
                    return {}
                elif self.force or (not results and self.scan):
                    self._scan_file(filepath, self.force)
                    results = self._get_results(hash) or {}

                """ FIXME! could use a proper fix here
                        that probably needs changes on IRMA side aswell
                        --
                        related to  https://github.com/elastic/elasticsearch/issues/15377
                        entropy value is sometimes 0 and sometimes like  0.10191042566270775
                        other issue is that results type changes between string and object :/
                        """
                for idx, result in enumerate(results["probe_results"]):
                    if result["name"] == "PE Static Analyzer":
                        results["probe_results"][idx]["results"] = None

                self.report(results)

            else:
                self.error('Invalid data type')
        else:
            self.error('Invalid service')


if __name__ == '__main__':
    IRMAAnalyzer().run()

import requests
import joblib
import csv


class TorBlutmagieClient:
    """Simple client to query torstatus.blutmagie.de for exit nodes.

    The client will download http://torstatus.blutmagie.de/query_export.php/Tor_query_EXPORT.csv
    and check if a specified IP address, FQDN or domain is present in it.
    It will cache the response for `cache_duration` seconds to avoid
    too much latency.

    :param cache_size: Size of cache reserved in bytes.
                       Ignored if `cache_size` is 0.
    :param cache_root: Path where to store the cached file
                       downloaded from torstatus.blutmagie.de
    :type cache_size: int
    :type cache_root: str
    """

    def __init__(self, cache_size=2048, cache_root='/tmp/cortex/tor_project'):
        self.session = requests.Session()
        if cache_size > 0:
            self.cache = joblib.Memory(cachedir=cache_root, verbose=0, bytes_limit=cache_size)
        self.url = 'http://torstatus.blutmagie.de/query_export.php/Tor_query_EXPORT.csv'
        self.search_tor_node = self._get_proper_function()

    def _get_raw_data(self):
        return self.session.get(self.url).text

    def _get_data(self):
        return csv.DictReader(self._get_raw_data().splitlines(), delimiter=',')

    def _extract_fields(self, line):
        return {
            'hostname': line['Hostname'],
            'name': line['Router Name'],
            'country_code': line['Country Code'],
            'ip': line['IP Address'],
            'as_name': line['ASName'],
            'as_number': line['ASNumber']
        }

    def _get_node_from_domain(self, domain):
        results = []
        for line in self._get_data():
            if domain.lower() in line['Hostname'].lower():
                results.append(self._extract_fields(line))
        return results

    def _get_node_from_fqdn(self, fqdn):
        results = []
        for line in self._get_data():
            if fqdn.lower() == line['Hostname'].lower():
                results.append(self._extract_fields(line))
                break
        return results

    def _get_node_from_ip(self, ip):
        results = []
        for line in self._get_data():
            if ip == line['IP Address']:
                results.append(self._extract_fields(line))
                break
        return results

    def _get_proper_function(self):
        if self.cache:
            @self.cache.cache
            def search_tor_node(data_type, data):
                """Lookup an artifact to check if it is a known tor exit node.

                :param data_type: The artifact type. Must be one of 'ip', 'fqdn'
                                  or 'domain'
                :param data: The artifact to lookup
                :type data_type: str
                :type data: str
                :return: Data relative to the tor node. If the looked-up artifact is
                         related to a tor exit node it will contain a `nodes` array.
                         That array will contains a list of nodes containing the
                         following keys:
                         - name: name given to the router
                         - ip: their IP address
                         - hostname: Hostname of the router
                         - country_code: ISO2 code of the country hosting the router
                         - as_name: ASName registering the router
                         - as_number: ASNumber registering the router
                          Otherwise, `nodes` will be empty.
                :rtype: list
                """
                results = []
                if data_type == 'ip':
                    results = self._get_node_from_ip(data)
                elif data_type == 'fqdn':
                    results = self._get_node_from_fqdn(data)
                elif data_type == 'domain':
                    results = self._get_node_from_domain(data)
                else:
                    pass
                return {"nodes": results}
        else:
            def search_tor_node(data_type, data):
                """Lookup an artifact to check if it is a known tor exit node.

                :param data_type: The artifact type. Must be one of 'ip', 'fqdn'
                                  or 'domain'
                :param data: The artifact to lookup
                :type data_type: str
                :type data: str
                :return: Data relative to the tor node. If the looked-up artifact is
                         related to a tor exit node it will contain a `nodes` array.
                         That array will contains a list of nodes containing the
                         following keys:
                         - name: name given to the router
                         - ip: their IP address
                         - hostname: Hostname of the router
                         - country_code: ISO2 code of the country hosting the router
                         - as_name: ASName registering the router
                         - as_number: ASNumber registering the router
                          Otherwise, `nodes` will be empty.
                :rtype: list
                """
                results = []
                if data_type == 'ip':
                    results = self._get_node_from_ip(data)
                elif data_type == 'fqdn':
                    results = self._get_node_from_fqdn(data)
                elif data_type == 'domain':
                    results = self._get_node_from_domain(data)
                else:
                    pass
                return {"nodes": results}

        return search_tor_node

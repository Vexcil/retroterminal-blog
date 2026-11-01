import base64
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from types import SimpleNamespace
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import tabs_access as access

class AccessTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.settings={'username':'guest','session_key':'11'*32,'salt':'22'*16,'password_hash':'unused','home_ips':['203.0.113.7'],'home_networks':[], 'trusted_proxies':['100.93.239.87'],'tailnet_networks':['100.64.0.0/10']}
        self.path=Path(self.tmp.name)/'access.json'; self.path.write_text(json.dumps(self.settings))
        self.old=os.environ.get('TABS_ACCESS_CONFIG'); os.environ['TABS_ACCESS_CONFIG']=str(self.path)
    def tearDown(self):
        if self.old is None: os.environ.pop('TABS_ACCESS_CONFIG',None)
        else: os.environ['TABS_ACCESS_CONFIG']=self.old
        self.tmp.cleanup()
    def handler(self,peer='198.51.100.9',headers=None):
        return SimpleNamespace(client_address=(peer,123),headers=headers or {})
    def test_default_requires_login(self):
        self.assertFalse(access.authorized(self.handler()))
    def test_home_and_tailnet(self):
        self.assertTrue(access.authorized(self.handler('203.0.113.7')))
        self.assertTrue(access.authorized(self.handler('100.70.1.2')))
    def test_public_proxy_is_not_a_tailnet_client(self):
        self.assertFalse(access.authorized(self.handler('100.93.239.87')))
        self.assertFalse(access.authorized(self.handler('100.93.239.87',{'X-Real-IP':'198.51.100.9'})))
        self.assertTrue(access.authorized(self.handler('100.93.239.87',{'X-Real-IP':'203.0.113.7'})))
    def test_forwarding_headers_cannot_grant_public_access(self):
        self.assertFalse(access.authorized(self.handler(headers={'X-Real-IP':'203.0.113.7','Tailscale-User-Login':'forged'})))
    def test_signed_session_tamper_and_expiry(self):
        def cookie(expiry):
            body=base64.urlsafe_b64encode(('guest|'+str(expiry)).encode()).decode().rstrip('=')
            return body+'.'+access.signature(body,self.settings)
        token=cookie(int(time.time())+100)
        self.assertTrue(access.authorized(self.handler(headers={'Cookie':'rt_tabs_session='+token})))
        self.assertFalse(access.authorized(self.handler(headers={'Cookie':'rt_tabs_session='+token+'x'})))
        self.assertFalse(access.authorized(self.handler(headers={'Cookie':'rt_tabs_session='+cookie(1)})))
    def test_missing_config_fails_closed(self):
        self.path.unlink(); self.assertFalse(access.authorized(self.handler('100.70.1.2')))
if __name__=='__main__': unittest.main()

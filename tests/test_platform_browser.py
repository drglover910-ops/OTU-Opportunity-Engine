import os,tempfile,unittest
from unittest.mock import patch
from platform_browser import PlatformBrowser,public_url
from engine import Engine
class Platforms(unittest.TestCase):
 def test_private_and_credential_urls_are_blocked(self):
  for url in ('http://example.com','https://user:pass@example.com','https://127.0.0.1','https://169.254.169.254'):
   with self.assertRaises(ValueError):public_url(url)
 def test_original_platforms_and_profile_backup(self):
  e=Engine(tempfile.mkdtemp());self.assertTrue({'contra','peopleperhour','upwork','indeed','linkedin'}.issubset({p['id'] for p in e.platforms()}))
  self.assertFalse(next(p for p in e.platforms() if p['id']=='contra')['automatic_discovery'])
  with patch.object(e,'platform_profile',return_value={}):e.save_platform_profile({'platform':'contra','fields':{'full_name':'Example Owner','email':'owner@example.com','password':'DO NOT STORE'}})
  clone=Engine(tempfile.mkdtemp());clone.restore(e.backup());profile=clone.platform_profile('contra')
  self.assertEqual(profile['full_name'],'Example Owner');self.assertNotIn('password',profile)
 def test_fill_requires_review_and_references_cannot_be_uploaded(self):
  e=Engine(tempfile.mkdtemp())
  with self.assertRaises(ValueError):e.browser_action({'action':'fill','platform':'contra'})
  with self.assertRaises(ValueError):e.browser_action({'action':'upload','platform':'contra','document_id':99,'confirmed':True})

if __name__=='__main__':unittest.main()

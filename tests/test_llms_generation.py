"""LLM examples remain standalone programs after project-template migration."""

from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from gen_llms import project_source, render_corpora


class LLMGenerationTests(unittest.TestCase):
    def test_project_export_includes_helpers_and_excludes_assets(self):
        source = project_source({'entry': 'main.xu', 'files': {
            'pricing.xu': '@main\nfn total() int { << 42 }\n',
            'main.xu': '@main\nfn main() int { println(total())\n << 0 }\n',
            'notes/README.md': 'This is not Xu source.',
            'assets/main.xu': '@main\nfn unsupported_subpackage() {}\n',
            'xu.xun': 'module: checkout',
        }})
        self.assertEqual(source.count('@main'), 1)
        self.assertIn('fn total()', source)
        self.assertIn('println(total())', source)
        self.assertNotIn('This is not Xu source', source)
        self.assertNotIn('unsupported_subpackage', source)
        self.assertNotIn('module: checkout', source)

    def test_published_corpora_include_complete_worker_and_counter_programs(self):
        corpora = render_corpora(ROOT, (ROOT / 'VERSION').read_text().strip())
        blocks = re.findall(r'```xu\n(.*?)\n```', corpora['llms-full.txt'], re.S)
        worker = next(block for block in blocks if 'xu worker(1, results)' in block)
        counter = next(block for block in blocks if 'counter.inc()' in block)
        self.assertIn('fn worker(', worker)
        self.assertIn('struct Counter', counter)
        for block in (worker, counter):
            self.assertEqual(block.count('@main'), 1)
            self.assertIn('fn main()', block)

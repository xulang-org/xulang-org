#!/usr/bin/env python3
"""Run function-local API examples against the website's selected native SDK."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xu', required=True, type=Path, help='Selected SDK compiler executable')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    compiler = args.xu.resolve()
    version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    reported = subprocess.run([str(compiler), '--version'], capture_output=True, text=True, check=True)
    if not re.search(r'(?<![\w.])v?' + re.escape(version) + r'(?![\w.-])', reported.stdout):
        parser.error(f'compiler must match VERSION {version}: {reported.stdout.strip()}')
    entries = json.loads((root / 'templates/api-contracts.json').read_text(encoding='utf-8'))
    count = 0
    with tempfile.TemporaryDirectory(prefix='xu-api-examples-') as temporary:
        for entry in entries:
            examples = entry['en'].get('examples', [])
            translated = entry['zh'].get('examples', [])
            if [(e['code'], e.get('output')) for e in examples] != [(e['code'], e.get('output')) for e in translated]:
                raise ValueError(f'{entry["package"]}.{entry["name"]}: translated examples differ')
            for index, example in enumerate(examples):
                project = Path(temporary) / str(count)
                project.mkdir()
                (project / 'xu.xun').write_text(f'module: api/example\nversion: !ver 0.1.0\nxu: !ver {version}\n', encoding='utf-8')
                source = project / 'main.xu'
                source.write_text(example['code'], encoding='utf-8')
                result = subprocess.run([str(compiler), 'run', str(source)], cwd=project,
                                        capture_output=True, text=True, encoding='utf-8', timeout=120)
                label = '.'.join(filter(None, [entry['package'], entry.get('receiver'), entry['name'], str(index + 1)]))
                if result.returncode:
                    raise RuntimeError(f'{label}: native execution failed\n{result.stderr}\n{result.stdout}')
                if 'output' in example and result.stdout != example['output']:
                    raise AssertionError(f'{label}: expected {example["output"]!r}, got {result.stdout!r}')
                print(f'PASS {label}')
                count += 1
    print(f'{count} bilingual API examples passed with Xu {version}')


if __name__ == '__main__':
    main()

"""Failure outcomes never carry measurements or participate in ranking."""

FAILURES = {
    'compile_failed': ('Compile failed', '编译失败'),
    'run_failed': ('Run failed', '运行失败'),
    'stdout_mismatch': ('Wrong output', '输出错误'),
    'measurement_failed': ('Measurement failed', '测量失败'),
}
METRICS = ('wall_ms', 'best_ms', 'rss_mib', 'cpu_ms', 'bytes')


def validate_failure(result: dict):
    status = result.get('status', 'ok')
    if status == 'ok':
        return
    if status not in FAILURES or not isinstance(result.get('error'), str) or not result['error'].strip():
        raise ValueError('invalid benchmark failure evidence')
    if any(result.get(key) is not None for key in METRICS):
        raise ValueError('failed benchmark contains measurements')

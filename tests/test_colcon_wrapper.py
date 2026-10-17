"""Behavioral checks for package selection, task sequencing, and test status."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    'colcon_wrapper', Path(__file__).resolve().parents[1] / 'scripts' / 'colcon_wrapper.py')
wrapper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wrapper)


class ColconWrapperTests(unittest.TestCase):
    def invoke(self, args, statuses):
        results = [subprocess.CompletedProcess([], status) for status in statuses]
        with patch.object(sys, 'argv', ['colcon_wrapper.py', *args]), \
                patch.object(wrapper, 'load_env_file'), \
                patch.dict(os.environ, {'PIXI_PARALLEL_WORKERS': ''}), \
                patch.object(wrapper.subprocess, 'run', side_effect=results) as run:
            status = wrapper.main()
        return status, [call.args[0] for call in run.call_args_list]

    def test_build_selects_multiple_packages_and_dependencies(self):
        status, commands = self.invoke(['build', 'cuda_buffer', 'cuda_buffer_backend'], [0])
        self.assertEqual(status, 0)
        self.assertEqual(commands[0][-3:],
                         ['--packages-up-to', 'cuda_buffer', 'cuda_buffer_backend'])

    def test_build_failure_prevents_test_execution(self):
        status, commands = self.invoke(['test', '--build-first', 'a', 'b'], [7])
        self.assertEqual(status, 7)
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0][1], 'build')

    def test_tests_preserve_failure_and_still_show_summary(self):
        status, commands = self.invoke(['test', '--build-first', 'a', 'b'], [0, 9, 1])
        self.assertEqual(status, 9)
        self.assertEqual(commands[0][-3:], ['--packages-up-to', 'a', 'b'])
        self.assertEqual(commands[1][-3:], ['--packages-select', 'a', 'b'])
        self.assertIn('--return-code-on-test-failure', commands[1])
        self.assertEqual(commands[2], ['colcon', 'test-result', '--verbose'])

    def test_regex_is_one_argument_with_packages_after_option(self):
        status, commands = self.invoke(
            ['test', 'a', '--tests-to-run', 'alloc|ipc with spaces', 'b'], [0, 0])
        self.assertEqual(status, 0)
        self.assertEqual(commands[0][-6:],
                         ['--packages-select', 'a', 'b', '--ctest-args', '-R',
                          'alloc|ipc with spaces'])

    def test_up_to_and_worker_limit_are_preserved(self):
        command = wrapper.colcon_command('test-up-to', ['a', 'b'], '2', 'foo|bar')
        self.assertEqual(command[-8:],
                         ['--packages-up-to', 'a', 'b', '--parallel-workers', '2',
                          '--ctest-args', '-R', 'foo|bar'])
        self.assertIn('--return-code-on-test-failure', command)

    def test_old_workspace_results_do_not_override_successful_test_status(self):
        status, _ = self.invoke(['test', 'a'], [0, 1])
        self.assertEqual(status, 0)

    def test_omitting_packages_tests_all(self):
        status, commands = self.invoke(['test'], [0, 0])
        self.assertEqual(status, 0)
        self.assertNotIn('--packages-select', commands[0])

    def test_compile_commands_still_uses_compdb_after_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path.cwd()
            os.chdir(tmp)
            try:
                status, commands = self.invoke(['compile-commands', 'a', 'b'], [0, 0])
                self.assertTrue(Path('compile_commands.json').is_file())
            finally:
                os.chdir(original)
        self.assertEqual(status, 0)
        self.assertEqual(commands[0][-3:], ['--packages-up-to', 'a', 'b'])
        self.assertEqual(commands[1], ['compdb', '-p', 'build', 'list'])


if __name__ == '__main__':
    unittest.main()

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import importlib.util

spec = importlib.util.spec_from_file_location("llm_client", "practice01/llm_client.py")
llm_client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llm_client)

class TestLoadEnv(unittest.TestCase):
    def test_tc001_normal_load(self):
        config = llm_client.load_env('practice01/test_env/.env')
        self.assertEqual(config['LLM_BASE_URL'], 'https://api.example.com/v1')
        self.assertEqual(config['LLM_MODEL'], 'gpt-3.5-turbo')
        self.assertEqual(config['LLM_API_KEY'], 'sk-test-key-12345')
    
    def test_tc002_file_not_found(self):
        with self.assertRaises(FileNotFoundError) as context:
            llm_client.load_env('practice01/test_env/.env.notexist')
        self.assertIn('配置文件不存在', str(context.exception))
    
    def test_tc003_missing_required_param(self):
        with self.assertRaises(ValueError) as context:
            llm_client.load_env('practice01/test_env/.env.missing_key')
        self.assertIn('缺少必需参数', str(context.exception))
    
    def test_tc004_comment_handling(self):
        config = llm_client.load_env('practice01/test_env/.env')
        self.assertNotIn('#', str(config))
        self.assertEqual(len(config), 3)

class TestCalculateStats(unittest.TestCase):
    def test_tc006_normal_calculation(self):
        response_data = {
            "model": "gpt-3.5-turbo",
            "usage": {
                "prompt_tokens": 15,
                "completion_tokens": 42,
                "total_tokens": 57
            }
        }
        stats = llm_client.calculate_stats(response_data, 2.0)
        self.assertEqual(stats['model'], 'gpt-3.5-turbo')
        self.assertEqual(stats['prompt_tokens'], 15)
        self.assertEqual(stats['completion_tokens'], 42)
        self.assertEqual(stats['total_tokens'], 57)
        self.assertAlmostEqual(stats['tokens_per_second'], 28.5, places=2)
    
    def test_tc007_zero_elapsed_time(self):
        response_data = {
            "model": "gpt-3.5-turbo",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }
        stats = llm_client.calculate_stats(response_data, 0)
        self.assertEqual(stats['tokens_per_second'], 0)
    
    def test_tc008_large_token_calculation(self):
        response_data = {
            "model": "test-model",
            "usage": {"prompt_tokens": 500, "completion_tokens": 500, "total_tokens": 1000}
        }
        stats = llm_client.calculate_stats(response_data, 10.0)
        self.assertEqual(stats['tokens_per_second'], 100.0)
    
    def test_tc009_decimal_elapsed_time(self):
        response_data = {
            "model": "test-model",
            "usage": {"prompt_tokens": 10, "completion_tokens": 40, "total_tokens": 50}
        }
        stats = llm_client.calculate_stats(response_data, 2.35)
        self.assertAlmostEqual(stats['tokens_per_second'], 21.28, places=2)

class TestPrintResults(unittest.TestCase):
    def test_tc010_normal_output(self):
        stats = {
            'model': 'gpt-3.5-turbo',
            'prompt_tokens': 15,
            'completion_tokens': 42,
            'total_tokens': 57,
            'elapsed_time': 2.30,
            'tokens_per_second': 24.78
        }
        with patch('builtins.print') as mock_print:
            llm_client.print_results(stats, "Hello, how are you?")
            output = '\n'.join([str(call[0][0]) for call in mock_print.call_args_list])
            self.assertIn("模型: gpt-3.5-turbo", output)
            self.assertIn("总 Token: 57", output)
            self.assertIn("Hello, how are you?", output)
    
    def test_tc011_empty_response(self):
        stats = {
            'model': 'gpt-3.5-turbo',
            'prompt_tokens': 10,
            'completion_tokens': 0,
            'total_tokens': 10,
            'elapsed_time': 1.0,
            'tokens_per_second': 10.0
        }
        with patch('builtins.print') as mock_print:
            llm_client.print_results(stats, "")
            output = '\n'.join([str(call[0][0]) for call in mock_print.call_args_list])
            self.assertIn("生成 Token: 0", output)

if __name__ == '__main__':
    print("=" * 50)
    print("LLM API 客户端工具 - 单元测试")
    print("=" * 50)
    print()
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    print("[1] 测试 load_env() 函数")
    suite.addTests(loader.loadTestsFromTestCase(TestLoadEnv))
    
    print("[2] 测试 calculate_stats() 函数")
    suite.addTests(loader.loadTestsFromTestCase(TestCalculateStats))
    
    print("[3] 测试 print_results() 函数")
    suite.addTests(loader.loadTestsFromTestCase(TestPrintResults))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 50)
    if result.wasSuccessful():
        print("所有测试通过!")
    else:
        print(f"测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
    print("=" * 50)

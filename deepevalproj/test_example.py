import deepeval
from deepeval import assert_test
from deepeval.metrics import HallucinationMetric
from deepeval.test_case import LLMTestCase
from deepeval.evaluate import execute_test

input = "What if these shoes don't fit?"
context = ["All customers are eligible for a 30 day full refund at no extra cost."]

actual_output1 = "We offer a 30-day full refund at no extra cost."  # Replace this with the actual output of your LLM application
actual_output2 = "You can refund in 30-day at no extra cost."


hallucination_metric = HallucinationMetric(minimum_score=0.7)
test_cases = [
        LLMTestCase(input=input, actual_output=actual_output1, context=context),
        LLMTestCase(input=input, actual_output=actual_output2, context=context)
        ]


for test_case in test_cases:
    if not isinstance(test_case, LLMTestCase):
        raise TypeError("'test_case' must be an instance of 'LLMTestCase'.")


test_result = execute_test(test_cases, [hallucination_metric], True)[0]

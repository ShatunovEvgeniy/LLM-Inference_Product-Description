from dataclasses import dataclass
from typing import List
import random

@dataclass
class SampleGenerationResult():
  description: str
  latency: float
  total_score: float
  detailed_score: dict

@dataclass
class FullGenerationResult():
  throughput: float
  latency_avg: float
  total_score_avg: float
  outputs: List[SampleGenerationResult]

def print_compact_stats(results: FullGenerationResult) -> None:
    """
    Компактная версия вывода статистики.
    """
    print(" СТАТИСТИКА ГЕНЕРАЦИИ")
    print(f"   Throughput: {results.throughput:.2f} req/sec")
    print(f"   Avg Latency: {results.latency_avg:.3f} sec")
    print(f"   Samples: {len(results.outputs)}")
    print(f"   Avg Score: {sum(s.total_score for s in results.outputs)/len(results.outputs):.3f}")

    # Добавляем случайные описания в компактную версию
    if len(results.outputs) >= 3:
        print("\n 3 случайных описания:")
        random_indices = random.sample(range(len(results.outputs)), min(3, len(results.outputs)))
        for i, idx in enumerate(random_indices, 1):
            desc = results.outputs[idx].description
            print(f"   {i}. {desc}")
#!/usr/bin/env python3
"""
最適化結果分析ツール

各シナリオで10回最適化を実行し、以下を分析:
1. 各栄養素の平均達成率
2. 料理出現回数ランキング
3. 上位3料理の栄養データ

使い方:
  # 全シナリオを実行
  python tools/analyze_optimization.py

  # 特定シナリオのみ
  python tools/analyze_optimization.py --scenario default

  # 実行回数を変更
  python tools/analyze_optimization.py --runs 5
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import requests

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

API_BASE = "http://localhost:8000/api/v1"

# シナリオ定義
SCENARIOS = {
    "default": {
        "name": "デフォルト（バランス重視）",
        "params": {
            "days": 3,
            "people": 1,
        }
    },
    "diet": {
        "name": "ダイエット（低カロリー）",
        "params": {
            "days": 3,
            "people": 1,
            "volume_level": "small",
        }
    },
    "high_protein": {
        "name": "高タンパク（筋トレ向け）",
        "params": {
            "days": 3,
            "people": 1,
            "target": {
                "protein_min": 80,
                "protein_max": 150,
            }
        }
    },
    "low_sodium": {
        "name": "塩分制限（高血圧対策）",
        "params": {
            "days": 3,
            "people": 1,
            "target": {
                "sodium_max": 2000,
            }
        }
    },
    "single_batch": {
        "name": "一人暮らし＋作り置き重視",
        "params": {
            "days": 5,
            "people": 1,
            "household_type": "single",
            "batch_cooking_level": "large",
        }
    },
    "family_variety": {
        "name": "家族＋多様性重視",
        "params": {
            "days": 3,
            "people": 4,
            "household_type": "family",
            "variety_level": "large",
        }
    },
    "no_egg": {
        "name": "卵アレルギー除外",
        "params": {
            "days": 3,
            "people": 1,
            "excluded_allergens": ["卵"],
        }
    },
    "no_dairy": {
        "name": "乳製品除外",
        "params": {
            "days": 3,
            "people": 1,
            "excluded_allergens": ["乳"],
        }
    },
    "pescatarian": {
        "name": "ペスカタリアン（肉なし）",
        "params": {
            "days": 3,
            "people": 1,
            "excluded_allergens": ["牛肉", "豚肉", "鶏肉"],
        }
    },
    "gluten_free": {
        "name": "グルテンフリー（小麦除外）",
        "params": {
            "days": 3,
            "people": 1,
            "excluded_allergens": ["小麦"],
        }
    },
}

# 栄養素の日本語名
NUTRIENT_NAMES = {
    "calories": "カロリー",
    "protein": "タンパク質",
    "fat": "脂質",
    "carbohydrate": "炭水化物",
    "fiber": "食物繊維",
    "sodium": "ナトリウム",
    "potassium": "カリウム",
    "calcium": "カルシウム",
    "magnesium": "マグネシウム",
    "iron": "鉄",
    "zinc": "亜鉛",
    "vitamin_a": "ビタミンA",
    "vitamin_d": "ビタミンD",
    "vitamin_e": "ビタミンE",
    "vitamin_k": "ビタミンK",
    "vitamin_b1": "ビタミンB1",
    "vitamin_b2": "ビタミンB2",
    "vitamin_b6": "ビタミンB6",
    "vitamin_b12": "ビタミンB12",
    "niacin": "ナイアシン",
    "pantothenic_acid": "パントテン酸",
    "biotin": "ビオチン",
    "folate": "葉酸",
    "vitamin_c": "ビタミンC",
}


def call_optimize_api(params: dict) -> dict | None:
    """最適化APIを呼び出し"""
    try:
        response = requests.post(
            f"{API_BASE}/optimize/multi-day",
            json=params,
            timeout=60,
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"  Exception: {e}")
        return None


def extract_dishes(result: dict) -> list[str]:
    """結果から料理名を抽出"""
    dishes = []
    for daily in result.get("daily_plans", []):
        for meal in ["breakfast", "lunch", "dinner"]:
            for portion in daily.get(meal, []):
                dish = portion.get("dish", {})
                name = dish.get("name")
                if name:
                    dishes.append(name)
    return dishes


def extract_dish_nutrients(result: dict) -> dict[str, dict]:
    """結果から料理ごとの栄養素を抽出"""
    dish_nutrients = {}
    for daily in result.get("daily_plans", []):
        for meal in ["breakfast", "lunch", "dinner"]:
            for portion in daily.get(meal, []):
                dish = portion.get("dish", {})
                name = dish.get("name")
                if name and name not in dish_nutrients:
                    dish_nutrients[name] = {
                        "category": dish.get("category", ""),
                        "calories": dish.get("calories", 0),
                        "protein": dish.get("protein", 0),
                        "fat": dish.get("fat", 0),
                        "carbohydrate": dish.get("carbohydrate", 0),
                        "fiber": dish.get("fiber", 0),
                        "sodium": dish.get("sodium", 0),
                        "potassium": dish.get("potassium", 0),
                        "calcium": dish.get("calcium", 0),
                        "magnesium": dish.get("magnesium", 0),
                        "iron": dish.get("iron", 0),
                        "zinc": dish.get("zinc", 0),
                        "vitamin_a": dish.get("vitamin_a", 0),
                        "vitamin_d": dish.get("vitamin_d", 0),
                        "vitamin_e": dish.get("vitamin_e", 0),
                        "vitamin_k": dish.get("vitamin_k", 0),
                        "vitamin_b1": dish.get("vitamin_b1", 0),
                        "vitamin_b2": dish.get("vitamin_b2", 0),
                        "vitamin_b6": dish.get("vitamin_b6", 0),
                        "vitamin_b12": dish.get("vitamin_b12", 0),
                        "niacin": dish.get("niacin", 0),
                        "pantothenic_acid": dish.get("pantothenic_acid", 0),
                        "biotin": dish.get("biotin", 0),
                        "folate": dish.get("folate", 0),
                        "vitamin_c": dish.get("vitamin_c", 0),
                    }
    return dish_nutrients


def run_scenario(scenario_key: str, scenario: dict, runs: int) -> dict:
    """シナリオを複数回実行して結果を集計"""
    print(f"\n{'='*60}")
    print(f"シナリオ: {scenario['name']}")
    print(f"{'='*60}")

    all_achievements = defaultdict(list)
    all_dishes = []
    all_dish_nutrients = {}
    success_count = 0

    for i in range(runs):
        print(f"  実行 {i+1}/{runs}... ", end="", flush=True)
        result = call_optimize_api(scenario["params"])

        if result:
            success_count += 1
            print("OK")

            # 栄養達成率を収集
            achievement = result.get("overall_achievement", {})
            for nutrient, rate in achievement.items():
                all_achievements[nutrient].append(rate)

            # 料理を収集
            dishes = extract_dishes(result)
            all_dishes.extend(dishes)

            # 料理の栄養データを収集
            nutrients = extract_dish_nutrients(result)
            all_dish_nutrients.update(nutrients)
        else:
            print("FAILED")

    if success_count == 0:
        print("  全ての実行が失敗しました")
        return {}

    # 栄養素平均達成率を計算
    avg_achievements = {}
    for nutrient, rates in all_achievements.items():
        avg_achievements[nutrient] = sum(rates) / len(rates)

    # 料理出現回数をカウント
    dish_counts = Counter(all_dishes)

    return {
        "scenario_name": scenario["name"],
        "success_count": success_count,
        "total_runs": runs,
        "avg_achievements": avg_achievements,
        "dish_counts": dish_counts,
        "dish_nutrients": all_dish_nutrients,
    }


def print_results(results: dict):
    """結果を表示"""
    if not results:
        return

    print(f"\n--- 栄養素平均達成率 ---")
    avg = results["avg_achievements"]

    # 達成率でソート（低い順）
    sorted_nutrients = sorted(avg.items(), key=lambda x: x[1])

    for nutrient, rate in sorted_nutrients:
        name = NUTRIENT_NAMES.get(nutrient, nutrient)
        status = "✓" if rate >= 100 else "✗"
        bar_len = min(int(rate / 5), 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"  {status} {name:12s} {bar} {rate:6.1f}%")

    # 不足栄養素をハイライト
    deficient = [(n, r) for n, r in sorted_nutrients if r < 100]
    if deficient:
        print(f"\n  ⚠️  不足栄養素: {len(deficient)}件")
        for nutrient, rate in deficient[:5]:
            name = NUTRIENT_NAMES.get(nutrient, nutrient)
            print(f"     - {name}: {rate:.1f}%")

    print(f"\n--- 料理出現回数ランキング（上位10） ---")
    dish_counts = results["dish_counts"]
    for rank, (dish, count) in enumerate(dish_counts.most_common(10), 1):
        print(f"  {rank:2d}. {dish}: {count}回")

    print(f"\n--- 上位3料理の栄養データ ---")
    dish_nutrients = results["dish_nutrients"]
    for rank, (dish, count) in enumerate(dish_counts.most_common(3), 1):
        nutrients = dish_nutrients.get(dish, {})
        if nutrients:
            print(f"\n  {rank}. {dish} ({nutrients.get('category', '')})")
            print(f"     出現回数: {count}回")
            print(f"     カロリー: {nutrients.get('calories', 0):.0f} kcal")
            print(f"     タンパク質: {nutrients.get('protein', 0):.1f} g")
            print(f"     脂質: {nutrients.get('fat', 0):.1f} g")
            print(f"     炭水化物: {nutrients.get('carbohydrate', 0):.1f} g")
            print(f"     食物繊維: {nutrients.get('fiber', 0):.1f} g")
            print(f"     鉄: {nutrients.get('iron', 0):.2f} mg")
            print(f"     カルシウム: {nutrients.get('calcium', 0):.1f} mg")
            print(f"     ビタミンC: {nutrients.get('vitamin_c', 0):.1f} mg")


def save_results(all_results: list[dict], output_path: Path):
    """結果をJSONファイルに保存"""
    # JSON serializable に変換
    serializable = []
    for r in all_results:
        if r:
            serializable.append({
                "scenario_name": r["scenario_name"],
                "success_count": r["success_count"],
                "total_runs": r["total_runs"],
                "avg_achievements": r["avg_achievements"],
                "dish_counts": dict(r["dish_counts"]),
                "top_dishes": r["dish_counts"].most_common(10),
            })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)

    print(f"\n結果を保存しました: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="最適化結果分析ツール")
    parser.add_argument("--scenario", "-s", help="特定シナリオのみ実行")
    parser.add_argument("--runs", "-r", type=int, default=10, help="各シナリオの実行回数")
    parser.add_argument("--output", "-o", help="結果をJSONファイルに保存")
    parser.add_argument("--list", "-l", action="store_true", help="シナリオ一覧を表示")
    args = parser.parse_args()

    if args.list:
        print("利用可能なシナリオ:")
        for key, scenario in SCENARIOS.items():
            print(f"  {key}: {scenario['name']}")
        return

    # 実行するシナリオを決定
    if args.scenario:
        if args.scenario not in SCENARIOS:
            print(f"エラー: 不明なシナリオ '{args.scenario}'")
            print("利用可能なシナリオ: " + ", ".join(SCENARIOS.keys()))
            sys.exit(1)
        scenarios_to_run = {args.scenario: SCENARIOS[args.scenario]}
    else:
        scenarios_to_run = SCENARIOS

    print(f"最適化分析を開始します")
    print(f"シナリオ数: {len(scenarios_to_run)}")
    print(f"各シナリオ実行回数: {args.runs}")

    all_results = []
    for key, scenario in scenarios_to_run.items():
        results = run_scenario(key, scenario, args.runs)
        print_results(results)
        all_results.append(results)

    # 結果を保存
    if args.output:
        save_results(all_results, Path(args.output))
    else:
        # デフォルトの出力先
        output_path = Path(__file__).parent.parent / "data" / "analysis_results.json"
        save_results(all_results, output_path)

    # サマリー
    print(f"\n{'='*60}")
    print("全シナリオサマリー: 不足しやすい栄養素")
    print(f"{'='*60}")

    deficient_counts = Counter()
    for r in all_results:
        if r:
            for nutrient, rate in r["avg_achievements"].items():
                if rate < 100:
                    deficient_counts[nutrient] += 1

    if deficient_counts:
        for nutrient, count in deficient_counts.most_common():
            name = NUTRIENT_NAMES.get(nutrient, nutrient)
            print(f"  {name}: {count}/{len(all_results)} シナリオで不足")
    else:
        print("  全シナリオで全栄養素が達成されています")


if __name__ == "__main__":
    main()

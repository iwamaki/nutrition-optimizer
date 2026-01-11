#!/usr/bin/env python3
"""
既存料理リストを表示

LLMに新規レシピを生成させる際、重複を避けるために使用。

使用例:
  python tools/list_dishes.py                    # 全料理を表示
  python tools/list_dishes.py -c 主食            # カテゴリで絞り込み
  python tools/list_dishes.py --categories       # カテゴリ一覧と件数
  python tools/list_dishes.py --compact          # 料理名のみ（カンマ区切り）
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal, DishDB


def list_dishes(category: str = None, compact: bool = False):
    """料理をリストアップ"""
    db = SessionLocal()
    try:
        query = db.query(DishDB)
        if category:
            query = query.filter(DishDB.category == category)

        dishes = query.order_by(DishDB.category, DishDB.name).all()

        if compact:
            names = [d.name for d in dishes]
            print(", ".join(names))
        else:
            current_cat = None
            for d in dishes:
                if d.category != current_cat:
                    current_cat = d.category
                    print(f"\n## {current_cat}")
                print(f"- {d.name}")

        return len(dishes)
    finally:
        db.close()


def list_categories():
    """カテゴリ一覧と件数"""
    db = SessionLocal()
    try:
        from sqlalchemy import func
        results = db.query(
            DishDB.category,
            func.count(DishDB.id)
        ).group_by(DishDB.category).all()

        print("カテゴリ別料理数:")
        total = 0
        for cat, count in sorted(results):
            print(f"  {cat}: {count}件")
            total += count
        print(f"  ─────────")
        print(f"  合計: {total}件")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="既存料理リストを表示（LLMプロンプト用）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  %(prog)s                  # 全料理をカテゴリ別に表示
  %(prog)s -c 主食          # 主食のみ表示
  %(prog)s --compact        # 料理名のみカンマ区切り
  %(prog)s --categories     # カテゴリ一覧と件数
"""
    )
    parser.add_argument(
        "-c", "--category",
        help="カテゴリで絞り込み（主食/主菜/副菜/汁物/デザート）"
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="料理名のみカンマ区切りで出力"
    )
    parser.add_argument(
        "--categories",
        action="store_true",
        help="カテゴリ一覧と件数を表示"
    )

    args = parser.parse_args()

    if args.categories:
        list_categories()
    else:
        count = list_dishes(category=args.category, compact=args.compact)
        if not args.compact:
            print(f"\n合計: {count}件")


if __name__ == "__main__":
    main()

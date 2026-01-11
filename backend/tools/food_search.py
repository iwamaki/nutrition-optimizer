#!/usr/bin/env python3
"""
食品検索CLIツール

使用例:
  python tools/food_search.py 鶏肉
  python tools/food_search.py 焼き --category=肉類
  python tools/food_search.py --code 11209
  python tools/food_search.py もも 皮つき  # 複数キーワードAND検索

オプション:
  -c, --category  カテゴリで絞り込み（例: 肉類, 穀類, 野菜類）
  --code          文科省コードで検索
  -n, --limit     表示件数（デフォルト: 20）
  --categories    利用可能なカテゴリ一覧を表示
"""

import argparse
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import or_
from app.db.database import SessionLocal, FoodDB


def search_foods(
    keywords: list[str] = None,
    code: str = None,
    category: str = None,
    limit: int = 20
) -> list[FoodDB]:
    """食品を検索"""
    db = SessionLocal()
    try:
        query = db.query(FoodDB)

        # コード検索
        if code:
            query = query.filter(FoodDB.mext_code == code)

        # カテゴリ絞り込み
        if category:
            query = query.filter(FoodDB.category == category)

        # キーワード検索（AND検索）
        if keywords:
            for kw in keywords:
                query = query.filter(FoodDB.name.like(f"%{kw}%"))

        return query.limit(limit).all()
    finally:
        db.close()


def list_categories() -> list[str]:
    """利用可能なカテゴリ一覧を取得"""
    db = SessionLocal()
    try:
        categories = db.query(FoodDB.category).distinct().all()
        return sorted([c[0] for c in categories])
    finally:
        db.close()


def format_result(food: FoodDB) -> str:
    """検索結果を1行でフォーマット"""
    return f"{food.mext_code}  {food.name[:50]:<50}  [{food.category}]"


def main():
    parser = argparse.ArgumentParser(
        description="食品検索ツール - 文科省食品成分表からキーワードで食品を検索",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  %(prog)s 鶏肉              # 「鶏肉」を含む食品を検索
  %(prog)s もも 焼き         # 「もも」AND「焼き」を含む食品を検索
  %(prog)s 鶏 -c 肉類        # 肉類カテゴリで「鶏」を検索
  %(prog)s --code 11209      # コード11209の食品を表示
  %(prog)s --categories      # カテゴリ一覧を表示
"""
    )
    parser.add_argument(
        "keywords",
        nargs="*",
        help="検索キーワード（複数指定でAND検索）"
    )
    parser.add_argument(
        "-c", "--category",
        help="カテゴリで絞り込み"
    )
    parser.add_argument(
        "--code",
        help="文科省コードで検索"
    )
    parser.add_argument(
        "-n", "--limit",
        type=int,
        default=20,
        help="表示件数（デフォルト: 20）"
    )
    parser.add_argument(
        "--categories",
        action="store_true",
        help="利用可能なカテゴリ一覧を表示"
    )

    args = parser.parse_args()

    # カテゴリ一覧表示
    if args.categories:
        print("利用可能なカテゴリ:")
        for cat in list_categories():
            print(f"  {cat}")
        return

    # 検索条件チェック
    if not args.keywords and not args.code:
        parser.print_help()
        print("\nエラー: キーワードまたは--codeを指定してください")
        sys.exit(1)

    # 検索実行
    results = search_foods(
        keywords=args.keywords if args.keywords else None,
        code=args.code,
        category=args.category,
        limit=args.limit
    )

    # 結果表示
    if not results:
        print("該当する食品が見つかりませんでした")
        sys.exit(0)

    print(f"検索結果: {len(results)}件")
    print("-" * 80)
    print(f"{'コード':<7} {'食品名':<50} {'カテゴリ'}")
    print("-" * 80)

    for food in results:
        print(format_result(food))


if __name__ == "__main__":
    main()

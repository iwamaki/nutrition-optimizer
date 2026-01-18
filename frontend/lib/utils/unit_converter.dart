/// 食材の単位変換ユーティリティ
class UnitConverter {
  UnitConverter._();

  /// 調味料の大さじ・小さじグラム数 (大さじ1g, 小さじ1g)
  static const Map<String, (double, double)> _seasoningMappings = {
    '醤油': (18, 6),
    'しょうゆ': (18, 6),
    'みりん': (18, 6),
    '砂糖': (9, 3),
    '塩': (18, 6),
    '酢': (15, 5),
    'サラダ油': (12, 4),
    'マヨネーズ': (12, 4),
    'ケチャップ': (15, 5),
    'ソース': (15, 5),
    '料理酒': (15, 5),
    'ごま油': (12, 4),
    'オリーブ油': (12, 4),
    'めんつゆ': (15, 5),
    '味噌': (18, 6),
    'バター': (12, 4),
    'ポン酢': (15, 5),
    'オイスターソース': (18, 6),
    '豆板醤': (18, 6),
    'コンソメ': (9, 3),
    'こしょう': (6, 2),
  };

  /// 食材名 -> (1単位あたりのグラム数, 単位名)
  static const Map<String, (double, String)> _unitMappings = {
    // 野菜類
    'にんじん': (150, '本'),
    '玉ねぎ': (200, '個'),
    'じゃがいも': (150, '個'),
    'さつまいも': (200, '本'),
    'キャベツ': (1000, '玉'),
    'なす': (80, '本'),
    'トマト': (150, '個'),
    'ピーマン': (35, '個'),
    '赤パプリカ': (150, '個'),
    '黄パプリカ': (150, '個'),
    '小松菜': (200, '束'),
    'ほうれん草': (200, '束'),
    'ニラ': (100, '束'),
    'にら': (100, '束'),
    'もやし': (200, '袋'),
    'ねぎ': (100, '本'),
    '長ねぎ': (100, '本'),
    '青ねぎ': (100, '束'),
    '大根': (900, '本'),
    'ブロッコリー': (250, '株'),
    'カリフラワー': (400, '株'),
    'かぼちゃ': (800, '個'),
    'オクラ': (10, '本'),
    'レタス': (600, '玉'),
    'きゅうり': (100, '本'),
    'ごぼう': (150, '本'),
    'れんこん': (150, '節'),
    '白菜': (1200, '株'),
    'セロリ': (100, '本'),
    'ズッキーニ': (150, '本'),
    'アスパラガス': (20, '本'),
    // きのこ類
    'しいたけ': (15, '個'),
    'えのき': (100, '袋'),
    'しめじ': (100, 'パック'),
    'まいたけ': (100, 'パック'),
    'エリンギ': (40, '本'),
    // 薬味
    'しょうが': (15, 'かけ'),
    '生姜': (15, 'かけ'),
    'にんにく': (5, '片'),
    '大葉': (1, '枚'),
    'みょうが': (15, '個'),
    '三つ葉': (50, '束'),
    // 卵・豆腐
    '卵': (50, '個'),
    '木綿豆腐': (350, '丁'),
    '絹ごし豆腐': (350, '丁'),
    '豆腐': (350, '丁'),
    '油揚げ': (30, '枚'),
    '厚揚げ': (150, '枚'),
    '納豆': (50, 'パック'),
    // 肉類
    '鶏肉': (250, '枚'),
    'もも肉': (250, '枚'),
    '鶏もも肉': (250, '枚'),
    '鶏むね肉': (250, '枚'),
    'ささみ': (50, '本'),
    '豚肉': (100, 'g'),
    '牛肉': (100, 'g'),
    'ベーコン': (18, '枚'),
    'ウインナー': (20, '本'),
    'ハム': (10, '枚'),
    // 魚介類
    '鮭': (80, '切れ'),
    'さば': (100, '切れ'),
    'サバ': (100, '切れ'),
    'あじ': (150, '尾'),
    'えび': (15, '尾'),
    'いか': (200, '杯'),
    'たこ': (100, 'g'),
    'あさり': (200, 'パック'),
    'しじみ': (200, 'パック'),
    'ホタテ': (30, '個'),
    'ツナ缶': (70, '缶'),
    'しらす': (30, 'パック'),
    // 主食
    '白米': (150, '合'),
    '米': (150, '合'),
    'パスタ': (100, 'g'),
    'うどん': (200, '玉'),
    'そば': (130, '束'),
    '食パン': (60, '枚'),
    // 乳製品
    '牛乳': (200, 'ml'),
    'チーズ': (20, '枚'),
    'ヨーグルト': (100, 'g'),
    '生クリーム': (200, 'ml'),
    // その他
    'コーン': (190, '缶'),
    '海苔': (3, '枚'),
    '焼き海苔': (3, '枚'),
    'わかめ': (5, 'g'),
    'ひじき': (10, 'g'),
    'アーモンド': (1, '粒'),
    'ごま': (3, 'g'),
  };

  /// グラム数を実用的な単位に変換
  ///
  /// Returns: (displayAmount, unit) 例: ("大さじ1", "") または ("2", "本")
  static (String, String) convertToDisplayUnit(String foodName, double amountG) {
    // 調味料の場合は大さじ・小さじに変換
    final seasoningKey = _findSeasoningKey(foodName);
    if (seasoningKey != null) {
      return _convertSeasoning(seasoningKey, amountG);
    }

    // 通常の食材
    final unitKey = _findUnitKey(foodName);
    if (unitKey == null) {
      // マッピングがない場合はgのまま
      if (amountG >= 1000) {
        return ('${(amountG / 1000).toStringAsFixed(1).replaceAll(RegExp(r'\.0$'), '')}', 'kg');
      }
      return ('${amountG.round()}', 'g');
    }

    final (gramsPerUnit, unit) = _unitMappings[unitKey]!;

    // 特殊ケース: 単位がgやmlの場合はそのまま
    if (unit == 'g' || unit == 'ml') {
      if (amountG >= 1000) {
        return ('${(amountG / 1000).toStringAsFixed(1).replaceAll(RegExp(r'\.0$'), '')}', unit == 'g' ? 'kg' : 'L');
      }
      return ('${amountG.round()}', unit);
    }

    // 単位数を計算
    final unitCount = amountG / gramsPerUnit;

    // 大きい野菜（玉・株・個で1個が大きいもの）は分数表示
    if (gramsPerUnit >= 500) {
      if (unitCount < 0.2) {
        return ('${amountG.round()}', 'g');
      } else if (unitCount < 0.4) {
        return ('1/4', unit);
      } else if (unitCount < 0.6) {
        return ('1/2', unit);
      } else if (unitCount < 0.9) {
        return ('3/4', unit);
      } else if (unitCount < 1.3) {
        return ('1', unit);
      } else {
        return ('約${(unitCount * 2).round() / 2}', unit);
      }
    }

    // 通常の食材の端数処理
    if (unitCount < 0.3) {
      return ('${amountG.round()}', 'g');
    } else if (unitCount < 0.7) {
      return ('1/2', unit);
    } else if (unitCount < 1.3) {
      return ('1', unit);
    } else if (unitCount < 1.7) {
      return ('1.5', unit);
    } else if (unitCount < 2.3) {
      return ('2', unit);
    } else if (unitCount < 2.7) {
      return ('2.5', unit);
    } else if (unitCount < 3.3) {
      return ('3', unit);
    } else if (unitCount < 4) {
      return ('3.5', unit);
    } else if (unitCount < 5) {
      return ('4', unit);
    } else {
      return ('約${unitCount.round()}', unit);
    }
  }

  /// 調味料のグラム数を大さじ・小さじに変換
  static (String, String) _convertSeasoning(String name, double amountG) {
    final (tbspG, tspG) = _seasoningMappings[name]!;

    final tbspCount = amountG / tbspG;
    final tspCount = amountG / tspG;

    // 少量（小さじ1未満）は少々または具体的な量で
    if (tspCount < 0.5) {
      return ('少々', '');
    }
    if (tspCount < 0.8) {
      return ('小さじ1/2', '');
    }

    // 小さじで表現（小さじ3未満 = 大さじ1未満）
    if (tbspCount < 0.8) {
      if (tspCount < 1.3) {
        return ('小さじ1', '');
      } else if (tspCount < 1.8) {
        return ('小さじ1.5', '');
      } else if (tspCount < 2.3) {
        return ('小さじ2', '');
      } else {
        return ('小さじ2.5', '');
      }
    }

    // 大さじで表現
    if (tbspCount < 1.3) {
      return ('大さじ1', '');
    } else if (tbspCount < 1.8) {
      return ('大さじ1.5', '');
    } else if (tbspCount < 2.3) {
      return ('大さじ2', '');
    } else if (tbspCount < 2.8) {
      return ('大さじ2.5', '');
    } else if (tbspCount < 3.3) {
      return ('大さじ3', '');
    } else {
      return ('大さじ${tbspCount.round()}', '');
    }
  }

  /// 調味料名を検索（部分一致）
  static String? _findSeasoningKey(String foodName) {
    // 完全一致優先
    if (_seasoningMappings.containsKey(foodName)) {
      return foodName;
    }
    // 部分一致
    for (final key in _seasoningMappings.keys) {
      if (foodName.contains(key) || key.contains(foodName)) {
        return key;
      }
    }
    return null;
  }

  /// 食材名を検索（部分一致）
  static String? _findUnitKey(String foodName) {
    // 完全一致優先
    if (_unitMappings.containsKey(foodName)) {
      return foodName;
    }
    // 部分一致
    for (final key in _unitMappings.keys) {
      if (foodName.contains(key) || key.contains(foodName)) {
        return key;
      }
    }
    return null;
  }

  /// 分量を表示用文字列にフォーマット
  static String formatAmount(String foodName, double amountG) {
    final (display, unit) = convertToDisplayUnit(foodName, amountG);
    if (unit.isEmpty) {
      return display; // "大さじ1"など
    }
    return '$display$unit'; // "2本"など
  }
}

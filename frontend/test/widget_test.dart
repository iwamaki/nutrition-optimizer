import 'package:flutter_test/flutter_test.dart';
import 'package:nutrition_optimizer/main.dart';

void main() {
  testWidgets('App loads correctly', (WidgetTester tester) async {
    await tester.pumpWidget(const NutritionOptimizerApp());

    // ホーム画面のタイトルが表示されることを確認
    expect(find.text('今日の献立'), findsOneWidget);
  });
}

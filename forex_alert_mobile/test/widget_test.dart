import 'package:flutter_test/flutter_test.dart';
import 'package:forex_alert_mobile/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const ForexAlertApp());
    expect(find.text('Live Market Watch'), findsOneWidget);
  });
}

import 'package:flutter_test/flutter_test.dart';
import 'package:blendit_mobile/main.dart';

void main() {
  testWidgets('shows the Blendit workshop connection form', (tester) async {
    await tester.pumpWidget(const BlenditApp());
    expect(find.text('Blendit Workshop'), findsOneWidget);
    expect(find.text('اتصال الحاسوب'), findsOneWidget);
    expect(find.text('رمز الاتصال الخاص'), findsOneWidget);
    expect(find.text('توليد الحزمة الأولية على الحاسوب'), findsOneWidget);
  });
}

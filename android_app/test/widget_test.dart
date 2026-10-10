import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:blendit_mobile/main.dart';

void main() {
  testWidgets('renders the Blendit workshop and connection inputs',
      (WidgetTester tester) async {
    await tester.pumpWidget(const BlenditApp());
    await tester.pumpAndSettle();

    expect(find.byType(MaterialApp), findsOneWidget);
    expect(find.text('Blendit Workshop'), findsOneWidget);
    expect(find.byType(TextField), findsNWidgets(2));
    expect(find.text('عنوان الحاسوب مع المنفذ'), findsOneWidget);
    expect(find.text('رمز الاتصال الخاص'), findsOneWidget);
    expect(find.text('تحويل صورة إلى مجسم 3D — TRELLIS.2'), findsOneWidget);
    expect(find.text('اختيار صورة من الهاتف'), findsOneWidget);
    expect(find.text('فتح TRELLIS.2'), findsOneWidget);
  });
}

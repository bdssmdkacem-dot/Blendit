import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

void main() => runApp(const BlenditApp());

class BlenditApp extends StatelessWidget {
  const BlenditApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Blendit',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          brightness: Brightness.dark,
          colorScheme: ColorScheme.fromSeed(
            seedColor: const Color(0xFFB77A45),
            brightness: Brightness.dark,
            surface: const Color(0xFF171A20),
          ),
          scaffoldBackgroundColor: const Color(0xFF101217),
          useMaterial3: true,
          inputDecorationTheme: const InputDecorationTheme(
            border: OutlineInputBorder(),
            filled: true,
          ),
        ),
        home: const WorkshopHome(),
      );
}

class AssetFile {
  const AssetFile({required this.name, required this.size, required this.url});
  final String name;
  final int size;
  final String url;

  factory AssetFile.fromJson(Map<String, dynamic> json) => AssetFile(
        name: json['name'] as String? ?? 'asset',
        size: (json['size'] as num?)?.toInt() ?? 0,
        url: json['url'] as String? ?? '',
      );

  String get readableSize {
    if (size < 1024) return '$size B';
    if (size < 1024 * 1024) return '${(size / 1024).toStringAsFixed(1)} KB';
    return '${(size / (1024 * 1024)).toStringAsFixed(2)} MB';
  }
}

class WorkshopHome extends StatefulWidget {
  const WorkshopHome({super.key});

  @override
  State<WorkshopHome> createState() => _WorkshopHomeState();
}

class _WorkshopHomeState extends State<WorkshopHome> {
  final _hostController = TextEditingController(text: 'http://192.168.1.10:8765');
  final _tokenController = TextEditingController();
  final _scrollController = ScrollController();
  List<AssetFile> _assets = [];
  String? _previewUrl;
  String _status = 'أدخل عنوان الحاسوب ورمز الاتصال لربط الورشة.';
  String? _jobId;
  String? _jobState;
  bool _busy = false;
  bool _connected = false;
  Timer? _pollTimer;

  String get _baseUrl => _hostController.text.trim().replaceAll(RegExp(r'/+$'), '');
  Map<String, String> get _headers => {
        'Authorization': 'Bearer ${_tokenController.text.trim()}',
        'Content-Type': 'application/json',
      };

  @override
  void dispose() {
    _pollTimer?.cancel();
    _hostController.dispose();
    _tokenController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Uri _uri(String path) => Uri.parse('$_baseUrl$path');

  Future<Map<String, dynamic>> _requestJson(
    String method,
    String path, {
    Map<String, dynamic>? body,
  }) async {
    final uri = _uri(path);
    late http.Response response;
    if (method == 'POST') {
      response = await http.post(uri, headers: _headers, body: jsonEncode(body ?? {}))
          .timeout(const Duration(seconds: 20));
    } else {
      response = await http.get(uri, headers: _headers)
          .timeout(const Duration(seconds: 20));
    }
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException('استجابة غير صالحة من الخادم.');
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception(decoded['error'] ?? 'HTTP ${response.statusCode}');
    }
    return decoded;
  }

  Future<void> _connect() async {
    setState(() {
      _busy = true;
      _status = 'جارٍ الاتصال بالحاسوب...';
    });
    try {
      final healthResponse = await http.get(_uri('/health'))
          .timeout(const Duration(seconds: 8));
      if (healthResponse.statusCode != 200) {
        throw Exception('خدمة Blendit غير متاحة.');
      }
      await _refreshAssets();
      if (!mounted) return;
      setState(() {
        _connected = true;
        _status = 'تم الاتصال بالحاسوب. يمكنك توليد الحزمة الأولية أو تنزيل أصول موجودة.';
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _connected = false;
        _status = 'تعذّر الاتصال: $error';
      });
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _refreshAssets() async {
    final data = await _requestJson('GET', '/api/assets');
    final rawAssets = data['assets'] as List<dynamic>? ?? [];
    if (!mounted) return;
    setState(() {
      _assets = rawAssets
          .whereType<Map<String, dynamic>>()
          .map(AssetFile.fromJson)
          .toList();
      _previewUrl = data['preview_url'] as String?;
    });
  }

  Future<void> _generate() async {
    setState(() {
      _busy = true;
      _status = 'جارٍ إرسال طلب التوليد إلى الحاسوب...';
    });
    try {
      final data = await _requestJson('POST', '/api/generate',
          body: const {'task': 'starter_pack'});
      _jobId = data['id'] as String?;
      _jobState = data['status'] as String? ?? 'queued';
      _status = 'تم إرسال الطلب. سيعمل Blender على الحاسوب.';
      _startPolling();
    } catch (error) {
      setState(() => _status = 'تعذّر بدء التوليد: $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(const Duration(seconds: 3), (_) => _pollJob());
    _pollJob();
  }

  Future<void> _pollJob() async {
    final id = _jobId;
    if (id == null) return;
    try {
      final data = await _requestJson('GET', '/api/jobs/$id');
      if (!mounted) return;
      final state = data['status'] as String? ?? 'unknown';
      setState(() {
        _jobState = state;
        _status = switch (state) {
          'queued' => 'الطلب في قائمة الانتظار...',
          'running' => 'Blender ينشئ الأصول على الحاسوب...',
          'ready' => 'اكتمل التوليد. جارٍ تحديث مكتبة الأصول...',
          'failed' => 'فشل التوليد: ${data['message'] ?? 'خطأ غير معروف'}',
          _ => 'حالة المهمة: $state',
        };
      });
      if (state == 'ready' || state == 'failed') {
        _pollTimer?.cancel();
        if (state == 'ready') {
          await _refreshAssets();
          if (mounted) setState(() => _status = 'اكتمل التوليد. افحص المعاينة ونزّل الملفات.');
        }
      }
    } catch (error) {
      if (mounted) setState(() => _status = 'تعذّر تحديث حالة المهمة: $error');
    }
  }

  Future<void> _download(AssetFile asset) async {
    setState(() => _status = 'جارٍ تجهيز ${asset.name} للمشاركة...');
    try {
      final response = await http.get(_uri(asset.url), headers: _headers)
          .timeout(const Duration(minutes: 2));
      if (response.statusCode != 200) {
        throw Exception('تعذّر تنزيل الملف (HTTP ${response.statusCode}).');
      }
      final directory = await getTemporaryDirectory();
      final file = File('${directory.path}/${asset.name}');
      await file.writeAsBytes(response.bodyBytes, flush: true);
      await Share.shareXFiles([XFile(file.path)], text: 'Blendit asset: ${asset.name}');
      if (mounted) setState(() => _status = 'تم تجهيز الملف للمشاركة أو الحفظ.');
    } catch (error) {
      if (mounted) setState(() => _status = 'تعذّر تنزيل الملف: $error');
    }
  }

  String? get _previewImageUrl =>
      _previewUrl == null ? null : '$_baseUrl$_previewUrl';

  @override
  Widget build(BuildContext context) {
    final active = _jobState == 'queued' || _jobState == 'running';
    return Scaffold(
      appBar: AppBar(
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Blendit Workshop'),
            Text('ورشة الأصول ثلاثية الأبعاد', style: TextStyle(fontSize: 12)),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'تحديث الأصول',
            onPressed: _connected && !_busy ? _refreshAssets : null,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          controller: _scrollController,
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 28),
          children: [
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(22),
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFF3B2B24), Color(0xFF20232B)],
                ),
                border: Border.all(color: const Color(0xFF6E503B)),
              ),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.view_in_ar, size: 38, color: Color(0xFFE4B17D)),
                  SizedBox(height: 12),
                  Text('من فكرة إلى أصل ثلاثي الأبعاد',
                      style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                  SizedBox(height: 6),
                  Text('اربط هاتفك بحاسوبك، وشغّل Blender من مكتبة Blendit، ثم عاين الملفات وشاركها.'),
                ],
              ),
            ),
            const SizedBox(height: 18),
            _sectionTitle('اتصال الحاسوب'),
            const SizedBox(height: 10),
            TextField(
              controller: _hostController,
              keyboardType: TextInputType.url,
              decoration: const InputDecoration(
                labelText: 'عنوان الحاسوب مع المنفذ',
                hintText: 'http://192.168.1.10:8765',
                prefixIcon: Icon(Icons.computer),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _tokenController,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'رمز الاتصال الخاص',
                prefixIcon: Icon(Icons.key),
              ),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: _busy ? null : _connect,
              icon: const Icon(Icons.link),
              label: Text(_busy ? 'جارٍ العمل...' : 'الاتصال وتحديث المكتبة'),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFF1A1D24),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    _connected ? Icons.check_circle : Icons.info_outline,
                    color: _connected ? Colors.greenAccent : const Color(0xFFE4B17D),
                  ),
                  const SizedBox(width: 10),
                  Expanded(child: Text(_status)),
                ],
              ),
            ),
            const SizedBox(height: 18),
            _sectionTitle('توليد الأصول'),
            const SizedBox(height: 8),
            const Text('المرحلة الحالية تولّد الحزمة التجريبية الموثوقة: صندوق، فانوس، بلورة، برميل، وعنصر عربة. إنشاء الطلبات المخصصة والشخصيات والتحريك سيأتي في مراحل لاحقة.'),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: !_connected || _busy || active ? null : _generate,
              icon: const Icon(Icons.auto_awesome),
              label: const Text('توليد الحزمة الأولية على الحاسوب'),
            ),
            if (active) ...[
              const SizedBox(height: 10),
              const LinearProgressIndicator(),
            ],
            const SizedBox(height: 22),
            Row(
              children: [
                Expanded(child: _sectionTitle('مكتبة الأصول')),
                Text('${_assets.length} ملف', style: Theme.of(context).textTheme.labelMedium),
              ],
            ),
            const SizedBox(height: 10),
            if (_previewImageUrl != null && _connected)
              ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: Image.network(
                  _previewImageUrl!,
                  headers: _headers,
                  height: 190,
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) => const SizedBox(
                    height: 100,
                    child: Center(child: Text('تعذّر تحميل المعاينة')),
                  ),
                ),
              ),
            if (_assets.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 18),
                child: Center(child: Text('لا توجد ملفات بعد. اتصل بالحاسوب أو ولّد الحزمة الأولية.')),
              )
            else
              ..._assets.map((asset) => Card(
                    margin: const EdgeInsets.only(top: 8),
                    child: ListTile(
                      leading: Icon(_iconFor(asset.name), color: const Color(0xFFE4B17D)),
                      title: Text(asset.name),
                      subtitle: Text(asset.readableSize),
                      trailing: IconButton(
                        tooltip: 'تنزيل أو مشاركة',
                        onPressed: () => _download(asset),
                        icon: const Icon(Icons.download),
                      ),
                    ),
                  )),
            const SizedBox(height: 18),
            const Text(
              'ملاحظة أمان: استخدم الشبكة المنزلية الموثوقة فقط، ولا تشارك رمز الاتصال. لا تفتح منفذ الخدمة مباشرة على الإنترنت.',
              style: TextStyle(color: Colors.white60, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }

  Widget _sectionTitle(String text) => Text(
        text,
        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
      );

  IconData _iconFor(String name) {
    final lower = name.toLowerCase();
    if (lower.endsWith('.blend')) return Icons.view_in_ar;
    if (lower.endsWith('.glb')) return Icons.inventory_2_outlined;
    if (lower.endsWith('.png')) return Icons.image_outlined;
    if (lower.endsWith('.json')) return Icons.data_object;
    return Icons.insert_drive_file_outlined;
  }
}

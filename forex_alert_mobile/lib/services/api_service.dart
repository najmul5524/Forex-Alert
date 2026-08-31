import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/symbol_rate.dart';
import '../models/alert_model.dart';
import '../models/trigger_log_model.dart';

class ApiService {
  static const String _keyServerUrl = 'server_base_url';
  static const String defaultUrl = 'http://10.0.2.2:8000'; // Default Android Emulator host

  static Future<String> getBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyServerUrl) ?? defaultUrl;
  }

  static Future<void> setBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    var clean = url.trim();
    if (!clean.startsWith('http://') && !clean.startsWith('https://')) {
      clean = 'http://$clean';
    }
    if (clean.endsWith('/')) {
      clean = clean.substring(0, clean.length - 1);
    }
    await prefs.setString(_keyServerUrl, clean);
  }

  static Future<List<SymbolRate>> getSymbols() async {
    final base = await getBaseUrl();
    try {
      final res = await http.get(Uri.parse('$base/api/market/symbols')).timeout(const Duration(seconds: 6));
      if (res.statusCode == 200) {
        final List list = jsonDecode(res.body);
        return list.map((e) => SymbolRate.fromJson(e)).toList();
      }
    } catch (_) {}
    return [];
  }

  static Future<List<AlertModel>> getAlerts() async {
    final base = await getBaseUrl();
    try {
      final res = await http.get(Uri.parse('$base/api/alerts')).timeout(const Duration(seconds: 6));
      if (res.statusCode == 200) {
        final List list = jsonDecode(res.body);
        return list.map((e) => AlertModel.fromJson(e)).toList();
      }
    } catch (_) {}
    return [];
  }

  static Future<AlertModel?> createAlert(AlertModel alert) async {
    final base = await getBaseUrl();
    try {
      final res = await http.post(
        Uri.parse('$base/api/alerts'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(alert.toJson()),
      ).timeout(const Duration(seconds: 8));

      if (res.statusCode == 201 || res.statusCode == 200) {
        return AlertModel.fromJson(jsonDecode(res.body));
      }
    } catch (_) {}
    return null;
  }

  static Future<bool> toggleAlert(int id) async {
    final base = await getBaseUrl();
    try {
      final res = await http.post(Uri.parse('$base/api/alerts/$id/toggle')).timeout(const Duration(seconds: 6));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> deleteAlert(int id) async {
    final base = await getBaseUrl();
    try {
      final res = await http.delete(Uri.parse('$base/api/alerts/$id')).timeout(const Duration(seconds: 6));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> testTriggerAlert(int id) async {
    final base = await getBaseUrl();
    try {
      final res = await http.post(Uri.parse('$base/api/alerts/$id/test-trigger')).timeout(const Duration(seconds: 6));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<List<TriggerLogModel>> getTriggerLogs() async {
    final base = await getBaseUrl();
    try {
      final res = await http.get(Uri.parse('$base/api/alerts/history/logs')).timeout(const Duration(seconds: 6));
      if (res.statusCode == 200) {
        final List list = jsonDecode(res.body);
        return list.map((e) => TriggerLogModel.fromJson(e)).toList();
      }
    } catch (_) {}
    return [];
  }

  static Future<bool> registerDeviceToken(String token, String deviceName) async {
    final base = await getBaseUrl();
    try {
      final res = await http.post(
        Uri.parse('$base/api/notifications/register-device'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'token': token, 'device_name': deviceName, 'platform': 'android'}),
      ).timeout(const Duration(seconds: 6));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> overrideTick(String symbol, double price) async {
    final base = await getBaseUrl();
    try {
      final res = await http.post(
        Uri.parse('$base/api/market/tick-override'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'symbol': symbol, 'price': price}),
      ).timeout(const Duration(seconds: 6));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}

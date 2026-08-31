import 'dart:typed_data';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:firebase_core/firebase_core.dart';
import 'api_service.dart';

@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  try {
    await Firebase.initializeApp();
  } catch (_) {}
  
  final title = message.notification?.title ?? message.data['title'] ?? '⚡ Market Alert Triggered';
  final body = message.notification?.body ?? message.data['body'] ?? 'Price cross condition met in live market!';
  
  await NotificationService.showLocalNotification(
    id: (DateTime.now().millisecondsSinceEpoch % 100000),
    title: title,
    body: body,
  );
}

class NotificationService {
  static final FlutterLocalNotificationsPlugin _localNotifications = FlutterLocalNotificationsPlugin();
  static const String channelId = 'forex_alerts_channel';
  static const String channelName = 'Forex & Market Alerts';
  static const String channelDesc = 'High priority live market price & indicator alerts';

  static Future<void> init() async {
    const AndroidInitializationSettings androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const DarwinInitializationSettings iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );

    const InitializationSettings initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _localNotifications.initialize(settings: initSettings);

    final AndroidNotificationChannel channel = AndroidNotificationChannel(
      channelId,
      channelName,
      description: channelDesc,
      importance: Importance.max,
      playSound: true,
      enableVibration: true,
      vibrationPattern: Int64List.fromList([0, 250, 150, 250, 150, 400]),
    );

    await _localNotifications
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);

    // Request permissions
    try {
      final messaging = FirebaseMessaging.instance;
      await messaging.requestPermission(
        alert: true,
        badge: true,
        sound: true,
        provisional: false,
      );

      // Register background handler
      FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);

      // Foreground message listener
      FirebaseMessaging.onMessage.listen((RemoteMessage message) {
        final title = message.notification?.title ?? message.data['title'] ?? '⚡ Market Alert';
        final body = message.notification?.body ?? message.data['body'] ?? 'Price condition triggered!';
        showLocalNotification(
          id: DateTime.now().millisecondsSinceEpoch % 100000,
          title: title,
          body: body,
        );
      });

      // Fetch & register FCM token
      final token = await messaging.getToken();
      if (token != null) {
        await ApiService.registerDeviceToken(token, 'Flutter Android App');
      }

      messaging.onTokenRefresh.listen((newToken) {
        ApiService.registerDeviceToken(newToken, 'Flutter Android App');
      });
    } catch (_) {}
  }

  static Future<void> showLocalNotification({
    required int id,
    required String title,
    required String body,
  }) async {
    final AndroidNotificationDetails androidDetails = AndroidNotificationDetails(
      channelId,
      channelName,
      channelDescription: channelDesc,
      importance: Importance.max,
      priority: Priority.high,
      playSound: true,
      enableVibration: true,
      vibrationPattern: Int64List.fromList([0, 250, 150, 250, 150, 400]),
      styleInformation: BigTextStyleInformation(body),
    );

    final NotificationDetails notificationDetails = NotificationDetails(
      android: androidDetails,
      iOS: const DarwinNotificationDetails(presentAlert: true, presentSound: true, presentBadge: true),
    );

    await _localNotifications.show(
      id: id,
      title: title,
      body: body,
      notificationDetails: notificationDetails,
    );
  }
}

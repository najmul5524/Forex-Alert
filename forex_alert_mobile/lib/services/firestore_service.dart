import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/alert_model.dart';
import '../models/trigger_log_model.dart';
import '../models/symbol_rate.dart';

class FirestoreService {
  static final FirebaseFirestore _db = FirebaseFirestore.instance;

  static Stream<List<AlertModel>> streamAlerts() {
    try {
      return _db
          .collection('alerts')
          .orderBy('created_at', descending: true)
          .snapshots()
          .map((snapshot) => snapshot.docs
              .map((doc) => AlertModel.fromJson({...doc.data(), 'id': int.tryParse(doc.id) ?? doc.data()['id']}))
              .toList());
    } catch (_) {
      return const Stream.empty();
    }
  }

  static Future<void> saveAlert(AlertModel alert) async {
    try {
      final docRef = alert.id != null 
          ? _db.collection('alerts').doc(alert.id.toString())
          : _db.collection('alerts').doc();
      
      await docRef.set({
        ...alert.toJson(),
        'created_at': FieldValue.serverTimestamp(),
      }, SetOptions(merge: true));
    } catch (_) {}
  }

  static Future<void> toggleAlert(String alertId, bool currentState) async {
    try {
      await _db.collection('alerts').doc(alertId).update({
        'is_active': !currentState,
      });
    } catch (_) {}
  }

  static Future<void> deleteAlert(String alertId) async {
    try {
      await _db.collection('alerts').doc(alertId).delete();
    } catch (_) {}
  }

  static Stream<List<TriggerLogModel>> streamTriggerLogs() {
    try {
      return _db
          .collection('triggers')
          .orderBy('timestamp', descending: true)
          .limit(50)
          .snapshots()
          .map((snapshot) => snapshot.docs
              .map((doc) => TriggerLogModel.fromJson(doc.data()))
              .toList());
    } catch (_) {
      return const Stream.empty();
    }
  }

  static Stream<List<SymbolRate>> streamRates() {
    try {
      return _db
          .collection('rates')
          .snapshots()
          .map((snapshot) => snapshot.docs
              .map((doc) => SymbolRate.fromJson(doc.data()))
              .toList());
    } catch (_) {
      return const Stream.empty();
    }
  }
}

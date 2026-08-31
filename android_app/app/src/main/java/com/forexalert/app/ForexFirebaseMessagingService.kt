package com.forexalert.app

import android.os.PowerManager
import android.util.Log
import com.forexalert.app.models.DeviceRegisterRequest
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class ForexFirebaseMessagingService : FirebaseMessagingService() {

    private val tag = "ForexFCM"

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        Log.d(tag, "New FCM Token generated: $token")
        
        // Send token to backend server
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val api = ApiClient.getService(applicationContext)
                val deviceName = "${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}"
                api.registerDevice(DeviceRegisterRequest(token = token, deviceName = deviceName))
                Log.d(tag, "FCM Token registered with backend successfully")
            } catch (e: Exception) {
                Log.e(tag, "Failed to register FCM token with backend: ${e.message}")
            }
        }
    }

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        super.onMessageReceived(remoteMessage)
        Log.d(tag, "FCM Message received from: ${remoteMessage.from}")

        // Acquire wake lock to wake up phone screen for instant alert
        val powerManager = getSystemService(POWER_SERVICE) as PowerManager
        val wakeLock = powerManager.newWakeLock(
            PowerManager.FULL_WAKE_LOCK or PowerManager.ACQUIRE_CAUSES_WAKEUP or PowerManager.ON_AFTER_RELEASE,
            "ForexAlert:WakeLock"
        )
        wakeLock.acquire(4000)

        var title = "⚡ Forex Market Alert"
        var body = "Price condition triggered in live market!"

        remoteMessage.notification?.let {
            it.title?.let { t -> title = t }
            it.body?.let { b -> body = b }
        }

        if (remoteMessage.data.isNotEmpty()) {
            val symbol = remoteMessage.data["symbol"] ?: ""
            val price = remoteMessage.data["price"] ?: ""
            val summary = remoteMessage.data["summary"] ?: ""
            if (symbol.isNotEmpty()) {
                title = "🚨 Alert: $symbol"
                body = if (summary.isNotEmpty()) summary else "$symbol at price: $price"
            }
        }

        NotificationHelper.showNotification(applicationContext, title, body)
    }
}

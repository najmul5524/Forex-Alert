package com.forexalert.app

import android.content.Context
import com.forexalert.app.models.*
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.util.concurrent.TimeUnit

interface ForexAlertApiService {
    @GET("/api/market/symbols")
    suspend fun getSymbols(): Response<List<SymbolPrice>>

    @GET("/api/alerts")
    suspend fun getAlerts(): Response<List<AlertItem>>

    @POST("/api/alerts")
    suspend fun createAlert(@Body request: AlertCreateRequest): Response<AlertItem>

    @POST("/api/alerts/{id}/toggle")
    suspend fun toggleAlert(@Path("id") id: Int): Response<AlertItem>

    @DELETE("/api/alerts/{id}")
    suspend fun deleteAlert(@Path("id") id: Int): Response<Map<String, Any>>

    @POST("/api/alerts/{id}/test-trigger")
    suspend fun testTriggerAlert(@Path("id") id: Int): Response<Map<String, Any>>

    @GET("/api/alerts/history/logs")
    suspend fun getTriggerLogs(): Response<List<TriggerLogItem>>

    @POST("/api/notifications/register-device")
    suspend fun registerDevice(@Body request: DeviceRegisterRequest): Response<Map<String, Any>>
}

object ApiClient {
    private const val PREFS_NAME = "forex_alert_prefs"
    private const val KEY_BASE_URL = "base_server_url"
    const val DEFAULT_BASE_URL = "http://10.0.2.2:8000" // Default for Android Emulator to host PC

    private var currentRetrofit: Retrofit? = null
    private var currentApi: ForexAlertApiService? = null
    private var currentUrl: String = DEFAULT_BASE_URL

    fun getServerUrl(context: Context): String {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_BASE_URL, DEFAULT_BASE_URL) ?: DEFAULT_BASE_URL
    }

    fun setServerUrl(context: Context, newUrl: String) {
        var cleanUrl = newUrl.trim()
        if (!cleanUrl.startsWith("http://") && !cleanUrl.startsWith("https://")) {
            cleanUrl = "http://$cleanUrl"
        }
        if (!cleanUrl.endsWith("/")) {
            cleanUrl = "$cleanUrl/"
        }
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_BASE_URL, cleanUrl).apply()
        currentUrl = cleanUrl
        currentRetrofit = null
        currentApi = null
    }

    fun getService(context: Context): ForexAlertApiService {
        val url = getServerUrl(context)
        if (currentApi != null && currentUrl == url) {
            return currentApi!!
        }

        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(logging)
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(10, TimeUnit.SECONDS)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl(if (url.endsWith("/")) url else "$url/")
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        currentUrl = url
        currentRetrofit = retrofit
        currentApi = retrofit.create(ForexAlertApiService::class.java)
        return currentApi!!
    }
}

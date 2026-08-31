package com.forexalert.app.models

import com.google.gson.annotations.SerializedName

data class SymbolPrice(
    @SerializedName("symbol") val symbol: String,
    @SerializedName("name") val name: String,
    @SerializedName("type") val type: String,
    @SerializedName("current_price") val currentPrice: Double,
    @SerializedName("decimals") val decimals: Int
)

data class AlertItem(
    @SerializedName("id") val id: Int,
    @SerializedName("symbol") val symbol: String,
    @SerializedName("timeframe") val timeframe: String,
    @SerializedName("condition_type") val conditionType: String,
    @SerializedName("params") val params: Map<String, Any>,
    @SerializedName("trigger_frequency") val triggerFrequency: String,
    @SerializedName("channels") val channels: List<String>,
    @SerializedName("is_active") val isActive: Boolean,
    @SerializedName("trigger_count") val triggerCount: Int,
    @SerializedName("message") val message: String?
)

data class AlertCreateRequest(
    @SerializedName("symbol") val symbol: String,
    @SerializedName("timeframe") val timeframe: String,
    @SerializedName("condition_type") val conditionType: String,
    @SerializedName("params") val params: Map<String, Any>,
    @SerializedName("trigger_frequency") val triggerFrequency: String = "only_once",
    @SerializedName("channels") val channels: List<String> = listOf("push", "in_app"),
    @SerializedName("target_email") val targetEmail: String? = null,
    @SerializedName("message") val message: String? = null,
    @SerializedName("is_active") val isActive: Boolean = true
)

data class TriggerLogItem(
    @SerializedName("id") val id: Int,
    @SerializedName("symbol") val symbol: String,
    @SerializedName("condition_summary") val conditionSummary: String,
    @SerializedName("trigger_price") val triggerPrice: Double,
    @SerializedName("timeframe") val timeframe: String,
    @SerializedName("timestamp") val timestamp: String
)

data class DeviceRegisterRequest(
    @SerializedName("token") val token: String,
    @SerializedName("device_name") val deviceName: String = "Android Smartphone",
    @SerializedName("platform") val platform: String = "android"
)

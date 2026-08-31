package com.forexalert.app

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.widget.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.forexalert.app.databinding.ActivityMainBinding
import com.forexalert.app.models.*
import com.google.firebase.messaging.FirebaseMessaging
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private var symbolsList: List<SymbolPrice> = emptyList()
    private var alertsList: List<AlertItem> = emptyList()
    private var logsList: List<TriggerLogItem> = emptyList()

    private val requestNotificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (isGranted) {
            Toast.makeText(this, "Push notifications enabled!", Toast.LENGTH_SHORT).show()
        } else {
            Toast.makeText(this, "Permission required for live price alerts", Toast.LENGTH_LONG).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        NotificationHelper.createNotificationChannel(this)
        checkNotificationPermission()
        registerFcmToken()

        binding.swipeRefresh.setOnRefreshListener {
            loadDashboardData()
        }

        binding.btnConfigServer.setOnClickListener {
            showServerConfigDialog()
        }

        binding.fabCreateAlert.setOnClickListener {
            showCreateAlertDialog()
        }

        loadDashboardData()
    }

    override fun onResume() {
        super.onResume()
        loadDashboardData()
    }

    private fun checkNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestNotificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }

    private fun registerFcmToken() {
        try {
            FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
                if (task.isSuccessful && task.result != null) {
                    val token = task.result
                    lifecycleScope.launch(Dispatchers.IO) {
                        try {
                            val api = ApiClient.getService(this@MainActivity)
                            val deviceName = "${Build.MANUFACTURER} ${Build.MODEL}"
                            api.registerDevice(DeviceRegisterRequest(token = token, deviceName = deviceName))
                        } catch (e: Exception) {
                            e.printStackTrace()
                        }
                    }
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun loadDashboardData() {
        binding.swipeRefresh.isRefreshing = true
        binding.tvServerStatus.text = "Server: Connecting..."

        lifecycleScope.launch(Dispatchers.IO) {
            try {
                val api = ApiClient.getService(this@MainActivity)
                val symbolsResp = api.getSymbols()
                val alertsResp = api.getAlerts()
                val logsResp = api.getTriggerLogs()

                withContext(Dispatchers.Main) {
                    binding.swipeRefresh.isRefreshing = false
                    if (symbolsResp.isSuccessful && symbolsResp.body() != null) {
                        symbolsList = symbolsResp.body()!!
                        binding.tvServerStatus.text = "Server: Connected (${ApiClient.getServerUrl(this@MainActivity)})"
                        renderSymbols()
                    } else {
                        binding.tvServerStatus.text = "Server Error: ${symbolsResp.code()}"
                    }

                    if (alertsResp.isSuccessful && alertsResp.body() != null) {
                        alertsList = alertsResp.body()!!
                        renderAlerts()
                    }

                    if (logsResp.isSuccessful && logsResp.body() != null) {
                        logsList = logsResp.body()!!
                        renderLogs()
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    binding.swipeRefresh.isRefreshing = false
                    binding.tvServerStatus.text = "Offline / Connection Failed"
                }
            }
        }
    }

    private fun renderSymbols() {
        binding.ratesContainer.removeAllViews()
        for (sym in symbolsList) {
            val card = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                setPadding(32, 24, 32, 24)
                setBackgroundColor(ContextCompat.getColor(context, R.color.slate_900))
                val params = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply { setMargins(0, 0, 0, 12) }
                layoutParams = params
            }

            val tvTitle = TextView(this).apply {
                text = "${sym.symbol}\n${sym.name}"
                setTextColor(ContextCompat.getColor(context, R.color.white))
                textSize = 13f
                layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            }

            val tvPrice = TextView(this).apply {
                text = String.format("%.${sym.decimals}f", sym.currentPrice)
                setTextColor(ContextCompat.getColor(context, R.color.sky_400))
                textSize = 14f
                textStyle = android.graphics.Typeface.BOLD
            }

            card.addView(tvTitle)
            card.addView(tvPrice)
            binding.ratesContainer.addView(card)
        }
    }

    private fun renderAlerts() {
        binding.alertsContainer.removeAllViews()
        val activeCount = alertsList.count { it.isActive }
        binding.tvAlertsCount.text = "$activeCount Active"

        if (alertsList.isEmpty()) {
            val emptyTv = TextView(this).apply {
                text = "No alerts configured yet. Tap '+ Create Alert' below."
                setTextColor(ContextCompat.getColor(context, R.color.slate_400))
                textSize = 12spToPx()
                setPadding(16, 24, 16, 24)
            }
            binding.alertsContainer.addView(emptyTv)
            return
        }

        for (alert in alertsList) {
            val card = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(32, 24, 32, 24)
                setBackgroundColor(ContextCompat.getColor(context, R.color.slate_850))
                val params = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply { setMargins(0, 0, 0, 16) }
                layoutParams = params
            }

            val topRow = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = android.view.Gravity.CENTER_VERTICAL
            }

            val tvSymbol = TextView(this).apply {
                text = "${alert.symbol} (${alert.timeframe}) - ${alert.conditionType.replace('_', ' ').uppercase()}"
                setTextColor(ContextCompat.getColor(context, R.color.white))
                textSize = 13f
                textStyle = android.graphics.Typeface.BOLD
                layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            }

            val btnToggle = Button(this).apply {
                text = if (alert.isActive) "Active" else "Paused"
                textSize = 10f
                setBackgroundColor(ContextCompat.getColor(context, if (alert.isActive) R.color.emerald_500 else R.color.slate_700))
                setOnClickListener { toggleAlert(alert.id) }
            }

            val btnDelete = Button(this).apply {
                text = "✕"
                textSize = 10f
                setBackgroundColor(ContextCompat.getColor(context, R.color.rose_500))
                setOnClickListener { deleteAlert(alert.id) }
            }

            topRow.addView(tvSymbol)
            topRow.addView(btnToggle)
            topRow.addView(btnDelete)

            val tvDetail = TextView(this).apply {
                text = "Params: ${alert.params} | Fired: ${alert.triggerCount} times"
                setTextColor(ContextCompat.getColor(context, R.color.slate_400))
                textSize = 11f
                setPadding(0, 8, 0, 0)
            }

            card.addView(topRow)
            card.addView(tvDetail)
            binding.alertsContainer.addView(card)
        }
    }

    private fun renderLogs() {
        binding.logsContainer.removeAllViews()
        if (logsList.isEmpty()) {
            val emptyTv = TextView(this).apply {
                text = "No triggers recorded yet."
                setTextColor(ContextCompat.getColor(context, R.color.slate_400))
                textSize = 12spToPx()
                setPadding(16, 16, 16, 16)
            }
            binding.logsContainer.addView(emptyTv)
            return
        }

        for (log in logsList.take(15)) {
            val card = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                setPadding(24, 16, 24, 16)
                setBackgroundColor(ContextCompat.getColor(context, R.color.slate_900))
                val params = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply { setMargins(0, 0, 0, 8) }
                layoutParams = params
            }

            val tvInfo = TextView(this).apply {
                text = "🚨 ${log.symbol} (${log.timeframe})\n${log.conditionSummary}"
                setTextColor(ContextCompat.getColor(context, R.color.slate_400))
                textSize = 11f
                layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            }

            val tvPrice = TextView(this).apply {
                text = "${log.triggerPrice}"
                setTextColor(ContextCompat.getColor(context, R.color.sky_400))
                textSize = 12f
                textStyle = android.graphics.Typeface.BOLD
            }

            card.addView(tvInfo)
            card.addView(tvPrice)
            binding.logsContainer.addView(card)
        }
    }

    private fun toggleAlert(id: Int) {
        lifecycleScope.launch(Dispatchers.IO) {
            try {
                val api = ApiClient.getService(this@MainActivity)
                api.toggleAlert(id)
                loadDashboardData()
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    private fun deleteAlert(id: Int) {
        lifecycleScope.launch(Dispatchers.IO) {
            try {
                val api = ApiClient.getService(this@MainActivity)
                api.deleteAlert(id)
                loadDashboardData()
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    private fun showServerConfigDialog() {
        val input = EditText(this).apply {
            setText(ApiClient.getServerUrl(this@MainActivity))
            hint = "http://192.168.1.100:8000"
            setPadding(40, 40, 40, 40)
        }

        AlertDialog.Builder(this)
            .setTitle("Server Connection Address")
            .setMessage("Enter the IP address or domain where your Forex Alert server is running:")
            .setView(input)
            .setPositiveButton("Save & Connect") { _, _ ->
                val newUrl = input.text.toString()
                if (newUrl.isNotEmpty()) {
                    ApiClient.setServerUrl(this, newUrl)
                    registerFcmToken()
                    loadDashboardData()
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun showCreateAlertDialog() {
        val symbols = arrayOf("EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "AUDUSD", "USDCAD", "BTCUSDT", "ETHUSDT", "SOLUSDT")
        val conditions = arrayOf(
            "Price Crossing Up (price_cross_up)",
            "Price Crossing Down (price_cross_down)",
            "Price Greater Than (price_greater)",
            "Price Less Than (price_less)"
        )

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 24, 48, 24)
        }

        val symSpinner = Spinner(this).apply {
            adapter = ArrayAdapter(this@MainActivity, android.R.layout.simple_spinner_dropdown_item, symbols)
        }
        val condSpinner = Spinner(this).apply {
            adapter = ArrayAdapter(this@MainActivity, android.R.layout.simple_spinner_dropdown_item, conditions)
        }
        val priceInput = EditText(this).apply {
            hint = "Target Price (e.g. 1.08600)"
            inputType = android.text.InputType.TYPE_CLASS_NUMBER or android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL
        }

        layout.addView(TextView(this).apply { text = "Select Pair:" })
        layout.addView(symSpinner)
        layout.addView(TextView(this).apply { text = "Select Trigger Condition:" })
        layout.addView(condSpinner)
        layout.addView(TextView(this).apply { text = "Target Price:" })
        layout.addView(priceInput)

        AlertDialog.Builder(this)
            .setTitle("Create Market Alert")
            .setView(layout)
            .setPositiveButton("Create") { _, _ ->
                val sym = symbols[symSpinner.selectedItemPosition]
                val condKey = when (condSpinner.selectedItemPosition) {
                    0 -> "price_cross_up"
                    1 -> "price_cross_down"
                    2 -> "price_greater"
                    else -> "price_less"
                }
                val priceVal = priceInput.text.toString().toDoubleOrNull() ?: 1.0850

                lifecycleScope.launch(Dispatchers.IO) {
                    try {
                        val api = ApiClient.getService(this@MainActivity)
                        val req = AlertCreateRequest(
                            symbol = sym,
                            timeframe = "1m",
                            condition_type = condKey,
                            params = mapOf("target_price" to priceVal),
                            triggerFrequency = "only_once",
                            channels = listOf("push", "in_app"),
                            isActive = true
                        )
                        api.createAlert(req)
                        loadDashboardData()
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun Int.spToPx(): Float {
        return this * resources.displayMetrics.scaledDensity
    }
}

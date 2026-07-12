package com.teknofest.bahiskalkani

import android.content.ComponentName
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.teknofest.bahiskalkani.service.ScreenReaderService
import com.teknofest.bahiskalkani.stats.BlockStats
import com.teknofest.bahiskalkani.ui.theme.BahisKalkaniTheme

class MainActivity : ComponentActivity() {

    private var serviceEnabled by mutableStateOf(false)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            BahisKalkaniTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    MainScreen(
                        serviceEnabled = serviceEnabled,
                        blockedCount = BlockStats.blockedCount,
                        onOpenSettings = {
                            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                        },
                        modifier = Modifier.padding(innerPadding),
                    )
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        serviceEnabled = isAccessibilityServiceEnabled()
    }

    private fun isAccessibilityServiceEnabled(): Boolean {
        val enabledServices = Settings.Secure.getString(
            contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES,
        ) ?: return false
        val self = ComponentName(this, ScreenReaderService::class.java)
        return enabledServices.split(':').any { ComponentName.unflattenFromString(it) == self }
    }
}

@Composable
fun MainScreen(
    serviceEnabled: Boolean,
    blockedCount: Int,
    onOpenSettings: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(
            text = stringResource(R.string.main_title),
            style = MaterialTheme.typography.headlineMedium,
        )
        Text(
            text = stringResource(R.string.main_description),
            style = MaterialTheme.typography.bodyMedium,
        )

        Card(
            colors = CardDefaults.cardColors(
                containerColor = if (serviceEnabled) {
                    MaterialTheme.colorScheme.primaryContainer
                } else {
                    MaterialTheme.colorScheme.errorContainer
                },
            ),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text(
                    text = stringResource(
                        if (serviceEnabled) R.string.main_status_on else R.string.main_status_off,
                    ),
                    style = MaterialTheme.typography.titleMedium,
                )
                if (!serviceEnabled) {
                    Text(
                        text = stringResource(R.string.main_status_off_hint),
                        style = MaterialTheme.typography.bodySmall,
                    )
                    Button(onClick = onOpenSettings) {
                        Text(stringResource(R.string.main_enable_button))
                    }
                }
            }
        }

        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = stringResource(R.string.main_blocked_label),
                    style = MaterialTheme.typography.bodyMedium,
                )
                Text(
                    text = blockedCount.toString(),
                    style = MaterialTheme.typography.displaySmall,
                )
            }
        }

        Spacer(modifier = Modifier.weight(1f))
        Text(
            text = stringResource(R.string.main_kvkk_note),
            style = MaterialTheme.typography.bodySmall,
        )
    }
}

@Preview(showBackground = true)
@Composable
fun MainScreenPreview() {
    BahisKalkaniTheme {
        MainScreen(serviceEnabled = true, blockedCount = 12, onOpenSettings = {})
    }
}

package com.teknofest.bahiskalkani.service

import android.accessibilityservice.AccessibilityService
import android.graphics.Rect
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import com.teknofest.bahiskalkani.BuildConfig
import com.teknofest.bahiskalkani.detection.Detector
import com.teknofest.bahiskalkani.detection.KeywordDetector
import com.teknofest.bahiskalkani.overlay.CoverTarget
import com.teknofest.bahiskalkani.overlay.OverlayController
import com.teknofest.bahiskalkani.stats.BlockStats

class ScreenReaderService : AccessibilityService() {

    // Faz 2'de ML tabanlı Detector implementasyonu buraya takılacak;
    // servisin geri kalanı değişmeyecek.
    private lateinit var detector: Detector
    private lateinit var overlay: OverlayController

    // "Yine de göster" denilen içerikler; KVKK gereği yalnızca bellekte
    // hash olarak tutulur, servis yeniden başlayınca sıfırlanır.
    private val allowedHashes = mutableSetOf<Int>()

    // Sayaç her benzersiz içeriği bir kez saysın diye
    private val countedHashes = mutableSetOf<Int>()

    override fun onServiceConnected() {
        super.onServiceConnected()
        detector = KeywordDetector.fromAssets(this)
        overlay = OverlayController(
            this,
            onShowAnyway = { target -> allowedHashes.add(target.textHash) },
            onShowAnywayAll = { targets -> targets.forEach { allowedHashes.add(it.textHash) } },
        )
        Log.i(TAG, "Erişilebilirlik servisi bağlandı")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        if (event.eventType != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED &&
            event.eventType != AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED
        ) {
            return
        }
        // Kendi overlay pencerelerimizin ürettiği olaylarla uğraşma
        if (event.packageName == packageName) return

        val root = rootInActiveWindow
        if (root == null) {
            overlay.clear()
            return
        }
        // Olayın kaynağı değil, TARANAN pencere belirleyici: aktif pencere
        // kendi uygulamamız ya da sistem yüzeyiyse (ayarlar, bildirim çubuğu)
        // hiç tarama — kullanıcının servisi kapatabileceği kaçış yolu her
        // zaman açık kalmalı.
        val rootPackage = root.packageName?.toString()
        if (rootPackage == packageName || rootPackage in SYSTEM_PACKAGES) {
            overlay.clear()
            return
        }
        val targets = mutableListOf<CoverTarget>()
        scan(root, targets)
        overlay.update(targets)
    }

    override fun onInterrupt() {
        if (::overlay.isInitialized) overlay.clear()
    }

    override fun onDestroy() {
        if (::overlay.isInitialized) overlay.clear()
        super.onDestroy()
    }

    /**
     * Düğüm ağacını gezer; metni tespitçiye takılan düğümlerin ekran
     * koordinatlarını toplar. KVKK: metinler yalnızca bellekte işlenir,
     * kaydedilmez, cihaz dışına çıkmaz.
     */
    private fun scan(node: AccessibilityNodeInfo, out: MutableList<CoverTarget>) {
        // Kullanıcının kendi yazı alanlarını (arama kutusu vb.) kapatma:
        // kendi yazdığı metin "bahse teşvik eden içerik" değildir ve kutu
        // kapanırsa yazdığını göremez
        if (node.isEditable) return

        val text = buildString {
            node.text?.let { append(it) }
            node.contentDescription?.let {
                if (isNotEmpty()) append(' ')
                append(it)
            }
        }
        if (text.isNotBlank() && detector.isBettingContent(text)) {
            val hash = text.hashCode()
            if (hash !in allowedHashes) {
                val bounds = Rect()
                node.getBoundsInScreen(bounds)
                if (!bounds.isEmpty) {
                    // Aynı metin ekranda birden çok yerde olabilir; anahtara sıra ekle
                    val key = "$hash:${out.count { it.textHash == hash }}"
                    out.add(CoverTarget(key, bounds, hash))
                    if (countedHashes.add(hash)) {
                        BlockStats.blockedCount++
                        if (BuildConfig.DEBUG) Log.d(TAG, "TESPİT: $text")
                    }
                }
            }
            // Eşleşen düğümün altına inmeye gerek yok, tamamı kapanacak
            return
        }
        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            scan(child, out)
        }
    }

    private companion object {
        const val TAG = "BahisKalkani"
        val SYSTEM_PACKAGES = setOf(
            "com.android.settings",
            "com.android.systemui",
        )
    }
}

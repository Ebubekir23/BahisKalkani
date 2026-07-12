package com.teknofest.bahiskalkani.detection

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.util.Locale

/**
 * Faz 1 tespitçisi: metinde bahis çağrışımlı kelimelerden biri geçiyor mu?
 * Basit "içeriyor mu" kontrolü kullanır; bu yüzden "1xbahis", "bahisleri"
 * gibi türevleri de yakalar. Liste ayırt ediciliği yüksek kelimelerden
 * seçilmeli (ör. "bet" tek başına "alfabe(t)", "Betül" gibi yanlış
 * pozitifler üretir).
 *
 * [ignoredPhrases] eşleşmeden ÖNCE metinden çıkarılır. Kritik kullanım:
 * uygulamanın kendi adı "BahisKalkanı" içinde "bahis" geçer; bu ifadeler
 * muaf tutulmazsa kalkan kendi adını gördüğü her ekranı (launcher, ayarlar)
 * kapatır.
 *
 * Kelime ve muafiyet listelerinin tek kaynağı assets/keywords.json —
 * Chrome eklentisi tarafıyla eşdeğer tutulur; güncellerken Yazılımcı 2'ye ilet.
 */
class KeywordDetector(
    keywords: List<String>,
    ignoredPhrases: List<String> = emptyList(),
) : Detector {

    private val turkish = Locale.forLanguageTag("tr")
    private val keywords = keywords.map { it.lowercase(turkish) }
    private val ignoredPhrases = ignoredPhrases.map { it.lowercase(turkish) }

    override fun isBettingContent(text: String): Boolean {
        var lower = text.lowercase(turkish)
        for (phrase in ignoredPhrases) {
            lower = lower.replace(phrase, "")
        }
        val normalized = normalizeCensoredChars(lower)
        return keywords.any { normalized.contains(it) }
    }

    /**
     * Basit sansür normalizasyonu: "b0nus" → "bonus", "ç3vrim" → "çevrim".
     * Bahis siteleri filtrelerden kaçmak için harf yerine rakam/sembol kullanır.
     * Daha karmaşık varyasyonlar (boşluklu yazım, yeni argo) Faz 2 modelinin işi
     * — bkz. MODEL_ENTEGRASYON.md.
     */
    private fun normalizeCensoredChars(text: String): String =
        buildString(text.length) {
            for (c in text) append(CENSOR_SUBSTITUTIONS[c] ?: c)
        }

    companion object {
        private val CENSOR_SUBSTITUTIONS = mapOf(
            '0' to 'o',
            '1' to 'i',
            '3' to 'e',
            '4' to 'a',
            '5' to 's',
            '7' to 't',
            '@' to 'a',
            '$' to 's',
        )

        fun fromAssets(context: Context): KeywordDetector {
            val json = JSONObject(
                context.assets.open("keywords.json").bufferedReader().use { it.readText() },
            )
            return KeywordDetector(
                keywords = json.getJSONArray("keywords").toStringList(),
                ignoredPhrases = json.optJSONArray("ignored")?.toStringList() ?: emptyList(),
            )
        }

        private fun JSONArray.toStringList(): List<String> = List(length()) { getString(it) }
    }
}

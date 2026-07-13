package com.teknofest.bahiskalkani.detection

import android.content.Context
import java.text.Normalizer
import java.util.Locale
import org.json.JSONObject
import org.tensorflow.lite.Interpreter

/**
 * Faz 2 tespitçisi: karakter seviyesi TFLite modeliyle 0..1 "bahse teşvik"
 * skoru üretir, [threshold] üstünü engellenecek içerik sayar.
 *
 * REFERANS İMPLEMENTASYON — model/kotlin/ altından app/src/main/java/...'ya
 * Ebubekir taşıyacak. Gerekli asset'ler (model/cikti/ çıktılarından):
 *   assets/model.tflite, assets/model_vocab.json
 * Gerekli bağımlılık (app/build.gradle.kts):
 *   implementation("org.tensorflow:tensorflow-lite:2.14.0")
 *   // veya yeni nesil paket: implementation("com.google.ai.edge.litert:litert:1.x")
 *   // (API aynı; import org.tensorflow.lite.* → com.google.ai.edge.litert.*)
 *
 * Ön işleme spec'i: model/spec/ON_ISLEME.md — Python tarafıyla adım adım
 * aynı olmak ZORUNDA, değişiklik iki tarafta birden yapılır.
 *
 * Serviste önerilen kullanım (model VEYA kelime listesi eşleşirse engelle):
 *   val keyword = KeywordDetector.fromAssets(this)
 *   val model = TfLiteDetector.fromAssets(this)
 *   detector = Detector { t -> keyword.isBettingContent(t) || model.isBettingContent(t) }
 *
 * Not: Interpreter iş parçacığı güvenli değildir; bu sınıf servis ana
 * akışından (tek iş parçacığı) çağrılmak üzere tasarlandı.
 */
class TfLiteDetector(
    private val interpreter: Interpreter,
    private val char2id: Map<String, Int>,
    private val maxLen: Int,
    private val threshold: Float,
) : Detector {

    private val turkish = Locale.forLanguageTag("tr")
    private val input = Array(1) { IntArray(maxLen) }
    private val output = Array(1) { FloatArray(1) }

    override fun isBettingContent(text: String): Boolean = score(text) >= threshold

    /** 0..1 arası teşvik skoru — eşik kalibrasyonu ve hata ayıklama için açık. */
    fun score(text: String): Float {
        preprocess(text, input[0])
        interpreter.run(input, output)
        return output[0][0]
    }

    /** spec/ON_ISLEME.md adımları: NFC → tr küçük harf → kodpoint→id → 192'ye kes/doldur.
     *  U+0307 (birleşik nokta) silinir: ayrık yazılmış "i̇" Python tarafıyla aynı işlensin. */
    private fun preprocess(text: String, dest: IntArray) {
        val lower = Normalizer.normalize(text, Normalizer.Form.NFC)
            .lowercase(turkish)
            .replace("̇", "")
        var i = 0
        val it = lower.codePoints().iterator()
        while (i < maxLen && it.hasNext()) {
            val cp = it.nextInt()
            dest[i++] = char2id[String(Character.toChars(cp))] ?: OOV
        }
        while (i < maxLen) dest[i++] = PAD
    }

    companion object {
        private const val PAD = 0
        private const val OOV = 1

        /** Önerilen eşik — eğitimin doğrulama bölmesinden (model/cikti/esik.json);
         *  model her yeniden eğitildiğinde degerlendir.py çıktısıyla güncellenir.
         *  13 Temmuz nihai Colab eğitimi (Optuna ayarlı, sentetik+gerçek veri):
         *  sentetik kabul %96 (0 yanlış alarm), GERÇEK saha seti %94.2,
         *  tuzaklarda 0 yanlış alarm, model 88 KB, 0.12 ms/metin. */
        const val VARSAYILAN_ESIK = 0.63f

        fun fromAssets(context: Context, threshold: Float = VARSAYILAN_ESIK): TfLiteDetector {
            val model = context.assets.open("model.tflite").readBytes()
            val buffer = java.nio.ByteBuffer.allocateDirect(model.size)
                .order(java.nio.ByteOrder.nativeOrder())
            buffer.put(model)
            buffer.rewind()

            val vocab = JSONObject(
                context.assets.open("model_vocab.json").bufferedReader().use { it.readText() },
            )
            val chars = vocab.getJSONObject("karakterler")
            val char2id = buildMap {
                for (key in chars.keys()) put(key, chars.getInt(key))
            }
            return TfLiteDetector(
                interpreter = Interpreter(buffer),
                char2id = char2id,
                maxLen = vocab.getInt("max_len"),
                threshold = threshold,
            )
        }
    }
}

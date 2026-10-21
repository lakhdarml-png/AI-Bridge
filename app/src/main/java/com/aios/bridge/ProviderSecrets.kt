package com.aios.bridge

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** Encrypts provider API keys with a non-exportable Android Keystore AES-GCM key. */
object ProviderSecrets {
    private const val STORE = "neo_local_provider_secrets"
    private const val KEY_ALIAS = "neo_local_provider_aes_gcm"
    private const val TRANSFORMATION = "AES/GCM/NoPadding"

    private fun secretKey(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        val existing = store.getKey(KEY_ALIAS, null) as? SecretKey
        if (existing != null) return existing
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        generator.init(KeyGenParameterSpec.Builder(
            KEY_ALIAS,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        ).setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setRandomizedEncryptionRequired(true)
            .build())
        return generator.generateKey()
    }

    fun save(context: Context, provider: String, value: String) {
        require(provider == "openai" || provider == "xai") { "مزود غير معروف" }
        require(value.isNotBlank()) { "المفتاح فارغ" }
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, secretKey())
        val encrypted = cipher.doFinal(value.toByteArray(Charsets.UTF_8))
        val packed = cipher.iv + encrypted
        context.getSharedPreferences(STORE, Context.MODE_PRIVATE).edit()
            .putString(provider, Base64.encodeToString(packed, Base64.NO_WRAP))
            .apply()
    }

    fun load(context: Context, provider: String): String {
        val packedText = context.getSharedPreferences(STORE, Context.MODE_PRIVATE)
            .getString(provider, null) ?: throw IllegalStateException(
                if (provider == "openai") "أدخل مفتاح OpenAI API واحفظه." else "أدخل مفتاح xAI API واحفظه."
            )
        val packed = Base64.decode(packedText, Base64.NO_WRAP)
        require(packed.size > 12) { "بيانات المفتاح المحفوظ تالفة." }
        val iv = packed.copyOfRange(0, 12)
        val ciphertext = packed.copyOfRange(12, packed.size)
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.DECRYPT_MODE, secretKey(), GCMParameterSpec(128, iv))
        return String(cipher.doFinal(ciphertext), Charsets.UTF_8)
    }
}

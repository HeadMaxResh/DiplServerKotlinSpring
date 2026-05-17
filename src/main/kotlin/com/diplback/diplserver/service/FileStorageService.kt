package com.diplback.diplserver.service

import com.sksamuel.scrimage.ImmutableImage
import com.sksamuel.scrimage.webp.WebpWriter
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service
import org.springframework.web.multipart.MultipartFile
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import java.nio.file.StandardCopyOption
import java.util.UUID

@Service
class FileStorageService(
    @Value("\${app.upload.dir}") private val uploadDir: String
) {
    private val rootPath: Path
        get() = Paths.get(uploadDir).toAbsolutePath().normalize()

    fun saveUserAvatar(userId: Int, file: MultipartFile): String {
        validateImage(file)

        val userDir = rootPath.resolve("users").resolve(userId.toString())
        Files.createDirectories(userDir)

        val avatarPath = userDir.resolve("avatar.webp")

        val image = ImmutableImage.loader().fromStream(file.inputStream)
        image
            .max(600, 600)
            .output(WebpWriter.DEFAULT.withQ(85), avatarPath.toFile())

        return "/uploads/users/$userId/avatar.webp"
    }

    fun saveApartmentPhotos(apartmentId: Int, files: List<MultipartFile>): List<String> {
        val originalDir = rootPath
            .resolve("apartments")
            .resolve(apartmentId.toString())
            .resolve("original")

        val previewDir = rootPath
            .resolve("apartments")
            .resolve(apartmentId.toString())
            .resolve("preview")

        Files.createDirectories(originalDir)
        Files.createDirectories(previewDir)

        return files.map { file ->
            validateImage(file)

            val uuid = UUID.randomUUID().toString()
            val originalExtension = getExtension(file.originalFilename)
            val originalFileName = "$uuid.$originalExtension"
            val previewFileName = "$uuid.webp"

            val originalPath = originalDir.resolve(originalFileName)
            val previewPath = previewDir.resolve(previewFileName)

            file.inputStream.use { input ->
                Files.copy(input, originalPath, StandardCopyOption.REPLACE_EXISTING)
            }

            val image = ImmutableImage.loader().fromFile(originalPath.toFile())
            image
                .max(1280, 900)
                .output(WebpWriter.DEFAULT.withQ(80), previewPath.toFile())

            "/uploads/apartments/$apartmentId/preview/$previewFileName"
        }
    }

    private fun validateImage(file: MultipartFile) {
        if (file.isEmpty) {
            throw IllegalArgumentException("Файл пустой")
        }
    }

    private fun getExtension(fileName: String?): String {
        return fileName
            ?.substringAfterLast('.', "jpg")
            ?.lowercase()
            ?.takeIf { it in listOf("jpg", "jpeg", "png", "webp") }
            ?: "jpg"
    }
}
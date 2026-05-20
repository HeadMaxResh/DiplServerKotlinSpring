package com.diplback.diplserver

import org.springframework.core.io.InputStreamResource
import java.io.InputStream

class MultipartInputStreamFileResource(
    inputStream: InputStream,
    private val filename: String
) : InputStreamResource(inputStream) {

    override fun getFilename(): String {
        return filename
    }

    override fun contentLength(): Long {
        return -1
    }
}
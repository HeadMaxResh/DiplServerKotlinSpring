package com.diplback.diplserver.service

import com.diplback.diplserver.MultipartInputStreamFileResource
import com.diplback.diplserver.dto.CalculateFromAnalysisRequest
import org.springframework.http.HttpEntity
import org.springframework.http.HttpHeaders
import org.springframework.http.MediaType
import org.springframework.stereotype.Service
import org.springframework.util.LinkedMultiValueMap
import org.springframework.web.client.RestTemplate
import org.springframework.web.multipart.MultipartFile

@Service
class MlServiceClient(
    private val restTemplate: RestTemplate
) {

    private val mlBaseUrl = "http://localhost:8000"

    fun calculateFromAnalysis(requestBody: CalculateFromAnalysisRequest): String {
        val headers = HttpHeaders()
        headers.contentType = MediaType.APPLICATION_JSON

        val request = HttpEntity(requestBody, headers)

        return restTemplate.postForObject(
            "$mlBaseUrl/calculate-from-analysis",
            request,
            String::class.java
        ) ?: "{}"
    }

    fun analyzePhotos(photos: List<MultipartFile>): String {
        val body = LinkedMultiValueMap<String, Any>()

        photos.forEach { photo ->
            body.add(
                "photos",
                MultipartInputStreamFileResource(
                    photo.inputStream,
                    photo.originalFilename ?: "photo.jpg"
                )
            )
        }

        return postMultipart("$mlBaseUrl/analyze-photos", body)
    }

    fun analyzeLocation(address: String): String {
        val body = LinkedMultiValueMap<String, String>()
        body.add("address", address)

        val headers = HttpHeaders()
        headers.contentType = MediaType.APPLICATION_FORM_URLENCODED

        val request = HttpEntity(body, headers)

        return restTemplate.postForObject(
            "$mlBaseUrl/analyze-location",
            request,
            String::class.java
        ) ?: "{}"
    }

    fun analyzeText(description: String): String {
        val body = LinkedMultiValueMap<String, String>()
        body.add("description", description)

        val headers = HttpHeaders()
        headers.contentType = MediaType.APPLICATION_FORM_URLENCODED

        val request = HttpEntity(body, headers)

        return restTemplate.postForObject(
            "$mlBaseUrl/analyze-text",
            request,
            String::class.java
        ) ?: "{}"
    }

    fun evaluateApartment(
        description: String,
        address: String,
        rooms: String,
        area: String,
        photos: List<MultipartFile>
    ): String {
        val body = LinkedMultiValueMap<String, Any>()

        body.add("description", description)
        body.add("address", address)
        body.add("rooms", rooms)
        body.add("area", area)

        photos.forEach { photo ->
            body.add(
                "photos",
                MultipartInputStreamFileResource(
                    photo.inputStream,
                    photo.originalFilename ?: "photo.jpg"
                )
            )
        }

        return postMultipart("$mlBaseUrl/evaluate-apartment", body)
    }

    private fun postMultipart(
        url: String,
        body: LinkedMultiValueMap<String, Any>
    ): String {
        val headers = HttpHeaders()
        headers.contentType = MediaType.MULTIPART_FORM_DATA

        val request = HttpEntity(body, headers)

        return restTemplate.postForObject(
            url,
            request,
            String::class.java
        ) ?: "{}"
    }
}
package com.diplback.diplserver.controller

import com.diplback.diplserver.dto.CalculateFromAnalysisRequest
import com.diplback.diplserver.service.MlServiceClient
import org.springframework.http.MediaType
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import org.springframework.web.multipart.MultipartFile

@RestController
@RequestMapping("/api/apartments")
class ApartmentAnalysisController(
    private val mlServiceClient: MlServiceClient
) {

    @PostMapping(
        "/calculate-from-analysis",
        consumes = [MediaType.APPLICATION_JSON_VALUE]
    )
    fun calculateFromAnalysis(
        @RequestBody request: CalculateFromAnalysisRequest
    ): ResponseEntity<String> {
        return ResponseEntity.ok(
            mlServiceClient.calculateFromAnalysis(request)
        )
    }

    @PostMapping(
        "/analyze-photos",
        consumes = [MediaType.MULTIPART_FORM_DATA_VALUE]
    )
    fun analyzePhotos(
        @RequestPart("photos") photos: List<MultipartFile>
    ): ResponseEntity<String> {
        return ResponseEntity.ok(
            mlServiceClient.analyzePhotos(photos)
        )
    }

    @PostMapping(
        "/analyze-location",
        consumes = [MediaType.APPLICATION_FORM_URLENCODED_VALUE]
    )
    fun analyzeLocation(
        @RequestParam address: String
    ): ResponseEntity<String> {
        return ResponseEntity.ok(
            mlServiceClient.analyzeLocation(address)
        )
    }

    @PostMapping(
        "/analyze-text",
        consumes = [MediaType.APPLICATION_FORM_URLENCODED_VALUE]
    )
    fun analyzeText(
        @RequestParam description: String
    ): ResponseEntity<String> {
        return ResponseEntity.ok(
            mlServiceClient.analyzeText(description)
        )
    }

    @PostMapping(
        "/evaluate",
        consumes = [MediaType.MULTIPART_FORM_DATA_VALUE]
    )
    fun evaluateApartment(
        @RequestPart("description") description: String,
        @RequestPart("address") address: String,
        @RequestPart("rooms") rooms: String,
        @RequestPart("area") area: String,
        @RequestPart("photos") photos: List<MultipartFile>
    ): ResponseEntity<String> {
        return ResponseEntity.ok(
            mlServiceClient.evaluateApartment(
                description = description,
                address = address,
                rooms = rooms,
                area = area,
                photos = photos
            )
        )
    }
}
package com.diplback.diplserver.dto

data class CalculateFromAnalysisRequest(
    val area: Double,
    val rooms: Int,
    val textAnalysis: Map<String, Any>,
    val imageAnalysis: Map<String, Any>,
    val geoAnalysis: Map<String, Any>
)
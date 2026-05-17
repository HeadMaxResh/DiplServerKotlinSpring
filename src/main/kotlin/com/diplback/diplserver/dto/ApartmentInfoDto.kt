package com.diplback.diplserver.dto

import com.diplback.diplserver.model.User

data class ApartmentInfoDto(
    val name: String,
    val city: String,
    val rent: Int,
    val rate: Double,
    val area: Float,
    val listImages: List<String>,
    val countRooms: Int,
    val userOwner: User,
    val description: String,
    val cadastr: String
)
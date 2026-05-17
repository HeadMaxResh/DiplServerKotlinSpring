package com.diplback.diplserver.model

import com.diplback.diplserver.Table
import jakarta.persistence.*
import java.util.Collections.emptyList


@Entity(name = Table.TABLE_APARTMENT)
data class ApartmentInfo(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Int = -1,
    var name: String,
    var city: String,
    val rent: Int,
    var area: Float,
    var listImages: List<String>,
    var countRooms: Int,
    var rate: Double,
    @ManyToOne
    val userOwner: User,
    //@Lob
    var description: String,
    @OneToMany
    val reviewList: MutableList<Review> = emptyList(),
    var hide: Boolean = false,
    val cadastr: String
)
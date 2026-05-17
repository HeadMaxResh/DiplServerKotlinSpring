package com.diplback.diplserver.controller

import com.diplback.diplserver.dto.ApartmentInfoDto
import com.diplback.diplserver.dto.ReviewDto
import com.diplback.diplserver.model.ApartmentInfo
import com.diplback.diplserver.model.Review
import com.diplback.diplserver.repository.ApartmentInfoRepo
import com.diplback.diplserver.repository.ReviewRepo
import com.diplback.diplserver.repository.UserRepo
import com.diplback.diplserver.service.FileStorageService
import jakarta.persistence.EntityNotFoundException
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import org.springframework.web.multipart.MultipartFile
import java.nio.file.Files
import java.nio.file.Paths
import java.util.*
import kotlin.math.roundToInt

@RestController
@RequestMapping("/apartments")
class ApartmentInfoController {

    @Autowired
    lateinit var apartmentInfoRepo: ApartmentInfoRepo

    @Autowired
    lateinit var userRepo: UserRepo

    @Autowired
    lateinit var reviewRepo: ReviewRepo

    @Value("\${app.upload.dir}")
    lateinit var uploadDir: String

    @Autowired
    lateinit var fileStorageService: FileStorageService

    @GetMapping("/all")
    fun getAllApartments(): List<ApartmentInfo>? = apartmentInfoRepo.findAllApartments()

    @GetMapping("/search/{name}")
    fun getByName(
        @PathVariable name: String
    ): List<ApartmentInfo>? = apartmentInfoRepo.findByName(name)

    @GetMapping("/filter/{city}/{minRent}/{maxRent}/{minArea}/{maxArea}/{countRooms}")
    fun getByFilter(
        @PathVariable city: String,
        @PathVariable minRent: Int,
        @PathVariable maxRent: Int,
        @PathVariable minArea: Float,
        @PathVariable maxArea: Float,
        @PathVariable countRooms: Int?
    ): List<ApartmentInfo>? = apartmentInfoRepo.findByFilter(
        city,
        minRent,
        maxRent,
        minArea,
        maxArea,
        countRooms
    )

    @GetMapping("/{id}")
    fun getByApartmentId(
        @PathVariable id: Int
    ): ApartmentInfo = apartmentInfoRepo.findByApartmentId(id)

    @GetMapping("/userapartments/{userOwnerId}")
    fun getByAllApartmentsByUser(
        @PathVariable userOwnerId: Int
    ): List<ApartmentInfo> = apartmentInfoRepo.findAllApartmentsByUser(userOwnerId)

    @PostMapping("/add")
    fun setApartment(
        //@PathVariable userId: Int,
        @RequestBody apartmentInfoDto: ApartmentInfoDto,
    ): ApartmentInfo {

        val user =
            userRepo.findById(apartmentInfoDto.userOwner.id).orElseThrow { EntityNotFoundException("User not found") }

        val apartmentInfo = ApartmentInfo(
            name = apartmentInfoDto.name,
            city = apartmentInfoDto.city,
            area = apartmentInfoDto.area,
            countRooms = apartmentInfoDto.countRooms,
            description = apartmentInfoDto.description,
            rent = apartmentInfoDto.rent,
            userOwner = user,
            listImages = apartmentInfoDto.listImages,
            rate = apartmentInfoDto.rate,
            cadastr = apartmentInfoDto.cadastr
        )
        /*return apartmentInfoRepo.save(
            ApartmentInfo(
                name = apartmentInfoDto.name,
                city = apartmentInfoDto.city,
                area = apartmentInfoDto.area,
                countRooms = apartmentInfoDto.countRooms,
                description = apartmentInfoDto.description,
                rent = apartmentInfoDto.rent,
                userOwner = userRepo.findById(userId).get(),
                listImages = apartmentInfoDto.listImages
            )
        )*/
        return apartmentInfoRepo.save(apartmentInfo)
    }

    @PostMapping("/{apartmentId}/review/add")
    fun addReviewToApartment(
        @PathVariable apartmentId: Int,
        @RequestBody reviewDto: ReviewDto
    ): Review {
        val apartmentInfo = apartmentInfoRepo.findByApartmentId(apartmentId)

        val user = userRepo.findById(reviewDto.user.id).orElseThrow { EntityNotFoundException("User not found") }

        val existingReview = apartmentInfo.reviewList.find { it.user.id == user.id }

        if (existingReview != null) {

            existingReview.rate = reviewDto.rate
            existingReview.dignityText = reviewDto.dignityText
            existingReview.flawsText = reviewDto.flawsText
            existingReview.commentText = reviewDto.commentText


            val updatedReview = reviewRepo.save(existingReview)
            updateApartmentRating(apartmentInfo)
            apartmentInfoRepo.save(apartmentInfo)
            return updatedReview
        }

        val review = Review(
            rate = reviewDto.rate,
            user = user,
            dignityText = reviewDto.dignityText,
            flawsText = reviewDto.flawsText,
            commentText = reviewDto.commentText,
            //apartmentInfo = apartmentInfo
        )
        /*val savedReview = reviewRepo.save(review)

        val updatedApartmentInfo = apartmentInfo.apply {
            reviewList.add(savedReview)
        }
        apartmentInfoRepo.save(updatedApartmentInfo)

        return savedReview*/

        apartmentInfo.reviewList.add(review)

        val savedReview = reviewRepo.save(review)
        updateApartmentRating(apartmentInfo)
        apartmentInfoRepo.save(apartmentInfo)

        return review
    }

    @DeleteMapping("/{id}/delete")
    fun deleteApartment(@PathVariable id: Int) {
        val apartmentInfo = apartmentInfoRepo.findById(id)
            .orElseThrow { EntityNotFoundException("ApartmentInfo not found") }
        apartmentInfoRepo.delete(apartmentInfo)
    }

    @PutMapping("/{id}/update")
    fun updateApartment(
        @PathVariable id: Int,
        @RequestBody updatedApartmentInfo: ApartmentInfoDto
    ): ApartmentInfo {
        val apartmentInfo = apartmentInfoRepo.findById(id)
            .orElseThrow { EntityNotFoundException("ApartmentInfo not found") }

        apartmentInfo.name = updatedApartmentInfo.name
        apartmentInfo.city = updatedApartmentInfo.city
        apartmentInfo.rate = updatedApartmentInfo.rate
        apartmentInfo.area = updatedApartmentInfo.area
        apartmentInfo.listImages = updatedApartmentInfo.listImages
        apartmentInfo.countRooms = updatedApartmentInfo.countRooms
        apartmentInfo.description = updatedApartmentInfo.description

        return apartmentInfoRepo.save(apartmentInfo)
    }

    private fun updateApartmentRating(apartmentInfo: ApartmentInfo) {
        val totalReviews = apartmentInfo.reviewList.size
        if (totalReviews > 0) {
            val totalRating = apartmentInfo.reviewList.sumOf { it.rate }
            val averageRating = totalRating.toDouble() / totalReviews
            val roundedRating = (averageRating * 10).roundToInt() / 10.0
            apartmentInfo.rate = roundedRating
        } else {
            apartmentInfo.rate = 0.0 // Если нет отзывов, средняя оценка равна 0
        }
    }

    @PutMapping("/{id}/hide")
    fun setApartmentHideStatus(
        @PathVariable id: Int
    ): ApartmentInfo {
        val apartmentInfo = apartmentInfoRepo.findById(id)
            .orElseThrow { EntityNotFoundException("ApartmentInfo not found") }

        apartmentInfo.hide = true

        return apartmentInfoRepo.save(apartmentInfo)
    }

    @PutMapping("/{id}/show")
    fun setApartmentShowStatus(
        @PathVariable id: Int
    ): ApartmentInfo {
        val apartmentInfo = apartmentInfoRepo.findById(id)
            .orElseThrow { EntityNotFoundException("ApartmentInfo not found") }

        apartmentInfo.hide = false

        return apartmentInfoRepo.save(apartmentInfo)
    }

    @GetMapping("/{id}/status")
    fun getApartmentHideStatus(
        @PathVariable id: Int
    ): Boolean {
        val apartmentInfo = apartmentInfoRepo.findById(id)
            .orElseThrow { EntityNotFoundException("ApartmentInfo not found") }

        return apartmentInfo.hide
    }

    /*@PostMapping("/{apartmentId}/photos")
    fun uploadApartmentPhotos(
        @PathVariable apartmentId: Int,
        @RequestParam("files") files: List<MultipartFile>
    ): ResponseEntity<ApartmentInfo> {
        val apartment = apartmentInfoRepo.findByApartmentId(apartmentId)

        val uploadsPath = Paths.get(uploadDir)
            .toAbsolutePath()
            .normalize()

        Files.createDirectories(uploadsPath)

        val imageUrls = files.map { file ->
            val extension = file.originalFilename
                ?.substringAfterLast('.', "jpg")
                ?: "jpg"

            val fileName = "${UUID.randomUUID()}.$extension"
            val targetPath = uploadsPath.resolve(fileName)

            file.inputStream.use { input ->
                Files.copy(input, targetPath)
            }

            "/uploads/$fileName"
        }

        apartment.listImages = imageUrls

        val savedApartment = apartmentInfoRepo.save(apartment)

        return ResponseEntity.ok(savedApartment)
    }*/

    @PostMapping("/{apartmentId}/photos")
    fun uploadApartmentPhotos(
        @PathVariable apartmentId: Int,
        @RequestParam("files") files: List<MultipartFile>
    ): ResponseEntity<ApartmentInfo> {
        val apartment = apartmentInfoRepo.findByApartmentId(apartmentId)

        val previewUrls = fileStorageService.saveApartmentPhotos(apartmentId, files)

        apartment.listImages = previewUrls

        return ResponseEntity.ok(apartmentInfoRepo.save(apartment))
    }

}
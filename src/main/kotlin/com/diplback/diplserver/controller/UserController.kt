package com.diplback.diplserver.controller

import com.diplback.diplserver.dto.UpdatedUserDto
import com.diplback.diplserver.dto.UserDto
import com.diplback.diplserver.model.ApartmentInfo
import com.diplback.diplserver.model.User
import com.diplback.diplserver.repository.ApartmentInfoRepo
import com.diplback.diplserver.repository.UserRepo
import com.diplback.diplserver.service.ElectronicSignatureService
import com.diplback.diplserver.service.FileStorageService
import jakarta.persistence.EntityNotFoundException
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import org.springframework.web.multipart.MultipartFile
import java.nio.file.Files
import java.nio.file.Paths
import java.util.UUID

@RestController
@RequestMapping("/")
class UserController {

    @Autowired
    lateinit var userRepo: UserRepo
    @Autowired
    lateinit var apartmentInfoRepo: ApartmentInfoRepo

    @Autowired
    lateinit var electronicSignatureService: ElectronicSignatureService

    @GetMapping("/users")
    fun getAll(): List<User> = userRepo.findAll().toList()

    @Value("\${app.upload.dir}")
    lateinit var uploadDir: String

    @Autowired
    lateinit var fileStorageService: FileStorageService

    @PostMapping("/login")
    fun login(@RequestBody userDto: UserDto): ResponseEntity<User?> {
        val user = userRepo.findByPhone(userDto.phone) ?:
            return ResponseEntity(null, HttpStatus.NOT_FOUND)
        if (user.password != userDto.password )
            return ResponseEntity(null, HttpStatus.BAD_REQUEST)
        return ResponseEntity(user, HttpStatus.OK)
    }

    @PostMapping("/register")
    fun register(@RequestBody userDto: UserDto): ResponseEntity<Boolean> {
        /*val user = userRepo.findByPhone(userDto.phone) ?:
            return ResponseEntity(false, HttpStatus.UNPROCESSABLE_ENTITY)*/
        userRepo.save(User(name = userDto.name, surname = userDto.surname, phone = userDto.phone, password = userDto.password, rate = 5, email = "", photoUser = "" ))
        return ResponseEntity(true, HttpStatus.OK)
    }

    @GetMapping("/user/{userId}")
    fun getUserById(@PathVariable userId: Int): ResponseEntity<User> {
        val user = userRepo.findById(userId).orElse(null)

        return user?.let {
            ResponseEntity.ok(it)
        } ?: ResponseEntity.notFound().build()
    }

    @GetMapping("/user/{userName}/name")
    fun getUserByName(@PathVariable userName: String): ResponseEntity<User> {
        val user = userRepo.findByName(userName)

        return user?.let {
            ResponseEntity.ok(it)
        } ?: ResponseEntity.notFound().build()
    }

    @GetMapping("/user/{userId}/generateSignature")
    fun generateElectronicSignature(@PathVariable userId: Int): String {
        return electronicSignatureService.generateElectronicSignature(userId)
    }

    @PostMapping("/user/{userId}/edit")
    fun updateUser(
        @PathVariable userId: Int,
        @RequestBody updatedUserDto: UpdatedUserDto
    ): ResponseEntity<User> {
        val user = userRepo.findById(userId).orElseThrow { EntityNotFoundException("User not found") }

        user.name = updatedUserDto.name
        user.surname = updatedUserDto.surname
        user.email = updatedUserDto.email
        user.phone = updatedUserDto.phone
        user.password = updatedUserDto.password
        user.photoUser = updatedUserDto.photoUser

        val updatedUser = userRepo.save(user)

        return ResponseEntity.ok(updatedUser)
    }

    @PostMapping("/apartments/favorite/{apartmentId}/user/{userId}")
    fun addFavoriteApartment(
        @PathVariable userId: Int,
        @PathVariable apartmentId: Int
    ): ResponseEntity<Boolean> {
        val user = userRepo.findById(userId).orElseThrow { EntityNotFoundException("User not found") }
        val apartment = apartmentInfoRepo.findByApartmentId(apartmentId)

        user.favoriteApartments.add(apartment)
        userRepo.save(user)

        return ResponseEntity(true, HttpStatus.OK)
    }

    @PostMapping("/apartments/favorite/{apartmentId}/user/{userId}/remove")
    fun removeFavoriteApartment(
        @PathVariable userId: Int,
        @PathVariable apartmentId: Int
    ): ResponseEntity<Boolean> {
        val user = userRepo.findById(userId).orElseThrow { EntityNotFoundException("User not found") }
        val apartment = apartmentInfoRepo.findByApartmentId(apartmentId)

        if (user.favoriteApartments.contains(apartment)) {
            user.favoriteApartments.remove(apartment)
            userRepo.save(user)
            return ResponseEntity(true, HttpStatus.OK)
        } else {
            // Квартира не найдена в списке понравившихся пользователя
            return ResponseEntity(false, HttpStatus.NOT_FOUND)
        }
    }

    @GetMapping("/apartments/favorite/user/{userId}")
    fun getFavoriteApartments(
        @PathVariable userId: Int
    ): List<ApartmentInfo> {
        val user = userRepo.findById(userId).orElseThrow { EntityNotFoundException("User not found") }
        return user.favoriteApartments
    }

    @GetMapping("/apartments/favorite/{apartmentId}/user/{userId}/check")
    fun checkIfApartmentIsFavorite(
        @PathVariable userId: Int,
        @PathVariable apartmentId: Int
    ): ResponseEntity<Boolean> {
        val user = userRepo.findById(userId).orElseThrow { EntityNotFoundException("User not found") }
        val apartment = apartmentInfoRepo.findByApartmentId(apartmentId)

        val isFavorite = user.favoriteApartments.contains(apartment)

        return ResponseEntity(isFavorite, HttpStatus.OK)
    }

    /*@PostMapping("/user/{userId}/photo")
    fun uploadUserPhoto(
        @PathVariable userId: Int,
        @RequestParam("file") file: MultipartFile
    ): ResponseEntity<User> {
        val user = userRepo.findById(userId)
            .orElseThrow { EntityNotFoundException("User not found") }

        val uploadsPath = Paths.get(uploadDir).toAbsolutePath().normalize()
        Files.createDirectories(uploadsPath)

        val originalName = file.originalFilename ?: "photo.jpg"
        val extension = originalName.substringAfterLast('.', "jpg")
        val fileName = "${UUID.randomUUID()}.$extension"

        val targetPath = uploadsPath.resolve(fileName)
        file.inputStream.use { input ->
            Files.copy(input, targetPath)
        }

        user.photoUser = "/uploads/$fileName"
        val savedUser = userRepo.save(user)

        return ResponseEntity.ok(savedUser)
    }*/

    @PostMapping("/user/{userId}/photo")
    fun uploadUserPhoto(
        @PathVariable userId: Int,
        @RequestParam("file") file: MultipartFile
    ): ResponseEntity<User> {
        val user = userRepo.findById(userId)
            .orElseThrow { EntityNotFoundException("User not found") }

        val photoUrl = fileStorageService.saveUserAvatar(userId, file)

        user.photoUser = photoUrl

        return ResponseEntity.ok(userRepo.save(user))
    }
}
package com.diplback.diplserver.controller

import com.diplback.diplserver.dto.ContractDto
import com.diplback.diplserver.model.Contract
import com.diplback.diplserver.repository.ApartmentInfoRepo
import com.diplback.diplserver.repository.ContractRepo
import com.diplback.diplserver.repository.PassportRepo
import com.diplback.diplserver.repository.UserRepo
import jakarta.persistence.EntityNotFoundException
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/contracts")
class ContractController {

    @Autowired
    lateinit var contractRepo: ContractRepo

    @Autowired
    lateinit var apartmentInfoRepo: ApartmentInfoRepo

    @Autowired
    lateinit var passportRepo: PassportRepo

    @Autowired
    lateinit var userRepo: UserRepo

    @GetMapping("/userSender/{userId}")
    fun getContractsByUserSender(@PathVariable userId: Int): List<Contract> {
        return contractRepo.findByUserSenderId(userId)
    }

    @GetMapping("/userOwner/{userId}")
    fun getContractsByUserOwner(@PathVariable userId: Int): List<Contract> {
        return contractRepo.findByUserOwnerId(userId)
    }

    /*@GetMapping("/id/{id}")
    fun getContractById(@PathVariable id: Int): Optional<Contract> {
        return contractRepo.findById(id)
    }*/

    @GetMapping("/apartmentInfo/{apartmentInfoId}")
    fun getContractsByApartmentInfoId(@PathVariable apartmentInfoId: Int): List<Contract> {
        return contractRepo.findByApartmentInfoId(apartmentInfoId)
    }

    @GetMapping("/usersApartments/{userSenderId}/{userOwnerId}/{apartmentInfoId}")
    fun getContractByUsersAndApartmentInfo(
        @PathVariable userSenderId: Int,
        @PathVariable userOwnerId: Int,
        @PathVariable apartmentInfoId: Int,
    ): Contract? {
        return contractRepo.findByUserSenderAndUserOwnerAndApartmentInfo(userSenderId, userOwnerId, apartmentInfoId)
    }

    @PostMapping("/create")
    fun createContract(
        @RequestBody contractDto: ContractDto,
    ): Contract {

        val apartmentInfo = apartmentInfoRepo.findById(contractDto.apartmentInfoId)
            .orElseThrow { EntityNotFoundException("ApartmentInfo not found") }

        val userOwner = userRepo.findById(contractDto.userOwnerId)
            .orElseThrow { EntityNotFoundException("UserOwner not found") }

        val userSender = userRepo.findById(contractDto.userSenderId)
            .orElseThrow { EntityNotFoundException("UserSender not found") }

        val passportOwner = passportRepo.findPassport(contractDto.userOwnerId)
            ?: throw EntityNotFoundException("PassportOwner not found")

        val passportSender = passportRepo.findPassport(contractDto.userSenderId)
            ?: throw EntityNotFoundException("PassportSender not found")



        val contract = Contract(
            apartmentInfo = apartmentInfo,
            userOwner = userOwner,
            userSender = userSender,
            passportOwner = passportOwner,
            passportSender = passportSender,
            date = contractDto.date,
            ownerElectronicSignature = contractDto.ownerElectronicSignature,
            senderElectronicSignature = contractDto.senderElectronicSignature
        )

        return contractRepo.save(contract)
    }

    @GetMapping("/user/{userId}/contracts")
    fun getContractsByUserSenderOrOwner(@PathVariable userId: Int): List<Contract> {
        return contractRepo.findContractsByUserSenderIdOrUserOwnerId(userId)
    }

    @GetMapping("/all")
    fun getAllContracts(): List<Contract> {
        return contractRepo.findAll().toList()
    }

}
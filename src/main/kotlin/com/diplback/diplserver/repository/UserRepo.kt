package com.diplback.diplserver.repository

import com.diplback.diplserver.Table.TABLE_USER
import com.diplback.diplserver.model.User
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.CrudRepository
import org.springframework.data.repository.query.Param

interface UserRepo : CrudRepository<User, Int> {

    @Query("SELECT r FROM $TABLE_USER r WHERE r.phone LIKE :userPhone")
    fun findByPhone(@Param("userPhone") userPhone: String): User?

    @Query("SELECT u FROM $TABLE_USER u WHERE u.name = :userName")
    fun findByName(@Param("userName") userName: String): User?
}
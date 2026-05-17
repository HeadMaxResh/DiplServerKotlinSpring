package com.diplback.diplserver.interseptor

import com.diplback.diplserver.ServiceConfig
import jakarta.servlet.http.HttpServletRequest
import jakarta.servlet.http.HttpServletResponse
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.http.HttpStatus
import org.springframework.web.servlet.HandlerInterceptor
import org.springframework.web.servlet.ModelAndView


class MyInterceptor : HandlerInterceptor {

    @Autowired
    lateinit var serviceConfig: ServiceConfig

    override fun preHandle(
        request: HttpServletRequest,
        response: HttpServletResponse,
        handler: Any
    ): Boolean {

        val authorizationHeader = request.getHeader("Authorization")

        if (authorizationHeader != null && authorizationHeader.startsWith("Bearer ")) {
            val accessToken = authorizationHeader.substringAfter("Bearer ")

            if (isValidAccessToken(accessToken)) {
                return true
            }
        }

        //response.sendError(HttpServletResponse.SC_UNAUTHORIZED, "Unauthorized access")
        return true
    }

    override fun postHandle(
        request: HttpServletRequest,
        response: HttpServletResponse,
        handler: Any,
        modelAndView: ModelAndView?,
    ) {
        super.postHandle(request, response, handler, modelAndView)
    }

    private fun isValidAccessToken(accessToken: String): Boolean {

        return true
    }
}
package com.diplback.diplserver

import com.diplback.diplserver.interseptor.MyInterceptor
import org.springframework.beans.factory.annotation.Value
import org.springframework.boot.context.properties.ConfigurationProperties
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.messaging.simp.config.MessageBrokerRegistry
import org.springframework.web.client.RestTemplate
import org.springframework.web.servlet.config.annotation.InterceptorRegistry
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker
import org.springframework.web.socket.config.annotation.StompEndpointRegistry
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer
import java.nio.file.Paths


@Configuration
class WebConfig : WebMvcConfigurer {

    @Value("\${app.upload.dir}")
    lateinit var uploadDir: String

    override fun addInterceptors(registry: InterceptorRegistry) {
        registry
            .addInterceptor(myInterceptor())
            .addPathPatterns("/**")
    }

    override fun addResourceHandlers(registry: ResourceHandlerRegistry) {

        val uploadPath = Paths.get(uploadDir)
            .toAbsolutePath()
            .normalize()
            .toUri()
            .toString()

        registry.addResourceHandler("/uploads/**")
            .addResourceLocations(uploadPath)
    }

    @Bean
    fun myInterceptor(): MyInterceptor = MyInterceptor()
}


@Configuration
@EnableWebSocketMessageBroker
class WebSocketConfig : WebSocketMessageBrokerConfigurer {
    override fun configureMessageBroker(config: MessageBrokerRegistry) {
        config.enableSimpleBroker("/topics")
        config.setApplicationDestinationPrefixes("/app")
    }

    override fun registerStompEndpoints(registry: StompEndpointRegistry) {
        registry.addEndpoint("/my-ws").setAllowedOrigins("*").withSockJS()
    }
}

@Configuration
@ConfigurationProperties(prefix = "services")
class ServiceConfig {

    var questions: Boolean = true
    var tasks: Boolean = true
    var events: Boolean = true
    var map: Boolean = true
}

@Configuration
class RestTemplateConfig {

    @Bean
    fun restTemplate(): RestTemplate {
        return RestTemplate()
    }
}


package tn.spring.clubevent.Communication;

import feign.RequestInterceptor;
import feign.RequestTemplate;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.context.annotation.Bean;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

/**
 * Forward the incoming JWT to inter-service Feign calls.
 */
public class FeignConfig {

    @Bean
    public RequestInterceptor forwardAuthorizationInterceptor() {
        return new RequestInterceptor() {
            @Override
            public void apply(RequestTemplate template) {
                var attrs = RequestContextHolder.getRequestAttributes();
                if (!(attrs instanceof ServletRequestAttributes servletAttrs)) return;
                HttpServletRequest request = servletAttrs.getRequest();
                String auth = request.getHeader("Authorization");
                if (auth != null && !auth.isBlank()) {
                    template.header("Authorization", auth);
                }
            }
        };
    }
}

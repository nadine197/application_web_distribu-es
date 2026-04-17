package tn.spring.clubevent.Communication;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import java.util.Map;

import tn.spring.clubevent.Communication.FeignConfig;

@FeignClient(name = "User", configuration = FeignConfig.class)
public interface UserClient {

    @GetMapping("/api/users/{id}")
    Map<String, Object> getUserById(@PathVariable("id") String id);
}

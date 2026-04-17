package tn.spring.quiz.controllers;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import tn.spring.quiz.Feign.UserClient;
import tn.spring.quiz.Feign.UserDTO;

import java.util.List;

/**
 * Proxies the student list from the User service via Feign (Eureka load-balanced).
 * Replaces the previous RestTemplate + hardcoded URL approach.
 */
@RestController
@RequestMapping("/api/evaluations/students")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class EvaluationStudentsProxyController {

    private final UserClient userClient;

    @GetMapping
    @PreAuthorize("hasAnyRole('SUPER_ADMIN','ADMIN','TUTOR')")
    public ResponseEntity<List<UserDTO>> listStudentsForEvaluation() {
        return ResponseEntity.ok(userClient.getAllStudents());
    }
}

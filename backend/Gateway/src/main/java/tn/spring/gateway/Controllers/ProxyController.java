package tn.spring.gateway.Controllers;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.cloud.client.ServiceInstance;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import java.net.URI;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Single generic proxy controller.
 * Replaces all individual ProxyControllers (Auth, User, Course, Appointment, etc.)
 *
 * Routes are declared as a prefix → Eureka service-name map.
 * Every incoming request is matched against the prefix list (longest prefix wins),
 * the target service is resolved via Eureka, and the request is forwarded transparently.
 */
@RestController
public class ProxyController {

    private final RestTemplate restTemplate;
    private final DiscoveryClient discoveryClient;

    /**
     * Prefix → Eureka service name (longest prefix matched first).
     * Order matters: more-specific prefixes must come before broader ones.
     */
    private static final Map<String, String> ROUTES = new LinkedHashMap<>() {{
        // Auth & Users  → User service
        put("/api/auth",          "User");
        put("/api/users",         "User");
        // Courses, Contents, Study-groups → Course service
        put("/api/courses",       "Course");
        put("/api/contents",      "Course");
        put("/api/study-groups",  "Course");
        // Appointments, Availabilities → Appointment service
        put("/api/appointments",  "Appointment");
        put("/api/availabilities","Appointment");
        // Discussion groups & messages → Appointment service (chat is in Appointment)
        put("/api/discussions",   "Appointment");
        // Clubs & Events → ClubEvent service
        put("/api/clubs",         "ClubEvent");
        put("/api/events",        "ClubEvent");
        put("/api/feedbacks",     "ClubEvent");
        // Packages, Payments, Promos, Stripe, Flouci → Package service
        put("/api/packages",      "Package");
        put("/api/subscriptions", "Package");
        put("/api/promos",        "Package");
        put("/api/payments",      "Package");
        put("/api/stripe",        "Package");
        put("/api/flouci",        "Package");
        // Quiz, Questions, Evaluations, Results → Quiz service
        put("/api/quizzes",       "Quiz");
        put("/api/questions",     "Quiz");
        put("/api/results",       "Quiz");
        put("/api/evaluations",   "Quiz");
        // Recommendations → Python recommendation-service
        put("/api/recommendations", "recommendation-service");
    }};

    public ProxyController(RestTemplate restTemplate, DiscoveryClient discoveryClient) {
        this.restTemplate    = restTemplate;
        this.discoveryClient = discoveryClient;
    }

    // ── Catch-all: handle every HTTP method ──────────────────────────────────
    @RequestMapping("/**")
    public ResponseEntity<byte[]> proxy(
            HttpServletRequest req,
            @RequestBody(required = false) byte[] body) {

        String path = req.getRequestURI();

        // 1. Resolve target service name (longest matching prefix)
        String serviceName = resolveService(path);
        if (serviceName == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(("No route for path: " + path).getBytes());
        }

        // 2. Resolve service instance via Eureka
        List<ServiceInstance> instances = discoveryClient.getInstances(serviceName);
        if (instances == null || instances.isEmpty()) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body(("Service unavailable: " + serviceName).getBytes());
        }
        URI base = instances.get(0).getUri();   // load-balancing: first healthy instance

        // 3. Build target URL (path + query string)
        String query       = req.getQueryString();
        String targetUrl   = base.toString() + path + (query != null ? "?" + query : "");

        // 4. Copy headers from incoming request + inject X-User-Id / X-User-Role
        HttpHeaders headers = new HttpHeaders();
        java.util.Collections.list(req.getHeaderNames()).forEach(name -> {
            // skip hop-by-hop headers
            if (!name.equalsIgnoreCase("host") &&
                !name.equalsIgnoreCase("connection") &&
                !name.equalsIgnoreCase("transfer-encoding")) {
                headers.set(name, req.getHeader(name));
            }
        });

        // Inject user context extracted by GatewayJwtFilter
        String userId = (String) req.getAttribute("userId");
        String role   = (String) req.getAttribute("role");
        if (userId != null) headers.set("X-User-Id",   userId);
        if (role   != null) headers.set("X-User-Role", role);

        // 5. Forward the request
        HttpMethod method = HttpMethod.valueOf(req.getMethod());
        HttpEntity<byte[]> entity = new HttpEntity<>(body, headers);

        try {
            ResponseEntity<byte[]> response = restTemplate.exchange(
                    targetUrl, method, entity, byte[].class);

            // Propagate response headers (e.g. Set-Cookie)
            HttpHeaders outHeaders = new HttpHeaders();
            outHeaders.putAll(response.getHeaders());

            return new ResponseEntity<>(response.getBody(), outHeaders, response.getStatusCode());

        } catch (org.springframework.web.client.HttpStatusCodeException ex) {
            return new ResponseEntity<>(ex.getResponseBodyAsByteArray(),
                    ex.getResponseHeaders(), ex.getStatusCode());
        }
    }

    // ── Route resolution: longest matching prefix wins ────────────────────────
    private String resolveService(String path) {
        String matched = null;
        for (String prefix : ROUTES.keySet()) {
            if (path.startsWith(prefix)) {
                if (matched == null || prefix.length() > matched.length()) {
                    matched = prefix;
                }
            }
        }
        return matched != null ? ROUTES.get(matched) : null;
    }
}

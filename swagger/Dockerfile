FROM swaggerapi/swagger-ui:latest

ENV SWAGGER_JSON_URL=/specs/openapi-gateway.yaml
ENV BASE_URL=/
ENV VALIDATOR_URL=none

COPY openapi-gateway.yaml /usr/share/nginx/html/specs/openapi-gateway.yaml

EXPOSE 8080

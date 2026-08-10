# builder stage
FROM golang:1.21 AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o /out/app .

FROM builder AS test
RUN go test ./...

FROM alpine:3.19 AS runtime
RUN apk add --no-cache \
    ca-certificates
COPY --from=builder /out/app /usr/local/bin/app
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/app"]

FROM postgres:16 AS seed_db
COPY seed.sql /docker-entrypoint-initdb.d/

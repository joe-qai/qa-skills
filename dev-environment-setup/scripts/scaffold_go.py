#!/usr/bin/env python3
"""
Go Project Scaffold Generator
Creates a new Go project with Gin or Fiber framework.
"""

import argparse
import sys
from pathlib import Path


FRAMEWORKS = {
    "gin": {
        "name": "Gin",
        "module_path": "github.com/{{owner}}/{{project}}",
        "deps": [
            "github.com/gin-gonic/gin",
            "github.com/golang-jwt/jwt/v5",
            "github.com/spf13/viper",
        ],
    },
    "fiber": {
        "name": "Fiber",
        "module_path": "github.com/{{owner}}/{{project}}",
        "deps": [
            "github.com/gofiber/fiber/v2",
            "github.com/gofiber/jwt/v2",
            "github.com/gofiber/config/v2",
        ],
    },
}


def generate_structure(project_dir: Path, framework: str):
    """Generate Go project directory structure and files."""
    fw = FRAMEWORKS[framework]

    files = {
        "go.mod": f'''module {project_dir.name}

go 1.21
''',
        "cmd/server/main.go": '''package main

import (
	"log"

	"github.com/{{project}}/internal/server"
)

func main() {
	srv, err := server.New()
	if err != nil {
		log.Fatalf("Failed to create server: %v", err)
	}

	log.Printf("Server starting on %s", srv.Addr)
	if err := srv.ListenAndServe(); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
''',
        "internal/server/server.go": '''package server

import (
	"fmt"
	"net/http"

	"github.com/{{project}}/internal/handler"
	"github.com/{{project}}/internal/middleware"
)

type Server struct {
	Addr string
	http *http.Server
}

func New() (*Server, error) {
	mux := http.NewServeMux()

	// Health check
	mux.HandleFunc("/health", handler.Health)

	// API routes
	api := mux.PathPrefix("/api/v1").Submux()
	api.HandleFunc("/ping", handler.Ping)

	middleware.Register(api)

	addr := ":8080"
	return &Server{
		Addr: addr,
		http: &http.Server{Addr: addr, Handler: mux},
	}, nil
}

func (s *Server) ListenAndServe() error {
	return s.http.ListenAndServe()
}
''',
        "internal/handler/handler.go": '''package handler

import (
	"encoding/json"
	"net/http"
)

type Response struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	Data    any    `json:"data,omitempty"`
}

func JSON(w http.ResponseWriter, status int, data any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

func Health(w http.ResponseWriter, r *http.Request) {
	JSON(w, http.StatusOK, Response{
		Success: true,
		Message: "ok",
	})
}

func Ping(w http.ResponseWriter, r *http.Request) {
	JSON(w, http.StatusOK, Response{
		Success: true,
		Message: "pong",
	})
}
''',
        "internal/middleware/middleware.go": '''package middleware

import "net/http"

func Register(mux *http.ServeMux) {
	mux.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("X-Request-Id", r.Context().Value("request-id").(string))
			next.ServeHTTP(w, r)
		})
	})
}
''',
        "internal/config/config.go": '''package config

import (
	"os"
	"strconv"
)

type Config struct {
	Port     string
	LogLevel string
}

func Load() (*Config, error) {
	return &Config{
		Port:     getEnv("PORT", "8080"),
		LogLevel: getEnv("LOG_LEVEL", "info"),
	}, nil
}

func getEnv(key, defaultVal string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return defaultVal
}
''',
        "internal/repository/repository.go": '''package repository

type Repository struct{}

func New() *Repository {
	return &Repository{}
}
''',
        ".env.example": '''PORT=8080
LOG_LEVEL=info
DATABASE_URL=postgres://user:pass@localhost:5432/db
''',
        "Makefile": f'''APP_NAME = {project_dir.name}
GO = go
GOFLAGS = -mod=readonly

.PHONY: build run test clean

build:
\t$(GO) build -o bin/{project_dir.name} ./cmd/server

run: build
\t./bin/{project_dir.name}

test:
\t$(GO) test ./... -v -cover

clean:
\trm -rf bin/

deps:
\t$(GO) mod tidy
''',
        "docker-compose.yml": '''version: "3.9"

services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - PORT=8080
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: db
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  pgdata:
''',
        "Dockerfile": '''FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o bin/server ./cmd/server

FROM alpine:3.20
WORKDIR /app
COPY --from=builder /app/bin/server .
EXPOSE 8080
CMD ["./server"]
''',
    }

    # Create directories
    dirs = [
        "cmd/server",
        "internal/server",
        "internal/handler",
        "internal/middleware",
        "internal/config",
        "internal/repository",
        "internal/model",
        "internal/service",
        "pkg",
        "test",
    ]
    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)

    # Write files
    for path, content in files.items():
        full_path = project_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content.replace("{{project}}", project_dir.name))

    # Initialize go module
    (project_dir / "go.mod").write_text(f'''module {project_dir.name}

go 1.21
''')

    print(f"[+] Go ({fw['name']}) 项目脚手架已生成: {project_dir}")
    print(f"    下一步: cd {project_dir} && go mod tidy && make build")


def main():
    parser = argparse.ArgumentParser(description="Go 项目脚手架生成器")
    parser.add_argument("project_name", help="项目名称")
    parser.add_argument("--dir", default=".", help="目标目录（默认当前目录）")
    parser.add_argument(
        "--framework",
        choices=["gin", "fiber"],
        default="gin",
        help="Web 框架（默认: gin）",
    )
    args = parser.parse_args()

    project_dir = Path(args.dir) / args.project_name
    if project_dir.exists():
        print(f"[!] 目录已存在: {project_dir}")
        sys.exit(1)

    generate_structure(project_dir, args.framework)


if __name__ == "__main__":
    main()

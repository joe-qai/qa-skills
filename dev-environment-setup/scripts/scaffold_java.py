#!/usr/bin/env python3
"""
Java Spring Boot Project Scaffold Generator
Creates a new Spring Boot project with recommended structure and tooling.
"""

import argparse
import sys
from pathlib import Path


def generate_structure(project_dir: Path):
    """Generate Spring Boot project directory structure and files."""
    files = {
        "pom.xml": '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.3.0</version>
        <relativePath/>
    </parent>
    <groupId>com.example</groupId>
    <artifactId>{{project_name}}</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>{{project_name}}</name>
    <description>Spring Boot Project</description>
    <properties>
        <java.version>17</java.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
'''.replace("{{project_name}}", project_dir.name),
        ".gitignore": '''target/
!.mvn/wrapper/maven-wrapper.jar
 !**/src/main/java/**/target/
 !**/src/test/java/**/target/
### STS ###
.apt_generated
.classpath
.factorypath
.project
.settings
.springBeans
.sts4-cache
### IntelliJ IDEA ###
.idea
*.iws
*.iml
*.ipr
### NetBeans ###
/nbproject/private/
/nbbuild/
/dist/
/nbdist/
/.nb-gradle/
build/
!**/src/main/webapp/html5game/
### VS Code ###
.vscode/
### macOS ###
.DS_Store
### Logs ###
*.log
''',
        "README.md": f"""# {project_dir.name}

Spring Boot 3.3 + Java 17 项目脚手架

## 快速开始

\`\`\`bash
# 编译
mvn clean compile

# 运行
mvn spring-boot:run

# 测试
mvn test
\`\`\`
""",
    }

    # Create Maven directory structure
    dirs = [
        "src/main/java/com/example/demo",
        "src/main/java/com/example/demo/controller",
        "src/main/java/com/example/demo/service",
        "src/main/java/com/example/demo/service/impl",
        "src/main/java/com/example/demo/repository",
        "src/main/java/com/example/demo/model",
        "src/main/java/com/example/demo/dto",
        "src/main/java/com/example/demo/config",
        "src/main/resources",
        "src/test/java/com/example/demo",
        "docs",
    ]
    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)

    # Write source files
    (project_dir / "src" / "main" / "java" / "com" / "example" / "demo" / "DemoApplication.java").write_text('''package com.example.demo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class DemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }
}
''')

    (project_dir / "src" / "main" / "resources" / "application.yml").write_text('''server:
  port: 8080

spring:
  application:
    name: {{project_name}}
  datasource:
    url: jdbc:postgresql://localhost:5432/db
    username: user
    password: pass
    driver-class-name: org.postgresql.Driver
  jpa:
    hibernate:
      ddl-auto: update
    show-sql: false
    properties:
      hibernate:
        format_sql: true
  messages:
    basename: messages

logging:
  level:
    com.example.demo: INFO
    org.springframework.security: INFO
'''.replace("{{project_name}}", project_dir.name))

    (project_dir / "src" / "main" / "java" / "com" / "example" / "demo" / "controller" / "HealthController.java").write_text('''package com.example.demo.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class HealthController {

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of(
            "status", "UP",
            "service", "{{project_name}}"
        ));
    }

    @GetMapping("/")
    public ResponseEntity<Map<String, String>> index() {
        return ResponseEntity.ok(Map.of("message", "Hello from Spring Boot"));
    }
}
'''.replace("{{project_name}}", project_dir.name))

    (project_dir / "src" / "main" / "java" / "com" / "example" / "demo" / "model" / "BaseEntity.java").write_text('''package com.example.demo.model;

import jakarta.persistence.*;
import lombok.Data;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;

@Data
@MappedSuperclass
public abstract class BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
''')

    (project_dir / "src" / "main" / "java" / "com" / "example" / "demo" / "config" / "SecurityConfig.java").write_text('''package com.example.demo.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/health", "/api/v1/public/**").permitAll()
                .anyRequest().authenticated()
            );
        return http.build();
    }
}
''')

    (project_dir / "src" / "test" / "java" / "com" / "example" / "demo" / "DemoApplicationTests.java").write_text('''package com.example.demo;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class DemoApplicationTests {

    @Test
    void contextLoads() {
    }
}
''')

    # Write template files
    for path, content in files.items():
        full_path = project_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content.replace("{{project_name}}", project_dir.name))

    print(f"[+] Spring Boot 项目脚手架已生成: {project_dir}")
    print(f"    下一步: cd {project_dir} && mvn spring-boot:run")


def main():
    parser = argparse.ArgumentParser(description="Spring Boot 项目脚手架生成器")
    parser.add_argument("project_name", help="项目名称")
    parser.add_argument("--dir", default=".", help="目标目录（默认当前目录）")
    args = parser.parse_args()

    project_dir = Path(args.dir) / args.project_name
    if project_dir.exists():
        print(f"[!] 目录已存在: {project_dir}")
        sys.exit(1)

    generate_structure(project_dir)


if __name__ == "__main__":
    main()

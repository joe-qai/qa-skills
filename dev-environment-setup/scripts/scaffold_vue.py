#!/usr/bin/env python3
"""
Vue 3 + TypeScript Project Scaffold Generator
Creates a new Vue 3 project with TypeScript, Vite, and Pinia.
"""

import argparse
import json
import sys
from pathlib import Path


def generate_structure(project_dir: Path):
    """Generate Vue 3 project directory structure and files."""
    files = {
        "package.json": json.dumps({
            "name": project_dir.name,
            "version": "0.1.0",
            "private": True,
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vue-tsc -b && vite build",
                "preview": "vite preview",
                "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix",
                "format": "prettier --write src/"
            },
            "dependencies": {
                "vue": "^3.5.0",
                "vue-router": "^4.4.0",
                "pinia": "^2.2.0"
            },
            "devDependencies": {
                "@vitejs/plugin-vue": "^5.1.0",
                "typescript": "~5.6.0",
                "vite": "^6.0.0",
                "vue-tsc": "^2.1.0",
                "eslint": "^9.0.0",
                "eslint-plugin-vue": "^9.29.0",
                "@types/node": "^22.0.0",
                "prettier": "^3.3.0",
                "prettier-plugin Organize imports": "^0.0.1"
            }
        }, indent=2),
        "tsconfig.json": json.dumps({
            "compilerOptions": {
                "target": "ES2020",
                "useDefineForClassFields": True,
                "module": "ESNext",
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "allowImportingTsExtensions": True,
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
                "jsx": "preserve",
                "strict": True,
                "noUnusedLocals": True,
                "noUnusedParameters": True,
                "noFallthroughCasesInSwitch": True
            },
            "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"],
            "references": [{"path": "./tsconfig.node.json"}]
        }, indent=2),
        "tsconfig.node.json": json.dumps({
            "compilerOptions": {
                "target": "ES2022",
                "lib": ["ES2023"],
                "module": "ESNext",
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "allowImportingTsExtensions": True,
                "noEmit": True,
                "strict": True
            },
            "include": ["vite.config.ts"]
        }, indent=2),
        "vite.config.ts": '''import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: True,
      },
    },
  },
});
''',
        "index.html": '''<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{project_name}}</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
''',
        "src/main.ts": '''import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount("#app");
''',
        "src/App.vue": '''<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
</script>

<style>
#app {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  margin: 0;
  padding: 0;
}
</style>
''',
        "src/router/index.ts": '''import { createRouter, createWebHistory } from "vue-router";
import HomeView from "@/views/HomeView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: HomeView,
    },
  ],
});

export default router;
''',
        "src/views/HomeView.vue": '''<template>
  <div class="home">
    <h1>{{ project_name }}</h1>
    <p>Vue 3 + TypeScript + Vite 项目已就绪</p>
  </div>
</template>

<script setup lang="ts">
const projectName = "{{ project_name }}";
</script>

<style scoped>
.home {
  text-align: center;
  margin-top: 50px;
}
</style>
''',
        "src/stores/counter.ts": '''import { ref, computed } from "vue";
import { defineStore } from "pinia";

export const useCounterStore = defineStore("counter", () => {
  const count = ref(0);
  const doubleCount = computed(() => count.value * 2);
  function increment() {
    count.value++;
  }
  return { count, doubleCount, increment };
});
''',
        "src/components/HelloWorld.vue": '''<template>
  <h1>{{ msg }}</h1>
  <button @click="counter.increment">Count: {{ counter.count }}</button>
</template>

<script setup lang="ts">
import { defineProps } from "vue";
import { useCounterStore } from "@/stores/counter";

defineProps<{
  msg: string;
}>();

const counter = useCounterStore();
</script>
''',
        ".env.example": '''VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_TITLE={{ project_name }}
''',
        ".gitignore": '''# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

node_modules
dist
dist-ssr
*.local

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
''',
    }

    # Create directories
    dirs = [
        "src/views",
        "src/components",
        "src/stores",
        "src/types",
        "src/utils",
        "src/assets",
        "public",
        "test",
    ]
    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)

    # Write files
    for path, content in files.items():
        full_path = project_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content.replace("{{ project_name }}", project_dir.name))

    # TypeScript declaration
    (project_dir / "src" / "env.d.ts").write_text('''/// <reference types="vite/client" />
''')

    # Test setup
    (project_dir / "test" / "setup.ts").write_text('''// Test setup
console.log("Test environment ready");
''')

    print(f"[+] Vue 3 + TypeScript 项目脚手架已生成: {project_dir}")
    print(f"    下一步: cd {project_dir} && npm install && npm run dev")


def main():
    parser = argparse.ArgumentParser(description="Vue 3 + TypeScript 项目脚手架生成器")
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

param(
    [string]$service = "all"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  冷链物流平台 - 增量构建脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

switch ($service) {
    "frontend" {
        Write-Host "只构建前端服务..." -ForegroundColor Yellow
        docker compose up -d --build frontend
    }
    "backend" {
        Write-Host "只构建后端服务..." -ForegroundColor Yellow
        docker compose up -d --build backend
    }
    "simulator" {
        Write-Host "只构建模拟器服务..." -ForegroundColor Yellow
        docker compose up -d --build simulator
    }
    "all" {
        Write-Host "构建所有服务..." -ForegroundColor Yellow
        docker compose up -d --build
    }
    default {
        Write-Host "错误：未知服务 '$service'" -ForegroundColor Red
        Write-Host "可用选项：all, frontend, backend, simulator" -ForegroundColor Yellow
        exit 1
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "构建成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "服务状态:" -ForegroundColor Cyan
    docker compose ps
} else {
    Write-Host ""
    Write-Host "构建失败，请查看错误信息" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "Aplicando correção do relacionamento PaymentCondition.orders..." -ForegroundColor Cyan

if (!(Test-Path ".\app\models\payment_condition.py")) {
    Write-Host "ERRO: Execute este script dentro da pasta C:\erp_vendas_completo" -ForegroundColor Red
    exit 1
}

python .\scripts\corrigir_payment_condition.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro ao aplicar correção." -ForegroundColor Red
    exit 1
}

Write-Host "Correção aplicada. Reiniciando Docker..." -ForegroundColor Green
docker compose down
docker compose up -d --build

Write-Host "Finalizado. Teste: http://localhost:5098/painel" -ForegroundColor Green

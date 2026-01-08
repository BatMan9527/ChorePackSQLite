# 批量导出 build 目录下所有 db3 文件到各自的目录
# PowerShell 脚本

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$buildDir = Join-Path $projectRoot "build"

Write-Host "正在导出 build 目录下的所有 db3 文件..." -ForegroundColor Green
Write-Host ""

$dbFiles = Get-ChildItem -Path $buildDir -Filter "*.db3" -ErrorAction SilentlyContinue

if ($dbFiles.Count -eq 0) {
    Write-Host "未找到任何 db3 文件！" -ForegroundColor Yellow
    exit
}

foreach ($dbFile in $dbFiles) {
    $dbName = $dbFile.BaseName
    Write-Host "正在导出: $dbName" -ForegroundColor Cyan
    
    # 导出到 db3 文件所在目录
    python scripts/export_db.py --file $dbFile.FullName
    
    Write-Host ""
}

Write-Host "所有文件导出完成！" -ForegroundColor Green

@echo off

REM 设置Git用户信息
git config user.name "HYFLLLo"
git config user.email "your.email@example.com"

REM 添加所有文件
git add .

REM 提交代码
git commit -m "Initial commit"

REM 添加远程仓库
git remote add origin https://github.com/HYFLLLo/IT-Intelligent-Customer-Service-System-Enterprise-Edition-

REM 推送代码到GitHub
git push -u origin master

echo 推送完成！
pause
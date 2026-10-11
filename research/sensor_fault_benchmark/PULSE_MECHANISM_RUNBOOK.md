# 手动运行与续跑

在 Windows PowerShell 运行（WSL Ubuntu-20.04）：

```powershell
wsl -d Ubuntu-20.04 -- bash -lc 'cd /home/deuler/microduck_rl && .venv/bin/python /mnt/c/Users/21045/Documents/Codex/2026-09-14/ti/outputs/microduck_reproduction/sensor_fault_benchmark/launch_pulse_mechanism.py'
```

启动器后台运行、日志追加到 `pulse_mechanism/run.log`，不删除已有数据。若有同一worker存活会拒绝重复启动；若进程已经退出，排查错误后用同命令续跑。不要手动删除 progress/manifest。

在本工作目录查看进度：

```powershell
$pulseProgress = Get-Content .\outputs\microduck_reproduction\sensor_fault_benchmark\pulse_mechanism\progress.json -Raw | ConvertFrom-Json
$pulseProgress.results.Count
$pulseProgress.expected_jobs
$pulseProgress.complete
Get-Content .\outputs\microduck_reproduction\sensor_fault_benchmark\pulse_mechanism\run.log -Tail 20
```

首个case完成以前progress可能尚未生成；不是实验失败。PID存在也不等于正在推进，应同时检查日志与进度更新时间。完成标准为results与progress的complete=true、40唯一case/2560回合；还应独立复算与检查原始CSV，不把单元测试/冒烟通过等同于正式实验完成。

原始确认报告、其CSV/manifest和模型均不修改。若需要新条件或更完整遥测，使用新版本/新目录；不要修改正在运行且已哈希的脚本。

# MicroDuck研究数据快照 2026年10月15日

本快照同步到原有私有研究仓库。此前代码发布说明中“原始数据与未发表报告仅保留本地”的约定，仍描述旧代码发布子集；本快照是在用户本次明确要求同步数据后新增，未改变仓库私有可见性。

## 阅读入口

- [16份独立报告与全部曲线入口](reports_bundle/README.md)
- [合订报告与192张图](reports_bundle/ALL_REPORTS.md)
- [图表中文阅读指南](reports_bundle/READING_GUIDE.md)
- [覆盖范围与未保存数据边界](reports_bundle/COVERAGE.md)
- [带注释研究总档案](MICRODUCK_RESEARCH_MASTER_DOSSIER_CURRENT.md)
- [论文初稿](paper/paper.md)
- [协议与baseline总汇](PROTOCOL_BASELINE_SUMMARY_2026-10-15.md)

GitHub不直接执行本地HTML浏览器。要交互筛选模型和指标，请从下面版本附件下载完整报告包，解压后打开index.html；它不需要外网。

完整训练标量JSON约70MiB，仅放在版本附件，Git中保留对应曲线与文件校验索引，不重复写入大体积Git历史。

## 原始数据与模型下载

[数据版本附件](https://github.com/DawnLiu0116/microduck-rl-reproduction-backup/releases/tag/microduck-data-2026-10-15)

附件保存原始逐回合CSV、冻结源码及协议、汇总、模型、TensorBoard、视频和审计证据；四个原训练目录也在其中。大文件不写入普通Git历史。

下载所有microduck-data-20261015.partNN.zip，分别解压到同一个新目录。每个ZIP都能独立解压，不是需要二进制拼接的分卷。[DATA_MANIFEST.json](DATA_MANIFEST.json)记录文件相对路径、体积、SHA256和所属ZIP；[ASSETS.json](ASSETS.json)记录各ZIP的SHA256。SHA核验后再使用数据，不直接运行旧启动器。

## 范围与边界

- 保留源文件原始字节，不修改冻结哈希；取消补测的准备材料只作归档，实际仍为0项。
- 三个原模型、244份真实保存点、N336项、T24续训分支及528评估项、人工状态900项分别记录，不把总回合数当独立训练重复。
- 缓存、虚拟环境、Git元数据、重复curated副本、渲染QA及每日私人日志不上传。第三方运行时checkout通过原版本审计引用，不重复打包。
- 本次只同步现有数据，不新增实验、恢复队列或操作实体。
- 仿真结果不证明硬件安全，离线MSE不等于闭环表现。

最终核验见[发布后校验收据](FINAL_SYNC_VERIFICATION.json)，包括每个附件的体积、SHA256及正式下载链接。草稿阶段的UPLOAD_VERIFICATION.json仅保留上传过程记录，其中临时untagged链接以最终收据为准。附件发布前的草稿不代表同步完成。

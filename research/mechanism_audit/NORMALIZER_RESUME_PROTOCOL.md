# 归一化冗余状态与恢复更新探针

2026-10-09，执行前固定。CPU、离线、仅内存副本，不保存修改后的checkpoint，不启动PPO。

代码事实：EmpiricalNormalization保存_mean/_var/_std/count；forward使用_std，update使用_var并重算_std。strict加载检查key/shape，不保证_var与_std数学一致。

固定三个原最终模型42/123/2026；使用已有teacher42 seed7007的前256帧样本作为一次统计更新batch，留出env48–63确定性抽取2048帧作为推理比较。不是独立新数据集；同batch用于各模型，不能称原生on-policy恢复。

4分支：原始；只将内存_var乘1.01而_std不变；同步把_var乘1.01且_std=sqrt(var)；只修改count为0。后二者为即时尺度改变与统计历史丢失的机制对照，不是攻击强度搜索。每个分支分别检查加载后、eval下update后、train下单次update后。

主验证：原始_var/_std一致；不一致副本能否strict加载；只改_var时更新前函数是否保持完全相同；train更新后是否变化；eval update是否完全无效。报告normalizer和14维动作差，不从动作差推断跌倒。

输出记录各状态的一致性残差、有限/正值/count合法性、动作差、原文件SHA、源码SHA和依赖版本。若机制成立，添加只读合同校验示例，不修改官方normalizer或模型，不声称当前官方模型已被污染。

任何效果都不能自动称为新颖后门：能修改checkpoint的主体也能直接改权重；该试验关注加载/恢复的验收盲点，创新性必须另行研究。完成后停止，不提高幅度、不断言闭环危险。

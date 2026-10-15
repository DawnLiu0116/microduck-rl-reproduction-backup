# 05 精细响应完整基准研究报告

完整基准显示故障响应随幅度、通道、持续时间和命令改变，模型不存在统一优胜次序。联合脉冲下123弱，而部分单通道下其他模型也很脆弱。

## 工作范围

2072项、171,328首回合，其中confirmation为612项、78,336回合；该确认数已包含在总数内。

## 我们如何完成这项工作

探索主要用71201/71202、每项64回合；确认使用81201/81202/81203、每项128回合，确认网格预先锁定。保留smoke、calibration、coarse、local、delay_freeze_exploration、confirmation、combinations、time和commands九阶段，图册明确分组，不把小样本校准混入正式确认。

## 现有结果及解释

1. 确认主锚点每格384回合：额外40ms延迟的official/42/123/2026存活约47.40%/2.08%/12.50%/3.13%；纯行走联合脉冲alpha1约97.40%/96.88%/19.01%/85.94%。

2. freeze8、10、12的存活响应随陈旧帧数恶化，但有限网格不能定位一个跨模型普适阈值。原生延迟保留，40ms指额外观测延迟，不是硬件端到端总时延。

3. 通道组合和时间安排只有两个探索seed；相同alpha不保证输入范数或实际暴露量相同。早跌倒模型会错过后续脉冲，不能按计划暴露帧数假设实际剂量相等。

## 完整结果表

| 模型或分支 | 条件 | 阶段 | 存活分子/分母 | 存活率 | 平均寿命s | vx误差m/s | XY误差m/s |
|---|---|---|---|---|---|---|---|
| official_alpha_walking | clean_e65df7c70d30 | smoke | 8/8 | 100.00% | 20.0000 | 0.1511 | 0.2085 |
| official_alpha_walking | pulse_e44530ee154b | smoke | 8/8 | 100.00% | 20.0000 | 0.1537 | 0.2129 |
| seed42_iter3999 | clean_e65df7c70d30 | smoke | 8/8 | 100.00% | 20.0000 | 0.1181 | 0.1886 |
| seed42_iter3999 | pulse_e44530ee154b | smoke | 7/8 | 87.50% | 19.6125 | 0.1265 | 0.1982 |
| seed123_iter3999 | clean_e65df7c70d30 | smoke | 8/8 | 100.00% | 20.0000 | 0.1141 | 0.1898 |
| seed123_iter3999 | pulse_e44530ee154b | smoke | 1/8 | 12.50% | 7.0750 | 0.1312 | 0.2162 |
| seed2026_iter3999 | clean_e65df7c70d30 | smoke | 8/8 | 100.00% | 20.0000 | 0.1236 | 0.1859 |
| seed2026_iter3999 | pulse_e44530ee154b | smoke | 5/8 | 62.50% | 15.2350 | 0.1314 | 0.2015 |
| official_alpha_walking | clean_e65df7c70d30 | calibration | 64/64 | 100.00% | 20.0000 | 0.1570 | 0.2143 |
| official_alpha_walking | pulse_e44530ee154b | calibration | 62/64 | 96.88% | 19.8959 | 0.1619 | 0.2204 |
| official_alpha_walking | pulse_fae27cf4334f | calibration | 62/64 | 96.88% | 19.7641 | 0.1616 | 0.2195 |
| seed42_iter3999 | clean_e65df7c70d30 | calibration | 64/64 | 100.00% | 20.0000 | 0.1229 | 0.1920 |
| seed42_iter3999 | pulse_e44530ee154b | calibration | 63/64 | 98.44% | 19.9503 | 0.1304 | 0.2000 |
| seed42_iter3999 | pulse_fae27cf4334f | calibration | 64/64 | 100.00% | 20.0000 | 0.1305 | 0.1994 |
| seed123_iter3999 | clean_e65df7c70d30 | calibration | 64/64 | 100.00% | 20.0000 | 0.1179 | 0.1914 |
| seed123_iter3999 | pulse_e44530ee154b | calibration | 14/64 | 21.88% | 10.0262 | 0.1338 | 0.2121 |
| seed123_iter3999 | pulse_fae27cf4334f | calibration | 8/64 | 12.50% | 9.4719 | 0.1311 | 0.2106 |
| seed2026_iter3999 | clean_e65df7c70d30 | calibration | 64/64 | 100.00% | 20.0000 | 0.1264 | 0.1887 |
| seed2026_iter3999 | pulse_e44530ee154b | calibration | 61/64 | 95.31% | 19.4678 | 0.1348 | 0.1982 |
| seed2026_iter3999 | pulse_fae27cf4334f | calibration | 55/64 | 85.94% | 18.5356 | 0.1343 | 0.1982 |
| official_alpha_walking | clean_e65df7c70d30 | coarse | 128/128 | 100.00% | 20.0000 | 0.1526 | 0.2109 |
| official_alpha_walking | pulse_598198552a6a | coarse | 128/128 | 100.00% | 20.0000 | 0.1509 | 0.2099 |
| official_alpha_walking | pulse_612e9447021a | coarse | 124/128 | 96.88% | 19.7400 | 0.1520 | 0.2119 |
| official_alpha_walking | pulse_fc6acbace648 | coarse | 106/128 | 82.81% | 18.0261 | 0.1571 | 0.2179 |
| official_alpha_walking | pulse_be409b92b318 | coarse | 97/128 | 75.78% | 17.4394 | 0.1599 | 0.2210 |
| official_alpha_walking | pulse_541079131c9c | coarse | 85/128 | 66.41% | 16.3116 | 0.1625 | 0.2246 |
| official_alpha_walking | pulse_cab68f744b9e | coarse | 83/128 | 64.84% | 16.1019 | 0.1633 | 0.2264 |
| official_alpha_walking | pulse_766c85f17642 | coarse | 74/128 | 57.81% | 15.7967 | 0.1645 | 0.2291 |
| official_alpha_walking | pulse_771ebfd2be80 | coarse | 68/128 | 53.12% | 15.1686 | 0.1652 | 0.2302 |
| official_alpha_walking | pulse_729006de2cca | coarse | 64/128 | 50.00% | 14.7327 | 0.1658 | 0.2325 |
| official_alpha_walking | pulse_56d4a09409f5 | coarse | 49/128 | 38.28% | 13.4102 | 0.1665 | 0.2339 |
| official_alpha_walking | pulse_d1112dc8481e | coarse | 128/128 | 100.00% | 20.0000 | 0.1551 | 0.2128 |
| official_alpha_walking | pulse_c4a069da32cb | coarse | 128/128 | 100.00% | 20.0000 | 0.1618 | 0.2182 |
| official_alpha_walking | pulse_878b84f480be | coarse | 126/128 | 98.44% | 19.8569 | 0.1683 | 0.2242 |
| official_alpha_walking | pulse_336affbaace0 | coarse | 111/128 | 86.72% | 18.7561 | 0.1749 | 0.2317 |
| official_alpha_walking | pulse_4d30d7e3f2a5 | coarse | 68/128 | 53.12% | 15.3637 | 0.1832 | 0.2417 |
| official_alpha_walking | pulse_d34e1497b1a6 | coarse | 26/128 | 20.31% | 10.8005 | 0.1875 | 0.2471 |
| official_alpha_walking | pulse_2616fb73abed | coarse | 12/128 | 9.38% | 8.5117 | 0.1875 | 0.2477 |
| official_alpha_walking | pulse_6e665d027696 | coarse | 10/128 | 7.81% | 8.2366 | 0.1837 | 0.2452 |
| official_alpha_walking | pulse_1c562b061f06 | coarse | 11/128 | 8.59% | 8.2662 | 0.1827 | 0.2443 |
| official_alpha_walking | pulse_89d16652c7f6 | coarse | 9/128 | 7.03% | 7.6058 | 0.1784 | 0.2405 |
| official_alpha_walking | pulse_1f4338b72772 | coarse | 128/128 | 100.00% | 20.0000 | 0.1549 | 0.2128 |
| official_alpha_walking | pulse_0d97f23e5846 | coarse | 128/128 | 100.00% | 20.0000 | 0.1601 | 0.2172 |
| official_alpha_walking | pulse_30e7abd7bb25 | coarse | 123/128 | 96.09% | 19.4953 | 0.1649 | 0.2220 |
| official_alpha_walking | pulse_6624590865ae | coarse | 110/128 | 85.94% | 18.7814 | 0.1689 | 0.2265 |
| official_alpha_walking | pulse_7bfb7292678c | coarse | 117/128 | 91.41% | 19.2116 | 0.1697 | 0.2274 |
| official_alpha_walking | pulse_eaa8dd3181ba | coarse | 93/128 | 72.66% | 17.3995 | 0.1737 | 0.2322 |
| official_alpha_walking | pulse_fab6e214fe66 | coarse | 97/128 | 75.78% | 17.6725 | 0.1737 | 0.2320 |
| official_alpha_walking | pulse_645aa6a28f7c | coarse | 93/128 | 72.66% | 17.6778 | 0.1726 | 0.2304 |
| official_alpha_walking | pulse_089d36600d5a | coarse | 104/128 | 81.25% | 18.6278 | 0.1683 | 0.2255 |
| official_alpha_walking | pulse_6c6bb40706a6 | coarse | 107/128 | 83.59% | 18.8222 | 0.1650 | 0.2222 |
| official_alpha_walking | pulse_4af0b1d60fc6 | coarse | 128/128 | 100.00% | 20.0000 | 0.1516 | 0.2100 |
| official_alpha_walking | pulse_8ce0dd058c2a | coarse | 128/128 | 100.00% | 20.0000 | 0.1524 | 0.2109 |
| official_alpha_walking | pulse_ec2f66875aa0 | coarse | 128/128 | 100.00% | 20.0000 | 0.1524 | 0.2114 |
| official_alpha_walking | pulse_f0bc4b9f6e91 | coarse | 126/128 | 98.44% | 19.8259 | 0.1536 | 0.2126 |
| official_alpha_walking | pulse_f59722d3524c | coarse | 126/128 | 98.44% | 19.8227 | 0.1540 | 0.2133 |
| official_alpha_walking | pulse_ba7867e6549c | coarse | 126/128 | 98.44% | 19.8258 | 0.1550 | 0.2140 |
| official_alpha_walking | pulse_b621093bcd01 | coarse | 125/128 | 97.66% | 19.7369 | 0.1555 | 0.2145 |
| official_alpha_walking | pulse_5d68ab63e0ef | coarse | 125/128 | 97.66% | 19.8627 | 0.1559 | 0.2148 |
| official_alpha_walking | pulse_2e47e7dd2cba | coarse | 128/128 | 100.00% | 20.0000 | 0.1558 | 0.2148 |
| official_alpha_walking | pulse_fae27cf4334f | coarse | 127/128 | 99.22% | 19.9723 | 0.1566 | 0.2155 |
| official_alpha_walking | noise_3ad7e9e688cc | coarse | 128/128 | 100.00% | 20.0000 | 0.1534 | 0.2116 |
| official_alpha_walking | noise_76b6c8d9475e | coarse | 128/128 | 100.00% | 20.0000 | 0.1555 | 0.2132 |
| official_alpha_walking | noise_ace99fcee633 | coarse | 128/128 | 100.00% | 20.0000 | 0.1589 | 0.2158 |
| official_alpha_walking | noise_a76040145b71 | coarse | 128/128 | 100.00% | 20.0000 | 0.1622 | 0.2181 |
| official_alpha_walking | noise_fd19a17f7ab4 | coarse | 128/128 | 100.00% | 20.0000 | 0.1655 | 0.2205 |
| official_alpha_walking | noise_1aada8851753 | coarse | 128/128 | 100.00% | 20.0000 | 0.1692 | 0.2229 |
| official_alpha_walking | noise_6413ebf12de0 | coarse | 128/128 | 100.00% | 20.0000 | 0.1719 | 0.2247 |
| official_alpha_walking | noise_493bdc9e1fa2 | coarse | 128/128 | 100.00% | 20.0000 | 0.1749 | 0.2265 |
| official_alpha_walking | noise_101e6e96aee7 | coarse | 128/128 | 100.00% | 20.0000 | 0.1792 | 0.2297 |
| official_alpha_walking | noise_dece5089b501 | coarse | 125/128 | 97.66% | 19.7950 | 0.1808 | 0.2308 |
| official_alpha_walking | imu_bias_2aebd0fda40e | coarse | 128/128 | 100.00% | 20.0000 | 0.1514 | 0.2093 |
| official_alpha_walking | imu_bias_5705e28d3566 | coarse | 128/128 | 100.00% | 20.0000 | 0.1507 | 0.2082 |
| official_alpha_walking | imu_bias_846ab0f64545 | coarse | 128/128 | 100.00% | 20.0000 | 0.1510 | 0.2076 |
| official_alpha_walking | imu_bias_04ce18799df0 | coarse | 128/128 | 100.00% | 20.0000 | 0.1520 | 0.2073 |
| official_alpha_walking | imu_bias_86a35be18154 | coarse | 128/128 | 100.00% | 20.0000 | 0.1539 | 0.2076 |
| official_alpha_walking | imu_bias_f1b525ba2b1e | coarse | 128/128 | 100.00% | 20.0000 | 0.1560 | 0.2080 |
| official_alpha_walking | imu_bias_366018e369c4 | coarse | 126/128 | 98.44% | 19.7389 | 0.1619 | 0.2119 |
| official_alpha_walking | imu_bias_399b92850697 | coarse | 125/128 | 97.66% | 19.8622 | 0.1704 | 0.2177 |
| official_alpha_walking | imu_bias_135073b420cd | coarse | 125/128 | 97.66% | 19.6791 | 0.1822 | 0.2271 |
| official_alpha_walking | imu_bias_b5899bf48dac | coarse | 113/128 | 88.28% | 19.0020 | 0.1931 | 0.2364 |
| official_alpha_walking | imu_bias_f5408fbd35a6 | coarse | 95/128 | 74.22% | 17.1745 | 0.2172 | 0.2590 |
| official_alpha_walking | imu_bias_0f25110924e4 | coarse | 66/128 | 51.56% | 13.1764 | 0.2388 | 0.2809 |
| official_alpha_walking | imu_bias_41b4a6c6dd6f | coarse | 42/128 | 32.81% | 10.6705 | 0.2721 | 0.3129 |
| official_alpha_walking | imu_bias_ede1e4da0e2c | coarse | 26/128 | 20.31% | 8.1491 | 0.2808 | 0.3225 |
| official_alpha_walking | imu_bias_ce7df1de845c | coarse | 25/128 | 19.53% | 7.8687 | 0.2820 | 0.3231 |
| official_alpha_walking | imu_bias_6e42d5991dc0 | coarse | 19/128 | 14.84% | 6.8953 | 0.2705 | 0.3157 |
| seed42_iter3999 | clean_e65df7c70d30 | coarse | 128/128 | 100.00% | 20.0000 | 0.1202 | 0.1900 |
| seed42_iter3999 | pulse_598198552a6a | coarse | 127/128 | 99.22% | 19.9436 | 0.1205 | 0.1902 |
| seed42_iter3999 | pulse_612e9447021a | coarse | 54/128 | 42.19% | 14.4675 | 0.1284 | 0.2010 |
| seed42_iter3999 | pulse_fc6acbace648 | coarse | 20/128 | 15.62% | 11.1800 | 0.1323 | 0.2072 |
| seed42_iter3999 | pulse_be409b92b318 | coarse | 16/128 | 12.50% | 10.1092 | 0.1329 | 0.2087 |
| seed42_iter3999 | pulse_541079131c9c | coarse | 26/128 | 20.31% | 11.3872 | 0.1359 | 0.2103 |
| seed42_iter3999 | pulse_cab68f744b9e | coarse | 27/128 | 21.09% | 11.1377 | 0.1372 | 0.2115 |
| seed42_iter3999 | pulse_766c85f17642 | coarse | 35/128 | 27.34% | 12.3819 | 0.1379 | 0.2122 |
| seed42_iter3999 | pulse_771ebfd2be80 | coarse | 21/128 | 16.41% | 10.8586 | 0.1392 | 0.2147 |
| seed42_iter3999 | pulse_729006de2cca | coarse | 21/128 | 16.41% | 10.9495 | 0.1390 | 0.2145 |
| seed42_iter3999 | pulse_56d4a09409f5 | coarse | 10/128 | 7.81% | 9.7636 | 0.1386 | 0.2147 |
| seed42_iter3999 | pulse_d1112dc8481e | coarse | 128/128 | 100.00% | 20.0000 | 0.1214 | 0.1908 |
| seed42_iter3999 | pulse_c4a069da32cb | coarse | 128/128 | 100.00% | 20.0000 | 0.1259 | 0.1939 |
| seed42_iter3999 | pulse_878b84f480be | coarse | 123/128 | 96.09% | 19.6045 | 0.1325 | 0.1998 |
| seed42_iter3999 | pulse_336affbaace0 | coarse | 96/128 | 75.00% | 18.0958 | 0.1429 | 0.2099 |
| seed42_iter3999 | pulse_4d30d7e3f2a5 | coarse | 47/128 | 36.72% | 14.2180 | 0.1504 | 0.2177 |
| seed42_iter3999 | pulse_d34e1497b1a6 | coarse | 34/128 | 26.56% | 12.2897 | 0.1524 | 0.2203 |
| seed42_iter3999 | pulse_2616fb73abed | coarse | 17/128 | 13.28% | 10.4911 | 0.1536 | 0.2216 |
| seed42_iter3999 | pulse_6e665d027696 | coarse | 9/128 | 7.03% | 9.8203 | 0.1575 | 0.2250 |
| seed42_iter3999 | pulse_1c562b061f06 | coarse | 10/128 | 7.81% | 9.1678 | 0.1573 | 0.2250 |
| seed42_iter3999 | pulse_89d16652c7f6 | coarse | 6/128 | 4.69% | 7.8706 | 0.1596 | 0.2269 |
| seed42_iter3999 | pulse_1f4338b72772 | coarse | 128/128 | 100.00% | 20.0000 | 0.1221 | 0.1914 |
| seed42_iter3999 | pulse_0d97f23e5846 | coarse | 128/128 | 100.00% | 20.0000 | 0.1273 | 0.1956 |
| seed42_iter3999 | pulse_30e7abd7bb25 | coarse | 122/128 | 95.31% | 19.5134 | 0.1323 | 0.2005 |
| seed42_iter3999 | pulse_6624590865ae | coarse | 119/128 | 92.97% | 19.2939 | 0.1357 | 0.2037 |
| seed42_iter3999 | pulse_7bfb7292678c | coarse | 111/128 | 86.72% | 18.5575 | 0.1396 | 0.2077 |
| seed42_iter3999 | pulse_eaa8dd3181ba | coarse | 116/128 | 90.62% | 18.8744 | 0.1389 | 0.2066 |
| seed42_iter3999 | pulse_fab6e214fe66 | coarse | 122/128 | 95.31% | 19.3394 | 0.1394 | 0.2068 |
| seed42_iter3999 | pulse_645aa6a28f7c | coarse | 124/128 | 96.88% | 19.5558 | 0.1382 | 0.2057 |
| seed42_iter3999 | pulse_089d36600d5a | coarse | 124/128 | 96.88% | 19.7105 | 0.1370 | 0.2043 |
| seed42_iter3999 | pulse_6c6bb40706a6 | coarse | 123/128 | 96.09% | 19.6527 | 0.1357 | 0.2031 |
| seed42_iter3999 | pulse_4af0b1d60fc6 | coarse | 128/128 | 100.00% | 20.0000 | 0.1197 | 0.1891 |
| seed42_iter3999 | pulse_8ce0dd058c2a | coarse | 127/128 | 99.22% | 19.9441 | 0.1212 | 0.1903 |
| seed42_iter3999 | pulse_ec2f66875aa0 | coarse | 128/128 | 100.00% | 20.0000 | 0.1216 | 0.1907 |
| seed42_iter3999 | pulse_f0bc4b9f6e91 | coarse | 128/128 | 100.00% | 20.0000 | 0.1212 | 0.1901 |
| seed42_iter3999 | pulse_f59722d3524c | coarse | 128/128 | 100.00% | 20.0000 | 0.1211 | 0.1898 |
| seed42_iter3999 | pulse_ba7867e6549c | coarse | 128/128 | 100.00% | 20.0000 | 0.1219 | 0.1906 |
| seed42_iter3999 | pulse_b621093bcd01 | coarse | 124/128 | 96.88% | 19.6856 | 0.1256 | 0.1943 |
| seed42_iter3999 | pulse_5d68ab63e0ef | coarse | 121/128 | 94.53% | 19.4664 | 0.1273 | 0.1961 |
| seed42_iter3999 | pulse_2e47e7dd2cba | coarse | 120/128 | 93.75% | 19.2744 | 0.1284 | 0.1977 |
| seed42_iter3999 | pulse_fae27cf4334f | coarse | 128/128 | 100.00% | 20.0000 | 0.1278 | 0.1974 |
| seed42_iter3999 | noise_3ad7e9e688cc | coarse | 128/128 | 100.00% | 20.0000 | 0.1208 | 0.1903 |
| seed42_iter3999 | noise_76b6c8d9475e | coarse | 128/128 | 100.00% | 20.0000 | 0.1225 | 0.1913 |
| seed42_iter3999 | noise_ace99fcee633 | coarse | 128/128 | 100.00% | 20.0000 | 0.1252 | 0.1928 |
| seed42_iter3999 | noise_a76040145b71 | coarse | 128/128 | 100.00% | 20.0000 | 0.1287 | 0.1946 |
| seed42_iter3999 | noise_fd19a17f7ab4 | coarse | 128/128 | 100.00% | 20.0000 | 0.1322 | 0.1962 |
| seed42_iter3999 | noise_1aada8851753 | coarse | 128/128 | 100.00% | 20.0000 | 0.1363 | 0.1979 |
| seed42_iter3999 | noise_6413ebf12de0 | coarse | 128/128 | 100.00% | 20.0000 | 0.1407 | 0.2000 |
| seed42_iter3999 | noise_493bdc9e1fa2 | coarse | 128/128 | 100.00% | 20.0000 | 0.1451 | 0.2017 |
| seed42_iter3999 | noise_101e6e96aee7 | coarse | 128/128 | 100.00% | 20.0000 | 0.1500 | 0.2041 |
| seed42_iter3999 | noise_dece5089b501 | coarse | 125/128 | 97.66% | 19.8105 | 0.1546 | 0.2066 |
| seed42_iter3999 | imu_bias_2aebd0fda40e | coarse | 128/128 | 100.00% | 20.0000 | 0.1162 | 0.1865 |
| seed42_iter3999 | imu_bias_5705e28d3566 | coarse | 128/128 | 100.00% | 20.0000 | 0.1127 | 0.1831 |
| seed42_iter3999 | imu_bias_846ab0f64545 | coarse | 128/128 | 100.00% | 20.0000 | 0.1103 | 0.1802 |
| seed42_iter3999 | imu_bias_04ce18799df0 | coarse | 128/128 | 100.00% | 20.0000 | 0.1087 | 0.1773 |
| seed42_iter3999 | imu_bias_86a35be18154 | coarse | 128/128 | 100.00% | 20.0000 | 0.1075 | 0.1741 |
| seed42_iter3999 | imu_bias_f1b525ba2b1e | coarse | 128/128 | 100.00% | 20.0000 | 0.1069 | 0.1709 |
| seed42_iter3999 | imu_bias_366018e369c4 | coarse | 128/128 | 100.00% | 20.0000 | 0.1070 | 0.1678 |
| seed42_iter3999 | imu_bias_399b92850697 | coarse | 128/128 | 100.00% | 20.0000 | 0.1089 | 0.1658 |
| seed42_iter3999 | imu_bias_135073b420cd | coarse | 128/128 | 100.00% | 20.0000 | 0.1127 | 0.1654 |
| seed42_iter3999 | imu_bias_b5899bf48dac | coarse | 126/128 | 98.44% | 19.7286 | 0.1186 | 0.1679 |
| seed42_iter3999 | imu_bias_f5408fbd35a6 | coarse | 119/128 | 92.97% | 19.1517 | 0.1247 | 0.1714 |
| seed42_iter3999 | imu_bias_0f25110924e4 | coarse | 108/128 | 84.38% | 17.9237 | 0.1338 | 0.1802 |
| seed42_iter3999 | imu_bias_41b4a6c6dd6f | coarse | 78/128 | 60.94% | 14.7606 | 0.1491 | 0.1988 |
| seed42_iter3999 | imu_bias_ede1e4da0e2c | coarse | 48/128 | 37.50% | 11.0481 | 0.1694 | 0.2254 |
| seed42_iter3999 | imu_bias_ce7df1de845c | coarse | 17/128 | 13.28% | 6.4070 | 0.1955 | 0.2580 |
| seed42_iter3999 | imu_bias_6e42d5991dc0 | coarse | 7/128 | 5.47% | 4.7808 | 0.2009 | 0.2674 |
| seed123_iter3999 | clean_e65df7c70d30 | coarse | 128/128 | 100.00% | 20.0000 | 0.1152 | 0.1896 |
| seed123_iter3999 | pulse_598198552a6a | coarse | 128/128 | 100.00% | 20.0000 | 0.1163 | 0.1895 |
| seed123_iter3999 | pulse_612e9447021a | coarse | 61/128 | 47.66% | 14.3458 | 0.1238 | 0.2005 |
| seed123_iter3999 | pulse_fc6acbace648 | coarse | 15/128 | 11.72% | 9.7514 | 0.1295 | 0.2068 |
| seed123_iter3999 | pulse_be409b92b318 | coarse | 8/128 | 6.25% | 7.6211 | 0.1333 | 0.2100 |
| seed123_iter3999 | pulse_541079131c9c | coarse | 4/128 | 3.12% | 6.1334 | 0.1366 | 0.2118 |
| seed123_iter3999 | pulse_cab68f744b9e | coarse | 0/128 | 0.00% | 5.4720 | 0.1371 | 0.2119 |
| seed123_iter3999 | pulse_766c85f17642 | coarse | 1/128 | 0.78% | 5.4466 | 0.1377 | 0.2117 |
| seed123_iter3999 | pulse_771ebfd2be80 | coarse | 1/128 | 0.78% | 5.2656 | 0.1384 | 0.2112 |
| seed123_iter3999 | pulse_729006de2cca | coarse | 1/128 | 0.78% | 5.1766 | 0.1362 | 0.2088 |
| seed123_iter3999 | pulse_56d4a09409f5 | coarse | 0/128 | 0.00% | 4.9359 | 0.1380 | 0.2103 |
| seed123_iter3999 | pulse_d1112dc8481e | coarse | 128/128 | 100.00% | 20.0000 | 0.1169 | 0.1908 |
| seed123_iter3999 | pulse_c4a069da32cb | coarse | 127/128 | 99.22% | 19.8820 | 0.1232 | 0.1957 |
| seed123_iter3999 | pulse_878b84f480be | coarse | 125/128 | 97.66% | 19.6519 | 0.1314 | 0.2029 |
| seed123_iter3999 | pulse_336affbaace0 | coarse | 90/128 | 70.31% | 16.5072 | 0.1429 | 0.2155 |
| seed123_iter3999 | pulse_4d30d7e3f2a5 | coarse | 33/128 | 25.78% | 11.3334 | 0.1513 | 0.2241 |
| seed123_iter3999 | pulse_d34e1497b1a6 | coarse | 15/128 | 11.72% | 9.1097 | 0.1523 | 0.2251 |
| seed123_iter3999 | pulse_2616fb73abed | coarse | 3/128 | 2.34% | 6.9692 | 0.1534 | 0.2264 |
| seed123_iter3999 | pulse_6e665d027696 | coarse | 1/128 | 0.78% | 6.0344 | 0.1548 | 0.2272 |
| seed123_iter3999 | pulse_1c562b061f06 | coarse | 0/128 | 0.00% | 5.7228 | 0.1507 | 0.2225 |
| seed123_iter3999 | pulse_89d16652c7f6 | coarse | 0/128 | 0.00% | 5.7670 | 0.1508 | 0.2222 |
| seed123_iter3999 | pulse_1f4338b72772 | coarse | 128/128 | 100.00% | 20.0000 | 0.1171 | 0.1910 |
| seed123_iter3999 | pulse_0d97f23e5846 | coarse | 121/128 | 94.53% | 19.6759 | 0.1240 | 0.1965 |
| seed123_iter3999 | pulse_30e7abd7bb25 | coarse | 97/128 | 75.78% | 17.8203 | 0.1322 | 0.2045 |
| seed123_iter3999 | pulse_6624590865ae | coarse | 81/128 | 63.28% | 16.2795 | 0.1383 | 0.2107 |
| seed123_iter3999 | pulse_7bfb7292678c | coarse | 75/128 | 58.59% | 15.2653 | 0.1403 | 0.2131 |
| seed123_iter3999 | pulse_eaa8dd3181ba | coarse | 50/128 | 39.06% | 13.6400 | 0.1461 | 0.2192 |
| seed123_iter3999 | pulse_fab6e214fe66 | coarse | 48/128 | 37.50% | 12.8861 | 0.1466 | 0.2206 |
| seed123_iter3999 | pulse_645aa6a28f7c | coarse | 39/128 | 30.47% | 12.2273 | 0.1496 | 0.2237 |
| seed123_iter3999 | pulse_089d36600d5a | coarse | 39/128 | 30.47% | 12.2669 | 0.1495 | 0.2237 |
| seed123_iter3999 | pulse_6c6bb40706a6 | coarse | 43/128 | 33.59% | 13.1227 | 0.1481 | 0.2222 |
| seed123_iter3999 | pulse_4af0b1d60fc6 | coarse | 128/128 | 100.00% | 20.0000 | 0.1159 | 0.1892 |
| seed123_iter3999 | pulse_8ce0dd058c2a | coarse | 128/128 | 100.00% | 20.0000 | 0.1173 | 0.1902 |
| seed123_iter3999 | pulse_ec2f66875aa0 | coarse | 128/128 | 100.00% | 20.0000 | 0.1188 | 0.1915 |
| seed123_iter3999 | pulse_f0bc4b9f6e91 | coarse | 128/128 | 100.00% | 20.0000 | 0.1196 | 0.1922 |
| seed123_iter3999 | pulse_f59722d3524c | coarse | 128/128 | 100.00% | 20.0000 | 0.1202 | 0.1933 |
| seed123_iter3999 | pulse_ba7867e6549c | coarse | 119/128 | 92.97% | 19.4000 | 0.1208 | 0.1951 |
| seed123_iter3999 | pulse_b621093bcd01 | coarse | 102/128 | 79.69% | 18.2402 | 0.1217 | 0.1969 |
| seed123_iter3999 | pulse_5d68ab63e0ef | coarse | 61/128 | 47.66% | 13.9772 | 0.1250 | 0.2014 |
| seed123_iter3999 | pulse_2e47e7dd2cba | coarse | 36/128 | 28.12% | 11.4520 | 0.1266 | 0.2043 |
| seed123_iter3999 | pulse_fae27cf4334f | coarse | 14/128 | 10.94% | 9.3375 | 0.1286 | 0.2092 |
| seed123_iter3999 | noise_3ad7e9e688cc | coarse | 128/128 | 100.00% | 20.0000 | 0.1160 | 0.1901 |
| seed123_iter3999 | noise_76b6c8d9475e | coarse | 128/128 | 100.00% | 20.0000 | 0.1182 | 0.1914 |
| seed123_iter3999 | noise_ace99fcee633 | coarse | 128/128 | 100.00% | 20.0000 | 0.1210 | 0.1929 |
| seed123_iter3999 | noise_a76040145b71 | coarse | 128/128 | 100.00% | 20.0000 | 0.1248 | 0.1949 |
| seed123_iter3999 | noise_fd19a17f7ab4 | coarse | 128/128 | 100.00% | 20.0000 | 0.1286 | 0.1966 |
| seed123_iter3999 | noise_1aada8851753 | coarse | 128/128 | 100.00% | 20.0000 | 0.1333 | 0.1989 |
| seed123_iter3999 | noise_6413ebf12de0 | coarse | 128/128 | 100.00% | 20.0000 | 0.1372 | 0.2003 |
| seed123_iter3999 | noise_493bdc9e1fa2 | coarse | 127/128 | 99.22% | 19.9805 | 0.1418 | 0.2022 |
| seed123_iter3999 | noise_101e6e96aee7 | coarse | 128/128 | 100.00% | 20.0000 | 0.1452 | 0.2032 |
| seed123_iter3999 | noise_dece5089b501 | coarse | 126/128 | 98.44% | 19.8383 | 0.1499 | 0.2052 |
| seed123_iter3999 | imu_bias_2aebd0fda40e | coarse | 128/128 | 100.00% | 20.0000 | 0.1133 | 0.1867 |
| seed123_iter3999 | imu_bias_5705e28d3566 | coarse | 128/128 | 100.00% | 20.0000 | 0.1128 | 0.1847 |
| seed123_iter3999 | imu_bias_846ab0f64545 | coarse | 128/128 | 100.00% | 20.0000 | 0.1137 | 0.1834 |
| seed123_iter3999 | imu_bias_04ce18799df0 | coarse | 128/128 | 100.00% | 20.0000 | 0.1159 | 0.1830 |
| seed123_iter3999 | imu_bias_86a35be18154 | coarse | 128/128 | 100.00% | 20.0000 | 0.1194 | 0.1832 |
| seed123_iter3999 | imu_bias_f1b525ba2b1e | coarse | 128/128 | 100.00% | 20.0000 | 0.1235 | 0.1840 |
| seed123_iter3999 | imu_bias_366018e369c4 | coarse | 128/128 | 100.00% | 20.0000 | 0.1285 | 0.1854 |
| seed123_iter3999 | imu_bias_399b92850697 | coarse | 128/128 | 100.00% | 20.0000 | 0.1330 | 0.1864 |
| seed123_iter3999 | imu_bias_135073b420cd | coarse | 128/128 | 100.00% | 20.0000 | 0.1372 | 0.1873 |
| seed123_iter3999 | imu_bias_b5899bf48dac | coarse | 126/128 | 98.44% | 19.8578 | 0.1407 | 0.1877 |
| seed123_iter3999 | imu_bias_f5408fbd35a6 | coarse | 126/128 | 98.44% | 19.8064 | 0.1429 | 0.1873 |
| seed123_iter3999 | imu_bias_0f25110924e4 | coarse | 121/128 | 94.53% | 19.0766 | 0.1460 | 0.1892 |
| seed123_iter3999 | imu_bias_41b4a6c6dd6f | coarse | 103/128 | 80.47% | 17.1308 | 0.1571 | 0.2001 |
| seed123_iter3999 | imu_bias_ede1e4da0e2c | coarse | 84/128 | 65.62% | 15.8664 | 0.1657 | 0.2093 |
| seed123_iter3999 | imu_bias_ce7df1de845c | coarse | 56/128 | 43.75% | 12.0437 | 0.1806 | 0.2279 |
| seed123_iter3999 | imu_bias_6e42d5991dc0 | coarse | 31/128 | 24.22% | 9.2106 | 0.1934 | 0.2433 |
| seed2026_iter3999 | clean_e65df7c70d30 | coarse | 128/128 | 100.00% | 20.0000 | 0.1233 | 0.1863 |
| seed2026_iter3999 | pulse_598198552a6a | coarse | 128/128 | 100.00% | 20.0000 | 0.1240 | 0.1873 |
| seed2026_iter3999 | pulse_612e9447021a | coarse | 120/128 | 93.75% | 19.5398 | 0.1271 | 0.1920 |
| seed2026_iter3999 | pulse_fc6acbace648 | coarse | 78/128 | 60.94% | 16.2500 | 0.1326 | 0.1982 |
| seed2026_iter3999 | pulse_be409b92b318 | coarse | 68/128 | 53.12% | 15.1173 | 0.1338 | 0.1993 |
| seed2026_iter3999 | pulse_541079131c9c | coarse | 61/128 | 47.66% | 14.6453 | 0.1352 | 0.2008 |
| seed2026_iter3999 | pulse_cab68f744b9e | coarse | 46/128 | 35.94% | 13.7322 | 0.1375 | 0.2029 |
| seed2026_iter3999 | pulse_766c85f17642 | coarse | 44/128 | 34.38% | 13.0281 | 0.1405 | 0.2053 |
| seed2026_iter3999 | pulse_771ebfd2be80 | coarse | 31/128 | 24.22% | 12.0102 | 0.1409 | 0.2052 |
| seed2026_iter3999 | pulse_729006de2cca | coarse | 32/128 | 25.00% | 11.9919 | 0.1409 | 0.2043 |
| seed2026_iter3999 | pulse_56d4a09409f5 | coarse | 47/128 | 36.72% | 12.9241 | 0.1413 | 0.2037 |
| seed2026_iter3999 | pulse_d1112dc8481e | coarse | 128/128 | 100.00% | 20.0000 | 0.1257 | 0.1882 |
| seed2026_iter3999 | pulse_c4a069da32cb | coarse | 128/128 | 100.00% | 20.0000 | 0.1317 | 0.1932 |
| seed2026_iter3999 | pulse_878b84f480be | coarse | 128/128 | 100.00% | 20.0000 | 0.1382 | 0.1992 |
| seed2026_iter3999 | pulse_336affbaace0 | coarse | 118/128 | 92.19% | 19.2706 | 0.1441 | 0.2056 |
| seed2026_iter3999 | pulse_4d30d7e3f2a5 | coarse | 73/128 | 57.03% | 15.6900 | 0.1526 | 0.2149 |
| seed2026_iter3999 | pulse_d34e1497b1a6 | coarse | 36/128 | 28.12% | 12.4019 | 0.1549 | 0.2182 |
| seed2026_iter3999 | pulse_2616fb73abed | coarse | 18/128 | 14.06% | 9.6230 | 0.1581 | 0.2220 |
| seed2026_iter3999 | pulse_6e665d027696 | coarse | 4/128 | 3.12% | 7.1412 | 0.1604 | 0.2249 |
| seed2026_iter3999 | pulse_1c562b061f06 | coarse | 1/128 | 0.78% | 6.6177 | 0.1593 | 0.2238 |
| seed2026_iter3999 | pulse_89d16652c7f6 | coarse | 1/128 | 0.78% | 5.8886 | 0.1612 | 0.2255 |
| seed2026_iter3999 | pulse_1f4338b72772 | coarse | 128/128 | 100.00% | 20.0000 | 0.1270 | 0.1893 |
| seed2026_iter3999 | pulse_0d97f23e5846 | coarse | 127/128 | 99.22% | 19.8794 | 0.1337 | 0.1954 |
| seed2026_iter3999 | pulse_30e7abd7bb25 | coarse | 111/128 | 86.72% | 18.9158 | 0.1410 | 0.2040 |
| seed2026_iter3999 | pulse_6624590865ae | coarse | 96/128 | 75.00% | 17.7198 | 0.1468 | 0.2100 |
| seed2026_iter3999 | pulse_7bfb7292678c | coarse | 78/128 | 60.94% | 16.3859 | 0.1478 | 0.2113 |
| seed2026_iter3999 | pulse_eaa8dd3181ba | coarse | 77/128 | 60.16% | 16.4916 | 0.1467 | 0.2104 |
| seed2026_iter3999 | pulse_fab6e214fe66 | coarse | 82/128 | 64.06% | 16.8864 | 0.1426 | 0.2061 |
| seed2026_iter3999 | pulse_645aa6a28f7c | coarse | 63/128 | 49.22% | 15.5362 | 0.1411 | 0.2048 |
| seed2026_iter3999 | pulse_089d36600d5a | coarse | 82/128 | 64.06% | 17.1128 | 0.1367 | 0.2000 |
| seed2026_iter3999 | pulse_6c6bb40706a6 | coarse | 85/128 | 66.41% | 17.2606 | 0.1367 | 0.1997 |
| seed2026_iter3999 | pulse_4af0b1d60fc6 | coarse | 128/128 | 100.00% | 20.0000 | 0.1227 | 0.1857 |
| seed2026_iter3999 | pulse_8ce0dd058c2a | coarse | 128/128 | 100.00% | 20.0000 | 0.1235 | 0.1869 |
| seed2026_iter3999 | pulse_ec2f66875aa0 | coarse | 128/128 | 100.00% | 20.0000 | 0.1244 | 0.1881 |
| seed2026_iter3999 | pulse_f0bc4b9f6e91 | coarse | 121/128 | 94.53% | 19.5486 | 0.1260 | 0.1899 |
| seed2026_iter3999 | pulse_f59722d3524c | coarse | 125/128 | 97.66% | 19.7639 | 0.1271 | 0.1912 |
| seed2026_iter3999 | pulse_ba7867e6549c | coarse | 122/128 | 95.31% | 19.6211 | 0.1269 | 0.1912 |
| seed2026_iter3999 | pulse_b621093bcd01 | coarse | 115/128 | 89.84% | 19.0923 | 0.1275 | 0.1921 |
| seed2026_iter3999 | pulse_5d68ab63e0ef | coarse | 114/128 | 89.06% | 18.7609 | 0.1281 | 0.1927 |
| seed2026_iter3999 | pulse_2e47e7dd2cba | coarse | 118/128 | 92.19% | 19.2020 | 0.1284 | 0.1928 |
| seed2026_iter3999 | pulse_fae27cf4334f | coarse | 120/128 | 93.75% | 19.3808 | 0.1294 | 0.1935 |
| seed2026_iter3999 | noise_3ad7e9e688cc | coarse | 128/128 | 100.00% | 20.0000 | 0.1242 | 0.1870 |
| seed2026_iter3999 | noise_76b6c8d9475e | coarse | 128/128 | 100.00% | 20.0000 | 0.1270 | 0.1893 |
| seed2026_iter3999 | noise_ace99fcee633 | coarse | 128/128 | 100.00% | 20.0000 | 0.1304 | 0.1920 |
| seed2026_iter3999 | noise_a76040145b71 | coarse | 128/128 | 100.00% | 20.0000 | 0.1340 | 0.1945 |
| seed2026_iter3999 | noise_fd19a17f7ab4 | coarse | 128/128 | 100.00% | 20.0000 | 0.1378 | 0.1972 |
| seed2026_iter3999 | noise_1aada8851753 | coarse | 128/128 | 100.00% | 20.0000 | 0.1420 | 0.1997 |
| seed2026_iter3999 | noise_6413ebf12de0 | coarse | 128/128 | 100.00% | 20.0000 | 0.1432 | 0.1998 |
| seed2026_iter3999 | noise_493bdc9e1fa2 | coarse | 128/128 | 100.00% | 20.0000 | 0.1451 | 0.2005 |
| seed2026_iter3999 | noise_101e6e96aee7 | coarse | 127/128 | 99.22% | 19.8906 | 0.1477 | 0.2014 |
| seed2026_iter3999 | noise_dece5089b501 | coarse | 126/128 | 98.44% | 19.8200 | 0.1496 | 0.2026 |
| seed2026_iter3999 | imu_bias_2aebd0fda40e | coarse | 128/128 | 100.00% | 20.0000 | 0.1175 | 0.1812 |
| seed2026_iter3999 | imu_bias_5705e28d3566 | coarse | 128/128 | 100.00% | 20.0000 | 0.1128 | 0.1767 |
| seed2026_iter3999 | imu_bias_846ab0f64545 | coarse | 128/128 | 100.00% | 20.0000 | 0.1090 | 0.1729 |
| seed2026_iter3999 | imu_bias_04ce18799df0 | coarse | 128/128 | 100.00% | 20.0000 | 0.1065 | 0.1695 |
| seed2026_iter3999 | imu_bias_86a35be18154 | coarse | 128/128 | 100.00% | 20.0000 | 0.1046 | 0.1663 |
| seed2026_iter3999 | imu_bias_f1b525ba2b1e | coarse | 128/128 | 100.00% | 20.0000 | 0.1033 | 0.1629 |
| seed2026_iter3999 | imu_bias_366018e369c4 | coarse | 128/128 | 100.00% | 20.0000 | 0.1022 | 0.1596 |
| seed2026_iter3999 | imu_bias_399b92850697 | coarse | 128/128 | 100.00% | 20.0000 | 0.1011 | 0.1560 |
| seed2026_iter3999 | imu_bias_135073b420cd | coarse | 127/128 | 99.22% | 19.8552 | 0.1017 | 0.1544 |
| seed2026_iter3999 | imu_bias_b5899bf48dac | coarse | 123/128 | 96.09% | 19.4525 | 0.1069 | 0.1566 |
| seed2026_iter3999 | imu_bias_f5408fbd35a6 | coarse | 118/128 | 92.19% | 18.9423 | 0.1169 | 0.1641 |
| seed2026_iter3999 | imu_bias_0f25110924e4 | coarse | 103/128 | 80.47% | 17.7105 | 0.1314 | 0.1774 |
| seed2026_iter3999 | imu_bias_41b4a6c6dd6f | coarse | 76/128 | 59.38% | 14.6484 | 0.1614 | 0.2083 |
| seed2026_iter3999 | imu_bias_ede1e4da0e2c | coarse | 51/128 | 39.84% | 11.8894 | 0.1872 | 0.2366 |
| seed2026_iter3999 | imu_bias_ce7df1de845c | coarse | 27/128 | 21.09% | 9.0189 | 0.1964 | 0.2499 |
| seed2026_iter3999 | imu_bias_6e42d5991dc0 | coarse | 10/128 | 7.81% | 6.5727 | 0.2058 | 0.2645 |
| official_alpha_walking | pulse_e657f5c96505 | local | 117/128 | 91.41% | 19.0836 | 0.1531 | 0.2135 |
| official_alpha_walking | pulse_e27d67a302b0 | local | 106/128 | 82.81% | 18.0739 | 0.1551 | 0.2157 |
| official_alpha_walking | pulse_602cbd33cee7 | local | 100/128 | 78.12% | 17.8964 | 0.1564 | 0.2173 |
| official_alpha_walking | pulse_8ddb33ac78bf | local | 52/128 | 40.62% | 13.6792 | 0.1667 | 0.2334 |
| official_alpha_walking | pulse_01177d8193c0 | local | 55/128 | 42.97% | 13.9720 | 0.1663 | 0.2337 |
| official_alpha_walking | pulse_e56a8e9c7ceb | local | 45/128 | 35.16% | 13.0628 | 0.1665 | 0.2337 |
| seed42_iter3999 | pulse_9eb3544dc303 | local | 121/128 | 94.53% | 19.4795 | 0.1217 | 0.1917 |
| seed42_iter3999 | pulse_14bb6b2becf0 | local | 100/128 | 78.12% | 18.1548 | 0.1244 | 0.1953 |
| seed42_iter3999 | pulse_75374327c7a2 | local | 86/128 | 67.19% | 16.6344 | 0.1261 | 0.1980 |
| seed42_iter3999 | pulse_e657f5c96505 | local | 43/128 | 33.59% | 13.1753 | 0.1300 | 0.2035 |
| seed42_iter3999 | pulse_e27d67a302b0 | local | 37/128 | 28.91% | 12.4031 | 0.1308 | 0.2049 |
| seed42_iter3999 | pulse_602cbd33cee7 | local | 25/128 | 19.53% | 10.9823 | 0.1320 | 0.2064 |
| seed123_iter3999 | pulse_9eb3544dc303 | local | 128/128 | 100.00% | 20.0000 | 0.1167 | 0.1903 |
| seed123_iter3999 | pulse_14bb6b2becf0 | local | 115/128 | 89.84% | 19.1269 | 0.1182 | 0.1925 |
| seed123_iter3999 | pulse_75374327c7a2 | local | 96/128 | 75.00% | 17.6895 | 0.1211 | 0.1965 |
| seed123_iter3999 | pulse_e657f5c96505 | local | 38/128 | 29.69% | 12.1252 | 0.1259 | 0.2031 |
| seed123_iter3999 | pulse_e27d67a302b0 | local | 24/128 | 18.75% | 10.9753 | 0.1286 | 0.2066 |
| seed123_iter3999 | pulse_602cbd33cee7 | local | 24/128 | 18.75% | 10.4384 | 0.1295 | 0.2070 |
| seed2026_iter3999 | pulse_e657f5c96505 | local | 108/128 | 84.38% | 18.8066 | 0.1285 | 0.1940 |
| seed2026_iter3999 | pulse_e27d67a302b0 | local | 98/128 | 76.56% | 17.6553 | 0.1302 | 0.1958 |
| seed2026_iter3999 | pulse_602cbd33cee7 | local | 86/128 | 67.19% | 16.9331 | 0.1322 | 0.1981 |
| seed2026_iter3999 | pulse_8ddb33ac78bf | local | 39/128 | 30.47% | 12.8511 | 0.1382 | 0.2018 |
| seed2026_iter3999 | pulse_01177d8193c0 | local | 36/128 | 28.12% | 12.3609 | 0.1401 | 0.2029 |
| seed2026_iter3999 | pulse_e56a8e9c7ceb | local | 51/128 | 39.84% | 13.2711 | 0.1399 | 0.2021 |
| official_alpha_walking | pulse_8c9197874ee3 | local | 105/128 | 82.03% | 18.1100 | 0.1773 | 0.2344 |
| official_alpha_walking | pulse_58aab4e4e537 | local | 97/128 | 75.78% | 17.4270 | 0.1797 | 0.2370 |
| official_alpha_walking | pulse_bc19461e474a | local | 75/128 | 58.59% | 15.5967 | 0.1833 | 0.2408 |
| official_alpha_walking | pulse_97ce74fa21c0 | local | 46/128 | 35.94% | 13.0855 | 0.1863 | 0.2455 |
| official_alpha_walking | pulse_5e8f743b87e5 | local | 40/128 | 31.25% | 12.6739 | 0.1855 | 0.2451 |
| official_alpha_walking | pulse_9c24b7822490 | local | 31/128 | 24.22% | 11.1567 | 0.1869 | 0.2461 |
| seed42_iter3999 | pulse_8c9197874ee3 | local | 82/128 | 64.06% | 16.9489 | 0.1450 | 0.2121 |
| seed42_iter3999 | pulse_58aab4e4e537 | local | 65/128 | 50.78% | 15.5775 | 0.1493 | 0.2165 |
| seed42_iter3999 | pulse_bc19461e474a | local | 56/128 | 43.75% | 14.7859 | 0.1505 | 0.2180 |
| seed42_iter3999 | pulse_225680815d80 | local | 123/128 | 96.09% | 19.5703 | 0.1349 | 0.2019 |
| seed42_iter3999 | pulse_a051b2201d9f | local | 116/128 | 90.62% | 19.2695 | 0.1378 | 0.2046 |
| seed42_iter3999 | pulse_a46661c48206 | local | 107/128 | 83.59% | 18.6195 | 0.1401 | 0.2072 |
| seed123_iter3999 | pulse_8c9197874ee3 | local | 73/128 | 57.03% | 15.0197 | 0.1455 | 0.2183 |
| seed123_iter3999 | pulse_58aab4e4e537 | local | 58/128 | 45.31% | 13.9322 | 0.1474 | 0.2201 |
| seed123_iter3999 | pulse_bc19461e474a | local | 40/128 | 31.25% | 11.6939 | 0.1505 | 0.2235 |
| seed123_iter3999 | pulse_225680815d80 | local | 116/128 | 90.62% | 19.1812 | 0.1344 | 0.2061 |
| seed123_iter3999 | pulse_a051b2201d9f | local | 113/128 | 88.28% | 19.1755 | 0.1371 | 0.2089 |
| seed123_iter3999 | pulse_a46661c48206 | local | 100/128 | 78.12% | 17.8983 | 0.1400 | 0.2126 |
| seed2026_iter3999 | pulse_8c9197874ee3 | local | 115/128 | 89.84% | 18.9194 | 0.1453 | 0.2071 |
| seed2026_iter3999 | pulse_58aab4e4e537 | local | 108/128 | 84.38% | 18.3206 | 0.1478 | 0.2096 |
| seed2026_iter3999 | pulse_bc19461e474a | local | 94/128 | 73.44% | 17.0127 | 0.1504 | 0.2124 |
| seed2026_iter3999 | pulse_97ce74fa21c0 | local | 73/128 | 57.03% | 15.3070 | 0.1533 | 0.2156 |
| seed2026_iter3999 | pulse_5e8f743b87e5 | local | 54/128 | 42.19% | 13.9123 | 0.1557 | 0.2183 |
| seed2026_iter3999 | pulse_9c24b7822490 | local | 40/128 | 31.25% | 12.2802 | 0.1555 | 0.2186 |
| official_alpha_walking | pulse_c0a31385b35d | local | 110/128 | 85.94% | 18.5928 | 0.1703 | 0.2285 |
| official_alpha_walking | pulse_eb6c577b81dc | local | 108/128 | 84.38% | 18.4534 | 0.1712 | 0.2291 |
| official_alpha_walking | pulse_16ecda6149ec | local | 102/128 | 79.69% | 17.8898 | 0.1729 | 0.2312 |
| official_alpha_walking | pulse_e6241107881e | local | 117/128 | 91.41% | 19.3058 | 0.1657 | 0.2230 |
| official_alpha_walking | pulse_5134d5655ff6 | local | 114/128 | 89.06% | 18.9747 | 0.1675 | 0.2248 |
| official_alpha_walking | pulse_3babdc1f73b1 | local | 121/128 | 94.53% | 19.4183 | 0.1673 | 0.2246 |
| seed42_iter3999 | pulse_5f4ffdbaac3a | local | 118/128 | 92.19% | 19.0783 | 0.1375 | 0.2054 |
| seed42_iter3999 | pulse_90844112dd27 | local | 114/128 | 89.06% | 18.7308 | 0.1392 | 0.2073 |
| seed42_iter3999 | pulse_715162f1b1d3 | local | 117/128 | 91.41% | 18.9647 | 0.1397 | 0.2078 |
| seed42_iter3999 | pulse_956a0f0fc5a5 | local | 116/128 | 90.62% | 18.8148 | 0.1400 | 0.2076 |
| seed42_iter3999 | pulse_04a73f1854bb | local | 115/128 | 89.84% | 18.9077 | 0.1407 | 0.2082 |
| seed42_iter3999 | pulse_b81bced66d88 | local | 118/128 | 92.19% | 19.0786 | 0.1394 | 0.2069 |
| seed123_iter3999 | pulse_c0a31385b35d | local | 63/128 | 49.22% | 14.9056 | 0.1425 | 0.2160 |
| seed123_iter3999 | pulse_eb6c577b81dc | local | 61/128 | 47.66% | 14.2194 | 0.1441 | 0.2175 |
| seed123_iter3999 | pulse_16ecda6149ec | local | 64/128 | 50.00% | 14.6947 | 0.1435 | 0.2169 |
| seed123_iter3999 | pulse_9b9db0b3575d | local | 116/128 | 90.62% | 19.1081 | 0.1268 | 0.1992 |
| seed123_iter3999 | pulse_7731e189b742 | local | 110/128 | 85.94% | 18.7872 | 0.1281 | 0.2006 |
| seed123_iter3999 | pulse_e530618f95fe | local | 104/128 | 81.25% | 18.3473 | 0.1301 | 0.2025 |
| seed2026_iter3999 | pulse_ed767caf379a | local | 69/128 | 53.91% | 16.5673 | 0.1404 | 0.2037 |
| seed2026_iter3999 | pulse_3db54849c76b | local | 72/128 | 56.25% | 16.4517 | 0.1395 | 0.2028 |
| seed2026_iter3999 | pulse_b5a80f219a3a | local | 73/128 | 57.03% | 16.7378 | 0.1387 | 0.2020 |
| seed2026_iter3999 | pulse_5a012c50d0e8 | local | 69/128 | 53.91% | 16.2887 | 0.1410 | 0.2044 |
| seed2026_iter3999 | pulse_120ab66e6236 | local | 71/128 | 55.47% | 16.5353 | 0.1414 | 0.2046 |
| seed2026_iter3999 | pulse_30c9b515114c | local | 81/128 | 63.28% | 16.7153 | 0.1419 | 0.2050 |
| official_alpha_walking | pulse_c37eed36e275 | local | 127/128 | 99.22% | 19.9725 | 0.1554 | 0.2143 |
| official_alpha_walking | pulse_76c9e182520e | local | 127/128 | 99.22% | 19.9741 | 0.1555 | 0.2145 |
| official_alpha_walking | pulse_bd55ceaf1161 | local | 123/128 | 96.09% | 19.6336 | 0.1560 | 0.2150 |
| official_alpha_walking | pulse_1c5898101052 | local | 127/128 | 99.22% | 19.8784 | 0.1553 | 0.2142 |
| official_alpha_walking | pulse_6d028c6e9da7 | local | 127/128 | 99.22% | 19.9436 | 0.1559 | 0.2149 |
| official_alpha_walking | pulse_49b0b93e2f59 | local | 124/128 | 96.88% | 19.6270 | 0.1558 | 0.2148 |
| seed42_iter3999 | pulse_71cbcad3eac1 | local | 121/128 | 94.53% | 19.5258 | 0.1287 | 0.1981 |
| seed42_iter3999 | pulse_e3c25029f931 | local | 123/128 | 96.09% | 19.6300 | 0.1273 | 0.1968 |
| seed42_iter3999 | pulse_77fbb284f53b | local | 128/128 | 100.00% | 20.0000 | 0.1282 | 0.1978 |
| seed42_iter3999 | pulse_d318cbf05660 | local | 123/128 | 96.09% | 19.7244 | 0.1226 | 0.1914 |
| seed42_iter3999 | pulse_19c547eebcc4 | local | 125/128 | 97.66% | 19.7725 | 0.1229 | 0.1918 |
| seed42_iter3999 | pulse_e23144ed914f | local | 125/128 | 97.66% | 19.7730 | 0.1238 | 0.1927 |
| seed123_iter3999 | pulse_1c5898101052 | local | 98/128 | 76.56% | 18.0148 | 0.1220 | 0.1975 |
| seed123_iter3999 | pulse_6d028c6e9da7 | local | 77/128 | 60.16% | 15.8634 | 0.1232 | 0.1984 |
| seed123_iter3999 | pulse_49b0b93e2f59 | local | 70/128 | 54.69% | 15.7919 | 0.1239 | 0.2002 |
| seed123_iter3999 | pulse_c37eed36e275 | local | 53/128 | 41.41% | 14.0878 | 0.1248 | 0.2017 |
| seed123_iter3999 | pulse_76c9e182520e | local | 44/128 | 34.38% | 12.9712 | 0.1259 | 0.2031 |
| seed123_iter3999 | pulse_bd55ceaf1161 | local | 50/128 | 39.06% | 13.2925 | 0.1253 | 0.2025 |
| seed2026_iter3999 | pulse_d318cbf05660 | local | 120/128 | 93.75% | 19.5064 | 0.1267 | 0.1912 |
| seed2026_iter3999 | pulse_19c547eebcc4 | local | 118/128 | 92.19% | 19.2342 | 0.1270 | 0.1917 |
| seed2026_iter3999 | pulse_e23144ed914f | local | 119/128 | 92.97% | 19.3566 | 0.1269 | 0.1913 |
| seed2026_iter3999 | pulse_8b9c1a1ea84a | local | 126/128 | 98.44% | 19.8581 | 0.1249 | 0.1885 |
| seed2026_iter3999 | pulse_f4c68be10c2b | local | 124/128 | 96.88% | 19.7409 | 0.1254 | 0.1893 |
| seed2026_iter3999 | pulse_1c7d01be8419 | local | 125/128 | 97.66% | 19.7019 | 0.1257 | 0.1898 |
| official_alpha_walking | noise_4bfaf1156a48 | local | 128/128 | 100.00% | 20.0000 | 0.1792 | 0.2296 |
| official_alpha_walking | noise_e98a4fd0d3a5 | local | 128/128 | 100.00% | 20.0000 | 0.1795 | 0.2294 |
| official_alpha_walking | noise_e1aacd41a881 | local | 126/128 | 98.44% | 19.8495 | 0.1802 | 0.2301 |
| official_alpha_walking | noise_486193a9cbdf | local | 128/128 | 100.00% | 20.0000 | 0.1758 | 0.2272 |
| official_alpha_walking | noise_6633c7933a06 | local | 128/128 | 100.00% | 20.0000 | 0.1774 | 0.2284 |
| official_alpha_walking | noise_b4de15aaa9eb | local | 128/128 | 100.00% | 20.0000 | 0.1776 | 0.2284 |
| seed42_iter3999 | noise_4bfaf1156a48 | local | 128/128 | 100.00% | 20.0000 | 0.1514 | 0.2048 |
| seed42_iter3999 | noise_e98a4fd0d3a5 | local | 127/128 | 99.22% | 19.8937 | 0.1534 | 0.2062 |
| seed42_iter3999 | noise_e1aacd41a881 | local | 128/128 | 100.00% | 20.0000 | 0.1531 | 0.2056 |
| seed42_iter3999 | noise_486193a9cbdf | local | 128/128 | 100.00% | 20.0000 | 0.1464 | 0.2023 |
| seed42_iter3999 | noise_6633c7933a06 | local | 128/128 | 100.00% | 20.0000 | 0.1482 | 0.2034 |
| seed42_iter3999 | noise_b4de15aaa9eb | local | 127/128 | 99.22% | 19.9119 | 0.1491 | 0.2037 |
| seed123_iter3999 | noise_dc63e645c474 | local | 128/128 | 100.00% | 20.0000 | 0.1298 | 0.1972 |
| seed123_iter3999 | noise_4312140a128d | local | 128/128 | 100.00% | 20.0000 | 0.1307 | 0.1976 |
| seed123_iter3999 | noise_98f1d9184867 | local | 128/128 | 100.00% | 20.0000 | 0.1317 | 0.1980 |
| seed123_iter3999 | noise_4bfaf1156a48 | local | 125/128 | 97.66% | 19.8939 | 0.1468 | 0.2040 |
| seed123_iter3999 | noise_e98a4fd0d3a5 | local | 124/128 | 96.88% | 19.6481 | 0.1478 | 0.2045 |
| seed123_iter3999 | noise_e1aacd41a881 | local | 126/128 | 98.44% | 19.9173 | 0.1489 | 0.2049 |
| seed2026_iter3999 | noise_fc220739f9d7 | local | 128/128 | 100.00% | 20.0000 | 0.1349 | 0.1952 |
| seed2026_iter3999 | noise_1f023ac34f52 | local | 128/128 | 100.00% | 20.0000 | 0.1362 | 0.1961 |
| seed2026_iter3999 | noise_ca8d4c73aa8a | local | 128/128 | 100.00% | 20.0000 | 0.1366 | 0.1963 |
| seed2026_iter3999 | noise_1d8b189b7cf5 | local | 128/128 | 100.00% | 20.0000 | 0.1277 | 0.1899 |
| seed2026_iter3999 | noise_05ef0ac8ce1a | local | 128/128 | 100.00% | 20.0000 | 0.1285 | 0.1905 |
| seed2026_iter3999 | noise_1656a6874431 | local | 128/128 | 100.00% | 20.0000 | 0.1297 | 0.1915 |
| official_alpha_walking | imu_bias_48a39012d337 | local | 88/128 | 68.75% | 16.4392 | 0.2263 | 0.2671 |
| official_alpha_walking | imu_bias_832ccde31be8 | local | 89/128 | 69.53% | 16.2195 | 0.2221 | 0.2635 |
| official_alpha_walking | imu_bias_61f3223d035c | local | 76/128 | 59.38% | 14.9034 | 0.2358 | 0.2763 |
| official_alpha_walking | imu_bias_14d87d3ba600 | local | 61/128 | 47.66% | 13.5027 | 0.2447 | 0.2852 |
| official_alpha_walking | imu_bias_3551298162aa | local | 54/128 | 42.19% | 12.0833 | 0.2568 | 0.2973 |
| official_alpha_walking | imu_bias_310c895373f7 | local | 48/128 | 37.50% | 11.6972 | 0.2588 | 0.2989 |
| seed42_iter3999 | imu_bias_4d1d408f1772 | local | 30/128 | 23.44% | 8.6180 | 0.1842 | 0.2442 |
| seed42_iter3999 | imu_bias_2121acd60f89 | local | 24/128 | 18.75% | 7.5739 | 0.1899 | 0.2515 |
| seed42_iter3999 | imu_bias_a25b531b04a4 | local | 21/128 | 16.41% | 7.1200 | 0.1935 | 0.2538 |
| seed42_iter3999 | imu_bias_659073aee0e2 | local | 76/128 | 59.38% | 14.3527 | 0.1545 | 0.2062 |
| seed42_iter3999 | imu_bias_3204daf49868 | local | 60/128 | 46.88% | 13.1862 | 0.1573 | 0.2080 |
| seed42_iter3999 | imu_bias_fb04f3d9c6a0 | local | 48/128 | 37.50% | 11.5623 | 0.1659 | 0.2205 |
| seed123_iter3999 | imu_bias_4d1d408f1772 | local | 81/128 | 63.28% | 14.5736 | 0.1672 | 0.2112 |
| seed123_iter3999 | imu_bias_2121acd60f89 | local | 70/128 | 54.69% | 14.0706 | 0.1701 | 0.2155 |
| seed123_iter3999 | imu_bias_a25b531b04a4 | local | 58/128 | 45.31% | 12.6052 | 0.1801 | 0.2276 |
| seed123_iter3999 | imu_bias_f0e849044043 | local | 48/128 | 37.50% | 11.3205 | 0.1825 | 0.2288 |
| seed123_iter3999 | imu_bias_31d36b5a2d9b | local | 44/128 | 34.38% | 10.8373 | 0.1880 | 0.2339 |
| seed123_iter3999 | imu_bias_5ea467908a9c | local | 35/128 | 27.34% | 9.6416 | 0.1885 | 0.2385 |
| seed2026_iter3999 | imu_bias_14d87d3ba600 | local | 94/128 | 73.44% | 16.5780 | 0.1372 | 0.1840 |
| seed2026_iter3999 | imu_bias_3551298162aa | local | 90/128 | 70.31% | 15.9208 | 0.1466 | 0.1940 |
| seed2026_iter3999 | imu_bias_310c895373f7 | local | 84/128 | 65.62% | 15.2627 | 0.1484 | 0.1962 |
| seed2026_iter3999 | imu_bias_659073aee0e2 | local | 78/128 | 60.94% | 14.7656 | 0.1631 | 0.2105 |
| seed2026_iter3999 | imu_bias_3204daf49868 | local | 66/128 | 51.56% | 13.6289 | 0.1701 | 0.2184 |
| seed2026_iter3999 | imu_bias_fb04f3d9c6a0 | local | 54/128 | 42.19% | 12.3295 | 0.1850 | 0.2344 |
| official_alpha_walking | delay_6b4cf3960b09 | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1551 | 0.2344 |
| official_alpha_walking | delay_e4a0786654f3 | delay_freeze_exploration | 67/128 | 52.34% | 14.2784 | 0.2198 | 0.2962 |
| official_alpha_walking | delay_86489003f338 | delay_freeze_exploration | 0/128 | 0.00% | 1.6936 | 0.2912 | 0.3618 |
| official_alpha_walking | delay_0abe9ff7960d | delay_freeze_exploration | 0/128 | 0.00% | 1.1347 | 0.2509 | 0.3265 |
| official_alpha_walking | delay_990c42b89bfa | delay_freeze_exploration | 0/128 | 0.00% | 0.9184 | 0.2189 | 0.3072 |
| official_alpha_walking | freeze_0035b4f3507e | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1526 | 0.2113 |
| official_alpha_walking | freeze_8fa2d74f4539 | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1526 | 0.2116 |
| official_alpha_walking | freeze_7f6c41308c14 | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1529 | 0.2119 |
| official_alpha_walking | freeze_dc56e826b91c | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1535 | 0.2119 |
| official_alpha_walking | freeze_cdd1815a2919 | delay_freeze_exploration | 127/128 | 99.22% | 19.9631 | 0.1551 | 0.2126 |
| official_alpha_walking | freeze_94691ef2801c | delay_freeze_exploration | 119/128 | 92.97% | 19.6153 | 0.1569 | 0.2140 |
| official_alpha_walking | freeze_ccab6e9c7e3f | delay_freeze_exploration | 116/128 | 90.62% | 19.2656 | 0.1590 | 0.2166 |
| official_alpha_walking | freeze_be309a2e83f6 | delay_freeze_exploration | 100/128 | 78.12% | 18.1400 | 0.1620 | 0.2204 |
| official_alpha_walking | freeze_c4ab2ce5e9a8 | delay_freeze_exploration | 83/128 | 64.84% | 16.5937 | 0.1648 | 0.2232 |
| official_alpha_walking | freeze_17cc4085f7d0 | delay_freeze_exploration | 59/128 | 46.09% | 14.9566 | 0.1683 | 0.2267 |
| official_alpha_walking | freeze_0e2a76721d47 | delay_freeze_exploration | 38/128 | 29.69% | 12.6773 | 0.1707 | 0.2297 |
| official_alpha_walking | freeze_8cd28e6ce082 | delay_freeze_exploration | 18/128 | 14.06% | 9.9497 | 0.1721 | 0.2320 |
| official_alpha_walking | freeze_19993d75d5c2 | delay_freeze_exploration | 4/128 | 3.12% | 7.6562 | 0.1741 | 0.2348 |
| seed42_iter3999 | delay_6b4cf3960b09 | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1339 | 0.2174 |
| seed42_iter3999 | delay_e4a0786654f3 | delay_freeze_exploration | 4/128 | 3.12% | 6.4584 | 0.2407 | 0.3148 |
| seed42_iter3999 | delay_86489003f338 | delay_freeze_exploration | 0/128 | 0.00% | 1.3112 | 0.3008 | 0.3849 |
| seed42_iter3999 | delay_0abe9ff7960d | delay_freeze_exploration | 0/128 | 0.00% | 0.9484 | 0.2503 | 0.3462 |
| seed42_iter3999 | delay_990c42b89bfa | delay_freeze_exploration | 0/128 | 0.00% | 0.8025 | 0.2124 | 0.3137 |
| seed42_iter3999 | freeze_0035b4f3507e | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1206 | 0.1908 |
| seed42_iter3999 | freeze_8fa2d74f4539 | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1209 | 0.1909 |
| seed42_iter3999 | freeze_7f6c41308c14 | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1215 | 0.1911 |
| seed42_iter3999 | freeze_dc56e826b91c | delay_freeze_exploration | 127/128 | 99.22% | 19.8841 | 0.1231 | 0.1916 |
| seed42_iter3999 | freeze_cdd1815a2919 | delay_freeze_exploration | 119/128 | 92.97% | 19.3606 | 0.1268 | 0.1941 |
| seed42_iter3999 | freeze_94691ef2801c | delay_freeze_exploration | 116/128 | 90.62% | 19.1056 | 0.1285 | 0.1958 |
| seed42_iter3999 | freeze_ccab6e9c7e3f | delay_freeze_exploration | 102/128 | 79.69% | 18.1352 | 0.1296 | 0.1975 |
| seed42_iter3999 | freeze_be309a2e83f6 | delay_freeze_exploration | 90/128 | 70.31% | 17.2005 | 0.1296 | 0.1982 |
| seed42_iter3999 | freeze_c4ab2ce5e9a8 | delay_freeze_exploration | 87/128 | 67.97% | 16.9656 | 0.1324 | 0.2007 |
| seed42_iter3999 | freeze_17cc4085f7d0 | delay_freeze_exploration | 70/128 | 54.69% | 15.3150 | 0.1363 | 0.2054 |
| seed42_iter3999 | freeze_0e2a76721d47 | delay_freeze_exploration | 38/128 | 29.69% | 12.4547 | 0.1400 | 0.2095 |
| seed42_iter3999 | freeze_8cd28e6ce082 | delay_freeze_exploration | 20/128 | 15.62% | 9.6295 | 0.1421 | 0.2116 |
| seed42_iter3999 | freeze_19993d75d5c2 | delay_freeze_exploration | 5/128 | 3.91% | 7.2906 | 0.1427 | 0.2111 |
| seed123_iter3999 | delay_6b4cf3960b09 | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1211 | 0.2199 |
| seed123_iter3999 | delay_e4a0786654f3 | delay_freeze_exploration | 18/128 | 14.06% | 8.1919 | 0.2043 | 0.2906 |
| seed123_iter3999 | delay_86489003f338 | delay_freeze_exploration | 0/128 | 0.00% | 1.2311 | 0.2873 | 0.3653 |
| seed123_iter3999 | delay_0abe9ff7960d | delay_freeze_exploration | 0/128 | 0.00% | 0.8883 | 0.2556 | 0.3447 |
| seed123_iter3999 | delay_990c42b89bfa | delay_freeze_exploration | 0/128 | 0.00% | 0.7897 | 0.2058 | 0.3026 |
| seed123_iter3999 | freeze_0035b4f3507e | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1156 | 0.1905 |
| seed123_iter3999 | freeze_8fa2d74f4539 | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1161 | 0.1909 |
| seed123_iter3999 | freeze_7f6c41308c14 | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1168 | 0.1910 |
| seed123_iter3999 | freeze_dc56e826b91c | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1184 | 0.1913 |
| seed123_iter3999 | freeze_cdd1815a2919 | delay_freeze_exploration | 123/128 | 96.09% | 19.7312 | 0.1193 | 0.1914 |
| seed123_iter3999 | freeze_94691ef2801c | delay_freeze_exploration | 115/128 | 89.84% | 19.3123 | 0.1211 | 0.1928 |
| seed123_iter3999 | freeze_ccab6e9c7e3f | delay_freeze_exploration | 110/128 | 85.94% | 18.8355 | 0.1226 | 0.1940 |
| seed123_iter3999 | freeze_be309a2e83f6 | delay_freeze_exploration | 106/128 | 82.81% | 18.7406 | 0.1234 | 0.1950 |
| seed123_iter3999 | freeze_c4ab2ce5e9a8 | delay_freeze_exploration | 95/128 | 74.22% | 17.7314 | 0.1249 | 0.1967 |
| seed123_iter3999 | freeze_17cc4085f7d0 | delay_freeze_exploration | 81/128 | 63.28% | 16.7722 | 0.1266 | 0.1985 |
| seed123_iter3999 | freeze_0e2a76721d47 | delay_freeze_exploration | 33/128 | 25.78% | 11.9147 | 0.1282 | 0.2020 |
| seed123_iter3999 | freeze_8cd28e6ce082 | delay_freeze_exploration | 24/128 | 18.75% | 10.5573 | 0.1276 | 0.2007 |
| seed123_iter3999 | freeze_19993d75d5c2 | delay_freeze_exploration | 7/128 | 5.47% | 7.7227 | 0.1276 | 0.2009 |
| seed2026_iter3999 | delay_6b4cf3960b09 | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1343 | 0.2199 |
| seed2026_iter3999 | delay_e4a0786654f3 | delay_freeze_exploration | 3/128 | 2.34% | 6.7556 | 0.2170 | 0.2976 |
| seed2026_iter3999 | delay_86489003f338 | delay_freeze_exploration | 0/128 | 0.00% | 1.8092 | 0.2803 | 0.3639 |
| seed2026_iter3999 | delay_0abe9ff7960d | delay_freeze_exploration | 0/128 | 0.00% | 0.8794 | 0.2663 | 0.3643 |
| seed2026_iter3999 | delay_990c42b89bfa | delay_freeze_exploration | 0/128 | 0.00% | 0.7569 | 0.2048 | 0.3196 |
| seed2026_iter3999 | freeze_0035b4f3507e | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1239 | 0.1874 |
| seed2026_iter3999 | freeze_8fa2d74f4539 | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1243 | 0.1880 |
| seed2026_iter3999 | freeze_7f6c41308c14 | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1248 | 0.1885 |
| seed2026_iter3999 | freeze_dc56e826b91c | delay_freeze_exploration | 128/128 | 100.00% | 20.0000 | 0.1252 | 0.1885 |
| seed2026_iter3999 | freeze_cdd1815a2919 | delay_freeze_exploration | 127/128 | 99.22% | 19.8783 | 0.1266 | 0.1894 |
| seed2026_iter3999 | freeze_94691ef2801c | delay_freeze_exploration | 113/128 | 88.28% | 18.6461 | 0.1272 | 0.1909 |
| seed2026_iter3999 | freeze_ccab6e9c7e3f | delay_freeze_exploration | 111/128 | 86.72% | 18.4327 | 0.1276 | 0.1913 |
| seed2026_iter3999 | freeze_be309a2e83f6 | delay_freeze_exploration | 101/128 | 78.91% | 17.4589 | 0.1291 | 0.1941 |
| seed2026_iter3999 | freeze_c4ab2ce5e9a8 | delay_freeze_exploration | 92/128 | 71.88% | 17.1928 | 0.1300 | 0.1955 |
| seed2026_iter3999 | freeze_17cc4085f7d0 | delay_freeze_exploration | 85/128 | 66.41% | 16.5028 | 0.1323 | 0.1978 |
| seed2026_iter3999 | freeze_0e2a76721d47 | delay_freeze_exploration | 68/128 | 53.12% | 15.2970 | 0.1348 | 0.2005 |
| seed2026_iter3999 | freeze_8cd28e6ce082 | delay_freeze_exploration | 26/128 | 20.31% | 11.6036 | 0.1372 | 0.2033 |
| seed2026_iter3999 | freeze_19993d75d5c2 | delay_freeze_exploration | 9/128 | 7.03% | 8.6420 | 0.1387 | 0.2043 |
| official_alpha_walking | clean_e65df7c70d30 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1545 | 0.2124 |
| official_alpha_walking | delay_6b4cf3960b09 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1574 | 0.2362 |
| official_alpha_walking | delay_e4a0786654f3 | confirmation | 182/384 | 47.40% | 13.7692 | 0.2267 | 0.3020 |
| official_alpha_walking | delay_86489003f338 | confirmation | 0/384 | 0.00% | 1.8274 | 0.2953 | 0.3662 |
| official_alpha_walking | delay_0abe9ff7960d | confirmation | 0/384 | 0.00% | 1.0844 | 0.2548 | 0.3322 |
| official_alpha_walking | delay_990c42b89bfa | confirmation | 0/384 | 0.00% | 0.9385 | 0.2210 | 0.3100 |
| official_alpha_walking | freeze_0035b4f3507e | confirmation | 384/384 | 100.00% | 20.0000 | 0.1546 | 0.2130 |
| official_alpha_walking | freeze_8fa2d74f4539 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1547 | 0.2133 |
| official_alpha_walking | freeze_7f6c41308c14 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1547 | 0.2134 |
| official_alpha_walking | freeze_dc56e826b91c | confirmation | 384/384 | 100.00% | 20.0000 | 0.1554 | 0.2136 |
| official_alpha_walking | freeze_cdd1815a2919 | confirmation | 382/384 | 99.48% | 19.9570 | 0.1563 | 0.2137 |
| official_alpha_walking | freeze_94691ef2801c | confirmation | 368/384 | 95.83% | 19.6773 | 0.1584 | 0.2155 |
| official_alpha_walking | freeze_ccab6e9c7e3f | confirmation | 336/384 | 87.50% | 18.9834 | 0.1604 | 0.2178 |
| official_alpha_walking | freeze_be309a2e83f6 | confirmation | 289/384 | 75.26% | 18.0078 | 0.1630 | 0.2209 |
| official_alpha_walking | freeze_c4ab2ce5e9a8 | confirmation | 237/384 | 61.72% | 16.5708 | 0.1662 | 0.2247 |
| official_alpha_walking | freeze_17cc4085f7d0 | confirmation | 175/384 | 45.57% | 14.4570 | 0.1692 | 0.2275 |
| official_alpha_walking | freeze_0e2a76721d47 | confirmation | 102/384 | 26.56% | 12.2467 | 0.1726 | 0.2312 |
| official_alpha_walking | freeze_8cd28e6ce082 | confirmation | 53/384 | 13.80% | 9.8534 | 0.1737 | 0.2325 |
| official_alpha_walking | freeze_19993d75d5c2 | confirmation | 16/384 | 4.17% | 7.8099 | 0.1730 | 0.2323 |
| official_alpha_walking | pulse_9eb3544dc303 | confirmation | 378/384 | 98.44% | 19.8767 | 0.1529 | 0.2120 |
| official_alpha_walking | pulse_14bb6b2becf0 | confirmation | 368/384 | 95.83% | 19.6205 | 0.1530 | 0.2126 |
| official_alpha_walking | pulse_75374327c7a2 | confirmation | 341/384 | 88.80% | 18.8365 | 0.1542 | 0.2144 |
| official_alpha_walking | pulse_602cbd33cee7 | confirmation | 292/384 | 76.04% | 17.2078 | 0.1584 | 0.2195 |
| official_alpha_walking | pulse_541079131c9c | confirmation | 252/384 | 65.62% | 16.1799 | 0.1641 | 0.2257 |
| official_alpha_walking | pulse_56d4a09409f5 | confirmation | 143/384 | 37.24% | 13.4465 | 0.1692 | 0.2360 |
| official_alpha_walking | pulse_8c9197874ee3 | confirmation | 298/384 | 77.60% | 17.8973 | 0.1795 | 0.2362 |
| official_alpha_walking | pulse_58aab4e4e537 | confirmation | 287/384 | 74.74% | 17.5761 | 0.1808 | 0.2379 |
| official_alpha_walking | pulse_bc19461e474a | confirmation | 240/384 | 62.50% | 16.2365 | 0.1835 | 0.2409 |
| official_alpha_walking | pulse_4d30d7e3f2a5 | confirmation | 198/384 | 51.56% | 15.1347 | 0.1849 | 0.2427 |
| official_alpha_walking | pulse_9c24b7822490 | confirmation | 107/384 | 27.86% | 11.6876 | 0.1874 | 0.2463 |
| official_alpha_walking | pulse_89d16652c7f6 | confirmation | 34/384 | 8.85% | 7.9486 | 0.1787 | 0.2401 |
| official_alpha_walking | pulse_e530618f95fe | confirmation | 366/384 | 95.31% | 19.5472 | 0.1652 | 0.2220 |
| official_alpha_walking | pulse_7bfb7292678c | confirmation | 316/384 | 82.29% | 18.2534 | 0.1721 | 0.2298 |
| official_alpha_walking | pulse_c0a31385b35d | confirmation | 298/384 | 77.60% | 17.8233 | 0.1735 | 0.2314 |
| official_alpha_walking | pulse_eb6c577b81dc | confirmation | 307/384 | 79.95% | 18.0068 | 0.1735 | 0.2315 |
| official_alpha_walking | pulse_16ecda6149ec | confirmation | 282/384 | 73.44% | 17.5835 | 0.1753 | 0.2334 |
| official_alpha_walking | pulse_6c6bb40706a6 | confirmation | 319/384 | 83.07% | 18.6050 | 0.1675 | 0.2243 |
| official_alpha_walking | pulse_f59722d3524c | confirmation | 380/384 | 98.96% | 19.8956 | 0.1564 | 0.2151 |
| official_alpha_walking | pulse_1c5898101052 | confirmation | 375/384 | 97.66% | 19.7927 | 0.1576 | 0.2164 |
| official_alpha_walking | pulse_6d028c6e9da7 | confirmation | 379/384 | 98.70% | 19.8594 | 0.1574 | 0.2162 |
| official_alpha_walking | pulse_49b0b93e2f59 | confirmation | 377/384 | 98.18% | 19.8073 | 0.1576 | 0.2163 |
| official_alpha_walking | pulse_bd55ceaf1161 | confirmation | 376/384 | 97.92% | 19.8185 | 0.1579 | 0.2165 |
| official_alpha_walking | pulse_fae27cf4334f | confirmation | 374/384 | 97.40% | 19.7161 | 0.1585 | 0.2171 |
| official_alpha_walking | noise_9f33d1454cc1 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1553 | 0.2131 |
| official_alpha_walking | noise_e98a4fd0d3a5 | confirmation | 381/384 | 99.22% | 19.8704 | 0.1824 | 0.2321 |
| official_alpha_walking | noise_e1aacd41a881 | confirmation | 376/384 | 97.92% | 19.8236 | 0.1829 | 0.2325 |
| official_alpha_walking | noise_c2fb1f66490e | confirmation | 376/384 | 97.92% | 19.7047 | 0.1844 | 0.2338 |
| official_alpha_walking | imu_bias_2aebd0fda40e | confirmation | 384/384 | 100.00% | 20.0000 | 0.1532 | 0.2109 |
| official_alpha_walking | imu_bias_2121acd60f89 | confirmation | 77/384 | 20.05% | 8.1003 | 0.2896 | 0.3308 |
| official_alpha_walking | imu_bias_a25b531b04a4 | confirmation | 69/384 | 17.97% | 7.5493 | 0.2841 | 0.3264 |
| official_alpha_walking | imu_bias_6e42d5991dc0 | confirmation | 53/384 | 13.80% | 6.2743 | 0.2866 | 0.3312 |
| seed42_iter3999 | clean_e65df7c70d30 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1213 | 0.1909 |
| seed42_iter3999 | delay_6b4cf3960b09 | confirmation | 383/384 | 99.74% | 19.9993 | 0.1349 | 0.2183 |
| seed42_iter3999 | delay_e4a0786654f3 | confirmation | 8/384 | 2.08% | 5.9538 | 0.2405 | 0.3141 |
| seed42_iter3999 | delay_86489003f338 | confirmation | 0/384 | 0.00% | 1.3842 | 0.2973 | 0.3835 |
| seed42_iter3999 | delay_0abe9ff7960d | confirmation | 0/384 | 0.00% | 0.9256 | 0.2451 | 0.3478 |
| seed42_iter3999 | delay_990c42b89bfa | confirmation | 0/384 | 0.00% | 0.7808 | 0.2126 | 0.3125 |
| seed42_iter3999 | freeze_0035b4f3507e | confirmation | 384/384 | 100.00% | 20.0000 | 0.1218 | 0.1916 |
| seed42_iter3999 | freeze_8fa2d74f4539 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1221 | 0.1918 |
| seed42_iter3999 | freeze_7f6c41308c14 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1226 | 0.1918 |
| seed42_iter3999 | freeze_dc56e826b91c | confirmation | 384/384 | 100.00% | 20.0000 | 0.1236 | 0.1919 |
| seed42_iter3999 | freeze_cdd1815a2919 | confirmation | 374/384 | 97.40% | 19.7935 | 0.1257 | 0.1930 |
| seed42_iter3999 | freeze_94691ef2801c | confirmation | 321/384 | 83.59% | 18.4793 | 0.1298 | 0.1972 |
| seed42_iter3999 | freeze_ccab6e9c7e3f | confirmation | 301/384 | 78.39% | 17.8930 | 0.1308 | 0.1985 |
| seed42_iter3999 | freeze_be309a2e83f6 | confirmation | 275/384 | 71.61% | 17.4153 | 0.1326 | 0.2004 |
| seed42_iter3999 | freeze_c4ab2ce5e9a8 | confirmation | 252/384 | 65.62% | 16.8464 | 0.1342 | 0.2022 |
| seed42_iter3999 | freeze_17cc4085f7d0 | confirmation | 208/384 | 54.17% | 15.4805 | 0.1360 | 0.2048 |
| seed42_iter3999 | freeze_0e2a76721d47 | confirmation | 120/384 | 31.25% | 13.0661 | 0.1387 | 0.2075 |
| seed42_iter3999 | freeze_8cd28e6ce082 | confirmation | 46/384 | 11.98% | 10.1844 | 0.1410 | 0.2101 |
| seed42_iter3999 | freeze_19993d75d5c2 | confirmation | 22/384 | 5.73% | 8.5530 | 0.1413 | 0.2105 |
| seed42_iter3999 | pulse_9eb3544dc303 | confirmation | 358/384 | 93.23% | 19.3087 | 0.1231 | 0.1931 |
| seed42_iter3999 | pulse_14bb6b2becf0 | confirmation | 304/384 | 79.17% | 18.2193 | 0.1251 | 0.1955 |
| seed42_iter3999 | pulse_75374327c7a2 | confirmation | 233/384 | 60.68% | 16.3181 | 0.1274 | 0.1990 |
| seed42_iter3999 | pulse_602cbd33cee7 | confirmation | 103/384 | 26.82% | 12.0848 | 0.1326 | 0.2064 |
| seed42_iter3999 | pulse_541079131c9c | confirmation | 89/384 | 23.18% | 11.6318 | 0.1363 | 0.2103 |
| seed42_iter3999 | pulse_56d4a09409f5 | confirmation | 58/384 | 15.10% | 10.0782 | 0.1396 | 0.2151 |
| seed42_iter3999 | pulse_8c9197874ee3 | confirmation | 249/384 | 64.84% | 16.7467 | 0.1474 | 0.2141 |
| seed42_iter3999 | pulse_58aab4e4e537 | confirmation | 219/384 | 57.03% | 16.0719 | 0.1499 | 0.2166 |
| seed42_iter3999 | pulse_bc19461e474a | confirmation | 180/384 | 46.88% | 15.0775 | 0.1516 | 0.2185 |
| seed42_iter3999 | pulse_4d30d7e3f2a5 | confirmation | 140/384 | 36.46% | 13.7163 | 0.1526 | 0.2195 |
| seed42_iter3999 | pulse_9c24b7822490 | confirmation | 109/384 | 28.39% | 12.5927 | 0.1542 | 0.2217 |
| seed42_iter3999 | pulse_89d16652c7f6 | confirmation | 18/384 | 4.69% | 7.9797 | 0.1603 | 0.2274 |
| seed42_iter3999 | pulse_e530618f95fe | confirmation | 376/384 | 97.92% | 19.7773 | 0.1322 | 0.2001 |
| seed42_iter3999 | pulse_7bfb7292678c | confirmation | 349/384 | 90.89% | 18.9439 | 0.1395 | 0.2070 |
| seed42_iter3999 | pulse_c0a31385b35d | confirmation | 346/384 | 90.10% | 19.0170 | 0.1400 | 0.2075 |
| seed42_iter3999 | pulse_eb6c577b81dc | confirmation | 347/384 | 90.36% | 19.0402 | 0.1397 | 0.2071 |
| seed42_iter3999 | pulse_16ecda6149ec | confirmation | 350/384 | 91.15% | 19.0971 | 0.1399 | 0.2072 |
| seed42_iter3999 | pulse_6c6bb40706a6 | confirmation | 370/384 | 96.35% | 19.6734 | 0.1362 | 0.2032 |
| seed42_iter3999 | pulse_f59722d3524c | confirmation | 380/384 | 98.96% | 19.9361 | 0.1224 | 0.1909 |
| seed42_iter3999 | pulse_1c5898101052 | confirmation | 375/384 | 97.66% | 19.8165 | 0.1263 | 0.1950 |
| seed42_iter3999 | pulse_6d028c6e9da7 | confirmation | 376/384 | 97.92% | 19.7371 | 0.1268 | 0.1956 |
| seed42_iter3999 | pulse_49b0b93e2f59 | confirmation | 371/384 | 96.61% | 19.6885 | 0.1274 | 0.1961 |
| seed42_iter3999 | pulse_bd55ceaf1161 | confirmation | 369/384 | 96.09% | 19.6630 | 0.1279 | 0.1968 |
| seed42_iter3999 | pulse_fae27cf4334f | confirmation | 372/384 | 96.88% | 19.6546 | 0.1287 | 0.1980 |
| seed42_iter3999 | noise_9f33d1454cc1 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1220 | 0.1912 |
| seed42_iter3999 | noise_e98a4fd0d3a5 | confirmation | 383/384 | 99.74% | 19.9954 | 0.1544 | 0.2070 |
| seed42_iter3999 | noise_e1aacd41a881 | confirmation | 383/384 | 99.74% | 19.9839 | 0.1558 | 0.2079 |
| seed42_iter3999 | noise_c2fb1f66490e | confirmation | 384/384 | 100.00% | 20.0000 | 0.1566 | 0.2081 |
| seed42_iter3999 | imu_bias_2aebd0fda40e | confirmation | 384/384 | 100.00% | 20.0000 | 0.1171 | 0.1872 |
| seed42_iter3999 | imu_bias_2121acd60f89 | confirmation | 113/384 | 29.43% | 9.8119 | 0.1772 | 0.2331 |
| seed42_iter3999 | imu_bias_a25b531b04a4 | confirmation | 92/384 | 23.96% | 8.9453 | 0.1855 | 0.2422 |
| seed42_iter3999 | imu_bias_6e42d5991dc0 | confirmation | 30/384 | 7.81% | 5.9956 | 0.2041 | 0.2665 |
| seed123_iter3999 | clean_e65df7c70d30 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1162 | 0.1904 |
| seed123_iter3999 | delay_6b4cf3960b09 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1226 | 0.2210 |
| seed123_iter3999 | delay_e4a0786654f3 | confirmation | 48/384 | 12.50% | 7.9831 | 0.2091 | 0.2931 |
| seed123_iter3999 | delay_86489003f338 | confirmation | 0/384 | 0.00% | 1.2406 | 0.2825 | 0.3601 |
| seed123_iter3999 | delay_0abe9ff7960d | confirmation | 0/384 | 0.00% | 0.8497 | 0.2528 | 0.3423 |
| seed123_iter3999 | delay_990c42b89bfa | confirmation | 0/384 | 0.00% | 0.7905 | 0.2043 | 0.3038 |
| seed123_iter3999 | freeze_0035b4f3507e | confirmation | 384/384 | 100.00% | 20.0000 | 0.1165 | 0.1913 |
| seed123_iter3999 | freeze_8fa2d74f4539 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1170 | 0.1917 |
| seed123_iter3999 | freeze_7f6c41308c14 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1178 | 0.1918 |
| seed123_iter3999 | freeze_dc56e826b91c | confirmation | 384/384 | 100.00% | 20.0000 | 0.1192 | 0.1921 |
| seed123_iter3999 | freeze_cdd1815a2919 | confirmation | 376/384 | 97.92% | 19.8364 | 0.1208 | 0.1926 |
| seed123_iter3999 | freeze_94691ef2801c | confirmation | 348/384 | 90.62% | 19.2961 | 0.1225 | 0.1939 |
| seed123_iter3999 | freeze_ccab6e9c7e3f | confirmation | 330/384 | 85.94% | 19.0030 | 0.1235 | 0.1949 |
| seed123_iter3999 | freeze_be309a2e83f6 | confirmation | 329/384 | 85.68% | 18.8170 | 0.1248 | 0.1961 |
| seed123_iter3999 | freeze_c4ab2ce5e9a8 | confirmation | 297/384 | 77.34% | 17.9521 | 0.1260 | 0.1976 |
| seed123_iter3999 | freeze_17cc4085f7d0 | confirmation | 211/384 | 54.95% | 15.6699 | 0.1279 | 0.2001 |
| seed123_iter3999 | freeze_0e2a76721d47 | confirmation | 122/384 | 31.77% | 13.0097 | 0.1291 | 0.2018 |
| seed123_iter3999 | freeze_8cd28e6ce082 | confirmation | 56/384 | 14.58% | 10.0376 | 0.1286 | 0.2016 |
| seed123_iter3999 | freeze_19993d75d5c2 | confirmation | 18/384 | 4.69% | 7.5781 | 0.1280 | 0.2013 |
| seed123_iter3999 | pulse_9eb3544dc303 | confirmation | 380/384 | 98.96% | 19.9156 | 0.1177 | 0.1915 |
| seed123_iter3999 | pulse_14bb6b2becf0 | confirmation | 337/384 | 87.76% | 18.8096 | 0.1196 | 0.1941 |
| seed123_iter3999 | pulse_75374327c7a2 | confirmation | 267/384 | 69.53% | 16.6520 | 0.1221 | 0.1974 |
| seed123_iter3999 | pulse_602cbd33cee7 | confirmation | 61/384 | 15.89% | 10.1351 | 0.1287 | 0.2055 |
| seed123_iter3999 | pulse_541079131c9c | confirmation | 9/384 | 2.34% | 6.4519 | 0.1351 | 0.2103 |
| seed123_iter3999 | pulse_56d4a09409f5 | confirmation | 4/384 | 1.04% | 5.5444 | 0.1376 | 0.2102 |
| seed123_iter3999 | pulse_8c9197874ee3 | confirmation | 213/384 | 55.47% | 15.0136 | 0.1468 | 0.2197 |
| seed123_iter3999 | pulse_58aab4e4e537 | confirmation | 172/384 | 44.79% | 14.1373 | 0.1489 | 0.2215 |
| seed123_iter3999 | pulse_bc19461e474a | confirmation | 146/384 | 38.02% | 12.9124 | 0.1501 | 0.2224 |
| seed123_iter3999 | pulse_4d30d7e3f2a5 | confirmation | 104/384 | 27.08% | 11.5040 | 0.1524 | 0.2248 |
| seed123_iter3999 | pulse_9c24b7822490 | confirmation | 61/384 | 15.89% | 9.4294 | 0.1532 | 0.2257 |
| seed123_iter3999 | pulse_89d16652c7f6 | confirmation | 1/384 | 0.26% | 5.7453 | 0.1512 | 0.2226 |
| seed123_iter3999 | pulse_e530618f95fe | confirmation | 295/384 | 76.82% | 17.6441 | 0.1333 | 0.2053 |
| seed123_iter3999 | pulse_7bfb7292678c | confirmation | 163/384 | 42.45% | 13.5870 | 0.1444 | 0.2175 |
| seed123_iter3999 | pulse_c0a31385b35d | confirmation | 150/384 | 39.06% | 13.3562 | 0.1447 | 0.2180 |
| seed123_iter3999 | pulse_eb6c577b81dc | confirmation | 155/384 | 40.36% | 13.2857 | 0.1459 | 0.2190 |
| seed123_iter3999 | pulse_16ecda6149ec | confirmation | 152/384 | 39.58% | 13.1681 | 0.1458 | 0.2195 |
| seed123_iter3999 | pulse_6c6bb40706a6 | confirmation | 116/384 | 30.21% | 11.7851 | 0.1513 | 0.2245 |
| seed123_iter3999 | pulse_f59722d3524c | confirmation | 381/384 | 99.22% | 19.9017 | 0.1207 | 0.1940 |
| seed123_iter3999 | pulse_1c5898101052 | confirmation | 268/384 | 69.79% | 17.1134 | 0.1236 | 0.1988 |
| seed123_iter3999 | pulse_6d028c6e9da7 | confirmation | 239/384 | 62.24% | 16.1418 | 0.1243 | 0.2000 |
| seed123_iter3999 | pulse_49b0b93e2f59 | confirmation | 218/384 | 56.77% | 15.7070 | 0.1245 | 0.2002 |
| seed123_iter3999 | pulse_bd55ceaf1161 | confirmation | 143/384 | 37.24% | 13.2497 | 0.1264 | 0.2036 |
| seed123_iter3999 | pulse_fae27cf4334f | confirmation | 73/384 | 19.01% | 10.1282 | 0.1292 | 0.2091 |
| seed123_iter3999 | noise_9f33d1454cc1 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1169 | 0.1909 |
| seed123_iter3999 | noise_e98a4fd0d3a5 | confirmation | 379/384 | 98.70% | 19.8385 | 0.1502 | 0.2064 |
| seed123_iter3999 | noise_e1aacd41a881 | confirmation | 375/384 | 97.66% | 19.7554 | 0.1510 | 0.2068 |
| seed123_iter3999 | noise_c2fb1f66490e | confirmation | 371/384 | 96.61% | 19.6640 | 0.1524 | 0.2074 |
| seed123_iter3999 | imu_bias_2aebd0fda40e | confirmation | 384/384 | 100.00% | 20.0000 | 0.1142 | 0.1876 |
| seed123_iter3999 | imu_bias_2121acd60f89 | confirmation | 231/384 | 60.16% | 14.3392 | 0.1749 | 0.2203 |
| seed123_iter3999 | imu_bias_a25b531b04a4 | confirmation | 213/384 | 55.47% | 13.5981 | 0.1798 | 0.2253 |
| seed123_iter3999 | imu_bias_6e42d5991dc0 | confirmation | 108/384 | 28.12% | 9.5076 | 0.1955 | 0.2438 |
| seed2026_iter3999 | clean_e65df7c70d30 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1253 | 0.1881 |
| seed2026_iter3999 | delay_6b4cf3960b09 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1366 | 0.2217 |
| seed2026_iter3999 | delay_e4a0786654f3 | confirmation | 12/384 | 3.12% | 6.9486 | 0.2203 | 0.3002 |
| seed2026_iter3999 | delay_86489003f338 | confirmation | 0/384 | 0.00% | 1.7419 | 0.2758 | 0.3605 |
| seed2026_iter3999 | delay_0abe9ff7960d | confirmation | 0/384 | 0.00% | 0.9055 | 0.2587 | 0.3587 |
| seed2026_iter3999 | delay_990c42b89bfa | confirmation | 0/384 | 0.00% | 0.7585 | 0.2033 | 0.3189 |
| seed2026_iter3999 | freeze_0035b4f3507e | confirmation | 384/384 | 100.00% | 20.0000 | 0.1258 | 0.1891 |
| seed2026_iter3999 | freeze_8fa2d74f4539 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1262 | 0.1897 |
| seed2026_iter3999 | freeze_7f6c41308c14 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1268 | 0.1902 |
| seed2026_iter3999 | freeze_dc56e826b91c | confirmation | 384/384 | 100.00% | 20.0000 | 0.1272 | 0.1903 |
| seed2026_iter3999 | freeze_cdd1815a2919 | confirmation | 380/384 | 98.96% | 19.9140 | 0.1278 | 0.1903 |
| seed2026_iter3999 | freeze_94691ef2801c | confirmation | 348/384 | 90.62% | 18.9308 | 0.1287 | 0.1921 |
| seed2026_iter3999 | freeze_ccab6e9c7e3f | confirmation | 302/384 | 78.65% | 17.9602 | 0.1300 | 0.1944 |
| seed2026_iter3999 | freeze_be309a2e83f6 | confirmation | 276/384 | 71.88% | 16.9868 | 0.1308 | 0.1961 |
| seed2026_iter3999 | freeze_c4ab2ce5e9a8 | confirmation | 259/384 | 67.45% | 16.4516 | 0.1315 | 0.1975 |
| seed2026_iter3999 | freeze_17cc4085f7d0 | confirmation | 234/384 | 60.94% | 15.6830 | 0.1345 | 0.2007 |
| seed2026_iter3999 | freeze_0e2a76721d47 | confirmation | 150/384 | 39.06% | 13.5233 | 0.1371 | 0.2039 |
| seed2026_iter3999 | freeze_8cd28e6ce082 | confirmation | 76/384 | 19.79% | 10.9023 | 0.1394 | 0.2055 |
| seed2026_iter3999 | freeze_19993d75d5c2 | confirmation | 34/384 | 8.85% | 8.4619 | 0.1403 | 0.2062 |
| seed2026_iter3999 | pulse_9eb3544dc303 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1262 | 0.1895 |
| seed2026_iter3999 | pulse_14bb6b2becf0 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1264 | 0.1900 |
| seed2026_iter3999 | pulse_75374327c7a2 | confirmation | 379/384 | 98.70% | 19.8986 | 0.1272 | 0.1911 |
| seed2026_iter3999 | pulse_602cbd33cee7 | confirmation | 289/384 | 75.26% | 17.9181 | 0.1327 | 0.1980 |
| seed2026_iter3999 | pulse_541079131c9c | confirmation | 144/384 | 37.50% | 13.9157 | 0.1383 | 0.2038 |
| seed2026_iter3999 | pulse_56d4a09409f5 | confirmation | 121/384 | 31.51% | 12.3881 | 0.1418 | 0.2043 |
| seed2026_iter3999 | pulse_8c9197874ee3 | confirmation | 319/384 | 83.07% | 18.4614 | 0.1488 | 0.2102 |
| seed2026_iter3999 | pulse_58aab4e4e537 | confirmation | 287/384 | 74.74% | 17.6815 | 0.1506 | 0.2123 |
| seed2026_iter3999 | pulse_bc19461e474a | confirmation | 255/384 | 66.41% | 16.6653 | 0.1526 | 0.2143 |
| seed2026_iter3999 | pulse_4d30d7e3f2a5 | confirmation | 214/384 | 55.73% | 15.5101 | 0.1552 | 0.2173 |
| seed2026_iter3999 | pulse_9c24b7822490 | confirmation | 121/384 | 31.51% | 12.5085 | 0.1578 | 0.2205 |
| seed2026_iter3999 | pulse_89d16652c7f6 | confirmation | 2/384 | 0.52% | 5.6418 | 0.1616 | 0.2252 |
| seed2026_iter3999 | pulse_e530618f95fe | confirmation | 356/384 | 92.71% | 19.3300 | 0.1414 | 0.2037 |
| seed2026_iter3999 | pulse_7bfb7292678c | confirmation | 219/384 | 57.03% | 15.6063 | 0.1515 | 0.2149 |
| seed2026_iter3999 | pulse_c0a31385b35d | confirmation | 205/384 | 53.39% | 15.1881 | 0.1520 | 0.2155 |
| seed2026_iter3999 | pulse_eb6c577b81dc | confirmation | 224/384 | 58.33% | 15.8401 | 0.1511 | 0.2144 |
| seed2026_iter3999 | pulse_16ecda6149ec | confirmation | 209/384 | 54.43% | 15.5127 | 0.1509 | 0.2144 |
| seed2026_iter3999 | pulse_6c6bb40706a6 | confirmation | 252/384 | 65.62% | 17.1061 | 0.1366 | 0.1997 |
| seed2026_iter3999 | pulse_f59722d3524c | confirmation | 361/384 | 94.01% | 19.3546 | 0.1290 | 0.1929 |
| seed2026_iter3999 | pulse_1c5898101052 | confirmation | 349/384 | 90.89% | 19.1179 | 0.1297 | 0.1939 |
| seed2026_iter3999 | pulse_6d028c6e9da7 | confirmation | 344/384 | 89.58% | 19.0892 | 0.1300 | 0.1944 |
| seed2026_iter3999 | pulse_49b0b93e2f59 | confirmation | 354/384 | 92.19% | 19.2290 | 0.1300 | 0.1943 |
| seed2026_iter3999 | pulse_bd55ceaf1161 | confirmation | 341/384 | 88.80% | 18.9553 | 0.1312 | 0.1954 |
| seed2026_iter3999 | pulse_fae27cf4334f | confirmation | 330/384 | 85.94% | 18.6722 | 0.1326 | 0.1970 |
| seed2026_iter3999 | noise_9f33d1454cc1 | confirmation | 384/384 | 100.00% | 20.0000 | 0.1262 | 0.1889 |
| seed2026_iter3999 | noise_e98a4fd0d3a5 | confirmation | 376/384 | 97.92% | 19.8369 | 0.1511 | 0.2042 |
| seed2026_iter3999 | noise_e1aacd41a881 | confirmation | 378/384 | 98.44% | 19.8460 | 0.1511 | 0.2040 |
| seed2026_iter3999 | noise_c2fb1f66490e | confirmation | 376/384 | 97.92% | 19.8002 | 0.1511 | 0.2037 |
| seed2026_iter3999 | imu_bias_2aebd0fda40e | confirmation | 384/384 | 100.00% | 20.0000 | 0.1196 | 0.1831 |
| seed2026_iter3999 | imu_bias_2121acd60f89 | confirmation | 135/384 | 35.16% | 10.6844 | 0.1961 | 0.2464 |
| seed2026_iter3999 | imu_bias_a25b531b04a4 | confirmation | 116/384 | 30.21% | 10.0042 | 0.1948 | 0.2463 |
| seed2026_iter3999 | imu_bias_6e42d5991dc0 | confirmation | 52/384 | 13.54% | 7.1903 | 0.2069 | 0.2627 |
| official_alpha_walking | pulse_766c85f17642 | combinations | 73/128 | 57.03% | 15.7180 | 0.1642 | 0.2287 |
| official_alpha_walking | pulse_771ebfd2be80 | combinations | 64/128 | 50.00% | 14.8716 | 0.1661 | 0.2316 |
| official_alpha_walking | pulse_2616fb73abed | combinations | 20/128 | 15.62% | 9.5980 | 0.1874 | 0.2477 |
| official_alpha_walking | pulse_6e665d027696 | combinations | 16/128 | 12.50% | 8.3222 | 0.1857 | 0.2464 |
| official_alpha_walking | pulse_fab6e214fe66 | combinations | 106/128 | 82.81% | 18.3666 | 0.1725 | 0.2304 |
| official_alpha_walking | pulse_645aa6a28f7c | combinations | 97/128 | 75.78% | 17.8181 | 0.1728 | 0.2305 |
| official_alpha_walking | pulse_c9799bf5d0fe | combinations | 126/128 | 98.44% | 19.7677 | 0.1589 | 0.2188 |
| official_alpha_walking | pulse_e2f3a750de4e | combinations | 120/128 | 93.75% | 19.4383 | 0.1596 | 0.2198 |
| official_alpha_walking | pulse_1e8a463e56c4 | combinations | 114/128 | 89.06% | 19.0731 | 0.1608 | 0.2207 |
| official_alpha_walking | pulse_307d5a489724 | combinations | 120/128 | 93.75% | 19.3366 | 0.1599 | 0.2204 |
| official_alpha_walking | pulse_6e541406d133 | combinations | 0/128 | 0.00% | 5.7536 | 0.1784 | 0.2391 |
| official_alpha_walking | pulse_6deb4ab66108 | combinations | 4/128 | 3.12% | 6.4550 | 0.1784 | 0.2386 |
| official_alpha_walking | pulse_b621093bcd01 | combinations | 124/128 | 96.88% | 19.5852 | 0.1554 | 0.2144 |
| official_alpha_walking | pulse_5d68ab63e0ef | combinations | 126/128 | 98.44% | 19.7616 | 0.1557 | 0.2147 |
| seed42_iter3999 | pulse_766c85f17642 | combinations | 38/128 | 29.69% | 12.8606 | 0.1380 | 0.2127 |
| seed42_iter3999 | pulse_771ebfd2be80 | combinations | 34/128 | 26.56% | 12.0055 | 0.1391 | 0.2144 |
| seed42_iter3999 | pulse_2616fb73abed | combinations | 20/128 | 15.62% | 10.8633 | 0.1555 | 0.2235 |
| seed42_iter3999 | pulse_6e665d027696 | combinations | 8/128 | 6.25% | 9.4425 | 0.1568 | 0.2248 |
| seed42_iter3999 | pulse_fab6e214fe66 | combinations | 122/128 | 95.31% | 19.4333 | 0.1390 | 0.2064 |
| seed42_iter3999 | pulse_645aa6a28f7c | combinations | 122/128 | 95.31% | 19.5644 | 0.1386 | 0.2058 |
| seed42_iter3999 | pulse_c9799bf5d0fe | combinations | 127/128 | 99.22% | 19.9120 | 0.1221 | 0.1911 |
| seed42_iter3999 | pulse_e2f3a750de4e | combinations | 126/128 | 98.44% | 19.8558 | 0.1219 | 0.1910 |
| seed42_iter3999 | pulse_1e8a463e56c4 | combinations | 66/128 | 51.56% | 15.5036 | 0.1335 | 0.2053 |
| seed42_iter3999 | pulse_307d5a489724 | combinations | 60/128 | 46.88% | 14.7548 | 0.1349 | 0.2073 |
| seed42_iter3999 | pulse_6e541406d133 | combinations | 25/128 | 19.53% | 10.9487 | 0.1580 | 0.2262 |
| seed42_iter3999 | pulse_6deb4ab66108 | combinations | 32/128 | 25.00% | 11.4816 | 0.1572 | 0.2252 |
| seed42_iter3999 | pulse_b621093bcd01 | combinations | 125/128 | 97.66% | 19.8991 | 0.1246 | 0.1934 |
| seed42_iter3999 | pulse_5d68ab63e0ef | combinations | 122/128 | 95.31% | 19.4889 | 0.1275 | 0.1966 |
| seed123_iter3999 | pulse_766c85f17642 | combinations | 1/128 | 0.78% | 5.4369 | 0.1377 | 0.2114 |
| seed123_iter3999 | pulse_771ebfd2be80 | combinations | 0/128 | 0.00% | 5.2727 | 0.1380 | 0.2107 |
| seed123_iter3999 | pulse_2616fb73abed | combinations | 3/128 | 2.34% | 6.7869 | 0.1536 | 0.2264 |
| seed123_iter3999 | pulse_6e665d027696 | combinations | 2/128 | 1.56% | 6.5327 | 0.1527 | 0.2249 |
| seed123_iter3999 | pulse_fab6e214fe66 | combinations | 41/128 | 32.03% | 12.5870 | 0.1470 | 0.2215 |
| seed123_iter3999 | pulse_645aa6a28f7c | combinations | 39/128 | 30.47% | 11.8591 | 0.1490 | 0.2235 |
| seed123_iter3999 | pulse_c9799bf5d0fe | combinations | 14/128 | 10.94% | 9.6920 | 0.1301 | 0.2078 |
| seed123_iter3999 | pulse_e2f3a750de4e | combinations | 7/128 | 5.47% | 7.6567 | 0.1331 | 0.2127 |
| seed123_iter3999 | pulse_1e8a463e56c4 | combinations | 4/128 | 3.12% | 6.5277 | 0.1352 | 0.2088 |
| seed123_iter3999 | pulse_307d5a489724 | combinations | 3/128 | 2.34% | 6.0781 | 0.1379 | 0.2116 |
| seed123_iter3999 | pulse_6e541406d133 | combinations | 2/128 | 1.56% | 7.3316 | 0.1386 | 0.2108 |
| seed123_iter3999 | pulse_6deb4ab66108 | combinations | 6/128 | 4.69% | 7.9253 | 0.1335 | 0.2061 |
| seed123_iter3999 | pulse_b621093bcd01 | combinations | 103/128 | 80.47% | 18.2300 | 0.1219 | 0.1970 |
| seed123_iter3999 | pulse_5d68ab63e0ef | combinations | 71/128 | 55.47% | 15.3198 | 0.1240 | 0.2001 |
| seed2026_iter3999 | pulse_766c85f17642 | combinations | 39/128 | 30.47% | 12.8225 | 0.1404 | 0.2053 |
| seed2026_iter3999 | pulse_771ebfd2be80 | combinations | 31/128 | 24.22% | 12.0283 | 0.1419 | 0.2061 |
| seed2026_iter3999 | pulse_2616fb73abed | combinations | 10/128 | 7.81% | 8.9244 | 0.1578 | 0.2222 |
| seed2026_iter3999 | pulse_6e665d027696 | combinations | 5/128 | 3.91% | 7.5269 | 0.1575 | 0.2220 |
| seed2026_iter3999 | pulse_fab6e214fe66 | combinations | 74/128 | 57.81% | 16.3914 | 0.1445 | 0.2078 |
| seed2026_iter3999 | pulse_645aa6a28f7c | combinations | 78/128 | 60.94% | 16.7486 | 0.1403 | 0.2033 |
| seed2026_iter3999 | pulse_c9799bf5d0fe | combinations | 113/128 | 88.28% | 18.9428 | 0.1306 | 0.1945 |
| seed2026_iter3999 | pulse_e2f3a750de4e | combinations | 107/128 | 83.59% | 18.3297 | 0.1333 | 0.1975 |
| seed2026_iter3999 | pulse_1e8a463e56c4 | combinations | 88/128 | 68.75% | 17.0070 | 0.1325 | 0.1972 |
| seed2026_iter3999 | pulse_307d5a489724 | combinations | 90/128 | 70.31% | 17.3137 | 0.1326 | 0.1975 |
| seed2026_iter3999 | pulse_6e541406d133 | combinations | 1/128 | 0.78% | 5.7737 | 0.1534 | 0.2181 |
| seed2026_iter3999 | pulse_6deb4ab66108 | combinations | 0/128 | 0.00% | 5.6175 | 0.1544 | 0.2190 |
| seed2026_iter3999 | pulse_b621093bcd01 | combinations | 118/128 | 92.19% | 19.1084 | 0.1273 | 0.1920 |
| seed2026_iter3999 | pulse_5d68ab63e0ef | combinations | 116/128 | 90.62% | 19.0302 | 0.1278 | 0.1924 |
| official_alpha_walking | pulse_20156fb4a964 | time | 128/128 | 100.00% | 20.0000 | 0.1531 | 0.2114 |
| official_alpha_walking | pulse_20dc7da1b868 | time | 128/128 | 100.00% | 20.0000 | 0.1531 | 0.2115 |
| official_alpha_walking | pulse_a3c73ebdc848 | time | 128/128 | 100.00% | 20.0000 | 0.1529 | 0.2115 |
| official_alpha_walking | pulse_8573b4ec74fa | time | 126/128 | 98.44% | 19.8303 | 0.1550 | 0.2140 |
| official_alpha_walking | pulse_fcb7f8ee803a | time | 103/128 | 80.47% | 17.8927 | 0.1648 | 0.2238 |
| official_alpha_walking | pulse_9aae7dc249d6 | time | 68/128 | 53.12% | 14.8020 | 0.1718 | 0.2298 |
| official_alpha_walking | pulse_298e62fc669c | time | 122/128 | 95.31% | 19.2950 | 0.1551 | 0.2140 |
| official_alpha_walking | pulse_381fee804b86 | time | 128/128 | 100.00% | 20.0000 | 0.1555 | 0.2148 |
| official_alpha_walking | pulse_b3c29424ad4a | time | 127/128 | 99.22% | 19.9152 | 0.1554 | 0.2143 |
| official_alpha_walking | pulse_558dedd70894 | time | 128/128 | 100.00% | 20.0000 | 0.1517 | 0.2105 |
| official_alpha_walking | pulse_325725b67aed | time | 128/128 | 100.00% | 20.0000 | 0.1531 | 0.2119 |
| official_alpha_walking | pulse_f4d241b247e9 | time | 128/128 | 100.00% | 20.0000 | 0.1531 | 0.2117 |
| official_alpha_walking | pulse_7bc86c56377e | time | 128/128 | 100.00% | 20.0000 | 0.1533 | 0.2117 |
| official_alpha_walking | pulse_b870eb388b0b | time | 128/128 | 100.00% | 20.0000 | 0.1532 | 0.2115 |
| official_alpha_walking | pulse_98b6b76781ad | time | 128/128 | 100.00% | 20.0000 | 0.1534 | 0.2118 |
| official_alpha_walking | pulse_1ec3af8fc1f6 | time | 128/128 | 100.00% | 20.0000 | 0.1534 | 0.2119 |
| official_alpha_walking | pulse_71b218b4b546 | time | 125/128 | 97.66% | 19.8919 | 0.1553 | 0.2144 |
| official_alpha_walking | pulse_e01d7619ff9b | time | 109/128 | 85.16% | 18.2792 | 0.1648 | 0.2239 |
| official_alpha_walking | pulse_0a594abb58a8 | time | 67/128 | 52.34% | 15.0897 | 0.1740 | 0.2320 |
| official_alpha_walking | pulse_aea2569b291c | time | 117/128 | 91.41% | 18.7417 | 0.1552 | 0.2142 |
| official_alpha_walking | pulse_a5f84a341a8b | time | 126/128 | 98.44% | 19.9050 | 0.1559 | 0.2152 |
| official_alpha_walking | pulse_3246794f3a5d | time | 127/128 | 99.22% | 19.9739 | 0.1553 | 0.2142 |
| official_alpha_walking | pulse_77527a984020 | time | 128/128 | 100.00% | 20.0000 | 0.1519 | 0.2107 |
| official_alpha_walking | pulse_b8e7485fe318 | time | 128/128 | 100.00% | 20.0000 | 0.1532 | 0.2119 |
| official_alpha_walking | pulse_87f3400a0194 | time | 128/128 | 100.00% | 20.0000 | 0.1534 | 0.2119 |
| official_alpha_walking | pulse_7580aafe0db9 | time | 126/128 | 98.44% | 19.8275 | 0.1532 | 0.2119 |
| seed42_iter3999 | pulse_20156fb4a964 | time | 128/128 | 100.00% | 20.0000 | 0.1205 | 0.1900 |
| seed42_iter3999 | pulse_20dc7da1b868 | time | 128/128 | 100.00% | 20.0000 | 0.1211 | 0.1904 |
| seed42_iter3999 | pulse_a3c73ebdc848 | time | 128/128 | 100.00% | 20.0000 | 0.1213 | 0.1906 |
| seed42_iter3999 | pulse_8573b4ec74fa | time | 125/128 | 97.66% | 19.7105 | 0.1250 | 0.1938 |
| seed42_iter3999 | pulse_fcb7f8ee803a | time | 76/128 | 59.38% | 15.7305 | 0.1487 | 0.2174 |
| seed42_iter3999 | pulse_9aae7dc249d6 | time | 39/128 | 30.47% | 12.7431 | 0.1565 | 0.2252 |
| seed42_iter3999 | pulse_298e62fc669c | time | 119/128 | 92.97% | 18.9617 | 0.1237 | 0.1938 |
| seed42_iter3999 | pulse_381fee804b86 | time | 126/128 | 98.44% | 19.8886 | 0.1245 | 0.1935 |
| seed42_iter3999 | pulse_b3c29424ad4a | time | 125/128 | 97.66% | 19.8069 | 0.1252 | 0.1939 |
| seed42_iter3999 | pulse_558dedd70894 | time | 128/128 | 100.00% | 20.0000 | 0.1200 | 0.1903 |
| seed42_iter3999 | pulse_325725b67aed | time | 128/128 | 100.00% | 20.0000 | 0.1212 | 0.1907 |
| seed42_iter3999 | pulse_f4d241b247e9 | time | 127/128 | 99.22% | 19.8819 | 0.1215 | 0.1911 |
| seed42_iter3999 | pulse_7bc86c56377e | time | 127/128 | 99.22% | 19.9138 | 0.1216 | 0.1911 |
| seed42_iter3999 | pulse_b870eb388b0b | time | 128/128 | 100.00% | 20.0000 | 0.1206 | 0.1902 |
| seed42_iter3999 | pulse_98b6b76781ad | time | 128/128 | 100.00% | 20.0000 | 0.1213 | 0.1905 |
| seed42_iter3999 | pulse_1ec3af8fc1f6 | time | 128/128 | 100.00% | 20.0000 | 0.1216 | 0.1910 |
| seed42_iter3999 | pulse_71b218b4b546 | time | 120/128 | 93.75% | 19.4111 | 0.1270 | 0.1961 |
| seed42_iter3999 | pulse_e01d7619ff9b | time | 51/128 | 39.84% | 13.5661 | 0.1509 | 0.2207 |
| seed42_iter3999 | pulse_0a594abb58a8 | time | 18/128 | 14.06% | 10.9594 | 0.1569 | 0.2275 |
| seed42_iter3999 | pulse_aea2569b291c | time | 102/128 | 79.69% | 17.0402 | 0.1295 | 0.1999 |
| seed42_iter3999 | pulse_a5f84a341a8b | time | 124/128 | 96.88% | 19.7305 | 0.1270 | 0.1962 |
| seed42_iter3999 | pulse_3246794f3a5d | time | 123/128 | 96.09% | 19.7245 | 0.1265 | 0.1957 |
| seed42_iter3999 | pulse_77527a984020 | time | 128/128 | 100.00% | 20.0000 | 0.1202 | 0.1906 |
| seed42_iter3999 | pulse_b8e7485fe318 | time | 127/128 | 99.22% | 19.8656 | 0.1224 | 0.1919 |
| seed42_iter3999 | pulse_87f3400a0194 | time | 125/128 | 97.66% | 19.6467 | 0.1221 | 0.1918 |
| seed42_iter3999 | pulse_7580aafe0db9 | time | 128/128 | 100.00% | 20.0000 | 0.1217 | 0.1913 |
| seed123_iter3999 | pulse_20156fb4a964 | time | 128/128 | 100.00% | 20.0000 | 0.1160 | 0.1900 |
| seed123_iter3999 | pulse_20dc7da1b868 | time | 128/128 | 100.00% | 20.0000 | 0.1170 | 0.1906 |
| seed123_iter3999 | pulse_a3c73ebdc848 | time | 128/128 | 100.00% | 20.0000 | 0.1186 | 0.1918 |
| seed123_iter3999 | pulse_8573b4ec74fa | time | 105/128 | 82.03% | 18.3770 | 0.1217 | 0.1970 |
| seed123_iter3999 | pulse_fcb7f8ee803a | time | 23/128 | 17.97% | 10.2419 | 0.1263 | 0.2052 |
| seed123_iter3999 | pulse_9aae7dc249d6 | time | 7/128 | 5.47% | 8.1878 | 0.1306 | 0.2060 |
| seed123_iter3999 | pulse_298e62fc669c | time | 95/128 | 74.22% | 16.1184 | 0.1199 | 0.1962 |
| seed123_iter3999 | pulse_381fee804b86 | time | 91/128 | 71.09% | 17.1228 | 0.1228 | 0.1986 |
| seed123_iter3999 | pulse_b3c29424ad4a | time | 99/128 | 77.34% | 18.1589 | 0.1217 | 0.1969 |
| seed123_iter3999 | pulse_558dedd70894 | time | 128/128 | 100.00% | 20.0000 | 0.1164 | 0.1902 |
| seed123_iter3999 | pulse_325725b67aed | time | 114/128 | 89.06% | 18.1112 | 0.1200 | 0.1955 |
| seed123_iter3999 | pulse_f4d241b247e9 | time | 124/128 | 96.88% | 19.5261 | 0.1170 | 0.1915 |
| seed123_iter3999 | pulse_7bc86c56377e | time | 124/128 | 96.88% | 19.6508 | 0.1168 | 0.1912 |
| seed123_iter3999 | pulse_b870eb388b0b | time | 127/128 | 99.22% | 19.9728 | 0.1162 | 0.1901 |
| seed123_iter3999 | pulse_98b6b76781ad | time | 128/128 | 100.00% | 20.0000 | 0.1172 | 0.1906 |
| seed123_iter3999 | pulse_1ec3af8fc1f6 | time | 127/128 | 99.22% | 19.9737 | 0.1191 | 0.1923 |
| seed123_iter3999 | pulse_71b218b4b546 | time | 65/128 | 50.78% | 15.0509 | 0.1246 | 0.2008 |
| seed123_iter3999 | pulse_e01d7619ff9b | time | 20/128 | 15.62% | 9.3784 | 0.1286 | 0.2079 |
| seed123_iter3999 | pulse_0a594abb58a8 | time | 3/128 | 2.34% | 6.5003 | 0.1310 | 0.2064 |
| seed123_iter3999 | pulse_aea2569b291c | time | 87/128 | 67.97% | 15.1464 | 0.1208 | 0.1975 |
| seed123_iter3999 | pulse_a5f84a341a8b | time | 56/128 | 43.75% | 14.5384 | 0.1253 | 0.2021 |
| seed123_iter3999 | pulse_3246794f3a5d | time | 58/128 | 45.31% | 14.6605 | 0.1241 | 0.2005 |
| seed123_iter3999 | pulse_77527a984020 | time | 128/128 | 100.00% | 20.0000 | 0.1164 | 0.1906 |
| seed123_iter3999 | pulse_b8e7485fe318 | time | 97/128 | 75.78% | 15.7980 | 0.1236 | 0.2005 |
| seed123_iter3999 | pulse_87f3400a0194 | time | 109/128 | 85.16% | 17.7270 | 0.1189 | 0.1941 |
| seed123_iter3999 | pulse_7580aafe0db9 | time | 117/128 | 91.41% | 19.0277 | 0.1173 | 0.1918 |
| seed2026_iter3999 | pulse_20156fb4a964 | time | 128/128 | 100.00% | 20.0000 | 0.1245 | 0.1873 |
| seed2026_iter3999 | pulse_20dc7da1b868 | time | 128/128 | 100.00% | 20.0000 | 0.1254 | 0.1883 |
| seed2026_iter3999 | pulse_a3c73ebdc848 | time | 128/128 | 100.00% | 20.0000 | 0.1259 | 0.1890 |
| seed2026_iter3999 | pulse_8573b4ec74fa | time | 116/128 | 90.62% | 19.1506 | 0.1269 | 0.1916 |
| seed2026_iter3999 | pulse_fcb7f8ee803a | time | 100/128 | 78.12% | 17.2828 | 0.1303 | 0.1963 |
| seed2026_iter3999 | pulse_9aae7dc249d6 | time | 55/128 | 42.97% | 13.4317 | 0.1347 | 0.2043 |
| seed2026_iter3999 | pulse_298e62fc669c | time | 122/128 | 95.31% | 19.2875 | 0.1272 | 0.1912 |
| seed2026_iter3999 | pulse_381fee804b86 | time | 115/128 | 89.84% | 18.8330 | 0.1267 | 0.1921 |
| seed2026_iter3999 | pulse_b3c29424ad4a | time | 118/128 | 92.19% | 19.3000 | 0.1270 | 0.1916 |
| seed2026_iter3999 | pulse_558dedd70894 | time | 128/128 | 100.00% | 20.0000 | 0.1239 | 0.1865 |
| seed2026_iter3999 | pulse_325725b67aed | time | 126/128 | 98.44% | 19.7283 | 0.1242 | 0.1878 |
| seed2026_iter3999 | pulse_f4d241b247e9 | time | 125/128 | 97.66% | 19.6386 | 0.1245 | 0.1879 |
| seed2026_iter3999 | pulse_7bc86c56377e | time | 121/128 | 94.53% | 19.3786 | 0.1246 | 0.1882 |
| seed2026_iter3999 | pulse_b870eb388b0b | time | 128/128 | 100.00% | 20.0000 | 0.1249 | 0.1876 |
| seed2026_iter3999 | pulse_98b6b76781ad | time | 128/128 | 100.00% | 20.0000 | 0.1256 | 0.1884 |
| seed2026_iter3999 | pulse_1ec3af8fc1f6 | time | 127/128 | 99.22% | 19.9122 | 0.1261 | 0.1894 |
| seed2026_iter3999 | pulse_71b218b4b546 | time | 118/128 | 92.19% | 19.1108 | 0.1275 | 0.1924 |
| seed2026_iter3999 | pulse_e01d7619ff9b | time | 99/128 | 77.34% | 17.2700 | 0.1307 | 0.1970 |
| seed2026_iter3999 | pulse_0a594abb58a8 | time | 54/128 | 42.19% | 13.1300 | 0.1364 | 0.2056 |
| seed2026_iter3999 | pulse_aea2569b291c | time | 119/128 | 92.97% | 18.9328 | 0.1289 | 0.1931 |
| seed2026_iter3999 | pulse_a5f84a341a8b | time | 117/128 | 91.41% | 19.1770 | 0.1271 | 0.1924 |
| seed2026_iter3999 | pulse_3246794f3a5d | time | 122/128 | 95.31% | 19.4022 | 0.1276 | 0.1920 |
| seed2026_iter3999 | pulse_77527a984020 | time | 128/128 | 100.00% | 20.0000 | 0.1240 | 0.1867 |
| seed2026_iter3999 | pulse_b8e7485fe318 | time | 125/128 | 97.66% | 19.5944 | 0.1248 | 0.1886 |
| seed2026_iter3999 | pulse_87f3400a0194 | time | 124/128 | 96.88% | 19.5203 | 0.1246 | 0.1883 |
| seed2026_iter3999 | pulse_7580aafe0db9 | time | 118/128 | 92.19% | 19.1092 | 0.1249 | 0.1887 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0011 | 0.0012 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0499 | 0.0499 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0998 | 0.0998 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1470 | 0.1499 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1532 | 0.1876 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1284 | 0.1928 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1525 | 0.2107 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1800 | 0.2325 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.2104 | 0.2578 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0076 | 0.0353 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0031 | 0.0134 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0012 | 0.0013 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0012 | 0.0013 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0011 | 0.0012 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0010 | 0.0011 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0011 | 0.0012 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0021 | 0.0065 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0071 | 0.0276 |
| official_alpha_walking | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0268 | 0.1056 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0016 | 0.0017 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0498 | 0.0498 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0997 | 0.0997 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1493 | 0.1497 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1682 | 0.1900 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0965 | 0.1753 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1202 | 0.1900 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1479 | 0.2091 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1785 | 0.2322 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0255 | 0.1366 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0074 | 0.0385 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0019 | 0.0083 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0010 | 0.0012 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0015 | 0.0016 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0015 | 0.0016 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0014 | 0.0043 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0037 | 0.0239 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0100 | 0.0696 |
| seed42_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0183 | 0.1241 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0015 | 0.0016 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0498 | 0.0498 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0996 | 0.0996 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0737 | 0.1599 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0841 | 0.1693 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0972 | 0.1778 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1151 | 0.1896 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1390 | 0.2065 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1671 | 0.2276 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0222 | 0.1385 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0188 | 0.1382 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0163 | 0.1374 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0101 | 0.0845 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0010 | 0.0011 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0010 | 0.0011 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0088 | 0.0818 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0171 | 0.1412 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0207 | 0.1434 |
| seed123_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0245 | 0.1446 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0015 | 0.0016 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0498 | 0.0498 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0997 | 0.0997 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0931 | 0.1508 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0849 | 0.1645 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1032 | 0.1748 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1234 | 0.1864 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1491 | 0.2034 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.1814 | 0.2279 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0206 | 0.1357 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0198 | 0.1316 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0153 | 0.1009 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0020 | 0.0082 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0009 | 0.0010 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0009 | 0.0010 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0071 | 0.0501 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0178 | 0.1359 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0204 | 0.1380 |
| seed2026_iter3999 | clean_e65df7c70d30 | commands | 128/128 | 100.00% | 20.0000 | 0.0234 | 0.1388 |

## 图表及读图注释

> 读图注释：本报告保留36张原始实验图，并增加九阶段全部任务点图及可查询原始case浏览器。合并探索图与确认图可能覆盖同一些点，不能再次计入回合数。

> 读图注释：行走脉冲始于200/400/600/800控制步，每次5步。重力字段0.8是投影向量分量，不是0.8rad躯干角。

> 读图注释：0.1秒显示网格的首回合曲线反映终止时刻，不等于每回合保存了完整机器人遥测。

> 英文坐标速查：survival=规定时长存活；duration/seconds=首回合有效寿命；vx=前向速度；XY=平面速度；yaw=绕竖直轴旋转；MSE=动作拟合平方误差；pp=百分点。完整解释见[读图指南](../READING_GUIDE.md)。

### 图1 全部任务点 calibration

![全部任务点 calibration](../figures/05_all_cases_calibration.png)

每个点是一项真实任务；横轴仅是文件记录顺序，不是连续变量，故不连线。点保留评估seed差异。条件、模型和分母可在全数据浏览器按编号查询；早停时误差只覆盖终止前。

### 图2 全部任务点 coarse

![全部任务点 coarse](../figures/05_all_cases_coarse.png)

每个点是一项真实任务；横轴仅是文件记录顺序，不是连续变量，故不连线。点保留评估seed差异。条件、模型和分母可在全数据浏览器按编号查询；早停时误差只覆盖终止前。

### 图3 全部任务点 combinations

![全部任务点 combinations](../figures/05_all_cases_combinations.png)

每个点是一项真实任务；横轴仅是文件记录顺序，不是连续变量，故不连线。点保留评估seed差异。条件、模型和分母可在全数据浏览器按编号查询；早停时误差只覆盖终止前。

### 图4 全部任务点 commands

![全部任务点 commands](../figures/05_all_cases_commands.png)

每个点是一项真实任务；横轴仅是文件记录顺序，不是连续变量，故不连线。点保留评估seed差异。条件、模型和分母可在全数据浏览器按编号查询；早停时误差只覆盖终止前。

### 图5 全部任务点 confirmation

![全部任务点 confirmation](../figures/05_all_cases_confirmation.png)

每个点是一项真实任务；横轴仅是文件记录顺序，不是连续变量，故不连线。点保留评估seed差异。条件、模型和分母可在全数据浏览器按编号查询；早停时误差只覆盖终止前。

### 图6 全部任务点 delay_freeze_exploration

![全部任务点 delay_freeze_exploration](../figures/05_all_cases_delay_freeze_exploration.png)

每个点是一项真实任务；横轴仅是文件记录顺序，不是连续变量，故不连线。点保留评估seed差异。条件、模型和分母可在全数据浏览器按编号查询；早停时误差只覆盖终止前。

### 图7 全部任务点 local

![全部任务点 local](../figures/05_all_cases_local.png)

每个点是一项真实任务；横轴仅是文件记录顺序，不是连续变量，故不连线。点保留评估seed差异。条件、模型和分母可在全数据浏览器按编号查询；早停时误差只覆盖终止前。

### 图8 全部任务点 smoke

![全部任务点 smoke](../figures/05_all_cases_smoke.png)

每个点是一项真实任务；横轴仅是文件记录顺序，不是连续变量，故不连线。点保留评估seed差异。条件、模型和分母可在全数据浏览器按编号查询；早停时误差只覆盖终止前。

### 图9 全部任务点 time

![全部任务点 time](../figures/05_all_cases_time.png)

每个点是一项真实任务；横轴仅是文件记录顺序，不是连续变量，故不连线。点保留评估seed差异。条件、模型和分母可在全数据浏览器按编号查询；早停时误差只覆盖终止前。

### 图10 channel combinations

![channel combinations](../original_figures/05_a9d3bb5533_channel_combinations.png)

横轴是通道组合类别，纵轴为存活/寿命等结果。组合响应不等于各单通道损害之和；同alpha的输入范数不同，不能直接当协同作用的因果证明。

### 图11 coarse imu bias all

![coarse imu bias all](../original_figures/05_82c03a29f2_coarse_imu_bias_all.png)

两个探索评估seed的幅度或机制扫描。本图关注IMU偏置；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图12 coarse noise all

![coarse noise all](../original_figures/05_a6d5ec0c26_coarse_noise_all.png)

两个探索评估seed的幅度或机制扫描。本图关注传感段噪声；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图13 coarse pulse all

![coarse pulse all](../original_figures/05_181132626c_coarse_pulse_all.png)

两个探索评估seed的幅度或机制扫描。本图关注联合传感段；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图14 coarse pulse gravity add

![coarse pulse gravity add](../original_figures/05_df0ea8cbc5_coarse_pulse_gravity_add.png)

两个探索评估seed的幅度或机制扫描。本图关注重力投影向量加性偏移；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图15 coarse pulse gyro

![coarse pulse gyro](../original_figures/05_198851a3c8_coarse_pulse_gyro.png)

两个探索评估seed的幅度或机制扫描。本图关注躯干角速度；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图16 coarse pulse joint velocity

![coarse pulse joint velocity](../original_figures/05_1dd7046d5b_coarse_pulse_joint_velocity.png)

两个探索评估seed的幅度或机制扫描。本图关注关节速度；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图17 confirmation delay all

![confirmation delay all](../original_figures/05_0c767c078c_confirmation_delay_all.png)

横轴为额外观测延迟步或其对应毫秒，一控制步20ms；原生延迟仍保留，不能把该轴叫硬件端到端总时延。纵轴存活和寿命须同时看。探索与确认是不同seed队列，不合并为新样本。

### 图18 confirmation freeze all

![confirmation freeze all](../original_figures/05_b2a727ffb2_confirmation_freeze_all.png)

横轴为观测冻结控制步数，一步20ms；名义持续时间与最后一帧实际陈旧年龄差一控制步。冻结越久不保证各模型排名不变；存活不等于任务成功。

### 图19 confirmation imu bias all

![confirmation imu bias all](../original_figures/05_03b5b9c212_confirmation_imu_bias_all.png)

三新评估seed确认。本图关注IMU偏置；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图20 confirmation noise all

![confirmation noise all](../original_figures/05_bebe582ad8_confirmation_noise_all.png)

三新评估seed确认。本图关注传感段噪声；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图21 confirmation pulse all

![confirmation pulse all](../original_figures/05_c024f29bd7_confirmation_pulse_all.png)

三新评估seed确认。本图关注联合传感段；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图22 confirmation pulse gravity add

![confirmation pulse gravity add](../original_figures/05_0f263f35bb_confirmation_pulse_gravity_add.png)

三新评估seed确认。本图关注重力投影向量加性偏移；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图23 confirmation pulse gyro

![confirmation pulse gyro](../original_figures/05_5aee2e74c1_confirmation_pulse_gyro.png)

三新评估seed确认。本图关注躯干角速度；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图24 confirmation pulse joint velocity

![confirmation pulse joint velocity](../original_figures/05_ae9a2a86b8_confirmation_pulse_joint_velocity.png)

三新评估seed确认。本图关注关节速度；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图25 delay freeze exploration delay all

![delay freeze exploration delay all](../original_figures/05_e47f5368e0_delay_freeze_exploration_delay_all.png)

横轴为观测冻结控制步数，一步20ms；名义持续时间与最后一帧实际陈旧年龄差一控制步。冻结越久不保证各模型排名不变；存活不等于任务成功。

### 图26 delay freeze exploration freeze all

![delay freeze exploration freeze all](../original_figures/05_97153ae665_delay_freeze_exploration_freeze_all.png)

横轴为观测冻结控制步数，一步20ms；名义持续时间与最后一帧实际陈旧年龄差一控制步。冻结越久不保证各模型排名不变；存活不等于任务成功。

### 图27 local imu bias all

![local imu bias all](../original_figures/05_5b691018ac_local_imu_bias_all.png)

两个探索评估seed的幅度或机制扫描。本图关注IMU偏置；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图28 local noise all

![local noise all](../original_figures/05_94cf4709af_local_noise_all.png)

两个探索评估seed的幅度或机制扫描。本图关注传感段噪声；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图29 local pulse all

![local pulse all](../original_figures/05_cb54ff4332_local_pulse_all.png)

两个探索评估seed的幅度或机制扫描。本图关注联合传感段；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图30 local pulse gravity add

![local pulse gravity add](../original_figures/05_960ced0d5d_local_pulse_gravity_add.png)

两个探索评估seed的幅度或机制扫描。本图关注重力投影向量加性偏移；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图31 local pulse gyro

![local pulse gyro](../original_figures/05_a34b8fcbad_local_pulse_gyro.png)

两个探索评估seed的幅度或机制扫描。本图关注躯干角速度；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图32 local pulse joint velocity

![local pulse joint velocity](../original_figures/05_a4025f1460_local_pulse_joint_velocity.png)

两个探索评估seed的幅度或机制扫描。本图关注关节速度；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图33 merged exploration delay all

![merged exploration delay all](../original_figures/05_ee8a540307_merged_exploration_delay_all.png)

横轴为额外观测延迟步或其对应毫秒，一控制步20ms；原生延迟仍保留，不能把该轴叫硬件端到端总时延。纵轴存活和寿命须同时看。探索与确认是不同seed队列，不合并为新样本。

### 图34 merged exploration freeze all

![merged exploration freeze all](../original_figures/05_e140f1dd1d_merged_exploration_freeze_all.png)

横轴为观测冻结控制步数，一步20ms；名义持续时间与最后一帧实际陈旧年龄差一控制步。冻结越久不保证各模型排名不变；存活不等于任务成功。

### 图35 merged exploration imu bias all

![merged exploration imu bias all](../original_figures/05_b167255452_merged_exploration_imu_bias_all.png)

两个探索评估seed的幅度或机制扫描。本图关注IMU偏置；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图36 merged exploration noise all

![merged exploration noise all](../original_figures/05_04693b7cb5_merged_exploration_noise_all.png)

两个探索评估seed的幅度或机制扫描。本图关注传感段噪声；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图37 merged exploration pulse all

![merged exploration pulse all](../original_figures/05_1226cad45d_merged_exploration_pulse_all.png)

两个探索评估seed的幅度或机制扫描。本图关注联合传感段；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图38 merged exploration pulse gravity add

![merged exploration pulse gravity add](../original_figures/05_5ddec79bab_merged_exploration_pulse_gravity_add.png)

两个探索评估seed的幅度或机制扫描。本图关注重力投影向量加性偏移；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图39 merged exploration pulse gyro

![merged exploration pulse gyro](../original_figures/05_f0e92b0076_merged_exploration_pulse_gyro.png)

两个探索评估seed的幅度或机制扫描。本图关注躯干角速度；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图40 merged exploration pulse joint velocity

![merged exploration pulse joint velocity](../original_figures/05_1156d86511_merged_exploration_pulse_joint_velocity.png)

两个探索评估seed的幅度或机制扫描。本图关注关节速度；存活百分比越高只表示越少提前终止，不代表跟踪更准。强度轴只按本故障定义解释，不能把不同通道同alpha视为等输入能量。探索与确认分开读，准确分母和seed见图例及数据浏览器。

### 图41 nominal Forward

![nominal Forward](../original_figures/05_cd91edd809_nominal_Forward.png)

固定命令扫描：Forward观察前向速度误差，Turning观察yaw误差及平移漂移。模型站住不等于跟随命令，目标速度变化时应按相应命令比较。

### 图42 nominal Turning

![nominal Turning](../original_figures/05_3f5e1944aa_nominal_Turning.png)

固定命令扫描：Forward观察前向速度误差，Turning观察yaw误差及平移漂移。模型站住不等于跟随命令，目标速度变化时应按相应命令比较。

### 图43 timing cluster

![timing cluster](../original_figures/05_83786840a2_timing_cluster.png)

比较脉冲在时间上的聚集安排。横轴为实际协议中的时间安排参数，不是新增训练轮数；暴露次数和早停的关系应结合原始条件查看。

### 图44 timing duration

![timing duration](../original_figures/05_0492cf5140_timing_duration.png)

横轴是每次脉冲持续控制步数，一步20ms；纵轴描述首回合结果。改变持续时间也改变计划暴露量，早终止会进一步改变实际暴露，不能当等剂量机制分离。

### 图45 timing single onset

![timing single onset](../original_figures/05_be1951243b_timing_single_onset.png)

横轴为单次注入起点所在控制步；越靠后意味着机器人所处状态和剩余观察窗口不同。仅两个探索seed，不外推精确最危险时刻。

### 图46 OLD VS NEW TEMPORAL

![OLD VS NEW TEMPORAL](../original_figures/05_7609eb4b67_OLD_VS_NEW_TEMPORAL.png)

历史补充图，保留用于追溯。本图的队列、幅度、分母或目的不同于本报告主表，不合并计数，不当成新增实验或最终主协议结论。

## 限制与不能支持的结论

本轮重新读取全部2072份CSV并核对记录SHA、唯一任务与主要均值；未重新跑仿真。不能把幅度扫描称为恶意训练投毒或部署攻击可达性证明。不存在未实际采样的25/30/35ms结果。

## 证据入口与复核范围

输入清单与SHA：[input_manifest.json](../data/input_manifest.json)。本轮计数/均值复算：[AUDIT.json](../data/AUDIT.json)。

- D:\MicroDuckResearch\ti\outputs\microduck_reproduction\fine_response\results\results.json　SHA256 c6cefb92297f8d694df1a9de1f745c16f7f0746f2179b591db1d9f2f38edd158

## 这项工作的价值

价值在于形成可复核、多维而非单点的故障响应基准，能用于定位失效范围、识别模型特有弱点以及检验后续解释；负结果和非单调结果同样保留。

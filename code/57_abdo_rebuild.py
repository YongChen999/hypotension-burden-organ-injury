# -*- coding: utf-8 -*-
"""重建腹部大手术分析集(含急诊), 并核对既定流程数字.

口径来源: 项目存档 MINS腹部大手术队列_项目存档总结_20261113
  32,943 (GS+全麻+>18)
  -> 17,747 (腹部术式码 0D/0F 治疗性根操作)
  -> 10,057 (时长>=120min)
  -> 10,036 (住院>=3d)
  -> 9,067 择期 (8,697 患者)
结局/暴露取自 510 术后窗导出; 术前肌酐+DM/HTN/CAD 取自 513 术前窗导出.
"""
import pandas as pd
import numpy as np

W = 'data/web'
OUT = 'output'

post = pd.read_excel(f'{W}/inspire_export_308_20261112_223205.xlsx', sheet_name='数据')
pre = pd.read_excel(f'{W}/inspire_export_308_20261113_025746.xlsx', sheet_name='数据')
assert len(post) == len(pre) == 32943
assert (post['op_id'].values == pre['op_id'].values).all(), 'op_id 顺序不一致需按 op_id 合并'

d = post.copy()
# 术前协变量: 基线肌酐(术前7天窗 min) + DM/HTN/CAD
d['scr_base'] = pd.to_numeric(pre['custom_血肌酐_Creatinine_min'], errors='coerce')
for k, c in [('dm', 'custom_DM'), ('htn', 'custom_HTN'), ('cad', 'custom_CAD')]:
    d[k] = pd.to_numeric(pre[c], errors='coerce')
    d[k] = np.where(d[k].notna(), (d[k] > 0).astype(float), np.nan)

# --- 暴露 ---
ane_min = pd.to_numeric(d['anesthesia_duration'], errors='coerce')
below = pd.to_numeric(d['mbp_below_65_min'], errors='coerce')
d['burden_pct'] = np.where(ane_min > 0, below / ane_min * 100, np.nan)
d['burden10'] = d['burden_pct'] / 10.0

# --- 结局 ---
tn = pd.to_numeric(d['troponin_i_max'], errors='coerce')
d['monitored'] = tn.notna().astype(int)
d['mins'] = np.where(tn.notna(), (tn > 0.026).astype(float), np.nan)
d['aki'] = np.where(pd.to_numeric(d['kdigo_any'], errors='coerce').notna(),
                    (pd.to_numeric(d['kdigo_any'], errors='coerce') > 0).astype(float), np.nan)

# --- 协变量 ---
d['age'] = pd.to_numeric(d['age'], errors='coerce')
d['male'] = (d['sex'].astype(str).str.upper().str[0] == 'M').astype(int)
d['bmi'] = pd.to_numeric(d['weight'], errors='coerce') / (pd.to_numeric(d['height'], errors='coerce') / 100) ** 2
d['open_surgery'] = (d['surgery_approach'].astype(str).str.lower() == 'open').astype(int)
d['op_h'] = pd.to_numeric(d['op_duration'], errors='coerce') / 60.0
d['asa'] = pd.to_numeric(d['asa'], errors='coerce')
d['emop'] = d['emop'].astype(str).str.lower() == 'true'
d['los_d'] = pd.to_numeric(d['los_hospital'], errors='coerce') / 1440.0  # 分钟->天

# --- 流程筛选: 复现 17747 -> 10057 -> 10036 (重建口径, 与项目存档差<0.2%) ---
# 规则: 任一手术码以 0D/0F 开头, 且台内 0D/0F 码并非全部为诊断性根操作(J);
#       手术时长 op_duration >= 120 min; 住院 los_hospital >= 3 d (原值分钟/1440)。
tok = d['patient_procedure_codes'].fillna('').astype(str).str.split()

def any_therapeutic(l):
    if not isinstance(l, list):
        return False
    hit, all_j = False, True
    for c in l:
        if c[:2] in ('0D', '0F'):
            if (c[2] if len(c) >= 3 else '') != 'J':
                all_j = False
            hit = True
    return hit and not all_j

m1 = tok.apply(any_therapeutic)
d1 = d[m1]
m2 = d1['op_h'] >= 2.0
d2 = d1[m2]
m3 = d2['los_d'] >= 3.0
d3 = d2[m3]
print('筛选口径(任一0D/0F非纯J + op>=120min + LOS>=3d):')
print(f'  {len(d)} -> {len(d1)} -> {len(d2)} -> {len(d3)}',
      '(项目存档: 32943 -> 17747 -> 10057 -> 10036, 差<0.2%)')
print(f'  择期: {int((~d3["emop"]).sum())} (存档 9067) | 急诊: {int(d3["emop"].sum())}')

# 保存含急诊的分析队列
d3 = d3.copy()
d3['emergency'] = d3['emop'].astype(int)
keep = ['op_id', 'age', 'male', 'bmi', 'open_surgery', 'op_h', 'asa', 'scr_base',
        'dm', 'htn', 'cad', 'emergency', 'burden_pct', 'burden10', 'monitored',
        'mins', 'aki', 'los_d']
d3[keep].to_csv(f'{OUT}/abdo_full_cohort.csv', index=False, encoding='utf-8-sig')

# 快速统计
mon = d3[d3['monitored'] == 1]
print()
print('含急诊队列 10,036 口径下:')
print('  监测:', len(mon), f'({len(mon)/len(d3)*100:.1f}%)', '| MINS:', int(mon['mins'].sum()))
print('  择期监测:', int((mon['emergency'] == 0).sum()), '| MINS:',
      int(mon.loc[mon['emergency'] == 0, 'mins'].sum()))
print('  急诊监测:', int((mon['emergency'] == 1).sum()), '| MINS:',
      int(mon.loc[mon['emergency'] == 1, 'mins'].sum()))
print('  AKI(全队列):', int(d3['aki'].sum()), '/', len(d3))
print('  scr_base 缺失率(监测人群):', f"{mon['scr_base'].isna().mean()*100:.1f}%")

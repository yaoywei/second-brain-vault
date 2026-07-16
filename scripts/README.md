# 🛠️ scripts/ 目录说明

> 这一目录放第二大脑的"程序骨架" — 脚本都是当前活跃的，跟备份脚本并列在 vault 根目录。

## 📜 现有脚本

### cimi_sync.py / cimi_sync.sh — 次幂数据同步

详见 [[40_资源/工具收藏/次幂数据同步方案]]。

```bash
./cimi_sync.sh dry-run           # 看会调哪些接口
./cimi_sync.sh check-balance     # 免费，验证鉴权
./cimi_sync.sh sync-all          # 跑完整快照
```

### backup-vault.sh — 周备份（在 vault 根目录）

```bash
./backup-vault.sh                 # 立即跑一次
crontab -e                        # 设每周日 9 点自动跑
```

---

## 🔒 安全约定

- **所有 API 凭据放在 vault 外部**：`/Users/yaoyouwei/.config/second-brain/*.env`
- **不进 vault、不进 git**
- 改凭据 → 编辑对应 `.env` 文件
- 跑前确认 → `dry-run` 一下

---

## 🗂️ 文件组织

```
scripts/
├── README.md           ← 本文件
├── cimi_sync.py        ← Python 主力脚本
├── cimi_sync.sh        ← bash 包装
└── .gitignore          ← 防止 .pyc 等被提交
```

---

*最后更新：2026-07-16*

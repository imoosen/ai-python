# VSCode 里用 Git（IntelliJ 视角迁移指南）

> 场景：mini / A1708 双机，仓库 `ai-python`，规矩是 commit/push 只由孟工本人做。
> 本文只讲日常用的那 20%，先能用，再补全。

## 0. IntelliJ → VSCode 对应关系

| IntelliJ | VSCode | 入口 |
|---|---|---|
| Commit 工具窗口（⌘K） | 源代码管理面板 | 左侧栏第三个图标，或 `Ctrl+Shift+G` |
| Local Changes / Changelists | Changes（未暂存）/ Staged Changes（已暂存） | 面板里两个分区 |
| Show Diff | 点文件名 | 左右分屏对比 |
| Update Project（⌘T） | Pull | 面板 `...` 菜单 → Pull |
| Push（⌘⇧K） | Push | 同上，或 commit 按钮旁的同步图标 |
| Rollback | Discard Changes（丢弃更改 ↩） | 文件行内按钮 |

## 1. 认识文件标记（先看懂状态）

| 标记 | 含义 | git 等价 |
|---|---|---|
| **U**（绿色） | 新文件，git 还没跟踪 | untracked |
| **M**（橙色） | 已跟踪文件被修改 | modified |
| **A** | 已暂存的新文件 | added |
| **D** | 删除 | deleted |

鼠标悬停文件名还能看到最后改动者——相当于 `git blame`。

## 2. 日常流程（90% 的操作就这一条链）

```
改文件 → stage（点 + 号）→ 写 commit message → Commit → Push
```

具体：

1. **左侧栏点源代码管理图标**（或 `Ctrl+Shift+G`），Changed Files 列出所有改动。
2. **暂存**：把鼠标放到文件上点 `+`（stage），文件从 Changes 移到 Staged Changes。
   - 只想提交部分文件时有用——和 `git add 文件名` 一一对应。
   - 嫌麻烦可点 Changes 标题栏的 `+` 全部暂存，或直接不 stage 用"Commit"旁下拉选 "Commit All"。
3. **写 message**：顶部输入框。格式建议 `类型: 内容`，如 `docs: 新增踩坑实录与标准库速查`。
4. **Commit**：点蓝色 ✓ 按钮（或 `Ctrl+Enter`）。
5. **Push**：commit 后面板会出现"同步更改"按钮（带数字角标），点它 = pull + push；稳妥起见用 `...` 菜单里的 **Pull** 再 **Push** 分开做。

## 3. 现在就实操一遍（仓库里正有一批改动等着）

当前 `git status` 有两项：

- `M src/config.py`（昨天的改动，先 `git diff` 确认内容）
- `?? doc/`（今天新增的两份 md）

操作：

1. `Ctrl+Shift+G` 打开源代码管理；
2. 点开 `config.py` 看一眼 diff（左旧右新，改动行高亮）——**先确认这是不是你要的内容**；
3. 把 `doc/` 两个文件和 `config.py` 一起点 `+` 暂存；
4. message 写 `docs: 新增踩坑实录与标准库速查`（config.py 若保留改动，改成 `docs+config: ...` 或分两次提交）；
5. 点 ✓ Commit → `...` → Push。

命令行等价（心里要有数，界面的每个按钮都对应一条命令）：

```bash
git add doc/ src/config.py
git commit -m "docs: 新增踩坑实录与标准库速查"
git push
```

## 4. 双机规矩对应到界面

- **写码前先 Pull**：打开项目第一件事，`...` → Pull。防止 mini 和 A1708 分叉。
- **commit 只由你做**：AI/WorkBuddy 生成的文件出现在面板里，由你审查 diff 后自己提交——commit 记录是你的学习日志，不能代写。

## 5. 常用补充

- **丢弃改动**（相当于 IntelliJ Rollback / `git checkout -- 文件`）：文件行内 `↩` 图标。⚠️ 不可恢复，点之前想清楚。
- **查看历史**：装 **GitLens** 扩展（必装），每行代码尾部显示"谁、何时、哪次提交改的"；文件时间线在资源管理器底部。
- **分支**：左下角状态栏显示当前分支名，点它可切换/新建。学习阶段先待在 main。
- **冲突**：Pull 后如果两个分支改了同一处，文件里会出现 `<<<<<<<` 标记，VSCode 会给"接受当前/传入/两者"按钮。双机都 pull 了就基本碰不到。
- **.gitignore**：`.venv/`、`__pycache__/`、`.env` 必须在里面（`.env` 里有 API key，**绝不能进 git**）。仓库已经配好，别动。

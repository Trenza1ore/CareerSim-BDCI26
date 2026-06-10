## 当前任务
开始一局新的职业模拟器游戏。按照 IDENTITY.md 中的规则和已安装技能进行游戏。

### 推荐的开始步骤
1. 调用 `show_employee_handbook` 一次，了解游戏规则。
2. 调用 `new_game`，打印 `SESSION_ID=<session_id>`。
3. 然后按核心规则循环：`observe` → 决策 → `take_action`，直到游戏结束。
4. 游戏结束时，打印完整的 `ending_score` 内容，然后输出 `DONE`。

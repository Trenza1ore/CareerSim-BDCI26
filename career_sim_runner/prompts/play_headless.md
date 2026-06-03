## Current Task
直接使用已安装的参赛者技能，完整玩一局职业模拟器游戏 (career-emulator MCP)。
请严格按照相关 SKILL 的指示进行游戏。

### Provided SKILLs
{participant_skills}

### General Instructions (Provided by system)
1. 调用 `show_employee_handbook` 一次。
2. 调用 `new_game`，并打印 `SESSION_ID=<session_id>`。
3. 每一回合调用 `observe`，使用已安装的参赛者技能作为决策策略，选择恰好一个有效动作。
4. 对选定的动作调用 `take_action(session_id, choice=N, notes=理由)`。
5. 在游戏结束之前不断执行 `observe`, `take_action` 直到游戏结束，不要停下来询问用户，你只能自己做出所有决定。
6. 遇到难题时可以查看相关先前的日志总结简略成功/失败经验。
7. 游戏结束时，打印完整的 `ending_score` 内容，然后输出 `DONE`。

# Feature Request Workflow

**Slash command:** `/feature-request`

**Description:** Implements a new feature following a complete development workflow: clarify requirements, request permissions, implement, iterate, test, verify, and deliver a working solution.

**Usage:** `/feature-request <feature description>`

---

## Workflow Steps

When this skill is invoked, follow these steps systematically:

### 1. **Clarify Requirements** 🤔
- Read and understand the feature request thoroughly
- Ask clarifying questions if:
  - The scope is ambiguous
  - There are multiple valid approaches
  - User preferences/constraints are unclear
  - Edge cases need consideration
- Use `AskUserQuestion` tool for quick clarifications
- Don't ask unnecessary questions - use judgment

### 2. **Request Permissions** 🔑
- Identify what permissions you'll need:
  - Bash commands (be specific: "run tests", "install dependencies", etc.)
  - File modifications
  - External API calls
- Request all needed permissions upfront using appropriate tools
- Explain why each permission is needed

### 3. **Plan & Todo** 📋
- **Always use TodoWrite tool** to create a task list
- Break down the feature into concrete steps
- Mark tasks as you progress:
  - `pending` → `in_progress` → `completed`
- Keep the todo list updated throughout implementation

### 4. **Implement** 💻
- Write clean, maintainable code following project conventions
- Check `CLAUDE.md` for project-specific guidelines
- Follow architecture principles (separation of concerns, type hints, etc.)
- Make incremental changes - don't try to do everything at once
- Update the todo list after completing each step

### 5. **Iterate** 🔄
- After implementing core functionality:
  - Review for bugs or issues
  - Improve code quality
  - Add error handling
  - Consider edge cases
- Keep iterating until the feature is polished
- **The user has granted you permission to iterate autonomously** - keep going until it's truly complete

### 6. **Test** 🧪
- Write tests for new functionality
- Run existing tests to ensure nothing broke
- Use `Bash` tool to run: `python -m pytest tests/ -v`
- Fix any test failures immediately
- Add regression tests if fixing bugs

### 7. **Verify** ✅
- **Critical**: Always verify the code works before declaring completion
- Use import checks: `python -c "from module import function"`
- Run the actual application to test the feature
- Test edge cases manually
- Ensure everything compiles/runs without errors

### 8. **Deliver** 🎉
- Provide a clear summary of what was implemented
- List all files created/modified
- Show test results (X tests passing)
- Give instructions on how to use the new feature
- Suggest next steps or follow-ups if relevant

---

## Best Practices

### Do's ✓
- Use TodoWrite tool to track progress
- Update todos as you complete tasks
- Test incrementally as you build
- Verify imports after creating new files
- Ask questions early if requirements are unclear
- Iterate until truly complete
- Show test results

### Don'ts ✗
- Don't skip verification steps
- Don't assume code works - always test it
- Don't leave todos incomplete
- Don't ask "should I proceed?" - the workflow grants you permission to iterate
- Don't declare completion without running tests
- Don't forget to update todo list

---

## Example Workflow

**User:** `/feature-request Add a CSV export feature for card data`

**You respond:**

1. **Clarify:** "Should the export include sensitive card numbers, or just metadata?"
2. **Plan:** Create todo list with 5 tasks
3. **Implement:**
   - Mark task 1 as in_progress
   - Add export function
   - Mark task 1 as completed
   - Continue through all tasks
4. **Test:** Write and run tests
5. **Verify:** Test CSV export manually
6. **Deliver:** "✓ CSV export feature complete. 3 new files, 15 tests passing. Use File → Export CSV in the UI."

---

## Notes

- This workflow assumes you have iterative permission - keep going until the feature is complete and working
- The user values working solutions over quick but incomplete implementations
- Quality matters - take time to do it right
- When in doubt, ask questions early rather than building the wrong thing

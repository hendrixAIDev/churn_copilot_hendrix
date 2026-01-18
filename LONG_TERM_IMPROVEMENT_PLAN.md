# Long-Term Improvement: Auto-Enrichment from Card Library

## Vision

**Before:** User extracts "Amex Platinum" from URL → Gets partial data → Manually adds 8 credits

**After:** User extracts "Amex Platinum" from URL → Auto-matched to library → All 8 credits included automatically → User just verifies and saves

---

## 8-Iteration Roadmap

### Iteration 1: Core Enrichment Logic
**Goal:** Build the matching and enrichment engine

**Tasks:**
- Enhance `match_to_library_template()` to return confidence scores
- Create `enrich_card_data()` function that merges library template with extracted data
- Smart merge strategy: Prefer extracted data, but add missing credits from template
- Handle edge cases: Partial matches, wrong matches, no matches

**Verification:**
- Unit tests for matching algorithm
- Test with example card names
- Verify enrichment doesn't overwrite good extracted data

### Iteration 2: Integration into Extraction Pipeline
**Goal:** Auto-enrich URL and text extractions

**Tasks:**
- Modify `extract_from_url()` to auto-enrich results
- Modify `extract_from_text()` to auto-enrich results
- Add `template_id` and `template_match_confidence` to Card model
- Log enrichment for debugging

**Verification:**
- Extract "Amex Platinum" from URL → Verify credits auto-added
- Extract partial card data → Verify enrichment happens
- Run app and test extraction flow

### Iteration 3: Integration into Spreadsheet Import
**Goal:** Auto-enrich imported cards

**Tasks:**
- Modify `SpreadsheetImporter` to enrich each parsed card
- Handle bulk enrichment efficiently
- Preserve user's existing data from spreadsheet
- Show enrichment stats (X cards enriched, Y credits added)

**Verification:**
- Import spreadsheet with card names → Verify credits added
- Import spreadsheet with partial credits → Verify gaps filled
- Test with various card name formats

### Iteration 4: UI Feedback - Show Enrichment Results
**Goal:** Users see what was auto-enriched

**Tasks:**
- Add "Auto-enriched from library" badge in card preview
- Show matched template name in extraction review UI
- Highlight newly added credits in green/with badge
- Add "X credits added from library" message

**Verification:**
- Extract card → See enrichment feedback in UI
- Import cards → See enrichment summary
- Visual check in browser

### Iteration 5: Improve Matching Algorithm
**Goal:** Better matching for edge cases

**Tasks:**
- Handle card name variations ("Amex" vs "American Express")
- Handle abbreviations ("CSP" → "Chase Sapphire Preferred")
- Handle card name changes over time
- Add fuzzy matching for typos
- Tune confidence thresholds

**Verification:**
- Test with various card name formats
- Test with typos and abbreviations
- Verify no false positives

### Iteration 6: User Control - Enrichment Preferences
**Goal:** Give users control over auto-enrichment

**Tasks:**
- Add setting: "Auto-enrich cards from library" (default: ON)
- Add setting: "Minimum confidence for auto-enrichment" (default: 0.7)
- Add UI option: "Re-enrich this card" button for existing cards
- Store preferences in `PreferencesStorage`

**Verification:**
- Toggle auto-enrichment off → Verify no enrichment happens
- Adjust confidence threshold → Verify behavior changes
- Test "Re-enrich" button on existing cards

### Iteration 7: Batch Re-Enrichment for Existing Cards
**Goal:** Enrich cards already in the system

**Tasks:**
- Add "Enrich All Cards" action in settings/tools
- Scan all existing cards, match to library, add missing credits
- Show preview: "Will add X credits to Y cards"
- Allow user to review before applying
- Create backup before batch operation

**Verification:**
- Run on existing test cards
- Verify backup created
- Verify credits added correctly
- Test rollback if user doesn't like results

### Iteration 8: Polish and Documentation
**Goal:** Production-ready feature

**Tasks:**
- Add enrichment statistics to dashboard (e.g., "15/20 cards enriched from library")
- Document enrichment logic in code comments
- Add troubleshooting guide for users
- Performance optimization for large card libraries
- Edge case handling and error messages
- Final comprehensive testing

**Verification:**
- Full end-to-end test of all workflows
- Performance test with 50+ cards
- Review all user-facing messages
- Check for any breaking changes

---

## Success Metrics

**Must Have (for completion):**
- ✅ Auto-enrichment works for URL extraction
- ✅ Auto-enrichment works for text extraction
- ✅ Auto-enrichment works for spreadsheet import
- ✅ Users can see what was enriched
- ✅ No data loss or overwrites
- ✅ App still works as before (backwards compatible)

**Nice to Have (stretch goals):**
- ✅ Batch re-enrichment for existing cards
- ✅ User preferences for enrichment behavior
- ✅ Fuzzy matching for variations
- ✅ Enrichment statistics in UI

---

## Risk Mitigation

**Risk 1: Overwriting user data**
- Solution: Always prefer extracted/user data over library data
- Verification: Test with cards that have custom benefits

**Risk 2: False positive matches**
- Solution: Confidence threshold, only enrich high-confidence matches
- Verification: Test with similar card names

**Risk 3: Breaking existing functionality**
- Solution: Commit after each iteration, test thoroughly
- Verification: Run full app test after each iteration

**Risk 4: Performance with large libraries**
- Solution: Cache matching results, optimize lookup
- Verification: Performance test with 100+ cards

---

## Rollback Plan

Each iteration is a separate commit. If anything breaks:

```bash
# Rollback specific iteration
git log --oneline  # Find commit hash
git revert <hash>

# Or rollback all enrichment work
git reset --hard HEAD~8
```

---

## Time Budget (9 hours)

- Iteration 1: 1.5 hours (core logic)
- Iteration 2: 1 hour (extraction integration)
- Iteration 3: 1 hour (import integration)
- Iteration 4: 1 hour (UI feedback)
- Iteration 5: 1 hour (better matching)
- Iteration 6: 1 hour (preferences)
- Iteration 7: 1 hour (batch re-enrichment)
- Iteration 8: 1.5 hours (polish and testing)
- **Total: 9 hours**

---

**Let's build something amazing! 🚀**

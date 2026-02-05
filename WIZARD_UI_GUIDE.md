# Onboarding Wizard UI Guide

## Visual Design Overview

### Overall Layout
```
┌─────────────────────────────────────────────────────────────┐
│                    FULL SCREEN OVERLAY                       │
│              Dark backdrop with blur effect                  │
│                                                              │
│     ┌───────────────────────────────────────────┐           │
│     │        [Skip ✕]  ← Top-right corner       │           │
│     │                                            │           │
│     │     ▬▬▬ ▬▬▬ ─── ← Progress bar (3 steps)  │           │
│     │                                            │           │
│     │              ✈️                            │           │
│     │         (Floating icon)                    │           │
│     │                                            │           │
│     │         Step Content Here                  │           │
│     │     Title + Description + Details          │           │
│     │                                            │           │
│     │                                            │           │
│     │        [Primary Action Button]             │           │
│     │                                            │           │
│     └───────────────────────────────────────────┘           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Welcome

### Visual Elements:
- **Icon:** ✈️ (airplane emoji, floating animation)
- **Title:** "Welcome to **ChurnPilot**" (ChurnPilot in gradient purple)
- **Description:** "Your personal credit card churning companion. Track signup bonuses, maximize benefits, and never miss a deadline again."
- **Button:** "Continue →" (primary blue gradient button)
- **Skip:** Top-right "Skip ✕" button

### Color Palette:
- Background: White to light gray gradient (dark mode: dark gray to darker gray)
- Title: Black/white with purple gradient on "ChurnPilot"
- Description: Medium gray
- Button: Blue gradient (#6366f1 to #a855f7)

---

## Step 2: Add Your First Card

### Visual Elements:
- **Icon:** 💳 (credit card emoji, floating animation)
- **Title:** "Add Your First Card"
- **Description:** "Choose the method that works best for you"
- **Feature Cards:** 3 clickable cards stacked vertically

#### Feature Card 1: Card Library
```
┌──────────────────────────────────────────────┐
│ 📚 Card Library                              │
│                                              │
│ Select from 18+ pre-built templates with    │
│ all details already filled in                │
│                                              │
│ [FASTEST] ← Purple gradient badge            │
└──────────────────────────────────────────────┘
```

#### Feature Card 2: AI Extraction
```
┌──────────────────────────────────────────────┐
│ 🤖 AI Extraction                             │
│                                              │
│ Paste any card offer URL and let AI         │
│ extract all the details automatically        │
│                                              │
│ [SMARTEST] ← Purple gradient badge           │
└──────────────────────────────────────────────┘
```

#### Feature Card 3: Manual Entry
```
┌──────────────────────────────────────────────┐
│ ✍️ Manual Entry                              │
│                                              │
│ Full control — enter all card details       │
│ yourself for maximum customization           │
│                                              │
└──────────────────────────────────────────────┘
```

### Interactions:
- Cards have hover effect (slight shift right + border color change)
- **Button:** "Add Card Now →" (takes user directly to Add Card tab)
- **Skip:** Still available in top-right

---

## Step 3: What's Next

### Visual Elements:
- **Icon:** 🎯 (target emoji, floating animation)
- **Title:** "What's Next?"
- **Description:** "Here's what you can do with ChurnPilot"
- **Next Steps:** 3 horizontal cards with icons + text

#### Next Step 1: Track Benefits
```
┌──────────────────────────────────────────────┐
│ 💰  Track Benefits & Credits                 │
│     Mark monthly credits as used so you      │
│     never leave money on the table           │
└──────────────────────────────────────────────┘
```

#### Next Step 2: Monitor 5/24
```
┌──────────────────────────────────────────────┐
│ 🎯  Monitor 5/24 Status                      │
│     Know exactly when you can apply for      │
│     more Chase cards                         │
└──────────────────────────────────────────────┘
```

#### Next Step 3: Portfolio Analytics
```
┌──────────────────────────────────────────────┐
│ 📊  View Portfolio Analytics                 │
│     See your total value, spend progress,    │
│     and upcoming deadlines                   │
└──────────────────────────────────────────────┘
```

### Interactions:
- **Button:** "Get Started! 🚀" (completes wizard, shows main dashboard)
- **Skip:** Still available in top-right

---

## Progress Bar States

### Step 1:
```
▰▰▰▰▰▰ ▱▱▱▱▱▱ ▱▱▱▱▱▱
(Active) (Inactive) (Inactive)
```

### Step 2:
```
▰▰▰▰▰▰ ▰▰▰▰▰▰ ▱▱▱▱▱▱
(Complete) (Active) (Inactive)
```

### Step 3:
```
▰▰▰▰▰▰ ▰▰▰▰▰▰ ▰▰▰▰▰▰
(Complete) (Complete) (Active)
```

---

## Animations

1. **Entrance:** Wizard slides up from bottom with fade-in (0.4s)
2. **Icon Float:** Icons gently float up/down continuously (3s loop)
3. **Progress Bar:** Active step has animated gradient, completed steps are green
4. **Card Hover:** Feature cards shift 4px to the right with color change
5. **Button Hover:** Primary button has subtle shadow and slight lift

---

## Responsive Design

### Desktop (>768px):
- Wizard container: 600px width, centered
- Feature cards: Full width stacked
- Large icons (4rem)
- Generous padding (48px)

### Mobile (<768px):
- Wizard container: 90vw width
- Padding reduced to 32px/24px
- Title font size reduced
- Icons slightly smaller
- Cards stack vertically (already designed for this)

---

## Dark Mode

All elements automatically adapt:
- Background: Dark gradients instead of light
- Text: Light colors instead of dark
- Borders: Subtle light borders instead of dark
- Feature cards: Dark backgrounds with subtle borders
- Buttons: Same gradient (already dark-compatible)

CSS uses `@media (prefers-color-scheme: dark)` for automatic switching.

---

## Accessibility

1. **Keyboard Navigation:**
   - All buttons are Streamlit native (keyboard accessible)
   - Tab order: Skip → Primary button

2. **Screen Readers:**
   - Semantic HTML structure
   - Button labels are descriptive
   - Progress bar shows current step visually

3. **Color Contrast:**
   - All text meets WCAG AA standards
   - Dark mode contrast verified
   - Gradient badges have sufficient contrast

---

## Copy Guidelines

### Tone:
- **Friendly but professional:** Not overly casual, not corporate
- **Concise:** Get to the point quickly
- **Action-oriented:** Tell users what they can DO
- **Benefit-focused:** Emphasize value, not features

### Examples:
- ✅ "Track signup bonuses, maximize benefits"
- ❌ "Our platform enables you to manage your credit card portfolio"
  
- ✅ "Never leave money on the table"
- ❌ "Optimize your benefit utilization"

### Emojis:
- Used strategically for visual interest
- Not overdone (1 emoji per section)
- Relevant to content (💳 for cards, 🎯 for goals, etc.)

---

## Technical Implementation

### CSS Variables Used:
- `--cp-primary` - Primary purple color
- `--cp-text` - Main text color
- `--cp-surface` - Card backgrounds
- `--cp-border` - Border colors
- `--cp-radius-lg` - Border radius (16px)
- `--cp-shadow-lg` - Box shadows

### Streamlit Components:
- `st.markdown()` for HTML/CSS injection
- `st.button()` for interactive buttons (not custom HTML)
- `st.columns()` for layout (not used in wizard, but available)
- `st.rerun()` for navigation between steps

### State Management:
```python
st.session_state.wizard_step = 1  # Current step (1-3)
st.session_state.wizard_completed = False  # Completion flag
```

Database persistence via `user_preferences.onboarding_completed`.

---

## User Flow Diagram

```
New User Logs In (0 cards)
        ↓
   Wizard Shows
        ↓
  ┌─────┴─────┐
  │           │
Step 1     Skip ────────┐
  │                     │
  ↓ Continue            │
Step 2                  │
  │                     │
  ├─ Add Card Now ──┐   │
  │                 │   │
  ↓ Continue        │   │
Step 3              │   │
  │                 │   │
  ↓ Get Started     │   │
  │                 │   │
  └─────────────────┴───┴→ Main Dashboard
                           (Wizard never shows again)
```

---

## Edge Cases Handled

1. **User refreshes mid-wizard:** Step state preserved in session
2. **User navigates away:** Wizard state lost but shows again on next login (until completed)
3. **User adds card outside wizard:** Wizard disappears (no longer new user)
4. **User completes wizard:** DB flag set, never shows again even after logout/login
5. **User skips wizard:** Same as completion - marked in DB, never shows again
6. **Database connection fails:** Wizard still works via session state (graceful degradation)

---

## Success Metrics (Recommended)

Track these in analytics:
1. **Completion Rate:** % of users who finish all 3 steps
2. **Skip Rate:** % of users who hit Skip button
3. **Step 2 Add Card Rate:** % who click "Add Card Now" from Step 2
4. **Time to First Card:** How long after seeing wizard do users add first card
5. **Wizard-to-Active User:** Do wizard completers add more cards/become more engaged?

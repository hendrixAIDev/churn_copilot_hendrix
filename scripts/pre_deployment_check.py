"""Pre-deployment checks for ChurnPilot.

Catches common UI/UX issues before deployment.
"""

import re
from pathlib import Path


def check_styling_issues(file_path):
    """Check for common CSS styling issues."""
    issues = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    # Check 1: background without color
    for i, line in enumerate(lines, 1):
        if 'background:' in line or "background: " in line:
            # Look for color specification in same line or nearby
            context = '\n'.join(lines[max(0, i-2):min(len(lines), i+2)])
            if "color:" not in context and "color: " not in context:
                issues.append(f"Line {i}: background without text color - may cause invisible text")

    # Check 2: Hardcoded colors that might not work in dark mode
    dark_mode_risky = ['#ffffff', '#fff', 'white']
    for i, line in enumerate(lines, 1):
        for color in dark_mode_risky:
            if f"color: {color}" in line or f"color:{color}" in line:
                issues.append(f"Line {i}: Hardcoded white text - won't work in dark mode")

    # Check 3: Missing alt text on images (accessibility)
    img_pattern = r'<img[^>]*src=[^>]*>'
    for i, line in enumerate(lines, 1):
        if re.search(img_pattern, line):
            if 'alt=' not in line:
                issues.append(f"Line {i}: Image missing alt text (accessibility)")

    return issues


def check_usability_issues(file_path):
    """Check for common usability issues."""
    issues = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    # Check 1: Button text is clear and action-oriented
    button_pattern = r'st\.button\(["\']([^"\']+)["\']\)'
    for i, line in enumerate(lines, 1):
        match = re.search(button_pattern, line)
        if match:
            button_text = match.group(1)
            if len(button_text) < 3:
                issues.append(f"Line {i}: Button text too short: '{button_text}'")
            if button_text.lower() in ['ok', 'submit', 'click']:
                issues.append(f"Line {i}: Vague button text: '{button_text}' - be more specific")

    # Check 2: Help text for complex inputs
    complex_inputs = ['st.text_area', 'st.file_uploader', 'st.date_input']
    for i, line in enumerate(lines, 1):
        for input_type in complex_inputs:
            if input_type in line:
                if 'help=' not in line:
                    issues.append(f"Line {i}: {input_type} without help text")

    return issues


def main():
    """Run all pre-deployment checks."""
    ui_file = Path("src/ui/app.py")

    print("=" * 60)
    print("PRE-DEPLOYMENT CHECKS FOR CHURNPILOT")
    print("=" * 60)

    all_issues = []

    # Styling checks
    print("\n[1/2] Checking styling issues...")
    styling_issues = check_styling_issues(ui_file)
    all_issues.extend(styling_issues)

    if styling_issues:
        print(f"  Found {len(styling_issues)} styling issues:")
        for issue in styling_issues:
            print(f"    - {issue}")
    else:
        print("  ✓ No styling issues found")

    # Usability checks
    print("\n[2/2] Checking usability issues...")
    usability_issues = check_usability_issues(ui_file)
    all_issues.extend(usability_issues)

    if usability_issues:
        print(f"  Found {len(usability_issues)} usability issues:")
        for issue in usability_issues:
            print(f"    - {issue}")
    else:
        print("  ✓ No usability issues found")

    # Summary
    print("\n" + "=" * 60)
    if all_issues:
        print(f"FOUND {len(all_issues)} ISSUES - Please review before deploying")
        print("=" * 60)
        return 1
    else:
        print("ALL CHECKS PASSED - Ready to deploy!")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    exit(main())

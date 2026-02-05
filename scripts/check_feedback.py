#!/usr/bin/env python3
"""Check recent feedback from ChurnPilot users.

This script queries the churnpilot_feedback table for recent entries
and formats them into a summary for review.

Usage:
    python check_feedback.py              # Last 24 hours
    python check_feedback.py --hours 48   # Last 48 hours
    python check_feedback.py --all        # All feedback
"""

import os
import sys
import argparse
import psycopg2
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


def get_feedback(hours: int = 24, all_feedback: bool = False):
    """Query feedback from the database.
    
    Args:
        hours: Number of hours to look back (default 24)
        all_feedback: If True, get all feedback regardless of time
        
    Returns:
        List of feedback entries as dictionaries
    """
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ DATABASE_URL not found in .env", file=sys.stderr)
        return []
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        if all_feedback:
            query = """
                SELECT id, user_email, feedback_type, message, page, user_agent, created_at
                FROM churnpilot_feedback
                ORDER BY created_at DESC
            """
            cursor.execute(query)
        else:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            query = """
                SELECT id, user_email, feedback_type, message, page, user_agent, created_at
                FROM churnpilot_feedback
                WHERE created_at >= %s
                ORDER BY created_at DESC
            """
            cursor.execute(query, (cutoff_time,))
        
        # Fetch all results
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        feedback = []
        for row in rows:
            feedback.append({
                'id': row[0],
                'user_email': row[1],
                'feedback_type': row[2],
                'message': row[3],
                'page': row[4],
                'user_agent': row[5],
                'created_at': row[6]
            })
        
        cursor.close()
        conn.close()
        
        return feedback
        
    except Exception as e:
        print(f"❌ Error fetching feedback: {e}", file=sys.stderr)
        return []


def format_summary(feedback: list, hours: int = None):
    """Format feedback into a readable summary.
    
    Args:
        feedback: List of feedback dictionaries
        hours: Number of hours queried (for header)
        
    Returns:
        Formatted summary string
    """
    if not feedback:
        timeframe = f"last {hours} hours" if hours else "all time"
        return f"📭 No feedback received in the {timeframe}.\n"
    
    # Count by type
    bug_count = sum(1 for f in feedback if f['feedback_type'] == 'bug')
    feature_count = sum(1 for f in feedback if f['feedback_type'] == 'feature')
    general_count = sum(1 for f in feedback if f['feedback_type'] == 'general')
    
    # Build summary
    lines = []
    lines.append("=" * 70)
    lines.append("📬 CHURNPILOT FEEDBACK SUMMARY")
    lines.append("=" * 70)
    lines.append("")
    
    timeframe = f"Last {hours} hours" if hours else "All time"
    lines.append(f"Timeframe: {timeframe}")
    lines.append(f"Total feedback: {len(feedback)}")
    lines.append(f"  🐛 Bug reports: {bug_count}")
    lines.append(f"  💡 Feature requests: {feature_count}")
    lines.append(f"  💬 General feedback: {general_count}")
    lines.append("")
    lines.append("=" * 70)
    lines.append("")
    
    # Group by type for detailed view
    for feedback_type, emoji, title in [
        ('bug', '🐛', 'BUG REPORTS'),
        ('feature', '💡', 'FEATURE REQUESTS'),
        ('general', '💬', 'GENERAL FEEDBACK')
    ]:
        items = [f for f in feedback if f['feedback_type'] == feedback_type]
        if items:
            lines.append(f"{emoji} {title}")
            lines.append("-" * 70)
            lines.append("")
            
            for item in items:
                lines.append(f"  ID: {item['id']}")
                lines.append(f"  From: {item['user_email'] or 'Anonymous'}")
                lines.append(f"  Page: {item['page'] or 'Unknown'}")
                lines.append(f"  Date: {item['created_at']}")
                lines.append(f"  Message:")
                # Indent message lines
                for msg_line in item['message'].split('\n'):
                    lines.append(f"    {msg_line}")
                lines.append("")
                lines.append("-" * 70)
                lines.append("")
    
    return '\n'.join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check recent ChurnPilot feedback",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Number of hours to look back (default: 24)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Get all feedback regardless of time'
    )
    
    args = parser.parse_args()
    
    # Get feedback
    feedback = get_feedback(
        hours=args.hours if not args.all else None,
        all_feedback=args.all
    )
    
    # Format and print summary
    summary = format_summary(
        feedback,
        hours=None if args.all else args.hours
    )
    print(summary)
    
    # Return exit code based on whether there's feedback
    return 0 if feedback else 1


if __name__ == "__main__":
    sys.exit(main())

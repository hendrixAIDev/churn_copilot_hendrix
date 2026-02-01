# ChurnPilot ✈️

**Stop leaving thousands of dollars on the table with your credit cards.**

ChurnPilot is a free, AI-powered credit card management dashboard for enthusiasts tracking 10-50+ cards. Track signup bonuses, maximize monthly benefits, monitor Chase 5/24 status, and never miss a deadline.

🔗 **[Try it now → churnpilot.streamlit.app](https://churnpilot.streamlit.app)**

---

## Why ChurnPilot?

The average credit card enthusiast leaves **$500-2,000/year** on the table:
- Forgetting monthly credits ($300/yr DoorDash on Amex Gold alone)
- Missing signup bonus spend deadlines ($1,000+ lost)
- Not knowing their Chase 5/24 status
- Losing track of annual fee renewal dates

**ChurnPilot fixes all of this in one dashboard.**

## Features

### Card Library (18+ templates)
Add cards from Chase, Amex, Capital One, Citi, Bilt, US Bank, and Wells Fargo with all benefits pre-loaded. No manual data entry.

### AI Card Extraction
Paste any card offer URL and let AI extract the annual fee, benefits, signup bonus, and spend requirements automatically.

### Benefit Tracking
Track monthly credits, annual credits, and special perks. See which ones you've used and which you're leaving on the table. Get your **usage rate** and **value extraction** percentage.

### Signup Bonus Tracker
Track spend requirements, deadlines, and progress. Never miss a bonus again.

### Chase 5/24 Tracker
Know exactly when you can apply for more Chase cards based on your application history.

### Portfolio Analytics
See your total annual fees, benefits value, net value, and ROI at a glance. Know if your cards are earning their keep.

### Export to CSV
Take your data anywhere.

## Tech Stack

- **Frontend:** Streamlit
- **Backend:** Python
- **Database:** Supabase (PostgreSQL)
- **AI:** Claude API (for card extraction)
- **Auth:** Custom bcrypt-based authentication
- **Session Persistence:** `st.query_params` (survives page refresh)

## Local Development

```bash
# Clone
git clone https://github.com/hendrixAIDev/churn_copilot_hendrix.git
cd churn_copilot_hendrix

# Setup
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your Supabase and Claude API credentials

# Run
streamlit run src/ui/app.py
```

Visit `http://localhost:8501`

## Running Tests

```bash
source venv/bin/activate
pytest tests/ -v
```

## Project Structure

```
churn_copilot_hendrix/
├── src/
│   ├── core/           # Business logic
│   │   ├── auth.py     # Authentication
│   │   ├── database.py # DB connection
│   │   ├── db_storage.py # Data persistence
│   │   ├── demo.py     # Demo mode
│   │   ├── library.py  # 18+ card templates
│   │   ├── models.py   # Data models
│   │   └── pipeline.py # AI extraction
│   └── ui/
│       ├── app.py      # Main application
│       └── components/  # UI components
├── tests/              # Test suite
├── scripts/
│   └── init_db.py      # Database initialization
└── requirements.txt
```

## Roadmap

- [x] Card library with 18+ templates
- [x] AI extraction from URLs
- [x] Benefit tracking
- [x] Chase 5/24 tracker
- [x] Session persistence
- [x] Demo mode
- [ ] Pro tier ($9.99/month)
- [ ] Plaid integration (auto-import transactions)
- [ ] Email reminders for deadlines
- [ ] Mobile-optimized layout
- [ ] Card comparison tool
- [ ] Annual fee analyzer

## About

Built by [Hendrix](https://hendrixaidev.github.io) -- an autonomous AI co-founder given $1,000 and a deadline (April 2026) to build sustainable revenue.

Follow the journey: [@HendrixVol328](https://x.com/HendrixVol328) | [The Hendrix Chronicles](https://hendrixchronicles.substack.com)

## License

MIT

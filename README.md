# Karunodaya Digital Platform

A mobile-first Django web application for book subscription and marketplace services, designed to provide curated book boxes for children based on their age, grade, and reading level.

## Overview

Karunodaya is a comprehensive book rental and purchase platform that helps parents discover age-appropriate books for their children through personalized curation. The platform manages physical inventory, subscriptions, returns, and purchases with integrated payment processing.

## Key Features

### For Parents
- **3-Step Onboarding** - Quick setup with HTMX-powered seamless flow
- **Personalized Curation** - Age and grade-based book recommendations
- **Subscription Management** - Monthly book boxes with automated selection
- **Marketplace** - Browse and purchase books with live search
- **Order Tracking** - Monitor subscriptions and purchases with status updates
- **Profile Management** - Manage up to 5 children per account

### For Administrators
- **Custom Dashboard** - Real-time stats on subscriptions, revenue, and inventory
- **Inventory Management** - Track physical copies with unique barcodes
- **Order Fulfillment** - Streamlined dispatch and delivery workflow
- **Returns Processing** - Automated late fee calculation (₹50/day after grace period)
- **Low Stock Alerts** - Automatic warnings for books with <5 copies
- **Audit Logs** - Complete inventory tracking history

## Technology Stack

- **Backend:** Django 5.0.9
- **Admin UI:** django-unfold 0.38.0
- **Frontend:** HTMX 2.0.4 + Tailwind CSS
- **Database:** SQLite (dev) / Turso with libsql (production)
- **Payments:** Razorpay integration
- **Image Processing:** Pillow 10.4.0

## Project Structure

```
karunodaya/
├── apps/
│   ├── profiles/       # Parent and child profile management
│   ├── catalog/        # Books and publishers
│   ├── inventory/      # Physical copy tracking with barcodes
│   ├── orders/         # Subscriptions and purchase orders
│   ├── payments/       # Transaction handling
│   └── portal/         # User-facing web portal
├── services/
│   └── curation.py     # Book matching and subscription logic
├── templates/
│   ├── admin/          # Custom admin dashboard
│   ├── portal/         # User portal templates
│   └── registration/   # Auth templates
├── static/             # CSS, JS, images
├── media/              # User uploads
├── karunodaya_project/ # Django settings
└── manage.py
```

## Installation

### Prerequisites
- Python 3.10+
- uv (recommended) or pip

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd karunodaya
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   uv pip install -r requirements.txt
   # OR
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (SECRET_KEY, RAZORPAY keys, etc.)
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Load seed data (optional)**
   ```bash
   python manage.py seed_data
   ```

8. **Run development server**
   ```bash
  Tue, Jan 27
   ```

9. **Access the application**
   - User Portal: http://localhost:8000/
   - Admin Dashboard: http://localhost:8000/admin/

## Business Rules

### Subscription Plans
- **Little Readers** (Ages 3-6): 3 books/month @ ₹499
- **Young Explorers** (Ages 7-10): 4 books/month @ ₹699
- **Teen Scholars** (Ages 11-14): 5 books/month @ ₹899

### Late Fee Policy
- 30-day subscription cycle
- 7-day grace period after expected return
- ₹50/day late fee (maximum ₹500)

### Inventory Rules
- Physical copies tracked with unique barcodes
- Low stock alert: <5 copies
- Critical stock alert: <2 copies
- Maximum 5 children per parent account

### Book Curation
Books are automatically matched based on:
- Child's reading level (Beginner/Intermediate/Advanced)
- Child's current grade
- Book's difficulty rating and grade range
- Book availability in inventory
- Excludes books currently issued to the child

## Management Commands

### Check Overdue Subscriptions
Run daily via cron to update overdue status and calculate late fees:
```bash
python manage.py check_overdue_subscriptions
```

### Seed Test Data
Create sample publishers, books, physical copies, and subscription plans:
```bash
python manage.py seed_data
```

## Development Status

### Completed Phases ✅
- **Phase 1:** Foundation - Django setup, apps, and base templates
- **Phase 2:** Core Models - 10 models with full admin integration
- **Phase 3:** Curation Service - Book matching and subscription logic
- **Phase 4:** Admin Dashboard - Custom stats, actions, and workflows
- **Phase 5:** Mobile Portal - User-facing web application with HTMX

### Pending Phases
- **Phase 6:** Payment Integration - Razorpay webhooks
- **Phase 7:** Complete Workflows - End-to-end flows
- **Phase 8:** Testing & Polish - QA and mobile testing
- **Phase 9:** Deployment - Production configuration and Turso migration

See [PROGRESS.md](PROGRESS.md) for detailed task breakdown.

## API Endpoints

Currently, the application is web-only. The portal URLs include:

- `/` - Dashboard
- `/register/` - User registration
- `/onboarding/` - Multi-step onboarding
- `/marketplace/` - Book marketplace with live search
- `/curated-box/<child_id>/` - Personalized book recommendations
- `/orders/` - Order history
- `/profile/` - User and children management

## Security Features

- All portal views protected with `@login_required`
- Data isolation ensures parents only access their own data
- CSRF protection on all forms
- Environment-based SECRET_KEY configuration
- Razorpay signature verification (when implemented)

## Configuration

Key environment variables (see `.env.example`):

```env
SECRET_KEY=your-secret-key
DEBUG=True
RAZORPAY_KEY_ID=your-key-id
RAZORPAY_KEY_SECRET=your-key-secret
DATABASE_URL=file:karunodaya.db  # For Turso in production
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

This project is proprietary software. See [LICENSE](LICENSE) for details.

## Support

For questions or issues:
- Check [CODEBASE_STRUCTURE.md](CODEBASE_STRUCTURE.md) for architecture details
- Review [BUSINESS_RULES.md](BUSINESS_RULES.md) for business logic
- See [TASK_BREAKDOWN.md](TASK_BREAKDOWN.md) for implementation tasks

## Acknowledgments

- Built with Django and django-unfold for a modern admin experience
- HTMX for seamless interactivity without heavy JavaScript
- Tailwind CSS for responsive mobile-first design

---

**Current Version:** 1.0.0-alpha
**Last Updated:** January 2026
**Development Status:** Active Development

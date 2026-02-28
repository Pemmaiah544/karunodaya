# Super Admin & Regular Admin RBAC System

## Overview
Single unified admin portal (`/admin/`) with **dual access levels**:
- **Super Admin**: Full unrestricted access, can create roles & manage admin users
- **Regular Admin**: Role-based access, see only permitted sections, perform only assigned actions
- Both log in at the same URL, UI/access controlled by permissions on request

---

## Setup Instructions

### 1. Create Django Superuser
```bash
cd /home/pemmu/projects/Karunodaya/karunodaya
source .venv/bin/activate
python manage.py createsuperuser
```
Example:
- Email: `admin@karunodaya.com`
- Password: `your_secure_password`

### 2. Promote to Super Admin
```bash
python manage.py create_super_admin --email admin@karunodaya.com
```

### 3. Start Server
```bash
python manage.py runserver
```

---

## Single Login Portal

**Both Super Admin and Regular Admin log in at the same place:**

1. Visit: `http://localhost:8000/admin/`
2. Enter credentials (email, password from previous steps)
3. System checks AdminProfile:
   - **If is_super_admin=True**: Unrestricted access, sees all 8 sections + **Super Admin** section
   - **If role assigned**: Sees only sections in role.permissions, actions limited to role
   - **If is_active=False**: Blocked immediately by middleware
4. **No separate Super Admin login URL** — UI automatically adapts based on permissions

---

## Creating a New Admin User

### Step 1: Super Admin creates role
1. Login to `/admin/` with Super Admin credentials
2. Navigate to **Super Admin → Admin Roles → Add Admin Role**
3. Name: e.g., "Catalog Manager"
4. Check permissions:
   - Expand each section tab (Catalog, Inventory, Orders, etc.)
   - Check desired actions (view, add, change, delete)
5. Save

### Step 2: Super Admin creates admin user
1. Navigate to **Super Admin → Admin Users → Add Admin User**
2. Fill form:
   - **First Name**: John
   - **Last Name**: Doe
   - **Email**: john@example.com (must be unique)
   - **Role**: Select "Catalog Manager" (or your created role)
   - **Is Active**: ✓ Checked
   - **Notes**: Optional
3. **Save**

### Step 3: Auto-Generated Password
- Super Admin sees the generated password in the admin list or confirmation page
- Admin user receives the password via:
  - Email notification (if email configured), OR
  - Password displayed to Super Admin for manual sharing

### Step 4: User Logs In
1. User visits `/admin/`
2. Enters email and the provided password
3. Sees only sections permitted by their role
4. Can only perform assigned actions

---

## Permission Structure

### Sections (8 total)
- `catalog` — Books, Publishers
- `inventory` — Physical Copies, Inventory Logs
- `orders` — Orders, Subscription Cycles, Plans
- `payments` — Transactions
- `profiles` — Children, Parent Profiles
- `portal` — Complaints
- `users` — Django Users (Authentication)
- `config` — Sites (Configuration)

### Actions (4 total)
- `view` — Can see list and detail pages
- `add` — Can create new records
- `change` — Can edit existing records
- `delete` — Can delete records

### Example Roles
| Role | Permissions |
|------|-------------|
| Catalog Viewer | catalog: [view] |
| Catalog Manager | catalog: [view, add, change, delete] |
| Order Manager | orders: [view, change], payments: [view] |
| Full Admin | All sections: [view, add, change, delete] |

---

## Technical Details

### URL Routing
- `/admin/` → Regular Admin Site (for role-based admins)
- `/super-admin/` → Super Admin Site (for super admin only)

### Authentication
- **Super Admin**: Must have `AdminProfile.is_super_admin = True`
- **Regular Admin**: Must have `AdminProfile.role` assigned and `is_active = True`
- **Inactive Admin**: Blocked from `/admin/` immediately by middleware

### Permission Enforcement
- `SectionPermissionMixin` applied to ALL ModelAdmins (first in MRO)
- Checks `has_view_permission()`, `has_add_permission()`, `has_change_permission()`, `has_delete_permission()`
- Super Admins always return `True` (no restrictions)
- Regular admins checked against `role.can_do(section, action)`

### Password Generation
- New admin passwords auto-generated using `get_random_string(16)`
- Password set on User object at creation time
- No reset email sent (to avoid email setup requirements)
- Super Admin displays password to share manually

---

## Database Models

### AdminRole
- `name` (unique)
- `description`
- `permissions` (JSON)
  - Structure: `{"section": ["action1", "action2"], ...}`
  - Example: `{"catalog": ["view", "add"], "orders": ["view"]}`
- `created_by` (FK to User)
- `created_at`, `updated_at`

### AdminProfile
- `user` (OneToOneField to User)
- `is_super_admin` (bool)
- `role` (FK to AdminRole, nullable for Super Admins)
- `is_active` (bool)
- `created_by` (FK to User, nullable)
- `notes` (text)
- `created_at`

---

## Common Operations

### Deactivate an Admin
1. Super Admin visits `/admin/` and logs in
2. Navigate to **Super Admin → Admin Users**
3. Click the admin to edit
4. Uncheck **Is Active**
5. Save
→ User immediately loses all admin access

### Change Admin's Role
1. Super Admin visits `/admin/` and logs in
2. Navigate to **Super Admin → Admin Users**
3. Click the admin to edit
4. Select new role from **Role** dropdown
5. Save
→ User's permissions instantly updated

### Delete a Role (if unused)
1. Super Admin visits `/admin/` and logs in
2. Navigate to **Admin Roles**
3. Click role to edit or delete
4. Delete
→ Users assigned to this role lose access (not recommended without reassignment)

---

## Security Notes

- All permission checks happen server-side (no client-side tricks)
- Middleware blocks unauthenticated/inactive users immediately
- Super Admin designation stored in database (not just Django is_superuser)
- Passwords auto-generated (no hardcoded defaults)
- AdminProfile.is_active flag double-checks on every request

---

## Troubleshooting

### "I see all sections but no Super Admin section"
→ Not marked as Super Admin. Run:
```bash
python manage.py create_super_admin --email your@email.com
```

### "User sees sections they shouldn't"
→ Check AdminProfile.role and its permissions
→ Check AdminProfile.is_active = True
→ Restart server to clear any cache

### "User can't log in"
→ Check AdminProfile.is_active = True
→ Check User.is_active = True
→ Check User.is_staff = True
→ Verify password (try `/admin/password_reset/`)

### "Email not sent when creating admin"
→ This is normal in dev — password shown in admin interface
→ For production, configure EMAIL_* settings in settings.py

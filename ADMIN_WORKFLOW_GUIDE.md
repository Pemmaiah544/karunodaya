# Admin User Creation Workflow Guide

This guide explains how to use the Super Admin interface to create and manage regular admin users with role-based access control.

## Quick Start

### 1. Initial Setup (One-time)

```bash
# Create Django superuser (if not already done)
python manage.py createsuperuser

# Promote to Super Admin (use the username of the superuser created above)
python manage.py create_super_admin --username superadmin
# OR if the user has unique email:
python manage.py create_super_admin --email admin@karunodaya.com
```

### 2. Super Admin Login

1. Navigate to: `http://localhost:8000/admin/`
2. Login with your Super Admin email and password
3. You'll see a "Super Admin" section in the sidebar with:
   - **Admin Roles** - Manage role definitions
   - **Admin Users** - Create and manage admin users

## Creating Admin Roles

### Step 1: Navigate to Admin Roles
1. Click **Super Admin** → **Admin Roles** in the sidebar
2. Click **Add Admin Role** button

### Step 2: Configure Role
The form shows:
- **Role Name**: e.g., "Catalog Manager"
- **Description**: Optional description
- **Permissions Tabs**: 8 tabs (Catalog, Inventory, Orders, Payments, Profiles, Portal, Users, Config)

### Step 3: Select Permissions
For each section, check the actions you want to allow:
- ✓ **View** - Can see the list and details
- ✓ **Add** - Can create new records
- ✓ **Change** - Can edit existing records
- ✓ **Delete** - Can delete records

**Example: Catalog Manager Role**
- Catalog section: View ✓, Add ✓, Change ✓, Delete ✓
- All other sections: Leave unchecked

### Step 4: Save
Click **Save** - the role is now available for admin user assignment.

---

## Creating Admin Users

### Step 1: Navigate to Admin Users
1. Click **Super Admin** → **Admin Users** in the sidebar
2. Click **Add Admin User** button

### Step 2: Fill in User Details
The form displays:
- **First Name**: Admin's first name (required)
- **Last Name**: Admin's last name (required)
- **Email**: Unique email address (required) - also used as login username
- **Role**: Select from existing roles (required)
- **Is Active**: Check to activate immediately
- **Notes**: Optional notes about the admin

### Step 3: Submit Form
Click **Save** - the system will:
1. ✓ Create a Django User with `is_staff=True`
2. ✓ Generate a random 16-character password
3. ✓ Create an AdminProfile with the selected role
4. ✓ Display success message with credentials

### Step 4: Access Auto-Generated Password
After creation, you'll see a **success message** at the top of the admin page showing:

```
✓ Admin user created successfully!

Email: john@example.com
Password: a7K3xP9mQ2vBdF5n

Share this password with the admin user.
```

**Important**:
- The password is displayed only once
- Copy and securely share it with the new admin user
- The new admin can change their password after first login

---

## Admin User Permissions

Once created, the admin user can:

1. **Login**: Use their email and password at `/admin/`
2. **See Permitted Sections**: Only sections in their role appear in sidebar
3. **Perform Role Actions**: Can only view/add/change/delete within their role's permissions
4. **View Dashboard**: Can see admin dashboard with stats for permitted data

### Example: Catalog Manager Access
- ✓ Can view all books and publishers
- ✓ Can add new books and publishers
- ✓ Can edit existing books and publishers
- ✓ Can delete books and publishers
- ✗ Cannot see Orders, Payments, or other sections

---

## Managing Existing Admin Users

### Change Admin's Role
1. Click **Super Admin** → **Admin Users**
2. Click the admin's name to edit
3. Select new **Role** from dropdown
4. Click **Save**
→ User's permissions update immediately

### Deactivate Admin
1. Click **Super Admin** → **Admin Users**
2. Click the admin's name to edit
3. **Uncheck** "Is Active"
4. Click **Save**
→ User loses all admin access immediately

### View Admin Details
1. Click **Super Admin** → **Admin Users**
2. View the list showing:
   - Email
   - Full Name
   - Assigned Role
   - Active Status
   - Creation Date

---

## Permission Reference

### 8 Admin Sections

| Section | Manages |
|---------|---------|
| **Catalog** | Books, Publishers |
| **Inventory** | Physical Copies, Inventory Logs |
| **Orders** | Orders, Subscription Plans, Cycles |
| **Payments** | Transactions |
| **Profiles** | Children, Parent Profiles |
| **Portal** | Complaints, Passages |
| **Users** | Django Users (Authentication) |
| **Config** | Sites Configuration |

### 4 Actions Per Section

| Action | Can... |
|--------|--------|
| **View** | See list and detail pages |
| **Add** | Create new records |
| **Change** | Edit existing records |
| **Delete** | Delete records |

---

## Common Workflows

### Create a Catalog Manager
```
1. Create Role: "Catalog Manager"
   - Catalog: View ✓, Add ✓, Change ✓, Delete ✓
2. Create Admin User: "John Smith" (john@example.com)
   - Assign to "Catalog Manager" role
3. Share credentials with John:
   - Email: john@example.com
   - Password: [auto-generated]
```

### Create an Order Viewer (Read-Only)
```
1. Create Role: "Order Viewer"
   - Orders: View ✓
   - Payments: View ✓
2. Create Admin User: "Sarah" (sarah@example.com)
   - Assign to "Order Viewer" role
```

### Create a Full Admin (except Super Admin features)
```
1. Create Role: "Full Admin"
   - Catalog: View ✓, Add ✓, Change ✓, Delete ✓
   - Inventory: View ✓, Add ✓, Change ✓, Delete ✓
   - Orders: View ✓, Add ✓, Change ✓, Delete ✓
   - Payments: View ✓, Add ✓, Change ✓, Delete ✓
   - Profiles: View ✓, Add ✓, Change ✓, Delete ✓
   - Portal: View ✓, Add ✓, Change ✓, Delete ✓
   - Users: View ✓, Add ✓, Change ✓, Delete ✓
   - Config: View ✓, Add ✓, Change ✓, Delete ✓
2. Create Admin User and assign to "Full Admin" role
```

---

## Technical Details

### How It Works

1. **Authentication**
   - Super Admin and Regular Admins login at the same URL: `/admin/`
   - System checks `AdminProfile.is_super_admin` flag
   - Different UIs shown based on user type

2. **Permission Enforcement**
   - `SectionPermissionMixin` applied to all ModelAdmin classes
   - Checks `AdminProfile.role.can_do(section, action)`
   - Super Admin always has unrestricted access

3. **Sidebar Navigation**
   - UNFOLD sidebar uses permission callbacks
   - Sections only appear if user has access
   - Super Admin section only visible to super admins

4. **Auto-Generated Passwords**
   - Generated using Django's `get_random_string(16)`
   - Set directly on User object during admin creation
   - No email reset required in development

### Database Models

**AdminRole**
```python
- name (unique)
- description
- permissions (JSON): {"section": ["action1", "action2"]}
- created_by (FK to User)
- created_at, updated_at
```

**AdminProfile**
```python
- user (OneToOneField to User)
- is_super_admin (bool)
- role (FK to AdminRole, nullable)
- is_active (bool)
- created_by (FK to User)
- notes (text)
- created_at
```

---

## Troubleshooting

### "I don't see the Super Admin section"
→ You're not logged in as Super Admin
→ Run: `python manage.py create_super_admin --username YOUR_USERNAME`

### "The 'Add Admin User' button doesn't appear"
→ You're not logged in as Super Admin
→ Only Super Admin can create and manage admins

### "New admin can't login"
→ Verify they use the **exact email** as username
→ Verify their `is_active` is checked in AdminProfile
→ Verify `User.is_active` and `User.is_staff` are True

### "Admin sees sections they shouldn't"
→ Check AdminProfile.role and its permissions
→ Check AdminProfile.is_active = True
→ Restart Django server to clear any cache

### "Password wasn't displayed after creation"
→ Check the browser console for error messages
→ Password is shown in success message at top of page
→ Look for green banner with "Admin user created successfully!"

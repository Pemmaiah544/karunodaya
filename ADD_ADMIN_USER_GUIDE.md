# Add Admin User - Direct Permission Selection Guide

## Overview

When a Super Admin clicks **"+ Add Admin User"** in the Admin Users list, they now see a comprehensive form with **all 8 sidebar sections and their 4 permission actions**. This allows the Super Admin to create an admin user and assign custom permissions in one unified workflow.

---

## The Add Admin User Form

### Location
Click: **Super Admin** → **Admin Users** → **+ Add Admin User** button

### Form Sections

The form is organized with **tabbed fieldsets** for easy navigation:

#### 1. **Admin User Information** (Main Tab)
- **First Name** (required) - Admin's first name
- **Last Name** (required) - Admin's last name
- **Email** (required, unique) - Used as login username
- **Is Active** (checkbox) - Check to activate immediately
- **Notes** (optional) - Internal notes about the admin

#### 2. **Catalog Permissions** (Tab)
- ☐ View - See books and publishers
- ☐ Add - Create new books and publishers
- ☐ Change - Edit books and publishers
- ☐ Delete - Delete books and publishers

#### 3. **Inventory Permissions** (Tab)
- ☐ View - See physical copies and logs
- ☐ Add - Create new inventory records
- ☐ Change - Edit inventory records
- ☐ Delete - Delete inventory records

#### 4. **Orders Permissions** (Tab)
- ☐ View - See orders and plans
- ☐ Add - Create new orders
- ☐ Change - Edit orders
- ☐ Delete - Delete orders

#### 5. **Payments Permissions** (Tab)
- ☐ View - See transactions
- ☐ Add - Create transaction records
- ☐ Change - Edit transactions
- ☐ Delete - Delete transactions

#### 6. **Profiles Permissions** (Tab)
- ☐ View - See children and parent profiles
- ☐ Add - Add new profiles
- ☐ Change - Edit profiles
- ☐ Delete - Delete profiles

#### 7. **Portal Permissions** (Tab)
- ☐ View - See complaints and passages
- ☐ Add - Create complaints/passages
- ☐ Change - Edit complaints/passages
- ☐ Delete - Delete complaints/passages

#### 8. **Users Permissions** (Tab)
- ☐ View - See user accounts
- ☐ Add - Create user accounts
- ☐ Change - Edit user accounts
- ☐ Delete - Delete user accounts

#### 9. **Config Permissions** (Tab)
- ☐ View - See configuration
- ☐ Add - Create config entries
- ☐ Change - Edit configuration
- ☐ Delete - Delete configuration

---

## Step-by-Step Workflow

### Step 1: Click Add Button
1. Login as Super Admin
2. Navigate to: **Super Admin** → **Admin Users**
3. Click the **+ Add Admin User** button (top-right or top-left)

### Step 2: Fill Basic Information
1. Enter **First Name**: e.g., "Sarah"
2. Enter **Last Name**: e.g., "Johnson"
3. Enter **Email**: e.g., "sarah@example.com" (must be unique)
4. Check **Is Active** to make the admin immediately active
5. Add optional **Notes**: e.g., "Order management specialist"

### Step 3: Select Permission Tabs & Check Actions
Navigate through the 8 tabs and select the actions you want to allow:

**Example 1: Order Manager**
- Orders tab: Check View ✓, Add ✓, Change ✓, Delete ✓
- Payments tab: Check View ✓ (leave Add/Change/Delete unchecked)
- All other tabs: Leave all unchecked

**Example 2: Catalog Viewer (Read-Only)**
- Catalog tab: Check View ✓ (leave Add/Change/Delete unchecked)
- All other tabs: Leave all unchecked

**Example 3: Full Administrator**
- Check View ✓, Add ✓, Change ✓, Delete ✓ in ALL 8 tabs

### Step 4: Submit Form
1. Scroll to bottom and click **Save** button
2. System processes the form:
   - Creates Django User with is_staff=True
   - Auto-generates 16-character password
   - Creates custom Role with selected permissions
   - Creates AdminProfile linking user to role

### Step 5: View Auto-Generated Password
After successful creation, you'll see a **green success message** at the top:

```
✓ Admin user created successfully!

Email: sarah@example.com
Password: k8tWy421XmERMeTX

Share this password with the admin user.
```

**Important**: Copy the password immediately - it's only shown once.

---

## How It Works Behind the Scenes

### Permission Selection → Role Creation
When you select permissions directly in the form:

1. **System analyzes your selections**
   - Identifies which sections and actions you checked

2. **Creates a custom role**
   - Role name: `Admin (user@example.com)`
   - Permissions stored as JSON: `{"orders": ["view", "add", "change", "delete"], "payments": ["view"]}`

3. **Assigns role to admin user**
   - AdminProfile.role points to the created role
   - Admin can only perform role-permitted actions

4. **Generates password**
   - Random 16-character string
   - Set directly on User object
   - No email configuration needed

---

## What Admin User Can Do After Login

Once the admin user logs in with their email and password:

1. **See sidebar sections**
   - Only sections they have access to appear
   - Catalog appears only if they have catalog access

2. **Perform permitted actions**
   - View buttons enabled for "view" permission
   - Add buttons visible for "add" permission
   - Edit/Change enabled for "change" permission
   - Delete buttons visible for "delete" permission

3. **Cannot see denied sections**
   - Sections without any permissions don't appear in sidebar
   - Accessing directly returns "Permission Denied"

---

## Common Use Cases

### Case 1: Create an Order Manager
```
First Name:  Steve
Last Name:   Williams
Email:       steve@company.com
Is Active:   ✓ Checked

Orders tab:    View ✓, Add ✓, Change ✓, Delete ✓
Payments tab:  View ✓
All others:    [Leave unchecked]
```
→ Steve can manage orders and view transactions, nothing else.

### Case 2: Create a Catalog Reviewer (View-Only)
```
First Name:  Alice
Last Name:   Brown
Email:       alice@company.com
Is Active:   ✓ Checked

Catalog tab:  View ✓
All others:   [Leave unchecked]
```
→ Alice can see books and publishers but cannot edit or delete.

### Case 3: Create a Super-Powered Admin
```
First Name:  David
Last Name:   Lee
Email:       david@company.com
Is Active:   ✓ Checked

ALL TABS: View ✓, Add ✓, Change ✓, Delete ✓
```
→ David can do everything except create other admins (only Super Admin can).

---

## Key Differences from Role-Based Approach

### Old Way (Pre-Create Roles):
1. Create role "Catalog Manager"
2. Create admin user "John"
3. Assign "Catalog Manager" role to John

### New Way (Direct Permissions):
1. Click "Add Admin User"
2. Fill name, email, and check permissions directly
3. Click Save

**Result**: Same outcome, but in one step instead of three.

---

## Important Notes

✓ **Unique Email Required** - Each admin must have a unique email address
✓ **Used as Username** - The email is also the login username
✓ **Custom Role Created** - A unique role is auto-created for each admin
✓ **Password Display** - Only shown once after creation, copy it immediately
✓ **No Email Needed** - Password is NOT sent via email (no SMTP config required)
✓ **Immediate Activation** - Admin can login right after creation
✓ **Modifiable Later** - Can change permissions by editing the admin's role

---

## Modifying Permissions Later

### Option 1: Edit the Admin User
1. Click **Super Admin** → **Admin Users**
2. Click the admin's name
3. Modify their role (not directly in the form)
4. Save

### Option 2: Edit the Role
1. Click **Super Admin** → **Admin Roles**
2. Find the admin's custom role (e.g., "Admin (sarah@example.com)")
3. Click to edit
4. Check/uncheck permissions
5. Save → Permissions update immediately

---

## Technical Details

### Form Fields
- **Total**: 37 fields
- **Basic Info**: 5 (first_name, last_name, email, is_active, notes)
- **Permissions**: 32 (8 sections × 4 actions)

### Permission Storage
- Stored as JSON in AdminRole.permissions
- Example: `{"orders": ["view", "add", "change"], "payments": ["view"]}`
- Accessed via `role.can_do(section, action)` method

### Password Generation
- Method: Django's `get_random_string(16)`
- Characters: Uppercase, lowercase, numbers, special chars
- Uniqueness: Random generation ensures uniqueness
- Storage: Set directly on User object

---

## Troubleshooting

### "Email already exists" error
→ That email is already used by another user
→ Use a different email address for this admin

### "Can't see all the permission checkboxes"
→ Make sure you're viewing the full form
→ Scroll down or click on the permission tabs
→ All 8 section tabs should appear below user info

### "Admin can see sections they shouldn't"
→ Verify you checked the correct permissions
→ Edit the admin's custom role to remove access
→ Clear browser cache and relogin

### "Password display disappeared"
→ Password only shows in the success message after creation
→ If you missed it, use Django's "Set password" feature for the User
→ Or delete and recreate the admin (admin will get new password)

---

## Summary

The **Add Admin User** form now provides a **direct, intuitive interface** for Super Admins to:

✅ Create new admin users
✅ Select which sections they can access
✅ Choose which actions they can perform (view/add/change/delete)
✅ Set them active immediately
✅ See auto-generated password

**All in one single form!**

This replaces the old workflow of pre-creating roles separately, making the process faster and more user-friendly.

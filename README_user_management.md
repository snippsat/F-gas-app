# User Management via Command Line

This document explains how to manage users for the F-Gas App via the command line interface in Render.

## Accessing the Render Shell

1. Log in to your Render account
2. Navigate to your F-Gas App web service
3. Click on the "Shell" tab
4. You now have access to a terminal where you can run commands

## Available Commands

### Listing Users

To list all users in the system:

```bash
python delete_user.py list
```

### Creating Admin Users

To create a new administrator user:

```bash
python create_admin.py <username> <email> <password>
```

For example:

```bash
python create_admin.py admin admin@example.com securepassword
```

### Creating Regular Users

To create a new regular (non-admin) user:

```bash
python create_user.py <username> <email> <password>
```

For example:

```bash
python create_user.py user1 user1@example.com userpassword
```

### Deleting Users

To delete a user from the system:

```bash
python delete_user.py delete <username>
```

For example:

```bash
python delete_user.py delete user1
```

## Important Notes

- Usernames and emails must be unique
- Passwords are stored securely and cannot be recovered if forgotten
- Admin users have access to features that regular users do not
- The commands must be run from the root directory of the application

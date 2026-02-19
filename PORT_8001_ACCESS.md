# 🔐 SSH Credentials Access - PORT 8001 FIXED!

## ✅ Port Configuration Updated!

The ALLOWED_HOSTS has been updated to support port 8001. You can now access SSH credentials on the correct port.

---

## 🚀 How to Access SSH Credentials on Port 8001

### **Step 1: Start Server on Port 8001**
```bash
python manage.py runserver 0.0.0.0:8001
```

### **Step 2: Login to System**
```
http://127.0.0.1:8001/login/
```

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

### **Step 3: Access SSH Credentials**
After successful login, you'll be redirected to the dashboard. Then:

```
http://127.0.0.1:8001/ssh-credentials/
```

---

## 🔧 Complete Access URLs (Port 8001)

### **Authentication:**
```
🔐 Login:    http://127.0.0.1:8001/login/
🚪 Logout:   http://127.0.0.1:8001/logout/
```

### **SSH Credentials Management:**
```
📋 List:           http://127.0.0.1:8001/ssh-credentials/
➕ Add:            http://127.0.0.1:8001/ssh-credentials/create/
✏️ Edit:           http://127.0.0.1:8001/ssh-credentials/<id>/edit/
🗑️ Delete:         http://127.0.0.1:8001/ssh-credentials/<id>/delete/
🔌 Test:           http://127.0.0.1:8001/ssh-credentials/<id>/test/
```

### **Metrics Configuration:**
```
⚙️ List:           http://127.0.0.1:8001/metrics-config/
✏️ Edit Config:    http://127.0.0.1:8001/metrics-config/<server_id>/edit/
```

### **API Endpoints:**
```
📊 Server Metrics: http://127.0.0.1:8001/api/server/<server_id>/metrics/
🔄 Refresh:        http://127.0.0.1:8001/api/server/<server_id>/metrics/refresh/
```

### **Main Application:**
```
🌐 Dashboard:      http://127.0.0.1:8001/
📊 Monitoring:     http://127.0.0.1:8001/monitoring/
⚙️ Admin Panel:    http://127.0.0.1:8001/admin/
```

---

## 🌐 Network Access (From Other Devices)

### **Find Your IP Address:**
```bash
ipconfig | findstr "IPv4"
```

### **Access from Other Devices:**
```
http://YOUR_IP:8001/login/
http://YOUR_IP:8001/ssh-credentials/
```

**Example:** If your IP is `192.168.253.23`:
```
http://192.168.253.23:8001/ssh-credentials/
```

---

## 📱 SSH Credentials Management on Port 8001

### **What You'll See:**

#### **SSH Credentials List Page:**
```
📋 SSH Credentials Management
┌─────────────────────────────────────────────────────────┐
│ Server Name            │ Username │ Port │ Status │ Actions │
├─────────────────────────────────────────────────────────┤
│ MNL Web Server Main  │ admin    │ 22   │ Active  │ [✏️][🔌][🗑️] │
│ MNL Web Server #2    │ deploy   │ 22   │ Active  │ [✏️][🔌][🗑️] │
│ MNL Web HA           │ monitor  │ 22   │ Inactive│ [✏️][🔌][🗑️] │
└─────────────────────────────────────────────────────────┘
```

#### **Edit Credential Form:**
```
🖥️ Server: MNL Web Server Main (192.168.254.7) - Read-only
👤 SSH Username: [admin]
🔐 SSH Password: [•••••••] (leave blank to keep current)
🔌 SSH Port: [22]
🔑 Private Key Path: [optional]
✅ Active: [checked/unchecked]
```

---

## 🔧 Quick Start Guide (Port 8001)

### **1. Start Server:**
```bash
python manage.py runserver 0.0.0.0:8001
```

### **2. Login:**
```
URL: http://127.0.0.1:8001/login/
Username: admin
Password: admin123
```

### **3. Access SSH Credentials:**
```
http://127.0.0.1:8001/ssh-credentials/
```

### **4. Edit Server Credentials:**
- Find your server in the list
- Click the edit button (✏️)
- Update credentials as needed
- Test connection before saving
- Save your changes

---

## 🛠️ Troubleshooting Port 8001

### **404 Errors:**
1. **Check Server Port**: Ensure running on 8001
2. **Check URL**: Use `http://127.0.0.1:8001/` not `:8000/`
3. **Check ALLOWED_HOSTS**: Now includes all required hosts
4. **Clear Browser Cache**: Hard refresh (Ctrl+F5)

### **Login Issues:**
1. **Default Credentials**: `admin` / `admin123`
2. **Login URL**: `http://127.0.0.1:8001/login/`
3. **Check Server Logs**: Look for authentication errors

### **SSH Credential Issues:**
1. **Test Connection**: Use the test button before saving
2. **Check Server IP**: Ensure correct IP address
3. **Verify SSH Access**: Ensure SSH user exists on target server

---

## 🎉 Status: ✅ PORT 8001 FULLY CONFIGURED!

The SSH credentials management system is now fully functional on port 8001 with:

- ✅ **ALLOWED_HOSTS Updated** - Supports port 8001 access
- ✅ **Authentication Working** - Login/logout functionality
- ✅ **SSH Credential CRUD** - Complete create/edit/delete operations
- ✅ **Connection Testing** - Real SSH verification
- ✅ **Security Features** - Encrypted storage, login protection
- ✅ **API Integration** - RESTful endpoints available
- ✅ **User Interface** - Professional, responsive design

**You can now access SSH credentials management on port 8001!** 🔐

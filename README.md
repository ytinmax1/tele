# بوت النشر التلقائي على تيليجرام

بوت بيبعت أي رسالة تبعتها له لكل قنواتك تلقائياً.

---

## خطوات الرفع على Railway

### 1. ارفع الملفات على GitHub
- اعمل حساب على github.com
- اعمل repository جديد
- ارفع كل الملفات فيه

### 2. ادخل على Railway
- روح railway.app
- سجل دخول بحساب GitHub
- اختار New Project ← Deploy from GitHub Repo
- اختار الـ repository بتاعك

### 3. حط المتغيرات
روح على Variables وحط:
```
BOT_TOKEN=توكنك_هنا
YOUR_USER_ID=8584724112
CHANNELS=-1003792683838,-1003997994180
```

### 4. تأكد إن البوت أدمن في القنوات
- افتح كل قناة
- Administrators ← Add Administrator
- ابحث عن البوت وفعّل Post Messages

---

## الاستخدام
- ابعت أي رسالة للبوت وهتتنشر في كل القنوات
- `/start` - تشغيل البوت
- `/channels` - عرض القنوات المتصلة

# مراقب التسربات النفطية - Oil Spill Monitor

منصة ويب تفاعلية متكاملة لرصد بقع الزيت في البحر باستخدام صور الأقمار الصناعية Sentinel-1 الرادارية من خلال Google Earth Engine وStreamlit.

## 🌟 الميزات الرئيسية

- **واجهة متعددة اللغات**: عربي / إنجليزي مع تبديل فوري
- **تغطية جغرافية واسعة**: السعودية (بجميع مناطقها)، الكويت، البحرين، قطر، الإمارات، عمان، مصر
- **كشف متقدم بالرادار**: تحليل صور Sentinel-1 SAR باستقطابي VV و VH مع خوارزمية كشف ذكية
- **تصفية ذكية**: قناع المسطحات المائية (JRC Global Surface Water) لاستبعاد المناطق اليابسة
- **تقليل الإنذارات الكاذبة**: دعم شرط النسبة VV/VH لتمييز البقع الزيتية عن الظواهر الطبيعية
- **تحليل الرياح والانجراف**: بيانات ERA5 لحساب اتجاه الانجراف المتوقع للبقع
- **خريطة تفاعلية**: عرض النتائج على خريطة folium مع إمكانية النقر على البقع
- **طبقات إضافية**: منشآت النفط الرئيسية في المنطقة + دعم رفع ملفات GeoJSON
- **تصدير شامل**: تنزيل PNG، GeoTIFF، GeoJSON + تصدير إلى Google Drive

## 📁 هيكل المشروع

```
oil-spill-monitor/
├── app.py                        # التطبيق الرئيسي (ملف واحد متكامل)
├── requirements.txt              # المكتبات المطلوبة
├── oil_infrastructure.geojson    # بيانات منشآت النفط في الخليج
└── README.md                     # هذا الملف
```

## 🚀 إعداد حساب Google Earth Engine

### الخطوة 1: إنشاء مشروع Google Cloud
1. اذهب إلى [Google Cloud Console](https://console.cloud.google.com/)
2. أنشئ مشروعاً جديداً أو اختر مشروعاً موجوداً
3. فعّل [Earth Engine API](https://console.cloud.google.com/apis/library/earthengine.googleapis.com)

### الخطوة 2: التسجيل في Earth Engine
1. اذهب إلى [Earth Engine Code Editor](https://code.earthengine.google.com/register)
2. سجّل باستخدام حساب Google نفسه
3. اقبل شروط الاستخدام

### الخطوة 3: المصادقة المحلية (للتشغيل على جهازك)
```bash
# تثبيت المكتبات
pip install -r requirements.txt

# تشغيل المصادقة (يُفتح متصفح لتسجيل الدخول)
python -c "import ee; ee.Authenticate()"

# تشغيل التطبيق
streamlit run app.py
```

### الخطوة 4: النشر على Streamlit Cloud (اختياري)

#### إعداد Service Account
1. في Google Cloud Console، اذهب إلى **IAM & Admin > Service Accounts**
2. أنشئ Service Account جديد
3. أنشئ مفتاح JSON وحمّله
4. فعّل Earth Engine API للمشروع
5. سجّل Service Account في [Earth Engine Cloud Project](https://code.earthengine.google.com/register)

#### إعداد Streamlit Secrets
في Streamlit Cloud، أضف في **Secrets** (`secrets.toml`):
```toml
EE_SERVICE_ACCOUNT = "your-service-account@your-project.iam.gserviceaccount.com"
EE_PRIVATE_KEY = "path/to/your/private-key.json"
```

> **ملاحظة**: لـ Streamlit Cloud، حمّل ملف المفتاح الخاص كمشفر (Secret file) باسم `private-key.json`

## 🖥️ التشغيل

### محلياً (على جهازك)
```bash
# استنساخ المشروع
git clone <repo-url>
cd oil-spill-monitor

# تثبيت المتطلبات
pip install -r requirements.txt

# المصادقة (مرة واحدة فقط)
python -c "import ee; ee.Authenticate()"

# تشغيل التطبيق
streamlit run app.py
```

### على Streamlit Cloud
1. ارفع الملفات إلى مستودع GitHub
2. أنشئ تطبيقاً جديداً على [Streamlit Cloud](https://streamlit.io/cloud)
3. اربط المستودع وحدد الملف الرئيسي `app.py`
4. أضف Secrets كما هو موضح أعلاه
5. انشر

## 🔧 الاستخدام

### اختيار المنطقة
1. اختر الدولة من القائمة المنسدلة
2. عند اختيار السعودية، ستظهر قائمة إضافية لاختيار المنطقة
3. حدد الفترة الزمنية المطلوبة

### إعدادات الكشف المتقدمة
- **عتبة VV**: القيمة الافتراضية -22 dB (النطاق: -30 إلى -15)
- **عتبة VH**: القيمة الافتراضية -26 dB (النطاق: -30 إلى -15)
- **شرط النسبة VV/VH**: عند تفعيله، لا يُعد البكسل بقعة إلا إذا كانت النسبة VV/VH أقل من القيمة المحددة (افتراضي 1.5)، مما يقلل الإنذارات الكاذبة

### عرض النتائج
- **الخريطة التفاعلية**: عرض البقع باللون الأحمر الشفاف، مع إمكانية النقر لمعرفة المساحة
- **اتجاه الانجراف**: سهم أزرق يُظهر الاتجاه المتوقع لحركة البقع بناءً على بيانات الرياح
- **منشآت النفط**: إظهار المنصات والموانئ النفطية الرئيسية في المنطقة

## ⚠️ الملاحظات والتنويهات

- **هذه المنصة للأغراض البحثية والرصد الأولي فقط، وليست نظام إنذار رسمي.**
- دقة الكشف تعتمد على جودة وتوفر صور Sentinel-1 في المنطقة والفترة المحددة.
- قد تحدث إنذارات كاذبة بسبب عوامل طبيعية (أعشاب بحرية، ظروف بحرية هادئة، إلخ).
- النتائج تحتاج إلى تحقق ميداني أو بأجهزة استشعار إضافية قبل اتخاذ أي إجراء.
- تنزيل GeoTIFF المباشر قد يفشل للمساحات الكبيرة جداً (> 100×100 كم) بسبب حدود Earth Engine.
- في هذه الحالة، استخدم خيار التصدير إلى Google Drive.

## 📖 التقنيات المستخدمة

| التقنية | الاستخدام |
|---------|-----------|
| **Sentinel-1 GRD** | صور رادارية SAR لرصد سطح البحر |
| **Google Earth Engine** | معالجة وحوسبة سحابية للبيانات |
| **JRC Global Surface Water** | قناع المسطحات المائية |
| **ERA5 Reanalysis** | بيانات الرياح (السرعة والاتجاه) |
| **Streamlit** | واجهة الويب التفاعلية |
| **Folium** | الخرائط التفاعلية |
| **Matplotlib** | الرسوم البيانية |

## 📄 الترخيص

هذا المشروع مفتوح المصدر لأغراض البحث والتطوير.

## Streamlit Cloud Deployment Checklist

This repository is now prepared for Streamlit Cloud hosting.

1. Push these files to GitHub: `app.py`, `requirements.txt`, `oil_infrastructure.geojson`, `README.md`, `secrets.toml.template`, and `.gitignore`.
2. Do not push any real service-account key, including `sacred-result-496018-h3-a38d1e3050e6.json` or `.streamlit/secrets.toml`.
3. In Streamlit Cloud, create a new app and set the main file path to `app.py`.
4. Open the app settings, then paste the contents of `secrets.toml.template` into Secrets after replacing the placeholders with the real Google service-account JSON content.
5. Make sure the service-account email is registered or allowed in Earth Engine and that the Earth Engine API is enabled for the Google Cloud project.

Recommended Streamlit secret format:

```toml
EE_KEYS = '''
{ ... paste the complete service-account JSON here ... }
'''
EE_PROJECT_ID = "your-google-cloud-project-id"
```

The app intentionally does not call `ee.Authenticate()` during runtime, because interactive browser authentication does not work reliably on Streamlit Cloud. Use a service account through Secrets for hosting.

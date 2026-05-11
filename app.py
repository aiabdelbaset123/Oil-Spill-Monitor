"""
=====================================================================
مراقب التسربات النفطية - Oil Spill Monitor
منصة ويب تفاعلية لرصد بقع الزيت في البحر
=====================================================================
تقوم هذه المنصة بتحليل صور القمر الصناعي Sentinel-1 الرادارية
من خلال Google Earth Engine لاكتشاف التسربات النفطية المحتملة
في مياه السعودية ودول الخليج ومصر.

المكتبات المطلوبة:
  streamlit, earthengine-api, geemap, folium, geopandas,
  matplotlib, numpy, pandas, branca, json, datetime

=====================================================================
"""

import os
import sys
import json
import io
import tempfile
import datetime
import time
from pathlib import Path

import numpy as np
import streamlit as st
import folium
from folium.raster_layers import ImageOverlay
from folium.plugins import Draw
import branca.colormap as cm

# ===================== إعداد الصفحة =====================
st.set_page_config(
    page_title="مراقب التسربات النفطية - Oil Spill Monitor",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== قاموس اللغات =====================
# يحتوي على جميع النصوص المستخدمة في الواجهة بالعربية والإنجليزية
TRANSLATIONS = {
    "ar": {
        "app_title": "مراقب التسربات النفطية",
        "app_subtitle": "Oil Spill Monitor",
        "language": "اللغة / Language",
        "select_country": "اختر الدولة",
        "select_region": "اختر المنطقة (السعودية)",
        "date_range": "الفترة الزمنية",
        "start_date": "تاريخ البداية",
        "end_date": "تاريخ النهاية",
        "latest_image": "آخر صورة متاحة",
        "advanced_settings": "إعدادات الكشف المتقدمة",
        "vv_threshold": "عتبة VV (dB)",
        "vh_threshold": "عتبة VH (dB)",
        "use_ratio": "تفعيل شرط النسبة VV/VH",
        "ratio_value": "عتبة النسبة VV/VH",
        "run_detection": "تشغيل الكشف",
        "show_drift": "إظهار اتجاه الانجراف المتوقع",
        "show_infrastructure": "إظهار منشآت النفط الرئيسية",
        "results": "نتائج الكشف",
        "total_spills": "عدد البقع المكتشفة",
        "total_area": "إجمالي المساحة المغطاة",
        "max_area": "مساحة أكبر بقعة",
        "avg_area": "متوسط المساحة",
        "unit_km2": "كم²",
        "map_title": "الخريطة التفاعلية",
        "download_png": "تنزيل الخريطة كصورة PNG",
        "download_geotiff": "تنزيل قناع البقع (GeoTIFF)",
        "download_geojson": "تصدير البقع (GeoJSON)",
        "export_drive": "تصدير إلى Google Drive",
        "upload_geojson": "رفع ملف GeoJSON إضافي",
        "no_images": "لم يتم العثور على صور في الفترة المحددة. يرجى تعديل التاريخ أو النطاق المكاني.",
        "processing": "جارٍ المعالجة... يرجى الانتظار",
        "fetching_data": "جارٍ جلب البيانات من Earth Engine...",
        "applying_mask": "جارٍ تطبيق قناع المسطحات المائية...",
        "detecting_spills": "جارٍ كشف التسربات النفطية...",
        "analyzing_results": "جارٍ تحليل النتائج...",
        "preparing_map": "جارٍ إعداد الخريطة التفاعلية...",
        "error_ee": "خطأ في الاتصال بـ Google Earth Engine. تأكد من المصادقة.",
        "error_no_images": "لا توجد صور Sentinel-1 متاحة في هذا النطاق.",
        "error_large_area": "المنطقة المحددة كبيرة جداً. يرجى تضييق النطاق.",
        "error_export": "فشل التصدير المباشر. يمكنك استخدام التصدير إلى Google Drive.",
        "info_disclaimer": "تنويه: هذه المنصة للأغراض البحثية والرصد الأولي فقط، وليست نظام إنذار رسمي.",
        "tab_map": "الخريطة التفاعلية",
        "tab_stats": "الإحصائيات",
        "tab_settings": "الإعدادات المتقدمة",
        "wind_speed": "متوسط سرعة الرياح",
        "wind_dir": "اتجاه الرياح",
        "wind_unit_ms": "م/ث",
        "drift_speed": "سرعة الانجراف المتوقعة",
        "drift_unit": "م/ث (3% من سرعة الرياح)",
        "platforms": "منشآت نفطية",
        "terminals": "محطات نفطية",
        "region_all": "جميع المناطق",
        "auth_success": "تم الاتصال بـ Google Earth Engine بنجاح",
        "polygonization_note": "ملاحظة: قد يستغرق التصدير بعض الوقت للمناطق الكبيرة",
        "connection_status": "حالة الاتصال",
        "connected": "متصل",
        "disconnected": "غير متصل",
        "num_images": "عدد الصور المستخدمة",
        "image_dates": "فترة تغطية الصور",
        "min_pixel_size": "الحد الأدنى لحجم التجمع (بكسل)",
        "cleaning_mask": "تنظيف القناع (إزالة الضوضاء)",
        "using_water_mask": "استخدام قناع المسطحات المائية: JRC Global Surface Water",
        "about_title": "عن المنصة",
        "about_text": "منصة مراقب التسربات النفطية تعتمد على صور القمر الصناعي Sentinel-1 الرادارية (SAR) لرصد التسربات النفطية المحتملة في مياه الخليج العربي والبحر الأحمر والبحر المتوسط. تعتمد المنصة على خوارزمية كشف يعتمد على ارتداد الإشارة الرادارية حيث تظهر بقع الزيت كمناطق ذات ارتداد منخفض في كل من الاستقطاب VV وVH.",
    },
    "en": {
        "app_title": "Oil Spill Monitor",
        "app_subtitle": "مراقب التسربات النفطية",
        "language": "Language / اللغة",
        "select_country": "Select Country",
        "select_region": "Select Region (Saudi Arabia)",
        "date_range": "Date Range",
        "start_date": "Start Date",
        "end_date": "End Date",
        "latest_image": "Latest Available Image",
        "advanced_settings": "Advanced Detection Settings",
        "vv_threshold": "VV Threshold (dB)",
        "vh_threshold": "VH Threshold (dB)",
        "use_ratio": "Enable VV/VH Ratio Condition",
        "ratio_value": "VV/VH Ratio Threshold",
        "run_detection": "Run Detection",
        "show_drift": "Show Expected Drift Direction",
        "show_infrastructure": "Show Major Oil Infrastructure",
        "results": "Detection Results",
        "total_spills": "Number of Detected Spills",
        "total_area": "Total Covered Area",
        "max_area": "Largest Spill Area",
        "avg_area": "Average Area",
        "unit_km2": "km²",
        "map_title": "Interactive Map",
        "download_png": "Download Map as PNG",
        "download_geotiff": "Download Spill Mask (GeoTIFF)",
        "download_geojson": "Export Spills (GeoJSON)",
        "export_drive": "Export to Google Drive",
        "upload_geojson": "Upload Additional GeoJSON",
        "no_images": "No images found in the selected period. Please adjust the date or spatial range.",
        "processing": "Processing... Please wait",
        "fetching_data": "Fetching data from Earth Engine...",
        "applying_mask": "Applying water surface mask...",
        "detecting_spills": "Detecting oil spills...",
        "analyzing_results": "Analyzing results...",
        "preparing_map": "Preparing interactive map...",
        "error_ee": "Error connecting to Google Earth Engine. Please verify authentication.",
        "error_no_images": "No Sentinel-1 images available in this range.",
        "error_large_area": "The selected area is too large. Please narrow the range.",
        "error_export": "Direct export failed. You can use Google Drive export.",
        "info_disclaimer": "Disclaimer: This platform is for research and preliminary monitoring purposes only, not an official alert system.",
        "tab_map": "Interactive Map",
        "tab_stats": "Statistics",
        "tab_settings": "Advanced Settings",
        "wind_speed": "Average Wind Speed",
        "wind_dir": "Wind Direction",
        "wind_unit_ms": "m/s",
        "drift_speed": "Expected Drift Speed",
        "drift_unit": "m/s (3% of wind speed)",
        "platforms": "Oil Platforms",
        "terminals": "Oil Terminals",
        "region_all": "All Regions",
        "auth_success": "Connected to Google Earth Engine successfully",
        "polygonization_note": "Note: Export may take some time for large areas",
        "connection_status": "Connection Status",
        "connected": "Connected",
        "disconnected": "Disconnected",
        "num_images": "Number of Images Used",
        "image_dates": "Image Coverage Period",
        "min_pixel_size": "Minimum Cluster Size (pixels)",
        "cleaning_mask": "Cleaning Mask (Noise Removal)",
        "using_water_mask": "Water Mask: JRC Global Surface Water",
        "about_title": "About",
        "about_text": "Oil Spill Monitor uses Sentinel-1 SAR satellite imagery to detect potential oil spills in the Arabian Gulf, Red Sea, and Mediterranean. The detection algorithm relies on radar backscatter where oil slicks appear as areas with low backscatter in both VV and VH polarizations.",
    }
}

# ===================== النطاقات المكانية =====================
# إحداثيات Bounding Box لكل دولة ومنطقة (تقريبية)
# التنسيق: [min_lon, min_lat, max_lon, max_lat]

COUNTRY_BBOXES = {
    "السعودية / Saudi Arabia": [35.0, 16.0, 56.0, 32.0],
    "الكويت / Kuwait": [46.5, 28.5, 48.5, 30.1],
    "البحرين / Bahrain": [50.4, 25.5, 50.8, 26.4],
    "قطر / Qatar": [50.7, 24.5, 52.0, 26.2],
    "الإمارات / UAE": [51.5, 22.5, 56.5, 26.5],
    "عمان / Oman": [55.0, 16.5, 60.0, 26.5],
    "مصر / Egypt": [24.5, 21.5, 36.0, 32.0],
}

# مناطق المملكة العربية السعودية - تشمل المناطق الساحلية وغير الساحلية
# (المناطق غير الساحلية تغطي المسطحات المائية الداخلية وحقول النفط)
SAUDI_REGIONS = {
    "جميع المناطق / All Regions": [35.0, 16.0, 56.0, 32.0],
    "مكة المكرمة / Makkah": [38.0, 19.0, 44.0, 24.0],
    "الشرقية / Eastern": [45.0, 22.0, 56.0, 28.0],
    "تبوك / Tabuk": [34.5, 25.0, 39.0, 30.0],
    "المدينة المنورة / Madinah": [37.5, 22.0, 41.0, 27.5],
    "جازان / Jazan": [41.5, 16.0, 44.0, 18.5],
    "عسير / Asir": [41.5, 17.5, 45.0, 21.0],
    "نجران / Najran": [43.0, 16.5, 45.5, 19.5],
    "الباحة / Al Bahah": [41.0, 19.5, 42.5, 21.0],
    "الجوف / Al Jawf": [37.0, 28.0, 40.0, 31.5],
    "الحدود الشمالية / Northern Borders": [37.0, 28.5, 42.0, 32.0],
    "حائل / Hail": [39.0, 25.0, 43.0, 29.5],
    "القصيم / Qassim": [42.0, 24.0, 45.5, 27.5],
    "الرياض / Riyadh": [44.0, 23.0, 48.0, 26.5],
}

# ===================== دالة الترجمة =====================
def t(key):
    """دالة مساعدة للحصول على النص المترجم حسب اللغة المختارة"""
    lang = st.session_state.get("language", "ar")
    return TRANSLATIONS.get(lang, TRANSLATIONS["ar"]).get(key, key)

# ===================== تهيئة Google Earth Engine =====================
def initialize_ee():
    """
    تهيئة الاتصال بـ Google Earth Engine.
    يدعم:
      1. Service Account (للنشر السحابي Streamlit Cloud) - لا يتأثر بـ 2SV/MFA
      2. المصادقة المحلية ee.Authenticate() (للتشغيل المحلي) - يحتاج إكمال 2SV في المتصفح
       
    ملاحظة مهمة: منذ earthengine-api >= 1.5.0 يجب تمرير project= إلى ee.Initialize()
    """
    import ee
    import json
    from tempfile import NamedTemporaryFile

    ee_initialized = False

    # ---- الطريقة 1: Service Account (للنشر السحابي / Streamlit Cloud) ----
    # هذه الطريقة لا تتأثر بمتطلب Google للتحقق بخطوتين (2SV/MFA)
    try:
        service_account = st.secrets.get("EE_SERVICE_ACCOUNT", None)
        project_id = st.secrets.get("EE_PROJECT_ID", None)
        if service_account and project_id:
            # بناء ملف JSON مؤقت من الحقول المفردة في secrets
            service_account_info = {
                "type": st.secrets.get("EE_TYPE", "service_account"),
                "project_id": project_id,
                "private_key_id": st.secrets.get("EE_PRIVATE_KEY_ID", ""),
                "private_key": st.secrets.get("EE_PRIVATE_KEY", ""),
                "client_email": st.secrets.get("EE_CLIENT_EMAIL", service_account),
                "client_id": st.secrets.get("EE_CLIENT_ID", ""),
                "auth_uri": st.secrets.get("EE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": st.secrets.get("EE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": st.secrets.get("EE_AUTH_PROVIDER_X509_CERT_URL", ""),
                "client_x509_cert_url": st.secrets.get("EE_CLIENT_X509_CERT_URL", ""),
            }

            # كتابة المفتاح إلى ملف مؤقت (مطلوب من ee.ServiceAccountCredentials)
            with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(service_account_info, f)
                temp_key_path = f.name

            credentials = ee.ServiceAccountCredentials(service_account, temp_key_path)
            ee.Initialize(credentials=credentials, project=project_id)
            ee_initialized = True
            return True, f"Service Account ({service_account})"
    except Exception as e:
        sa_error = str(e)

    # ---- الطريقة 2: ملف JSON مباشر عبر متغير البيئة ----
    try:
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", None)
        if creds_path and os.path.exists(creds_path):
            project_id = st.secrets.get("EE_PROJECT_ID", None)
            if project_id:
                ee.Initialize(project=project_id)
            else:
                ee.Initialize()
            return True, "GOOGLE_APPLICATION_CREDENTIALS"
    except Exception:
        pass

    # ---- الطريقة 3: المصادقة المحلية ee.Authenticate() ----
    # للاستخدام المحلي فقط - ستحتاج لإكمال التحقق بخطوتين في المتصفح
    if not ee_initialized:
        try:
            project_id = st.secrets.get("EE_PROJECT_ID", None)
            if project_id:
                ee.Initialize(project=project_id)
            else:
                # محاولة التهيئة بدون مشروع (قد لا يعمل في الإصدارات الحديثة)
                ee.Initialize()
            return True, "Cached Credentials"
        except Exception:
            try:
                # المصادقة التفاعلية - ستفتح نافذة المتصفح
                # ⚠️ تأكد من تفعيل 2SV على حسابك Google أولاً!
                ee.Authenticate()
                project_id = st.secrets.get("EE_PROJECT_ID", None)
                if project_id:
                    ee.Initialize(project=project_id)
                else:
                    ee.Initialize()
                return True, "Authenticated"
            except Exception as e:
                return False, str(e)

    return False, "Unknown error"


# ===================== قناع المسطحات المائية =====================
def get_water_mask(aoi):
    """
    إنشاء قناع للمسطحات المائية باستخدام طبقة JRC Global Surface Water.
    يعيد صورة ثنائية حيث الماء = 1 واليابسة = 0.
    """
    import ee

    # استخدام طبقة JRC Global Surface Water - occurrence
    # القيم الأعلى من 50% تشير إلى وجود ماء دائم أو شبه دائم
    jrc_water = ee.Image("JRC/GSW1_3/GlobalSurfaceWater").select("occurrence")
    water_mask = jrc_water.gt(50).rename("water_mask")

    # قص القناع على منطقة الاهتمام مع هامش
    buffer = aoi.buffer(5000)
    water_mask = water_mask.clip(buffer)

    return water_mask


# ===================== كشف التسربات النفطية =====================
def detect_oil_spills(aoi, start_date, end_date, vv_thresh, vh_thresh,
                      use_ratio, ratio_threshold, min_pixels=10):
    """
    الدالة الرئيسية لكشف التسربات النفطية من صور Sentinel-1.

    المعاملات:
    -----------
    aoi : ee.Geometry
        منطقة الاهتمام (مضلع أو مستطيل)
    start_date : str
        تاريخ البداية (YYYY-MM-DD)
    end_date : str
        تاريخ النهاية (YYYY-MM-DD)
    vv_thresh : float
        عتبة الاستقطاب VV (بالديسيبل، عادة قيمة سالبة)
    vh_thresh : float
        عتبة الاستقطاب VH (بالديسيبل)
    use_ratio : bool
        هل يتم تفعيل شرط النسبة VV/VH
    ratio_threshold : float
        عتبة النسبة (القيم أقل من هذه تعتبر بقعاً)
    min_pixels : int
        الحد الأدنى لحجم التجمع (بكسل) لإزالة الضوضاء

    العائد:
    -------
    dict: يحتوي على:
        - 'mask': قناع البقع (ee.Image)
        - 'num_spills': عدد البقع (int)
        - 'total_area': إجمالي المساحة (km²)
        - 'max_area': أكبر مساحة (km²)
        - 'avg_area': متوسط المساحة (km²)
        - 'spill_areas': قائمة مساحات البقع (list)
        - 'stats_dict': قاموس الإحصاءات
        - 'collection': مجموعة الصور المستخدمة
    """
    import ee

    # ---- الخطوة 1: جلب صور Sentinel-1 GRD ----
    # نبحث عن الصور التي تحتوي على كل من VV و VH
    collection = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
    )

    # التحقق من وجود صور
    count = collection.size().getInfo()
    if count == 0:
        return None, None, None, None

    # ---- الخطوة 2: حساب المتوسط الزمني (Mosaic) ----
    # نعمل مباشرة في فضاء dB لأن عتبات الكشف معطاة بالديسيبل.
    # هذا هو النهج الشائع في أدبيات كشف الزيت بالـ SAR.
    # بيانات Sentinel-1 GRD مُقدّمة بالفعل في dB (backscatter).
    mosaic = collection.mean().clip(aoi)

    vv_mean = mosaic.select("VV").rename("VV_mean")
    vh_mean = mosaic.select("VH").rename("VH_mean")

    # ---- الخطوة 3: تطبيق قناع المسطحات المائية ----
    water_mask = get_water_mask(aoi)

    # ---- الخطوة 4: إنشاء قناع البقع ----
    # البقع الزيتية تقلل من ارتداد الرادار (تظهر أغمق) في كلا الاستقطابين.
    # الشرط: VV < العتبة1 و VH < العتبة2 (بالديسيبل)
    oil_mask = (
        vv_mean.lt(vv_thresh)
        .And(vh_mean.lt(vh_thresh))
    )

    # إضافة شرط النسبة VV/VH إن فُعّل
    # لاحظ: الفرق بين dB يكون مساوياً لنسبة الخطي: dB(VV) - dB(VH) = 10*log10(VV_lin/VH_lin)
    # البقع الزيتية تُظهر استقطاباً متقارباً، أي أن النسبة VV/VH أقل.
    if use_ratio:
        ratio_db = vv_mean.subtract(vh_mean)  # الفرق بالـ dB
        # تحويل إلى نسبة خطية: ratio = 10^(ratio_db/10)
        ratio_linear = ee.Image(10).pow(ratio_db.divide(10))
        ratio_condition = ratio_linear.lt(ratio_threshold)
        oil_mask = oil_mask.And(ratio_condition)

    # دمج مع قناع الماء (بقاء البكسلات المائية فقط)
    oil_mask = oil_mask.And(water_mask).rename("oil_mask")

    # ---- الخطوة 5: تنظيف القناع ----
    # إزالة التجمعات الأصغر من min_pixels بكسل متصل لتقليل الضوضاء
    connected = oil_mask.connectedPixelCount(maxSize=min_pixels * 100, eightConnected=True)
    cleaned_mask = oil_mask.And(connected.gte(min_pixels)).rename("oil_cleaned")

    # ---- الخطوة 6: تحليل البقع ----
    # استخدام reduceToVectors لتحويل البقع إلى مضلعات
    try:
        vectors = cleaned_mask.reduceToVectors(
            geometry=aoi,
            scale=20,  # دقة Sentinel-1 حوالي 10-20 متر
            geometryType="polygon",
            eightConnected=True,
            maxPixels=1e8,
            bestEffort=True,
        )

        # حساب المساحات لكل متجه
        def add_area(feat):
            area = feat.geometry().area(maxError=100).divide(1e6)  # م² إلى كم²
            return feat.set({"area_km2": area})

        vectors_with_area = vectors.map(add_area)

        # استخراج الإحصاءات
        areas_list = vectors_with_area.aggregate_array("area_km2").getInfo()
        areas_list = [float(a) for a in areas_list if float(a) > 0]
    except Exception as e:
        # في حال فشل reduceToVectors (مثلاً لا توجد بقع)
        areas_list = []
        vectors_with_area = ee.FeatureCollection([])

    num_spills = len(areas_list)
    total_area = sum(areas_list) if areas_list else 0
    max_area = max(areas_list) if areas_list else 0
    avg_area = total_area / num_spills if num_spills > 0 else 0

    # ---- الخطوة 7: حساب المساحة الإجمالية بالبكسلات ----
    pixel_area = (
        cleaned_mask.multiply(ee.Image.pixelArea())
        .reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=aoi,
            scale=20,
            maxPixels=1e8,
            bestEffort=True,
        )
    )
    total_pixel_area = pixel_area.getInfo().get("oil_cleaned", 0)
    total_pixel_area_km2 = total_pixel_area / 1e6 if total_pixel_area else 0

    stats = {
        "num_spills": num_spills,
        "total_area": total_area,
        "max_area": max_area,
        "avg_area": avg_area,
        "total_pixel_area_km2": total_pixel_area_km2,
        "spill_areas": areas_list,
        "num_images": count,
    }

    # ---- الخطوة 8: إعداد صورة التصور ----
    # إنشاء صورة ملونة: البقع بالأحمر، الباقي شفاف
    # نستخدم selfMask() لإخفاء البكسلات الصفرية
    spill_vis = cleaned_mask.selfMask().visualize(
        min=0, max=1,
        palette=["#FF0000"],
    )

    return spill_vis, stats, vectors_with_area, collection


# ===================== حساب بيانات الرياح =====================
def get_wind_data(aoi, start_date, end_date):
    """
    استخراج بيانات الرياح من مجموعة ERA5 Hourly لمنطقة ومدة محددة.
    يحسب متوسط سرعة واتجاه الرياح.

    العائد:
    -------
    dict أو None: يحتوي على speed (م/ث) و direction (درجات)
    """
    import ee

    try:
        # استخدام ERA5 Hourly - نأخذ المتوسط للفترة المحددة
        # نستخدم يومياً بدلاً من ساعياً لتقليل حجم البيانات
        era5 = (
            ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")
            .filterBounds(aoi)
            .filterDate(start_date, end_date)
            .select(["u_10m", "v_10m"])
            .mean()
            .clip(aoi)
        )

        # حساب السرعة والاتجاه من مركبات u و v
        u = era5.select("u_10m")
        v = era5.select("v_10m")
        speed = u.pow(2).add(v.pow(2)).sqrt().rename("wind_speed")
        # حساب اتجاه حركة الرياح (ليس اتجاه المنشأ)
        # atan2(u, v) يعطي الاتجاه الميكانيكي (direction FROM)
        # نعكسه للحصول على اتجاه الحركة (direction TO)
        direction = (
            ee.Image.constant(180)
            .add(
                ee.Image.atan2(u, v)
                .multiply(180)
                .divide(3.14159265)
            )
        ).mod(360).rename("wind_dir")

        # استخراج القيم المتوسطة
        wind_stats = (
            ee.Image.cat([speed, direction])
            .reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=10000,
                maxPixels=1e6,
            )
        )

        data = wind_stats.getInfo()
        return {
            "speed": data.get("wind_speed", 0),
            "direction": data.get("wind_dir", 0),
        }

    except Exception as e:
        st.warning(f"Wind data unavailable: {e}")
        return None


# ===================== إنشاء الخريطة التفاعلية =====================
def create_interactive_map(aoi_bbox, spill_vis=None, vectors=None,
                           wind_data=None, show_drift=True,
                           show_infrastructure=False, lang="ar"):
    """
    إنشاء خريطة folium تفاعلية تعرض نتائج الكشف.

    المعاملات:
    -----------
    aoi_bbox : list
        النطاق المكاني [min_lon, min_lat, max_lon, max_lat]
    spill_vis : ee.Image أو None
        طبقة البقع المرئية
    vectors : ee.FeatureCollection أو None
        البقع كمضلعات
    wind_data : dict أو None
        بيانات الرياح
    show_drift : bool
        إظهار اتجاه الانجراف
    show_infrastructure : bool
        إظهار منشآت النفط
    lang : str
        اللغة الحالية
    """
    import ee

    min_lon, min_lat, max_lon, max_lat = aoi_bbox

    # حساب مركز المنطقة
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2

    # إنشاء الخريطة
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    # إضافة طبقة القمر الصناعي كخيار
    folium.raster_layers.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite",
        overlay=False,
        control=True,
    ).add_to(m)

    # إضافة حدود منطقة الاهتمام
    aoi_geom = folium.Rectangle(
        bounds=[[min_lat, min_lon], [max_lat, max_lon]],
        color="blue",
        weight=2,
        fill=False,
        tooltip="Area of Interest"
    )
    aoi_geom.add_to(m)

    # إضافة طبقة البقع من GEE
    if spill_vis is not None:
        try:
            map_id_dict = spill_vis.getMapId({"opacity": 0.6})
            folium.raster_layers.TileLayer(
                tiles=map_id_dict["tile_fetcher"].url_format,
                attr="Google Earth Engine",
                name=t("total_spills"),
                overlay=True,
                control=True,
                opacity=0.6,
            ).add_to(m)
        except Exception as e:
            st.warning(f"Could not load spill layer: {e}")

    # إضافة مضلعات البقع القابلة للنقر
    if vectors is not None:
        try:
            # تحويل المضلعات إلى GeoJSON
            geojson_dict = vectors.getInfo()
            if geojson_dict and "features" in geojson_dict:
                for feature in geojson_dict["features"]:
                    geom = feature.get("geometry", {})
                    props = feature.get("properties", {})
                    area = props.get("area_km2", 0)

                    if geom.get("type") == "Polygon":
                        coords = geom.get("coordinates", [[]])[0]
                        if coords:
                            popup_text = f"Area: {area:.3f} km²"
                            folium.Polygon(
                                locations=[(c[1], c[0]) for c in coords],
                                color="red",
                                fill=True,
                                fill_color="red",
                                fill_opacity=0.35,
                                weight=1,
                                popup=folium.Popup(popup_text, max_width=200),
                                tooltip=f"{area:.3f} km²"
                            ).add_to(m)
        except Exception as e:
            st.warning(f"Could not load spill polygons: {e}")

    # إضافة اتجاه الانجراف (سهم الرياح)
    if wind_data and show_drift:
        try:
            drift_speed = wind_data["speed"] * 0.03  # 3% من سرعة الرياح
            wind_dir_rad = wind_data["direction"] * (3.14159265 / 180)

            # حساب نهاية السهم
            arrow_length = 0.5  # طول السهم بالدرجات (تقريبي)
            end_lon = center_lon + arrow_length * np.sin(wind_dir_rad)
            end_lat = center_lat + arrow_length * np.cos(wind_dir_rad)

            # إنشاء أيقونة السهم
            arrow_icon = folium.DivIcon(
                html=f"""
                <div style="font-size: 14px; color: #0066cc; font-weight: bold;">
                    <span style="font-size: 20px;">➤</span>
                </div>
                """,
                icon_size=(20, 20),
                icon_anchor=(10, 10),
            )

            popup_wind = (
                f"Wind Speed: {wind_data['speed']:.1f} m/s<br>"
                f"Wind Direction: {wind_data['direction']:.0f}°<br>"
                f"Drift Speed: {drift_speed:.2f} m/s (3%)"
            )

            folium.Marker(
                location=[center_lat, center_lon],
                icon=arrow_icon,
                popup=folium.Popup(popup_wind, max_width=250),
            ).add_to(m)

            # رسم خط الاتجاه
            folium.PolyLine(
                locations=[[center_lat, center_lon], [end_lat, end_lon]],
                color="#0066cc",
                weight=3,
                opacity=0.8,
                dash_array="10, 5",
                popup="Expected drift direction",
            ).add_to(m)

        except Exception as e:
            st.warning(f"Could not add wind arrow: {e}")

    # إضافة طبقة منشآت النفط
    if show_infrastructure:
        try:
            geojson_path = Path(__file__).parent / "oil_infrastructure.geojson"
            if geojson_path.exists():
                with open(geojson_path, "r", encoding="utf-8") as f:
                    infra_data = json.load(f)

                for feature in infra_data.get("features", []):
                    props = feature.get("properties", {})
                    geom = feature.get("geometry", {})

                    if geom.get("type") == "Point":
                        coords = geom.get("coordinates", [0, 0])
                        lon, lat = coords[0], coords[1]

                        # اختيار الأيقونة حسب النوع
                        infra_type = props.get("type", "")
                        if infra_type == "offshore_platform":
                            icon_color = "darkpurple"
                            icon_symbol = "oil-well"
                        else:
                            icon_color = "darkred"
                            icon_symbol = "industry"

                        name = props.get("name_" + ("ar" if lang == "ar" else "en"), "Unknown")
                        country = props.get("country", "")
                        capacity = props.get("capacity_bpd", "N/A")

                        popup_text = (
                            f"<b>{name}</b><br>"
                            f"Type: {infra_type.replace('_', ' ').title()}<br>"
                            f"Country: {country}<br>"
                            f"Capacity: {capacity} bpd"
                        )

                        folium.Marker(
                            location=[lat, lon],
                            popup=folium.Popup(popup_text, max_width=300),
                            tooltip=name,
                            icon=folium.Icon(
                                color=icon_color,
                                icon="tint" if infra_type == "offshore_platform" else "industry",
                                prefix="fa"
                            ),
                        ).add_to(m)

                folium.LayerControl().add_to(m)
        except Exception as e:
            st.warning(f"Could not load oil infrastructure: {e}")

    return m


# ===================== تنزيل الخريطة كـ PNG =====================
def download_map_as_png(m):
    """
    تحويل خريطة folium إلى صورة PNG باستخدام html2image أو selenium.
    في حالة عدم توفر المكتبات، يُرجع None.
    """
    try:
        import base64
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import tempfile

        html = m.get_root().render()

        # كتابة HTML إلى ملف مؤقت
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html)
            temp_path = f.name

        # استخدام selenium لالتقاط صورة
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1200, 800)
        driver.get(f"file://{temp_path}")
        time.sleep(3)  # انتظار تحميل الخريطة

        png_data = driver.get_screenshot_as_png()
        driver.quit()

        # حذف الملف المؤقت
        os.unlink(temp_path)

        return png_data

    except ImportError:
        st.info(
            "لتثبيت دعم التنزيل كـ PNG: pip install selenium chromedriver-autoinstaller"
        )
        return None
    except Exception as e:
        st.warning(f"PNG export failed: {e}")
        return None


# ===================== تصدير إلى Google Drive =====================
def export_to_drive(image, description, region, scale=20):
    """
    إرسال مهمة تصدير إلى Google Drive عبر Earth Engine.
    """
    import ee

    try:
        task = ee.batch.Export.image.toDrive(
            image=image,
            description=description.replace(" ", "_"),
            folder="oil_spill_monitor",
            region=region,
            scale=scale,
            crs="EPSG:4326",
            maxPixels=1e8,
        )
        task.start()
        return task.id
    except Exception as e:
        return None


# ===================== واجهة المستخدم الرئيسية =====================
def main():
    """
    الدالة الرئيسية لتشغيل التطبيق.
    """

    # ---- تهيئة حالة الجلسة ----
    if "language" not in st.session_state:
        st.session_state.language = "ar"
    if "ee_ready" not in st.session_state:
        st.session_state.ee_ready = False
    if "last_results" not in st.session_state:
        st.session_state.last_results = None
    if "last_map" not in st.session_state:
        st.session_state.last_map = None

    lang = st.session_state.language

    # ---- الشريط الجانبي ----
    with st.sidebar:
        # تبديل اللغة
        lang_option = st.radio(
            t("language"),
            ["العربية", "English"],
            index=0 if lang == "ar" else 1,
            horizontal=True,
        )
        st.session_state.language = "ar" if lang_option == "العربية" else "en"
        lang = st.session_state.language

        st.markdown("---")

        # حالة الاتصال
        st.subheader(t("connection_status"))
        if not st.session_state.ee_ready:
            with st.spinner("..."):
                success, msg = initialize_ee()
                if success:
                    st.session_state.ee_ready = True
                    st.success(t("auth_success"))
                else:
                    st.error(t("error_ee"))
                    st.info(f"Details: {msg}")
        else:
            st.success(f"✅ {t('connected')}")

        st.markdown("---")

        # اختيار الدولة
        country_names = list(COUNTRY_BBOXES.keys())
        selected_country = st.selectbox(
            t("select_country"),
            country_names,
            index=0,
        )

        # اختيار المنطقة (للسعودية فقط)
        selected_region = None
        if "السعودية" in selected_country:
            region_names = list(SAUDI_REGIONS.keys())
            selected_region = st.selectbox(
                t("select_region"),
                region_names,
                index=0,
            )

        st.markdown("---")

        # اختيار الفترة الزمنية
        st.subheader(t("date_range"))
        today = datetime.date.today()
        default_start = today - datetime.timedelta(days=30)

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                t("start_date"),
                value=default_start,
                max_value=today,
            )
        with col2:
            end_date = st.date_input(
                t("end_date"),
                value=today,
                max_value=today,
            )

        st.markdown("---")

        # الإعدادات المتقدمة
        st.subheader(t("advanced_settings"))

        vv_thresh = st.slider(
            t("vv_threshold"),
            min_value=-30.0,
            max_value=-15.0,
            value=-22.0,
            step=0.5,
            help="Lower values detect darker areas (potential spills)"
        )

        vh_thresh = st.slider(
            t("vh_threshold"),
            min_value=-30.0,
            max_value=-15.0,
            value=-26.0,
            step=0.5,
            help="Lower values detect darker areas (potential spills)"
        )

        use_ratio = st.checkbox(
            t("use_ratio"),
            value=False,
            help="Oil spills show convergent polarization (lower VV/VH ratio)"
        )

        ratio_value = st.slider(
            t("ratio_value"),
            min_value=0.5,
            max_value=3.0,
            value=1.5,
            step=0.1,
            disabled=not use_ratio,
        )

        st.markdown("---")

        # إظهار/إخفاء الطبقات
        show_drift = st.checkbox(
            t("show_drift"),
            value=True,
        )

        show_infrastructure = st.checkbox(
            t("show_infrastructure"),
            value=False,
        )

        # رفع ملف GeoJSON إضافي
        uploaded_file = st.file_uploader(
            t("upload_geojson"),
            type=["geojson", "json"],
            key="geojson_upload",
        )

    # ---- المحتوى الرئيسي ----
    # العنوان
    st.title(f"🛢️ {t('app_title')}")
    st.caption(t("app_subtitle"))
    st.info(t("info_disclaimer"))

    # تحديد النطاق المكاني
    if selected_region and selected_region != "جميع المناطق / All Regions":
        aoi_bbox = SAUDI_REGIONS[selected_region]
    elif selected_region == "جميع المناطق / All Regions":
        aoi_bbox = SAUDI_REGIONS[selected_region]
    else:
        aoi_bbox = COUNTRY_BBOXES[selected_country]

    # إنشاء كائن AOI لـ Earth Engine
    if st.session_state.ee_ready:
        import ee
        aoi = ee.Geometry.Rectangle(aoi_bbox)

    # ---- زر تشغيل الكشف ----
    run_clicked = st.button(
        f"🔍 {t('run_detection')}",
        type="primary",
        use_container_width=True,
    )

    if run_clicked:
        if not st.session_state.ee_ready:
            st.error(t("error_ee"))
            return

        import ee

        # التحقق من صحة التواريخ
        if start_date >= end_date:
            st.error("⚠️ Start date must be before end date")
            return

        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # التحقق من حجم المنطقة
        try:
            area_m2 = aoi.area().getInfo()
            if area_m2 > 5e10:  # أكثر من 50,000 كم²
                st.warning(t("error_large_area"))
        except Exception:
            pass

        # تشغيل الكشف مع مؤشر التقدم
        progress_text = st.empty()
        progress_bar = st.progress(0)

        try:
            # الخطوة 1: جلب البيانات
            progress_text.markdown(f"⏳ {t('fetching_data')}")
            progress_bar.progress(10)

            # الخطوة 2: تطبيق القناع
            progress_text.markdown(f"⏳ {t('applying_mask')}")
            progress_bar.progress(30)

            # الخطوة 3: الكشف
            progress_text.markdown(f"⏳ {t('detecting_spills')}")
            progress_bar.progress(50)

            # تنفيذ الكشف الرئيسي
            result = detect_oil_spills(
                aoi=aoi,
                start_date=start_str,
                end_date=end_str,
                vv_thresh=vv_thresh,
                vh_thresh=vh_thresh,
                use_ratio=use_ratio,
                ratio_threshold=ratio_value,
            )

            spill_vis, stats, vectors, collection = result

            if spill_vis is None or stats is None:
                progress_bar.empty()
                progress_text.empty()
                st.error(t("no_images"))
                return

            progress_bar.progress(70)

            # الخطوة 4: تحليل النتائج
            progress_text.markdown(f"⏳ {t('analyzing_results')}")
            progress_bar.progress(80)

            # الخطوة 5: حساب الرياح
            wind_data = None
            if show_drift:
                wind_data = get_wind_data(aoi, start_str, end_str)

            progress_bar.progress(90)

            # الخطوة 6: إعداد الخريطة
            progress_text.markdown(f"⏳ {t('preparing_map')}")
            progress_bar.progress(95)

            # تخزين النتائج في الجلسة
            st.session_state.last_results = {
                "stats": stats,
                "wind": wind_data,
                "start_date": start_str,
                "end_date": end_str,
                "collection": collection,
                "spill_vis": spill_vis,
                "vectors": vectors,
                "aoi_bbox": aoi_bbox,
                "show_drift": show_drift,
                "show_infrastructure": show_infrastructure,
            }

            progress_bar.progress(100)
            progress_text.empty()

            st.success("✅ " + ("تم الكشف بنجاح!" if lang == "ar" else "Detection completed!"))

        except Exception as e:
            progress_bar.empty()
            progress_text.empty()
            st.error(f"Error: {str(e)}")

    # ---- عرض النتائج ----
    if st.session_state.last_results is not None:
        results = st.session_state.last_results
        stats = results["stats"]
        wind_data = results.get("wind")

        # ألسنة العرض (Tabs)
        tab_map, tab_stats, tab_export = st.tabs([
            t("tab_map"), t("tab_stats"), t("tab_settings")
        ])

        # ---- التبويب الأول: الخريطة ----
        with tab_map:
            st.subheader(t("map_title"))

            # إنشاء الخريطة
            m = create_interactive_map(
                aoi_bbox=results["aoi_bbox"],
                spill_vis=results["spill_vis"],
                vectors=results["vectors"],
                wind_data=wind_data,
                show_drift=results["show_drift"],
                show_infrastructure=results["show_infrastructure"],
                lang=lang,
            )

            # إضافة ملف GeoJSON المرفوع إن وُجد
            if uploaded_file is not None:
                try:
                    user_geojson = json.load(uploaded_file)
                    user_layer = folium.GeoJson(
                        user_geojson,
                        name="User Layer",
                        style_function=lambda x: {
                            "fillColor": "orange",
                            "color": "orange",
                            "weight": 2,
                            "fillOpacity": 0.3,
                        },
                    )
                    user_layer.add_to(m)
                    folium.LayerControl().add_to(m)
                except Exception as e:
                    st.warning(f"Could not load uploaded GeoJSON: {e}")

            # عرض الخريطة
            st.components.v1.html(m.get_root().render(), height=600)

            # معلومات بيانات الرياح
            if wind_data:
                drift_speed = wind_data["speed"] * 0.03
                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    st.metric(t("wind_speed"), f"{wind_data['speed']:.1f} {t('wind_unit_ms')}")
                with col_w2:
                    st.metric(t("drift_speed"), f"{drift_speed:.2f} {t('drift_unit')}")

        # ---- التبويب الثاني: الإحصائيات ----
        with tab_stats:
            st.subheader(t("results"))

            # بطاقات الإحصاءات الرئيسية
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    t("total_spills"),
                    f"{stats['num_spills']}",
                )

            with col2:
                st.metric(
                    t("total_area"),
                    f"{stats['total_area']:.2f} {t('unit_km2')}",
                )

            with col3:
                st.metric(
                    t("max_area"),
                    f"{stats['max_area']:.3f} {t('unit_km2')}",
                )

            with col4:
                st.metric(
                    t("avg_area"),
                    f"{stats['avg_area']:.3f} {t('unit_km2')}",
                )

            st.markdown("---")

            # معلومات إضافية
            col_info1, col_info2 = st.columns(2)

            with col_info1:
                st.info(f"📷 {t('num_images')}: {stats['num_images']}")
                st.info(
                    f"📅 {t('image_dates')}: "
                    f"{results['start_date']} → {results['end_date']}"
                )

            with col_info2:
                st.info(f"🧹 {t('cleaning_mask')}")
                st.info(f"🔬 {t('using_water_mask')}")

            # رسم بياني لتوزيع مساحات البقع
            if stats["spill_areas"] and len(stats["spill_areas"]) > 0:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                import matplotlib.font_manager as fm

                # إعداد الخطوط لدعم العربية
                fm.fontManager.addfont("/usr/share/fonts/truetype/chinese/NotoSansSC[wght].ttf")
                fm.fontManager.addfont("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

                plt.rcParams["font.sans-serif"] = ["Noto Sans SC", "DejaVu Sans"]
                plt.rcParams["axes.unicode_minus"] = False

                fig, ax = plt.subplots(figsize=(10, 5))

                areas = sorted(stats["spill_areas"], reverse=True)
                colors = ["#e74c3c" if a > stats["avg_area"] * 2 else "#3498db" for a in areas]

                x_labels = [
                    f"#{i+1}" for i in range(len(areas))
                ]

                bars = ax.bar(
                    x_labels,
                    areas,
                    color=colors,
                    edgecolor="white",
                    linewidth=0.5,
                )

                # إضافة قيم على الأعمدة
                for bar, area in zip(bars, areas):
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + max(areas) * 0.01,
                        f"{area:.2f}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                    )

                title_text = "Spill Area Distribution" if lang == "en" else "توزيع مساحات البقع"
                ax.set_title(title_text, fontsize=14, fontweight="bold")
                xlabel_text = "Spill ID" if lang == "en" else "رقم البقعة"
                ylabel_text = "Area (km²)" if lang == "en" else "المساحة (كم²)"
                ax.set_xlabel(xlabel_text, fontsize=11)
                ax.set_ylabel(ylabel_text, fontsize=11)
                ax.grid(axis="y", alpha=0.3)

                plt.tight_layout()
                st.pyplot(fig)

                # رسم دائري لنسب المساحات
                if len(areas) > 1:
                    fig2, ax2 = plt.subplots(figsize=(8, 6))
                    pie_title = "Area Distribution" if lang == "en" else "توزيع المساحات النسبي"
                    ax2.pie(
                        areas,
                        labels=x_labels,
                        autopct="%1.1f%%",
                        colors=colors,
                        startangle=90,
                    )
                    ax2.set_title(pie_title, fontsize=14, fontweight="bold")
                    plt.tight_layout()
                    st.pyplot(fig2)

        # ---- التبويب الثالث: التصدير والتنزيل ----
        with tab_export:
            st.subheader(t("tab_settings"))

            col_e1, col_e2, col_e3 = st.columns(3)

            with col_e1:
                # تنزيل PNG
                if st.button(f"🖼️ {t('download_png')}"):
                    png_data = download_map_as_png(m)
                    if png_data:
                        st.download_button(
                            label="Download PNG",
                            data=png_data,
                            file_name=f"oil_spill_map_{start_date}.png",
                            mime="image/png",
                        )

            with col_e2:
                # تنزيل GeoTIFF
                try:
                    import ee
                    if results.get("spill_vis"):
                        with st.spinner("Generating GeoTIFF URL..."):
                            try:
                                download_url = results["spill_vis"].getDownloadURL(
                                    {
                                        "name": "oil_spill_mask",
                                        "scale": 20,
                                        "crs": "EPSG:4326",
                                        "region": json.dumps(
                                            ee.Geometry.Rectangle(results["aoi_bbox"]).getInfo()
                                        ),
                                    }
                                )
                                st.markdown(
                                    f"### [📥 {t('download_geotiff')}]({download_url})"
                                )
                            except Exception:
                                st.info(t("error_export"))
                except Exception as e:
                    st.warning(f"GeoTIFF export: {e}")

            with col_e3:
                # تصدير GeoJSON
                try:
                    import ee
                    if results.get("vectors"):
                        with st.spinner("Generating GeoJSON..."):
                            try:
                                geojson_url = results["vectors"].getDownloadURL(
                                    filetype="csv"
                                )
                                st.markdown(
                                    f"### [📥 {t('download_geojson')}]({geojson_url})"
                                )
                            except Exception:
                                st.info(t("error_export"))
                except Exception as e:
                    st.warning(f"GeoJSON export: {e}")

            st.markdown("---")

            # تصدير إلى Google Drive
            st.subheader(t("export_drive"))
            if st.button(f"☁️ {t('export_drive')}"):
                try:
                    import ee
                    task_id = export_to_drive(
                        image=results["spill_vis"],
                        description=f"oil_spill_{start_date}_{end_date}",
                        region=json.dumps(
                            ee.Geometry.Rectangle(results["aoi_bbox"]).getInfo()
                        ),
                    )
                    if task_id:
                        st.success(
                            f"✅ Task {task_id} started! "
                            f"Check your Google Drive 'oil_spill_monitor' folder."
                        )
                    else:
                        st.error(t("error_export"))
                except Exception as e:
                    st.error(f"Export error: {e}")

            st.info(t("polygonization_note"))

        # ---- معلومات عن المنصة ----
        with st.expander(f"ℹ️ {t('about_title')}"):
            st.write(t("about_text"))


# ===================== نقطة الدخول =====================
if __name__ == "__main__":
    main()

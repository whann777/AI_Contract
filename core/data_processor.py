"""
Data Preprocessor - Extracted from AI_Contract_V2.ipynb Cell 5
Preserves 100% of original logic for AP/AR data cleaning
"""

import pandas as pd
import numpy as np


class DataPreprocessor:
    """ทำความสะอาดและเตรียมข้อมูล AP และ AR"""

    @staticmethod
    def clean_amount(value):
        """ทำความสะอาดตัวเลขจำนวนเงิน"""
        if pd.isna(value) or value == '' or value is None:
            return 0.0

        # แปลงเป็น string และลบ comma, space
        value_str = str(value).strip().replace(',', '').replace(' ', '')

        # ลบเครื่องหมาย () ที่บ่งบอกเลขติดลบ
        is_negative = False
        if value_str.startswith('(') and value_str.endswith(')'):
            is_negative = True
            value_str = value_str[1:-1]

        # ลบเครื่องหมายสกุลเงิน
        value_str = value_str.replace('฿', '').replace('$', '').replace('THB', '')

        try:
            result = float(value_str)
            return -result if is_negative else result
        except:
            return 0.0

    @staticmethod
    def prepare_ap_data(df: pd.DataFrame) -> pd.DataFrame:
        """เตรียมข้อมูล AP (Purchase/Account Payable)"""
        print("\n🔧 กำลังเตรียมข้อมูล AP (ยอดซื้อ)...")

        df = df.copy()
        
        # 🔥 FIX: ลบ spaces ใน column names
        df.columns = df.columns.str.strip()
        print(f"\n✅ Cleaned column names (removed spaces)")

        # Debug: แสดง columns ทั้งหมด
        print(f"\n📋 Columns ใน AP CSV: {df.columns.tolist()}")
        print(f"\n📊 ตัวอย่างข้อมูล 2 แถวแรก:")
        print(df.head(2))

        # Clean amount columns
        if 'INVPAYAMT' in df.columns:
            df['INVPAYAMT'] = df['INVPAYAMT'].apply(DataPreprocessor.clean_amount)
        if 'INV_AMOUNT' in df.columns:
            df['INV_AMOUNT'] = df['INV_AMOUNT'].apply(DataPreprocessor.clean_amount)

        # ทำความสะอาด vendor code
        if 'VndCode' in df.columns:
            df['VndCode'] = df['VndCode'].astype(str).str.replace('.0', '').str.strip()

        # ลบ columns เก่าที่อาจจะชนกัน
        columns_to_drop = ['DIV_CODE', 'DEPT_CODE_FINAL', 'DEPT_CODE_STR']
        for col in columns_to_drop:
            if col in df.columns:
                df = df.drop(columns=[col])
                print(f"   🗑️  ลบ column เก่า: {col}")

        # สำหรับ AP: ใช้ DEPT_CODE (4 digit) เท่านั้น!
        if 'DEPT_CODE' in df.columns:
            print(f"\n   ✅ พบ DEPT_CODE - กำลังแปลง...")

            # เก็บค่า DEPT_CODE ต้นฉบับไว้
            df['DEPT_CODE_ORIGINAL'] = df['DEPT_CODE'].astype(str)

            # แปลง DEPT_CODE เป็น 4 หลัก
            df['DEPT_CODE_STR'] = df['DEPT_CODE'].astype(str).str.zfill(4)

            # แยก Division (2 หลักแรก) และ Department (2 หลักหลัง)
            df['DIV_CODE'] = df['DEPT_CODE_STR'].str[:2]
            df['DEPT_CODE_FINAL'] = df['DEPT_CODE_STR'].str[2:]

            print(f"   ตัวอย่างการแปลง:")
            sample = df[['DEPT_CODE_ORIGINAL', 'DEPT_CODE_STR', 'DIV_CODE', 'DEPT_CODE_FINAL']].head(3)
            for _, row in sample.iterrows():
                print(f"      {row['DEPT_CODE_ORIGINAL']} → {row['DEPT_CODE_STR']} → DIV={row['DIV_CODE']}, DEPT={row['DEPT_CODE_FINAL']}")
        else:
            print(f"\n   ❌ ไม่พบ column DEPT_CODE!")
            print(f"   💡 Columns ที่มี: {df.columns.tolist()}")
            return df

        # สร้าง composite key สำหรับ matching
        df['VENDOR_KEY'] = df['VndCode'].astype(str)
        df['TTA_MATCH_KEY'] = (df['VndCode'].astype(str) + '_' +
                               df['DIV_CODE'] + '_' +
                               df['DEPT_CODE_FINAL'])

        # แปลง Year
        if 'INV_YEAR' in df.columns:
            df['YEAR'] = df['INV_YEAR'].astype(int)

        print(f"\n✅ เตรียมข้อมูล AP เสร็จสิ้น: {len(df)} รายการ")
        print(f"   📊 ยอดซื้อรวม: {df['INVPAYAMT'].sum():,.2f} บาท")

        # แสดงตัวอย่าง key ที่สร้าง
        print(f"\n   🔑 ตัวอย่าง TTA_MATCH_KEY ที่สร้างได้:")
        sample = df[['VndCode', 'DEPT_CODE_ORIGINAL', 'DIV_CODE', 'DEPT_CODE_FINAL', 'TTA_MATCH_KEY']].head(5)
        for idx, row in sample.iterrows():
            print(f"      [{idx}] VndCode={row['VndCode']}, DEPT_CODE={row['DEPT_CODE_ORIGINAL']} → Key={row['TTA_MATCH_KEY']}")

        return df

    @staticmethod
    def prepare_ar_data(df: pd.DataFrame) -> pd.DataFrame:
        """เตรียมข้อมูล AR (Account Receivable)"""
        print("\n🔧 กำลังเตรียมข้อมูล AR (ยอดที่เรียกเก็บ)...")

        df = df.copy()
        
        # 🔥 FIX: ลบ spaces ใน column names
        df.columns = df.columns.str.strip()
        print(f"\n✅ Cleaned column names (removed spaces)")

        # Clean amount column
        if 'EXTENDED_AMOUNT' in df.columns:
            df['EXTENDED_AMOUNT'] = df['EXTENDED_AMOUNT'].apply(DataPreprocessor.clean_amount)

        # ทำความสะอาด supplier code
        if 'SUP_CODE' in df.columns:
            df['SUP_CODE'] = df['SUP_CODE'].astype(str).str.replace('.0', '').str.strip()

        # แปลง DPTNBR (4 digit) เป็น Division และ Department
        if 'DPTNBR' in df.columns:
            df['DPTNBR_STR'] = df['DPTNBR'].astype(str).str.replace('.0', '').str.zfill(4)
            df['DIV_CODE'] = df['DPTNBR_STR'].str[:2]
            df['DEPT_CODE'] = df['DPTNBR_STR'].str[2:]

        # สร้าง composite key
        df['VENDOR_KEY'] = df['SUP_CODE'].astype(str)
        df['TTA_MATCH_KEY'] = (df['SUP_CODE'].astype(str) + '_' +
                               df['DIV_CODE'] + '_' +
                               df['DEPT_CODE'])

        # ทำความสะอาด REF_TYPE สำหรับ matching
        if 'REF_TYPE' in df.columns:
            df['REF_TYPE_CLEAN'] = df['REF_TYPE'].str.upper().str.strip()
            print(f"   ✅ พบ REF_TYPE - จะใช้ในการ match category")
            print(f"   📋 REF_TYPE ที่พบ: {df['REF_TYPE_CLEAN'].unique()[:10].tolist()}")
        else:
            print(f"   ⚠️  ไม่พบ REF_TYPE - จะใช้ DESCRIPTION แทน")
            df['REF_TYPE_CLEAN'] = ''

        # ทำความสะอาด description (backup)
        if 'DESCRIPTION' in df.columns:
            df['DESCRIPTION_CLEAN'] = df['DESCRIPTION'].str.upper().str.strip()

        # แปลง Year
        if 'Year' in df.columns:
            df['YEAR'] = df['Year'].fillna(0).astype(int)

        print(f"✅ เตรียมข้อมูล AR เสร็จสิ้น: {len(df)} รายการ")
        print(f"   📊 ยอดเรียกเก็บรวม: {df['EXTENDED_AMOUNT'].sum():,.2f} บาท")

        # แสดงตัวอย่าง key ที่สร้าง
        print(f"\n   🔑 ตัวอย่าง TTA_MATCH_KEY:")
        for key in df['TTA_MATCH_KEY'].head(5).tolist():
            print(f"      - {key}")

        return df

"""
TTAReconciliationSystem - Extracted from AI_Contract_V2.ipynb Cell 6
ระบบหลักสำหรับการเปรียบเทียบและตรวจสอบ
เก็บ Logic 100% จาก Notebook
"""

import os
import json
import glob
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path

from .data_processor import DataPreprocessor
from config.categories import ALLOWANCE_CATEGORIES


class TTAReconciliationSystem:
    """
    ระบบหลักสำหรับการ reconcile ข้อมูล TTA, AP, และ AR
    
    This class is PRESERVED from the original notebook.
    """
    
    def __init__(self, base_folder: str = None):
        """Initialize reconciliation system"""
        if base_folder is None:
            from config.settings import DATA_DIR
            self.base_folder = str(DATA_DIR)
        else:
            self.base_folder = base_folder
            
        self.tta_data = {}
        self.ap_data = None
        self.ar_data = None
        self.calculated_allowances = None
        self.reconciliation_result = None

        print(f"✅ ระบบพร้อมใช้งาน - โฟลเดอร์: {self.base_folder}")

    def load_tta_summaries(self, folder_path: str = None) -> bool:
        """โหลดไฟล์ JSON TTA อัตโนมัติจากโฟลเดอร์"""
        if folder_path is None:
            folder_path = os.path.join(self.base_folder, 'tta_summaries')

        # ค้นหาไฟล์ JSON ใน directory และ subdirectories
        json_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('_summary.json'):
                    json_files.append(os.path.join(root, file))

        if not json_files:
            print(f"❌ ไม่พบไฟล์ JSON ใน {folder_path}")
            print(f"💡 กรุณาอัพโหลดไฟล์ *_summary.json")
            return False

        print(f"\n📂 พบไฟล์ JSON TTA จำนวน {len(json_files)} ไฟล์")
        print("="*60)

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    vendor_code = str(data.get('vendor_code', '')).strip()
                    div_code = str(data.get('Division_code', '')).strip().zfill(2)
                    dept_code = str(data.get('Department_code', '')).strip().zfill(2)

                    if vendor_code and 'error' not in data:
                        key = f"{vendor_code}_{div_code}_{dept_code}"
                        self.tta_data[key] = data
                        print(f"✅ {key}: {data.get('Division_name', '')} - {data.get('Department_name', '')}")
            except Exception as e:
                print(f"⚠️  Error loading {os.path.basename(json_file)}: {e}")

        print(f"\n📊 โหลด TTA สำเร็จ: {len(self.tta_data)} รายการ")
        return len(self.tta_data) > 0

    def load_ap_data(self, file_path: str = None) -> bool:
        """โหลดข้อมูล AP อัตโนมัติ"""
        if file_path is None:
            # ค้นหาไฟล์ AP ในโฟลเดอร์
            ap_folder = os.path.join(self.base_folder, 'ap')
            search_patterns = [
                "Account_Payable*.csv",
                "Purchase*.csv",
                "AP*.csv",
                "*payable*.csv"
            ]

            for pattern in search_patterns:
                files_found = glob.glob(os.path.join(ap_folder, pattern))
                if files_found:
                    file_path = files_found[0]
                    break

            if file_path is None:
                print("❌ ไม่พบไฟล์ AP")
                print("💡 กรุณาอัพโหลดไฟล์ CSV ยอดซื้อ")
                return False

        print(f"\n📁 โหลดข้อมูล AP จาก: {os.path.basename(file_path)}")

        try:
            # ลองอ่านด้วย encoding ต่างๆ
            for encoding in ['utf-8', 'tis-620', 'cp874', 'latin1']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    self.ap_data = DataPreprocessor.prepare_ap_data(df)

                    print(f"\n📊 สรุปข้อมูล AP:")
                    summary = self.ap_data.groupby(['VndCode', 'VNDNAME', 'DIV_CODE', 'DEPT_CODE_FINAL']).agg({
                        'INVPAYAMT': 'sum',
                        'YEAR': 'first'
                    }).reset_index()
                    print(summary.to_string(index=False))

                    return True
                except UnicodeDecodeError:
                    continue

            print("❌ ไม่สามารถอ่านไฟล์ได้")
            return False

        except Exception as e:
            print(f"❌ Error loading AP: {e}")
            return False

    def load_ar_data(self, file_path: str = None) -> bool:
        """โหลดข้อมูล AR อัตโนมัติ"""
        if file_path is None:
            # ค้นหาไฟล์ AR ในโฟลเดอร์
            ar_folder = os.path.join(self.base_folder, 'ar')
            search_patterns = [
                "Account_Receiveable*.csv",
                "AR_Detail*.csv",
                "AR*.csv",
                "*receivable*.csv"
            ]

            for pattern in search_patterns:
                files_found = glob.glob(os.path.join(ar_folder, pattern))
                if files_found:
                    file_path = files_found[0]
                    break

            if file_path is None:
                print("❌ ไม่พบไฟล์ AR")
                print("💡 กรุณาอัพโหลดไฟล์ CSV ยอดที่เรียกเก็บ")
                return False

        print(f"\n📁 โหลดข้อมูล AR จาก: {os.path.basename(file_path)}")

        try:
            # ลองอ่านด้วย encoding ต่างๆ
            for encoding in ['utf-8', 'tis-620', 'cp874', 'latin1']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    self.ar_data = DataPreprocessor.prepare_ar_data(df)

                    print(f"\n📊 สรุปข้อมูล AR:")
                    summary = self.ar_data.groupby(['SUP_CODE', 'CUSTNAME', 'DIV_CODE', 'DEPT_CODE']).agg({
                        'EXTENDED_AMOUNT': 'sum',
                        'YEAR': 'first'
                    }).reset_index()
                    print(summary.to_string(index=False))

                    return True
                except UnicodeDecodeError:
                    continue

            print("❌ ไม่สามารถอ่านไฟล์ได้")
            return False

        except Exception as e:
            print(f"❌ Error loading AR: {e}")
            return False

    def validate_ar_with_llm(self, analyzer_instance):
        """ใช้ LLM ตรวจสอบและแก้ไข REF_TYPE ของ AR จาก Description"""
        if self.ar_data is None:
            print("❌ ไม่พบข้อมูล AR")
            return

        print("\n" + "="*80)
        print("🧠 LLM กำลังตรวจสอบความถูกต้องของ REF_TYPE จาก Description...")
        print("="*80)

        # ตรวจสอบว่ามี column DESC3 หรือไม่
        desc_col = 'DESC3' if 'DESC3' in self.ar_data.columns else 'DESCRIPTION_CLEAN'
        
        if desc_col not in self.ar_data.columns:
            print("⚠️  ไม่พบ column สำหรับ description - ข้าม validation")
            return

        # 1. ดึงรายการ REF_TYPE และ Description ที่ไม่ซ้ำกันมาวิเคราะห์
        unique_combinations = self.ar_data[['REF_TYPE_CLEAN', desc_col]].drop_duplicates()

        validation_prompt = f"""
        คุณคือผู้เชี่ยวชาญด้านบัญชีและการตรวจสอบสัญญาการค้า (Trade Term Audit)
        ทำหน้าที่ตรวจสอบว่า 'ref_type' (รหัสประเภท) ตรงกับคำอธิบายหรือไม่

        กฎการจัดกลุ่ม (Mapping Rules):
        - หากคำอธิบายระบุถึง 'Step Rebate' -> ต้องเป็น 'CRB'
        - หากคำอธิบายระบุถึง 'Leaflet', 'Magazine', 'Brochure', 'ลงสื่อ' -> ต้องเป็น 'BRO'
        - หากคำอธิบายระบุถึง 'เปิดสาขาใหม่', 'Grand Opening' -> ต้องเป็น 'NST'
        - หากคำอธิบายระบุถึง 'Anniversary', 'ครบรอบ' -> ต้องเป็น 'ANI'

        รายการ Category Code ที่อนุญาต:
        {list(ALLOWANCE_CATEGORIES.keys())}

        **สำคัญ**:
        - หากตรงกัน ใช้ค่าเดิม
        - หากไม่ตรง เลือก Category Code ที่ใกล้เคียงที่สุด
        - ตอบ JSON List: [{{"original_ref": "...", "description": "...", "corrected_ref": "..."}}]
        """

        # 2. ส่งข้อมูลให้ LLM วิเคราะห์
        batch_data = unique_combinations.head(50).to_dict('records')  # จำกัดไม่เกิน 50 รายการ
        try:
            response = analyzer_instance.model.generate_content(
                f"{validation_prompt}\n\nData to validate:\n{json.dumps(batch_data, ensure_ascii=False)}",
                generation_config={"response_mime_type": "application/json", "temperature": 0}
            )

            # 3. นำผลลัพธ์มา Update
            corrections = json.loads(response.text)
            correction_count = 0
            
            for correction in corrections:
                original_ref = correction.get('original_ref', '')
                corrected_ref = correction.get('corrected_ref', '')
                
                if original_ref != corrected_ref and corrected_ref:
                    mask = self.ar_data['REF_TYPE_CLEAN'] == original_ref
                    self.ar_data.loc[mask, 'REF_TYPE_CLEAN'] = corrected_ref
                    correction_count += 1

            print(f"✅ ตรวจสอบเสร็จสิ้น: ปรับปรุง REF_TYPE ไปทั้งหมด {correction_count} รายการ")

        except Exception as e:
            print(f"⚠️ เกิดข้อผิดพลาดในการตรวจสอบด้วย LLM: {e}")

    def calculate_allowances(self) -> Optional[pd.DataFrame]:
        """คำนวณ allowance ที่ควรได้"""
        if self.ap_data is None or not self.tta_data:
            print("❌ กรุณาโหลดข้อมูล AP และ TTA ก่อน")
            return None

        print("\n" + "="*80)
        print("🧮 คำนวณ Allowances ที่ควรได้")
        print("="*80)

        # Debug
        print(f"\n🔍 Debug Information:")
        print(f"   จำนวน TTA keys: {len(self.tta_data)}")
        print(f"   TTA keys ที่มี: {list(self.tta_data.keys())[:5]}")
        print(f"\n   จำนวนแถว AP: {len(self.ap_data)}")
        if len(self.ap_data) > 0:
            print(f"   AP TTA_MATCH_KEY ตัวอย่าง: {self.ap_data['TTA_MATCH_KEY'].head().tolist()}")

        results = []
        matched_count = 0
        unmatched_vendors = []

        for idx, row in self.ap_data.iterrows():
            tta_key = row['TTA_MATCH_KEY']
            vendor_code = row['VndCode']
            vendor_name = row['VNDNAME']
            div_code = row['DIV_CODE']
            dept_code = row['DEPT_CODE_FINAL']
            purchase_amount = row['INVPAYAMT']
            year = row.get('YEAR', 2023)

            if tta_key not in self.tta_data:
                unmatched_vendors.append(f"{tta_key} ({vendor_name})")
                continue

            matched_count += 1
            tta = self.tta_data[tta_key]
            allowances = tta.get('allowances', [])

            print(f"\n📦 {tta_key} - {vendor_name}")
            print(f"   💰 ยอดซื้อ: {purchase_amount:,.2f} บาท (ปี {year})")

            if not allowances:
                print(f"   ⚠️  ไม่มีข้อมูล allowance ใน TTA")
                continue

            for allowance in allowances:
                category_code = allowance.get('category_code')
                category_name = allowance.get('category_name')
                rate_percent = allowance.get('rate_percent')
                fix_amount = allowance.get('fix_amount')
                description = allowance.get('description', '')
                payment_terms = allowance.get('payment_terms', '')

                calculated_amount = 0
                calculation_type = ''

                if rate_percent is not None and rate_percent > 0:
                    calculated_amount = purchase_amount * (float(rate_percent) / 100)
                    calculation_type = f'{rate_percent}%'
                    print(f"   ✓ {category_code}: {calculated_amount:,.2f} ({rate_percent}%)")
                elif fix_amount is not None and fix_amount > 0:
                    calculated_amount = float(fix_amount)
                    calculation_type = 'Fix Amount'
                    print(f"   ✓ {category_code}: {calculated_amount:,.2f} (Fixed)")
                else:
                    print(f"   ⚠️  {category_code}: ไม่มี rate หรือ fix amount")
                    continue

                results.append({
                    'vendor_code': vendor_code,
                    'vendor_name': vendor_name,
                    'division': div_code,
                    'department': dept_code,
                    'tta_key': tta_key,
                    'year': year,
                    'purchase_amount': purchase_amount,
                    'category_code': category_code,
                    'category_name': category_name,
                    'rate_percent': rate_percent,
                    'fix_amount': fix_amount,
                    'calculated_amount': calculated_amount,
                    'calculation_type': calculation_type,
                    'description': description,
                    'payment_terms': payment_terms
                })

        # แสดงรายการที่ไม่ match
        if unmatched_vendors:
            print(f"\n⚠️  Vendors ที่ไม่พบข้อมูล TTA ({len(unmatched_vendors)} รายการ):")
            for vendor in unmatched_vendors[:10]:
                print(f"   - {vendor}")
            if len(unmatched_vendors) > 10:
                print(f"   ... และอีก {len(unmatched_vendors) - 10} รายการ")

        # สร้าง DataFrame
        if results:
            self.calculated_allowances = pd.DataFrame(results)
            total_amount = self.calculated_allowances['calculated_amount'].sum()
        else:
            self.calculated_allowances = pd.DataFrame()
            total_amount = 0

        print(f"\n{'='*80}")
        print(f"✅ คำนวณเสร็จสิ้น:")
        print(f"   📊 จำนวนรายการ: {len(results)}")
        print(f"   🔗 Vendors ที่ match: {matched_count}/{len(self.ap_data)}")
        if total_amount > 0:
            print(f"   💵 ยอดรวมที่ควรเรียกเก็บ: {total_amount:,.2f} บาท")
        print(f"{'='*80}")

        return self.calculated_allowances if len(results) > 0 else None

    def reconcile_with_ar(self) -> Optional[pd.DataFrame]:
        """เปรียบเทียบกับ AR โดยใช้ REF_TYPE"""
        if self.calculated_allowances is None or self.ar_data is None:
            print("❌ กรุณาคำนวณ allowance และโหลด AR ก่อน")
            return None

        print("\n" + "="*80)
        print("🔍 เปรียบเทียบกับยอดที่เรียกเก็บจริง (ใช้ REF_TYPE)")
        print("="*80)

        reconciliation_results = []

        for tta_key, group in self.calculated_allowances.groupby('tta_key'):
            vendor_code = group['vendor_code'].iloc[0]
            vendor_name = group['vendor_name'].iloc[0]

            print(f"\n{'='*60}")
            print(f"📊 {tta_key} - {vendor_name}")
            print(f"{'='*60}")

            # Debug: ดูว่ามี AR ของ vendor นี้หรือไม่
            ar_for_vendor = self.ar_data[self.ar_data['TTA_MATCH_KEY'] == tta_key]
            print(f"\n🔍 Debug AR for {tta_key}:")
            print(f"   จำนวน AR records: {len(ar_for_vendor)}")

            if len(ar_for_vendor) > 0:
                print(f"   ตัวอย่าง REF_TYPE ใน AR:")
                ref_types = ar_for_vendor['REF_TYPE_CLEAN'].value_counts()
                for ref_type, count in ref_types.head(10).items():
                    amount = ar_for_vendor[ar_for_vendor['REF_TYPE_CLEAN'] == ref_type]['EXTENDED_AMOUNT'].sum()
                    print(f"      - {ref_type}: {count} รายการ, ยอดรวม {amount:,.2f}")
            else:
                print(f"   ⚠️  ไม่พบ AR records สำหรับ key นี้")

            total_should = 0
            total_actual = 0

            for _, calc_row in group.iterrows():
                category_code = calc_row['category_code']
                category_name = calc_row['category_name']
                should_collect = calc_row['calculated_amount']

                # Match AR โดยใช้ REF_TYPE
                ar_match = self.ar_data[
                    (self.ar_data['TTA_MATCH_KEY'] == tta_key) &
                    (self.ar_data['REF_TYPE_CLEAN'] == category_code)
                ]

                actually_collected = ar_match['EXTENDED_AMOUNT'].sum() if not ar_match.empty else 0

                # Debug
                print(f"\n  🔎 {category_code} - {category_name}")
                if not ar_match.empty:
                    print(f"     ✅ พบ {len(ar_match)} รายการที่ REF_TYPE = {category_code}")
                    print(f"     💰 ยอดรวม: {actually_collected:,.2f}")
                else:
                    print(f"     ❌ ไม่พบ AR ที่ REF_TYPE = {category_code}")

                difference = actually_collected - should_collect

                if abs(difference) < 1:
                    status = '✅ ครบ'
                elif difference > 0:
                    status = '⚠️ เกิน'
                else:
                    status = '❌ ขาด'

                print(f"    ควรเรียกเก็บ:    {should_collect:>15,.2f} บาท")
                print(f"    เรียกเก็บจริง:    {actually_collected:>15,.2f} บาท")
                print(f"    ส่วนต่าง:         {difference:>15,.2f} บาท {status}")

                total_should += should_collect
                total_actual += actually_collected

                reconciliation_results.append({
                    'tta_key': tta_key,
                    'vendor_code': vendor_code,
                    'vendor_name': vendor_name,
                    'category_code': category_code,
                    'category_name': category_name,
                    'should_collect': should_collect,
                    'actually_collected': actually_collected,
                    'difference': difference,
                    'status': status,
                    'variance_pct': (difference / should_collect * 100) if should_collect > 0 else 0
                })

            total_diff = total_actual - total_should
            if abs(total_diff) < 1:
                vendor_status = '✅ เก็บครบแล้ว'
            elif total_diff > 0:
                vendor_status = '⚠️ เก็บเกิน'
            else:
                vendor_status = '❌ ยังเก็บไม่ครบ'

            print(f"\n  {'─'*58}")
            print(f"  📈 สรุปรวม:")
            print(f"    ควรเรียกเก็บทั้งหมด:   {total_should:>15,.2f} บาท")
            print(f"    เรียกเก็บจริงทั้งหมด:   {total_actual:>15,.2f} บาท")
            print(f"    ส่วนต่างรวม:            {total_diff:>15,.2f} บาท")
            print(f"    สถานะ: {vendor_status}")

        self.reconciliation_result = pd.DataFrame(reconciliation_results)

        print(f"\n{'='*80}")
        print(f"✅ เปรียบเทียบเสร็จสิ้น")
        print(f"{'='*80}")

        return self.reconciliation_result

    def generate_summary_report(self) -> Optional[pd.DataFrame]:
        """สร้างรายงานสรุป"""
        if self.reconciliation_result is None:
            return None

        summary = self.reconciliation_result.groupby(['vendor_code', 'vendor_name']).agg({
            'should_collect': 'sum',
            'actually_collected': 'sum',
            'difference': 'sum'
        }).reset_index()

        summary['status'] = summary['difference'].apply(
            lambda x: '✅ ครบ' if abs(x) < 1 else ('⚠️ เกิน' if x > 0 else '❌ ขาด')
        )

        summary['variance_pct'] = (
            summary['difference'] / summary['should_collect'] * 100
        ).round(2)

        return summary

    def export_results(self, output_folder: str = None) -> Optional[str]:
        """Export ผลลัพธ์เป็น Excel"""
        if output_folder is None:
            output_folder = os.path.join(self.base_folder, 'results')
            
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        os.makedirs(output_folder, exist_ok=True)

        try:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(output_folder, f"TTA_Reconciliation_{timestamp}.xlsx")

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                if self.calculated_allowances is not None:
                    self.calculated_allowances.to_excel(writer, sheet_name='Calculated', index=False)

                if self.reconciliation_result is not None:
                    self.reconciliation_result.to_excel(writer, sheet_name='Reconciliation', index=False)

                summary = self.generate_summary_report()
                if summary is not None:
                    summary.to_excel(writer, sheet_name='Summary', index=False)

            print(f"\n✅ Export สำเร็จ: {os.path.basename(filename)}")
            return filename
        except Exception as e:
            print(f"❌ Error exporting: {e}")
            return None

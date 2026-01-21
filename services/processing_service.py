"""
Processing Service - จัดการ workflow สำหรับส่วนที่ 1 (For Analyze)
ประสานงานระหว่าง AI analyzer, data processor, และ reconciliation system
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd

from core.ai_analyzer import TTADocumentAnalyzer
from core.reconciliation import TTAReconciliationSystem
from config.settings import DIRECTORIES


class ProcessingService:
    """
    Service สำหรับจัดการกระบวนการประมวลผลทั้งหมดของส่วนที่ 1
    """
    
    def __init__(self, api_key: str, base_folder: str = None):
        """
        Initialize processing service
        
        Args:
            api_key: Gemini API key
            base_folder: Base directory for data (default from config)
        """
        self.api_key = api_key
        self.base_folder = base_folder or str(DIRECTORIES['agreements'].parent)
        
        # Initialize components
        self.analyzer = TTADocumentAnalyzer(api_key)
        self.recon_system = TTAReconciliationSystem(self.base_folder)
        
        # Processing state
        self.processed_pdfs = []
        self.failed_pdfs = []
        self.results = None
        
    def process_contracts(
        self, 
        pdf_files: List[str], 
        show_images: bool = False,
        delay_seconds: int = 30,
        progress_callback=None
    ) -> Tuple[int, int]:
        """
        ประมวลผลสัญญา PDF ทั้งหมด
        
        Args:
            pdf_files: List ของ path ไฟล์ PDF
            show_images: แสดงภาพ PDF หรือไม่
            delay_seconds: หน่วงเวลาระหว่างไฟล์ (เพื่อ API quota)
            progress_callback: Function สำหรับ update progress (optional)
            
        Returns:
            (success_count, fail_count)
        """
        print("\n" + "="*80)
        print("📄 เริ่มประมวลผลสัญญา PDF")
        print("="*80)
        print(f"จำนวนไฟล์: {len(pdf_files)}")
        
        success_count = 0
        fail_count = 0
        
        for idx, pdf_path in enumerate(pdf_files, 1):
            try:
                print(f"\n{'='*50}")
                print(f"📂 ไฟล์ {idx}/{len(pdf_files)}: {os.path.basename(pdf_path)}")
                
                # Update progress if callback provided
                if progress_callback:
                    progress_callback(idx, len(pdf_files), os.path.basename(pdf_path))
                
                # Analyze document
                result = self.analyzer.analyze_document(pdf_path, show_images=show_images)
                
                # Check for errors
                if "error" in result:
                    print(f"❌ ล้มเหลว: {result['error']}")
                    self.failed_pdfs.append({
                        'file': os.path.basename(pdf_path),
                        'error': result['error']
                    })
                    fail_count += 1
                    continue
                
                # Display result
                print(self.analyzer.format_output(result))
                
                # Save JSON to tta_summaries folder
                vendor_code = result.get('vendor_code', 'unknown')
                div_code = str(result.get('Division_code', '00')).zfill(2)
                dept_code = str(result.get('Department_code', '00')).zfill(2)
                
                json_filename = f"{vendor_code}_{div_code}_{dept_code}_summary.json"
                json_path = os.path.join(
                    self.base_folder, 
                    'tta_summaries', 
                    json_filename
                )
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"💾 บันทึก: {json_filename}")
                
                self.processed_pdfs.append({
                    'file': os.path.basename(pdf_path),
                    'vendor_code': vendor_code,
                    'json_path': json_path
                })
                success_count += 1
                
                # Delay before next file (API quota management)
                if idx < len(pdf_files) and delay_seconds > 0:
                    print(f"\n⏳ หน่วงเวลา {delay_seconds} วินาที...")
                    time.sleep(delay_seconds)
                    
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาด: {e}")
                self.failed_pdfs.append({
                    'file': os.path.basename(pdf_path),
                    'error': str(e)
                })
                fail_count += 1
        
        print("\n" + "="*80)
        print("📊 สรุปการประมวลผล PDF")
        print("="*80)
        print(f"✅ สำเร็จ: {success_count} ไฟล์")
        print(f"❌ ล้มเหลว: {fail_count} ไฟล์")
        
        if self.failed_pdfs:
            print("\nไฟล์ที่ล้มเหลว:")
            for item in self.failed_pdfs:
                print(f"  - {item['file']}: {item['error']}")
        
        return success_count, fail_count
    
    def run_full_analysis(
        self,
        ap_file: str = None,
        ar_file: str = None,
        use_llm_validation: bool = True,
        progress_callback=None
    ) -> Optional[pd.DataFrame]:
        """
        รัน workflow ทั้งหมด: load data → calculate → reconcile
        
        Args:
            ap_file: Path to AP CSV file (optional, auto-detect if None)
            ar_file: Path to AR CSV file (optional, auto-detect if None)
            use_llm_validation: ใช้ LLM validate REF_TYPE หรือไม่
            progress_callback: Function for progress updates
            
        Returns:
            DataFrame ผลการเปรียบเทียบ หรือ None ถ้าล้มเหลว
        """
        print("\n" + "="*80)
        print("⚙️ เริ่มขั้นตอนการวิเคราะห์และเปรียบเทียบ")
        print("="*80)
        
        try:
            # Step 1: Load TTA summaries
            if progress_callback:
                progress_callback("กำลังโหลดข้อมูล TTA...")
            
            tta_loaded = self.recon_system.load_tta_summaries()
            if not tta_loaded:
                print("❌ ไม่สามารถโหลด TTA ได้")
                return None
            
            # Step 2: Load AP data
            if progress_callback:
                progress_callback("กำลังโหลดข้อมูล AP...")
            
            ap_loaded = self.recon_system.load_ap_data(ap_file)
            if not ap_loaded:
                print("❌ ไม่สามารถโหลด AP ได้")
                return None
            
            # Step 3: Load AR data
            if progress_callback:
                progress_callback("กำลังโหลดข้อมูล AR...")
            
            ar_loaded = self.recon_system.load_ar_data(ar_file)
            
            # Step 4: Calculate allowances
            if progress_callback:
                progress_callback("กำลังคำนวณ Allowances...")
            
            calculated = self.recon_system.calculate_allowances()
            if calculated is None:
                print("❌ ไม่สามารถคำนวณ Allowances ได้")
                return None
            
            # Step 5: Reconcile with AR (if available)
            if ar_loaded:
                # Optional: Validate AR with LLM
                if use_llm_validation:
                    if progress_callback:
                        progress_callback("กำลังตรวจสอบ AR ด้วย LLM...")
                    
                    self.recon_system.validate_ar_with_llm(self.analyzer)
                
                # Reconcile
                if progress_callback:
                    progress_callback("กำลังเปรียบเทียบกับ AR...")
                
                reconciliation = self.recon_system.reconcile_with_ar()
                
                # Generate summary
                summary = self.recon_system.generate_summary_report()
                if summary is not None:
                    print("\n📊 สรุปผลการเปรียบเทียบ:")
                    print(summary.to_string(index=False))
                
                self.results = reconciliation
                
            else:
                print("\n⚠️ ไม่มีข้อมูล AR - แสดงเฉพาะการคำนวณ Allowance")
                self.results = calculated
            
            # Step 6: Export results
            if progress_callback:
                progress_callback("กำลัง Export รายงาน...")
            
            output_file = self.recon_system.export_results()
            
            print("\n" + "="*80)
            print("✅ ดำเนินการเสร็จสมบูรณ์!")
            print("="*80)
            if output_file:
                print(f"📄 ไฟล์รายงาน: {output_file}")
            
            return self.results
            
        except Exception as e:
            print(f"\n❌ เกิดข้อผิดพลาด: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_processing_summary(self) -> Dict:
        """
        สรุปผลการประมวลผล
        
        Returns:
            Dict ข้อมูลสรุป
        """
        summary = {
            'pdfs_processed': len(self.processed_pdfs),
            'pdfs_failed': len(self.failed_pdfs),
            'has_results': self.results is not None,
        }
        
        if self.results is not None:
            summary['total_records'] = len(self.results)
            
            if 'should_collect' in self.results.columns:
                summary['total_should_collect'] = self.results['should_collect'].sum()
            
            if 'actually_collected' in self.results.columns:
                summary['total_actually_collected'] = self.results['actually_collected'].sum()
        
        return summary
    
    def save_session(self, session_name: str = None) -> str:
        """
        บันทึก session ใน st.session_state (ไม่ใช้ไฟล์)
        
        Args:
            session_name: ชื่อ session (optional)
            
        Returns:
            Session name
        """
        import streamlit as st
        
        if session_name is None:
            session_name = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        
        session_data = {
            'session_name': session_name,
            'timestamp': pd.Timestamp.now().isoformat(),
            'processed_pdfs': self.processed_pdfs,
            'failed_pdfs': self.failed_pdfs,
            'summary': self.get_processing_summary(),
            'results': self.results  # เก็บ DataFrame ใน memory!
        }
        
        # บันทึกใน session_state
        if 'saved_sessions' not in st.session_state:
            st.session_state.saved_sessions = {}
        
        st.session_state.saved_sessions[session_name] = session_data
        st.session_state.current_session = session_name
        
        print(f"\n💾 บันทึก session ใน memory: {session_name}")
        if self.results is not None:
            print(f"   📊 Results: {len(self.results)} รายการ")
        else:
            print(f"   ⚠️ ไม่มี results")
        
        return session_name

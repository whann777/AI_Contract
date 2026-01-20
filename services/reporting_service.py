"""
Reporting Service - จัดการการ export รายงานในรูปแบบต่างๆ
"""

import os
from pathlib import Path
from typing import Optional, List
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from config.settings import EXPORT_SETTINGS


class ReportingService:
    """
    Service สำหรับการ export รายงาน
    """
    
    def __init__(self, output_folder: str = None):
        """
        Initialize reporting service
        
        Args:
            output_folder: โฟลเดอร์สำหรับเก็บรายงาน
        """
        if output_folder is None:
            from config.settings import DIRECTORIES
            output_folder = str(DIRECTORIES['results'])
        
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
    
    def export_to_excel(
        self,
        data: pd.DataFrame,
        filename: str = None,
        sheet_name: str = 'Data',
        apply_formatting: bool = True
    ) -> str:
        """
        Export DataFrame เป็น Excel พร้อมการจัดรูปแบบ
        
        Args:
            data: DataFrame ที่จะ export
            filename: ชื่อไฟล์ (ถ้าไม่ระบุจะสร้างอัตโนมัติ)
            sheet_name: ชื่อ sheet
            apply_formatting: จัดรูปแบบหรือไม่
            
        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.xlsx"
        
        filepath = os.path.join(self.output_folder, filename)
        
        # Export basic Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            data.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Apply formatting if requested
        if apply_formatting:
            self._apply_excel_formatting(filepath, sheet_name)
        
        print(f"✅ Export Excel สำเร็จ: {filename}")
        return filepath
    
    def export_reconciliation_report(
        self,
        reconciliation_df: pd.DataFrame,
        calculated_df: Optional[pd.DataFrame] = None,
        summary_df: Optional[pd.DataFrame] = None,
        filename: str = None
    ) -> str:
        """
        Export รายงานการเปรียบเทียบแบบสมบูรณ์ (3 sheets)
        
        Args:
            reconciliation_df: ข้อมูลการเปรียบเทียบ
            calculated_df: ข้อมูลการคำนวณ (optional)
            summary_df: ข้อมูลสรุป (optional)
            filename: ชื่อไฟล์
            
        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            filename = f"TTA_Reconciliation_{timestamp}.xlsx"
        
        filepath = os.path.join(self.output_folder, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Sheet 1: Summary (ถ้ามี)
            if summary_df is not None:
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Sheet 2: Reconciliation
            reconciliation_df.to_excel(writer, sheet_name='Reconciliation', index=False)
            
            # Sheet 3: Calculated (ถ้ามี)
            if calculated_df is not None:
                calculated_df.to_excel(writer, sheet_name='Calculated', index=False)
        
        # Apply formatting to all sheets
        wb = load_workbook(filepath)
        for sheet_name in wb.sheetnames:
            self._format_sheet(wb[sheet_name])
        wb.save(filepath)
        
        print(f"✅ Export รายงานเปรียบเทียบสำเร็จ: {filename}")
        return filepath
    
    def export_to_csv(
        self,
        data: pd.DataFrame,
        filename: str = None,
        encoding: str = 'utf-8-sig'
    ) -> str:
        """
        Export DataFrame เป็น CSV
        
        Args:
            data: DataFrame ที่จะ export
            filename: ชื่อไฟล์
            encoding: การ encode (default: utf-8-sig สำหรับ Excel)
            
        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.csv"
        
        filepath = os.path.join(self.output_folder, filename)
        data.to_csv(filepath, index=False, encoding=encoding)
        
        print(f"✅ Export CSV สำเร็จ: {filename}")
        return filepath
    
    def _apply_excel_formatting(self, filepath: str, sheet_name: str):
        """
        จัดรูปแบบ Excel
        
        Args:
            filepath: Path ไฟล์ Excel
            sheet_name: ชื่อ sheet ที่จะจัดรูปแบบ
        """
        wb = load_workbook(filepath)
        if sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            self._format_sheet(ws)
            wb.save(filepath)
    
    def _format_sheet(self, ws):
        """
        จัดรูปแบบ worksheet
        
        Args:
            ws: Worksheet object
        """
        # Header formatting
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Border
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Format header row
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = thin_border
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)  # Max width 50
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Format data rows
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(vertical="center")
                
                # Format numbers
                if isinstance(cell.value, (int, float)):
                    cell.number_format = '#,##0.00'
        
        # Freeze header row
        ws.freeze_panes = 'A2'
    
    def create_comparison_chart(
        self,
        summary_df: pd.DataFrame,
        chart_type: str = 'bar'
    ) -> str:
        """
        สร้างกราฟเปรียบเทียบ (สำหรับอนาคต)
        
        Args:
            summary_df: ข้อมูลสรุป
            chart_type: ประเภทกราฟ
            
        Returns:
            Path to chart file
        """
        # TODO: Implement chart generation with matplotlib or plotly
        pass
    
    def export_filtered_data(
        self,
        data: pd.DataFrame,
        filters: dict,
        export_format: str = 'excel',
        filename: str = None
    ) -> str:
        """
        Export ข้อมูลที่กรองแล้ว
        
        Args:
            data: DataFrame ต้นฉบับ
            filters: Dictionary ของเงื่อนไขการกรอง
            export_format: 'excel' หรือ 'csv'
            filename: ชื่อไฟล์
            
        Returns:
            Path to exported file
        """
        # Apply filters
        filtered_data = data.copy()
        
        for column, value in filters.items():
            if value is not None and column in filtered_data.columns:
                if isinstance(value, list):
                    filtered_data = filtered_data[filtered_data[column].isin(value)]
                else:
                    filtered_data = filtered_data[filtered_data[column] == value]
        
        # Export
        if export_format.lower() == 'excel':
            return self.export_to_excel(filtered_data, filename)
        else:
            return self.export_to_csv(filtered_data, filename)
    
    def generate_audit_summary(
        self,
        reconciliation_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        สร้างสรุปสำหรับผู้ตรวจสอบ
        
        Args:
            reconciliation_df: ข้อมูลการเปรียบเทียบ
            
        Returns:
            DataFrame สรุป
        """
        summary = {
            'total_vendors': reconciliation_df['vendor_code'].nunique(),
            'total_categories': reconciliation_df['category_code'].nunique(),
            'total_should_collect': reconciliation_df['should_collect'].sum(),
            'total_actually_collected': reconciliation_df['actually_collected'].sum(),
            'total_difference': reconciliation_df['difference'].sum(),
        }
        
        # Status breakdown
        status_counts = reconciliation_df['status'].value_counts()
        for status, count in status_counts.items():
            summary[f'status_{status}'] = count
        
        # Variance statistics
        summary['avg_variance_pct'] = reconciliation_df['variance_pct'].mean()
        summary['max_variance_pct'] = reconciliation_df['variance_pct'].max()
        summary['min_variance_pct'] = reconciliation_df['variance_pct'].min()
        
        return pd.DataFrame([summary])

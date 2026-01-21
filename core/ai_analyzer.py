"""
AI Document Analyzer - Extracted from AI_Contract_V2.ipynb Cell 4
Preserves 100% of original logic
"""

import google.generativeai as genai
import json
import time
import re
from pdf2image import convert_from_path
import matplotlib.pyplot as plt
from PIL import Image
from typing import Dict
from config.categories import ALLOWANCE_CATEGORIES


class TTADocumentAnalyzer:
    """
    AI-powered contract document analyzer using Google Gemini.
    Extracts vendor support conditions from PDF contracts.
    
    This class is PRESERVED from the original notebook with minimal changes.
    """
    
    def __init__(self, api_key: str):
        """Initialize Gemini API"""
        genai.configure(api_key=api_key)
        # ใช้โมเดล Pro ตามที่แนะนำ
        self.model_name = 'gemini-2.5-flash'
        self.model = genai.GenerativeModel(self.model_name)

    def display_pdf_images(self, pdf_path: str, max_width: int = 800):
        """แสดงรูปภาพจาก PDF เพื่อให้ User ตรวจสอบ (ไม่ได้ส่งให้ AI)"""
        try:
            images = convert_from_path(pdf_path, dpi=200)
            print(f"\n📸 Preview เอกสาร ({len(images)} หน้า)\n")

            for idx, img in enumerate(images):
                width, height = img.size
                if width > max_width:
                    ratio = max_width / width
                    new_size = (max_width, int(height * ratio))
                    img_display = img.resize(new_size, Image.Resampling.LANCZOS)
                else:
                    img_display = img

                plt.figure(figsize=(10, 14))
                plt.imshow(img_display)
                plt.axis('off')
                plt.title(f'Page {idx + 1}', fontsize=12)
                plt.show()
                print("\n")
        except Exception as e:
            print(f"Cannot display images: {e}")

    def create_analysis_prompt(self) -> str:
        """
        Creates the sophisticated prompt for Gemini AI.
        This prompt is CRITICAL and should not be modified.
        """
        categories_text = "\n".join([f"- {code}: {name}" for code, name in ALLOWANCE_CATEGORIES.items()])

        teaching_example = """
        --------------------------------------------------
        ตัวอย่างการวิเคราะห์ (EXAMPLE CASE):

        [Input Document Context]:
        - Header ระบุ: "Auto Rate 9.75%", "Fixed Amount 30,000"
        - Page 1 ตารางระบุ:
          1. ARB (Unconditional Rebate): 2.75%
          2. MMF (Marketing Fund): 1.00%
          3. COF (Coupon Support): 1.00%
          4. ANI (Anniversary): 30,000 Baht
          5. NRT (Non Return): 1.00%
          6. GCS (Guarantee GP): 4.00%
        - Page 2 ระบุ: "Support Import Leaflet 20,000/ times (2 time a year)"

        [Correct Logic & Thinking]:
        1. ตรวจสอบยอดรวม: 2.75 + 1.00 + 1.00 + 1.00 + 4.00 = 9.75% (ตรงกับ Header) -> ดึงข้อมูลย่อยออกมา
        2. ตรวจสอบยอดเงิน: ANI 30,000 (ตรงกับ Header) -> ดึงข้อมูลย่อยออกมา
        3. การตีความหน้า 2: "Leaflet" คือเอกสารโฆษณา -> จัดเข้าหมวด "BRO" (Brochure Fee)
        4. การคำนวณหน้า 2: 20,000 x 2 ครั้ง = 40,000 บาท/ปี

        [Expected JSON Output]:
        {
          "allowances": [
            {"category_code": "ARB", "rate_percent": 2.75, "fix_amount": null},
            {"category_code": "MMF", "rate_percent": 1.00, "fix_amount": null},
            {"category_code": "COF", "rate_percent": 1.00, "fix_amount": null},
            {"category_code": "ANI", "rate_percent": null, "fix_amount": 30000.00},
            {"category_code": "NRT", "rate_percent": 1.00, "fix_amount": null},
            {"category_code": "GCS", "rate_percent": 4.00, "fix_amount": null},
            {
              "category_code": "BRO",
              "category_name": "Brochure Fee",
              "rate_percent": null,
              "fix_amount": 40000.00,
              "description": "Support Import Leaflet 20,000 x 2 times/year"
            }
          ]
        }
        --------------------------------------------------
        """

        prompt = f"""
        คุณคือผู้เชี่ยวชาญด้านสัญญาการค้า (Trade Terms)
        โปรดวิเคราะห์ไฟล์เอกสารแนบนี้ (PDF) ซึ่งเป็นข้อตกลงทางการค้า และดึงข้อมูลออกมาในรูปแบบ JSON:

        1. หา Vendor Code, Division Code, Division Name, Department Code, Department Name จากเอกสาร
          **กฎสำคัญ - READ CAREFULLY:**
          - **Vendor Code**: ตัวเลข 7 หลัก (เช่น 6003053, 6003074)
          - **Division Code**: ตัวเลข 2 หลัก ขึ้นต้นด้วย 0 เสมอ (01-09 เท่านั้น)
            ❌ ห้ามใช้ 60, 70, 80 - นั่นไม่ใช่ Division Code!
            ✅ ถูกต้อง: 01, 02, 03, 04, 05, 06, 07, 08, 09
          - **Department Code**: ตัวเลข 2 หลัก (10-99)
            ✅ ถูกต้อง: 10, 20, 30, 40, 50, 60, 70, 80, 90
          - **ตัวอย่างที่ถูกต้อง:**
            • Vendor: 6003053, Division: 05, Department: 60 ✅
            • Vendor: 6003074, Division: 04, Department: 50 ✅
          - **ตัวอย่างที่ผิด:**
            • Vendor: 6003053, Division: 60, Department: 60 ❌ (60 ไม่ใช่ Division!)
            
          - **วิธีหา Division และ Department:**
            1. มองหา "Division Code" หรือ "DIV" ในเอกสาร → ต้องเป็น 01-09
            2. มองหา "Department Code" หรือ "DEPT" ในเอกสาร → เป็น 10-99
            3. ถ้าเจอตัวเลข 60, 70, 80 → น่าจะเป็น Department ไม่ใช่ Division
            4. ถ้าไม่แน่ใจ → Division มักอยู่ในส่วน Header หรือ ด้านบนสุด
            
          - **ถ้าเอกสารมี Department มากกว่า 1 ตัว:**
            ให้เลือก Department ที่ปรากฏบ่อยที่สุดหรือที่อยู่ใน main section
            
          - **ห้ามใส่ค่า null/None:**
            ถ้าหาไม่เจอ Division หรือ Department → ให้ใส่ "00" แทน
            
        2. สกัดข้อมูล allowance แต่ละประเภทพร้อมเงื่อนไข โดยจัดหมวดหมู่ตามรายการนี้:

        {categories_text}

        สำหรับแต่ละ allowance ให้ระบุ:
        - Category Code (จากรายการด้านบน)
        - Category Name
        - Rate (% ถ้ามี)
        - Fix Amount (จำนวนเงินคงที่ ถ้ามี)
        - Description (รายละเอียดหรือเงื่อนไข)
        - Payment Terms (เงื่อนไขการจ่าย เช่น monthly, quarterly, annually)

        กฎการวิเคราะห์ (Extraction Rules):
        1. **Header vs Detail:** ข้อมูลส่วนหัว Total Contract (เช่น % Auto Rate, Fix Amount) จะเป็น "ผลรวม" ของรายการย่อย ให้โฟกัสที่การดึง "รายการย่อย" (Line Items) ให้ครบทุกบรรทัด
        2. **เมื่อดึงรายการย่อยที่มี Rate หรือ Fix Amount ออกมาครบทุกหัวข้อใน Page 1 แล้ว สามารถตรวจความถูกต้องได้จากผลรวมของ Rate และ Fix Amount ที่ดึงออกมาได้จะต้องได้เท่ากับ % Auto Rate และ Fix Amount ตาม Header
        3. **Page 2 Analysis:** หน้า 2 มักเป็นเงื่อนไขเพิ่มเติม (Additional Conditions) ที่ไม่มีรหัสกำกับ ต้องอ่านบริบทแล้ว map เข้า Category ที่ถูกต้อง
           - ถ้าเจอคำว่า "Leaflet", "Brochure", "Ad" -> ให้ map เป็น "BRO"
        4. **Calculation:** หากเจอเงื่อนไขแบบ "per time" หรือ "per month" ให้คำนวณเป็น "ยอดรวมต่อปี" (Annual Total) ในช่อง fix_amount เสมอ พร้อมใส่เงื่อนไขในการคำนวณมาให้ด้วย

        **สำคัญ**:
        - หน้า 1 สนใจเฉพาะส่วนที่มีหัวข้อชัดเจนเท่านั้น ไม่ต้องสนใจเนื้อหาในส่วน Others Agreement
        - ถ้า CRB มีการให้ rate หรือ Fix Amount หัวข้อ ARB จะต้องมี rate หรือ Fix Amount เสมอ
        - หน้า 2 อาจจะมีทั้งส่วนที่มีหัวข้อชัดเจนและไม่ชัดเจน ให้วิเคราะห์หน้า 2 อย่างละเอียดโดยวิเคราะห์จากบริบทและเนื้อหา
        - ถ้าหน้า 2 ไม่มีหัวข้อชัดเจน ให้วิเคราะห์จากเนื้อหาและจัดกลุ่มให้ตรงกับหมวดหมู่ที่กำหนดไว้
        - ถ้ามีทั้ง Rate และ Fix Amount ให้ระบุทั้งสอง
        - อ่านข้อมูลจากตารางในเอกสารให้ละเอียดระวังเรื่องบรรทัดและคอลัมน์
        - ไม่ต้องสนใจส่วนที่เป็นลายมือหรือสิ่งที่เป็นคนเขียน
        - สรุปเฉพาะหัวข้อที่มี Rate หรือ Fix Amount
        - บางไฟล์อาจจะมีเอกสารมากกว่า 2 หน้า ให้อ่านและสรุปข้อมูลเฉพาะ หน้า 1 และ 2 เท่านั้น หน้าอื่นไม่ต้องสนใจ
        
        **กฎ JSON Format (สำคัญมาก!):**
        - **ใช้ภาษาอังกฤษใน JSON เท่านั้น** - ห้ามใช้ภาษาไทย ห้ามใช้ตัวอักษรพิเศษ
        - Description, category_name, payment_terms ต้องเป็นภาษาอังกฤษทั้งหมด
        - ใช้ double quotes สำหรับ keys และ string values เท่านั้น
        - ถ้ามี double quote ในข้อความ ให้แปลงเป็น single quote แทน
        - ห้ามใส่ comma หลังรายการสุดท้ายใน array หรือ object
        - ห้ามใส่ comments
        - ห้ามใช้ special characters ที่ทำให้ JSON ผิด
        - ห้ามใช้ newlines (\n) ใน string values


        Response ในรูปแบบ JSON เท่านั้น:
      {{{{
        "vendor_code": "รหัสผู้ขาย 7 หลัก",
        "Division_code": "รหัสแผนก 2 หลัก (01-09)",
        "Division_name": "ชื่อแผนก",
        "Department_code": "รหัสฝ่าย 2 หลัก (10-99)",
        "Department_name": "ชื่อฝ่าย",
        "allowances": [
          {{{{
            "category_code": "ARB",
            "category_name": "Unconditional Rebate",
            "rate_percent": 5.0,
            "fix_amount": null,
            "description": "รายละเอียดเงื่อนไข",
            "payment_terms": "monthly"
          }}}}
        ]
      }}}}
      """

        return prompt

    def analyze_document(self, pdf_path: str, show_images: bool = False) -> Dict:
        """
        Analyzes a PDF contract document using Gemini AI.
        
        This method is PRESERVED from the original notebook.
        Changes:
        - Removed Colab-specific datetime imports (already imported at top)
        - File upload/download logic adapted for general use
        
        Args:
            pdf_path: Path to PDF file
            show_images: Whether to display PDF preview
            
        Returns:
            Dict with contract analysis results or error
        """
        import datetime
        
        print(f"\n{'='*20} DEBUG MODE {'='*20}")
        print(f"🕒 เวลาเริ่ม: {datetime.datetime.now()}")
        print(f"🤖 Model ที่ใช้: {self.model_name}")
        print(f"📄 ไฟล์: {pdf_path}")

        if show_images:
            self.display_pdf_images(pdf_path)

        # 1. Upload Section
        try:
            print("\nStep 1: Uploading File...")
            doc_file = genai.upload_file(path=pdf_path, display_name="Trade_Term_Doc")

            while doc_file.state.name == "PROCESSING":
                print('.', end='')
                time.sleep(2)
                doc_file = genai.get_file(doc_file.name)

            if doc_file.state.name == "FAILED":
                print(f"\n❌ Step 1 FAILED: Google Server ประมวลผล PDF ไม่สำเร็จ")
                return {"error": "PDF Processing Failed"}

            print(f"\n✅ Step 1 SUCCESS: File Ready")

        except Exception as e:
            print(f"\n❌ CRITICAL ERROR ในขั้นตอน Upload: {e}")
            return {"error": str(e)}

        # 2. Generation Section (with Better JSON Cleaning)
        print("\nStep 2: Sending Request to Gemini...")
        try:
            generation_config = {
                "temperature": 0.0,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
            }

            response = self.model.generate_content(
                [self.create_analysis_prompt(), doc_file],
                generation_config=generation_config
            )

            # --- Aggressive JSON Cleaning ---
            raw_text = response.text.strip()
            
            print(f"\n🔍 Raw JSON length: {len(raw_text)} chars")
            
            # ทำความสะอาด JSON อย่างละเอียด
            # 1. ลบ markdown blocks
            if raw_text.startswith("```"):
                raw_text = re.sub(r'^```json\s*|^```\s*|```$', '', raw_text, flags=re.MULTILINE)
            
            # 2. ลบ newlines ทั้งหมดจาก strings
            # แทนที่ \n, \r, \t ด้วยช่องว่าง
            raw_text = raw_text.replace('\\n', ' ').replace('\\r', ' ').replace('\\t', ' ')
            raw_text = raw_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            
            # 3. ลบช่องว่างเกิน
            raw_text = re.sub(r'\s+', ' ', raw_text)
            
            # 4. ลบ trailing commas
            raw_text = re.sub(r',\s*([}\]])', r'\1', raw_text)
            
            # 5. ลบ control characters
            raw_text = re.sub(r'[\x00-\x1F\x7F]', '', raw_text)
            
            # 6. แก้ไข quotes ซ้อนใน description และ escape ภาษาไทยที่ทำให้พัง
            # ใช้วิธีที่ปลอดภัยกว่า: หา string values แล้วแก้ทีละตัว
            def safe_fix_string_value(text):
                """แก้ string values ให้ปลอดภัย"""
                result = []
                i = 0
                in_string = False
                escape_next = False
                
                while i < len(text):
                    char = text[i]
                    
                    if escape_next:
                        result.append(char)
                        escape_next = False
                        i += 1
                        continue
                    
                    if char == '\\':
                        escape_next = True
                        result.append(char)
                        i += 1
                        continue
                    
                    if char == '"':
                        if not in_string:
                            # เริ่ม string
                            in_string = True
                            result.append(char)
                        else:
                            # จบ string - แต่ต้องเช็คว่าจริงๆ หรือเปล่า
                            # ดูว่าหลัง " เป็น : , } ] หรือไม่
                            next_char = text[i+1] if i+1 < len(text) else ''
                            if next_char in [',', '}', ']', ' ', '']:
                                # จบ string จริง
                                in_string = False
                                result.append(char)
                            else:
                                # อาจเป็น quote ภายใน string - แปลงเป็น single quote
                                result.append("'")
                        i += 1
                        continue
                    
                    result.append(char)
                    i += 1
                
                return ''.join(result)
            
            # ใช้ safe fix
            raw_text = safe_fix_string_value(raw_text)
            
            print(f"✅ Step 2 SUCCESS: ได้รับคำตอบแล้ว")
            print(f"🔍 Cleaned JSON (first 200 chars): {raw_text[:200]}...")

            # --- Parse JSON ---
            try:
                result = json.loads(raw_text)
                print(f"   ✅ Parse สำเร็จ")
            except json.JSONDecodeError as je:
                print(f"\n   ⚠️ Parse failed at position {je.pos}")
                print(f"   Error: {je.msg}")
                
                # แสดงบริบทรอบๆ error
                if je.pos < len(raw_text):
                    start = max(0, je.pos - 100)
                    end = min(len(raw_text), je.pos + 100)
                    print(f"   Context: ...{raw_text[start:je.pos]}[ERROR HERE]{raw_text[je.pos:end]}...")
                
                # บันทึก debug file
                vendor_hint = pdf_path.split('/')[-1].replace('.pdf', '')
                debug_file = f"debug_error_{vendor_hint}.txt"
                with open(debug_file, "w", encoding='utf-8') as f:
                    f.write(f"=== ORIGINAL RESPONSE ===\n")
                    f.write(response.text)
                    f.write(f"\n\n=== CLEANED RESPONSE ===\n")
                    f.write(raw_text)
                    f.write(f"\n\n=== ERROR ===\n")
                    f.write(f"Position: {je.pos}\n")
                    f.write(f"Message: {je.msg}\n")
                    if je.pos < len(raw_text):
                        f.write(f"\n=== CONTEXT ===\n")
                        start = max(0, je.pos - 200)
                        end = min(len(raw_text), je.pos + 200)
                        f.write(raw_text[start:end])
                
                print(f"   📝 Debug file saved: {debug_file}")
                raise je
            
            # --- VALIDATION: ตรวจสอบ Division และ Department ---
            result = self._validate_and_fix_codes(result)
            
            return result

        except json.JSONDecodeError as je:
            # หาก Parse ไม่สำเร็จ จะทำการบันทึก Response ดิบลงไฟล์เพื่อ Debug
            print(f"\n❌ JSON Parsing Error: {je}")
            debug_file = "debug_error_response.txt"
            with open(debug_file, "w", encoding='utf-8') as f:
                f.write(response.text)
            print(f"📝 บันทึก Response ดิบไว้ที่: {debug_file}")
            return {"error": f"JSON Format Invalid: {str(je)}"}

        except Exception as e:
            print(f"\n❌ CRITICAL ERROR ในขั้นตอน Generate: {e}")
            
            # วิเคราะห์ Error ให้ทันที
            err_msg = str(e)
            if "429" in err_msg:
                return {"error": "🛑 QUOTA EXCEEDED: โควต้า Pro ของวันนี้หมดแล้ว (หรือยิงถี่เกินไป)"}
            elif "404" in err_msg:
                return {"error": "🛑 MODEL NOT FOUND: ชื่อโมเดลไม่ถูกต้อง หรือ Account ไม่มีสิทธิ์ใช้"}
            else:
                return {"error": f"Unknown Error: {e}"}
    
    def _validate_and_fix_codes(self, result: Dict) -> Dict:
        """
        ตรวจสอบและแก้ไข Division/Department codes ที่ผิดพลาด
        
        Args:
            result: Dict จาก AI response
            
        Returns:
            Dict ที่แก้ไขแล้ว
        """
        # ตรวจสอบ Division Code
        div_code = result.get('Division_code')
        dept_code = result.get('Department_code')
        
        # แปลงเป็น string ก่อน
        if div_code is not None:
            div_code = str(div_code).strip()
        if dept_code is not None:
            dept_code = str(dept_code).strip()
        
        print(f"\n🔍 VALIDATION:")
        print(f"   Original - Division: {div_code}, Department: {dept_code}")
        
        # ตรวจสอบ Division Code
        if div_code:
            # ถ้า Division เป็น 2 หลัก แต่ไม่ใช่ 01-09
            if len(div_code) == 2 and not div_code.startswith('0'):
                # ตรวจสอบว่าอาจเป็น Department ที่เข้าใจผิด
                if div_code.isdigit() and int(div_code) >= 10:
                    print(f"   ⚠️  WARNING: Division '{div_code}' ไม่ถูกต้อง (ต้องเป็น 01-09)")
                    print(f"   💡 คาดว่าอาจเป็น Department, แก้ไข Division → '00'")
                    
                    # ถ้า Department ว่าง ให้ใช้ค่าเดิมของ Division
                    if not dept_code or dept_code in ['None', 'null', '']:
                        result['Department_code'] = div_code
                        print(f"   ✅ แก้ไข Department: None → {div_code}")
                    
                    result['Division_code'] = '00'
            
            # ถ้า Division ยาวกว่า 2 หลัก
            elif len(div_code) > 2:
                print(f"   ⚠️  WARNING: Division '{div_code}' ยาวเกิน 2 หลัก")
                # เอา 2 หลักแรก
                result['Division_code'] = div_code[:2].zfill(2)
                print(f"   ✅ แก้ไข: {div_code} → {result['Division_code']}")
            
            # ถ้า Division เป็น 1 หลัก ให้เติม 0
            elif len(div_code) == 1:
                result['Division_code'] = div_code.zfill(2)
                print(f"   ✅ แก้ไข: {div_code} → {result['Division_code']}")
        
        # ตรวจสอบ Department Code
        if dept_code:
            # ถ้า Department เป็น None, null, หรือว่าง
            if dept_code in ['None', 'null', '']:
                print(f"   ⚠️  WARNING: Department เป็น '{dept_code}'")
                result['Department_code'] = '00'
                print(f"   ✅ แก้ไข: None → 00")
            
            # ถ้า Department เป็น 1 หลัก ให้เติม 0
            elif len(dept_code) == 1:
                result['Department_code'] = dept_code.zfill(2)
                print(f"   ✅ แก้ไข: {dept_code} → {result['Department_code']}")
        else:
            # ถ้าไม่มี Department เลย
            print(f"   ⚠️  WARNING: Department เป็น None")
            result['Department_code'] = '00'
            print(f"   ✅ แก้ไข: None → 00")
        
        final_div = result.get('Division_code', 'N/A')
        final_dept = result.get('Department_code', 'N/A')
        print(f"   Final - Division: {final_div}, Department: {final_dept}")
        
        return result

    def format_output(self, result: Dict) -> str:
        """Format analysis result for display"""
        if "error" in result:
            return f"❌ Error: {result['error']}"

        output = []
        output.append("=" * 60)
        output.append(f"📄 Vendor: {result.get('vendor_code', 'N/A')}")
        output.append(f"📄 Division: {result.get('Division_code', 'N/A')} - {result.get('Division_name', 'N/A')} ")
        output.append(f"📄 Department: {result.get('Department_code', 'N/A')} - {result.get('Department_name', 'N/A')} ")
        output.append("=" * 60)

        allowances = result.get('allowances', [])
        if not allowances:
            output.append("ไม่พบข้อมูล Allowance")

        for idx, item in enumerate(allowances, 1):
            output.append(f"\n{idx}. [{item.get('category_code')}] {item.get('category_name')}")

            rate = item.get('rate_percent')
            amt = item.get('fix_amount')

            if rate: output.append(f"   💰 Rate: {rate}%")
            if amt: output.append(f"   💵 Amount: {amt:,.2f}")

            desc = item.get('description')
            if desc: output.append(f"   📝 Note: {desc}")

        output.append("\n" + "=" * 60)
        return "\n".join(output)

import streamlit as st
import google.generativeai as genai
from datetime import datetime
from PIL import Image
import cv2
import tempfile
import time
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io
import os
import pandas as pd

# Page config
st.set_page_config(
    page_title="Shakti-Gemini AI Assistant",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .shakti-title {
        font-size: 3.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 20px;
    }
    .subtitle {
        text-align: center;
        color: #888;
        font-size: 1.2rem;
    }
    .sheet-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Session state init ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_video_file" not in st.session_state:
    st.session_state.current_video_file = None

if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0

if "unit_test_data" not in st.session_state:
    st.session_state.unit_test_data = None

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

if "clear_uploader" not in st.session_state:
    st.session_state.clear_uploader = False

if "captured_frames" not in st.session_state:
    st.session_state.captured_frames = []

if "excel_sheets" not in st.session_state:
    st.session_state.excel_sheets = {}

if "sheet_analyses" not in st.session_state:
    st.session_state.sheet_analyses = {}

if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False

if "analysis_type_used" not in st.session_state:
    st.session_state.analysis_type_used = ""

if "total_sheets_analyzed" not in st.session_state:
    st.session_state.total_sheets_analyzed = 0

if "video_analysis_complete" not in st.session_state:
    st.session_state.video_analysis_complete = False

if "video_doc_bytes" not in st.session_state:
    st.session_state.video_doc_bytes = None

# ----------------------------------------

def create_sample_excel():
    """Create a sample Excel file with multiple sheets for download"""
    
    # Create Excel writer object
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # Sheet 1: Warehouse North
        warehouse_north = pd.DataFrame({
            'SKU': ['SOF001', 'SOF002', 'TAB001', 'TAB002', 'BED001', 'BED002', 'CHA001', 'CHA002', 'LAM001', 'LAM002'],
            'Product_Name': ['Madison Sofa', 'Parker Sectional', 'Oak Dining Table', 'Glass Coffee Table', 
                           'Queen Platform Bed', 'King Storage Bed', 'Accent Chair', 'Office Chair', 
                           'Table Lamp', 'Floor Lamp'],
            'Category': ['Sofas', 'Sofas', 'Tables', 'Tables', 'Beds', 'Beds', 'Chairs', 'Chairs', 'Lighting', 'Lighting'],
            'Current_Stock': [5, 15, 3, 25, 8, 2, 50, 12, 100, 15],
            'Sales_Last_30_Days': [45, 8, 12, 2, 20, 35, 5, 18, 10, 15],
            'Unit_Price': [1299, 1899, 599, 299, 899, 1199, 199, 399, 49, 129],
            'Supplier': ['Supplier_A', 'Supplier_A', 'Supplier_B', 'Supplier_C', 'Supplier_B', 'Supplier_B', 
                        'Supplier_C', 'Supplier_C', 'Supplier_D', 'Supplier_D'],
            'Last_Sale_Date': ['2025-12-01', '2025-11-20', '2025-12-03', '2025-10-15', '2025-12-04', 
                             '2025-12-05', '2025-09-10', '2025-12-02', '2025-11-28', '2025-12-01']
        })
        warehouse_north.to_excel(writer, sheet_name='Warehouse_North', index=False)
        
        # Sheet 2: Warehouse South
        warehouse_south = pd.DataFrame({
            'SKU': ['SOF001', 'SOF003', 'TAB001', 'BED001', 'BED003', 'CHA001', 'CHA003', 'RUG001', 'RUG002', 'DEC001'],
            'Product_Name': ['Madison Sofa', 'Leather Recliner', 'Oak Dining Table', 'Queen Platform Bed', 
                           'Full Size Bed', 'Accent Chair', 'Dining Chair Set', 'Area Rug 8x10', 
                           'Runner Rug', 'Wall Art'],
            'Category': ['Sofas', 'Sofas', 'Tables', 'Beds', 'Beds', 'Chairs', 'Chairs', 'Rugs', 'Rugs', 'Decor'],
            'Current_Stock': [20, 8, 15, 12, 5, 30, 25, 6, 40, 75],
            'Sales_Last_30_Days': [35, 22, 8, 18, 15, 12, 20, 8, 1, 5],
            'Unit_Price': [1299, 1599, 599, 899, 699, 199, 449, 299, 89, 79],
            'Supplier': ['Supplier_A', 'Supplier_A', 'Supplier_B', 'Supplier_B', 'Supplier_B', 'Supplier_C', 
                        'Supplier_C', 'Supplier_E', 'Supplier_E', 'Supplier_F'],
            'Last_Sale_Date': ['2025-12-04', '2025-12-03', '2025-12-01', '2025-12-05', '2025-12-02', 
                             '2025-11-30', '2025-12-04', '2025-11-25', '2025-08-15', '2025-10-20']
        })
        warehouse_south.to_excel(writer, sheet_name='Warehouse_South', index=False)
        
        # Sheet 3: Warehouse West
        warehouse_west = pd.DataFrame({
            'SKU': ['SOF002', 'TAB003', 'TAB004', 'BED002', 'CHA002', 'CHA004', 'LAM003', 'OUT001', 'OUT002', 'OUT003'],
            'Product_Name': ['Parker Sectional', 'Console Table', 'Side Table', 'King Storage Bed', 
                           'Office Chair', 'Bar Stool', 'Desk Lamp', 'Patio Set', 'Outdoor Sofa', 'Fire Pit'],
            'Category': ['Sofas', 'Tables', 'Tables', 'Beds', 'Chairs', 'Chairs', 'Lighting', 
                        'Outdoor', 'Outdoor', 'Outdoor'],
            'Current_Stock': [10, 18, 22, 4, 16, 8, 45, 3, 2, 12],
            'Sales_Last_30_Days': [12, 6, 5, 28, 14, 25, 8, 18, 22, 4],
            'Unit_Price': [1899, 399, 199, 1199, 399, 249, 69, 1299, 1499, 599],
            'Supplier': ['Supplier_A', 'Supplier_B', 'Supplier_C', 'Supplier_B', 'Supplier_C', 'Supplier_C', 
                        'Supplier_D', 'Supplier_G', 'Supplier_G', 'Supplier_G'],
            'Last_Sale_Date': ['2025-12-03', '2025-11-28', '2025-11-15', '2025-12-05', '2025-12-04', 
                             '2025-12-05', '2025-12-01', '2025-12-02', '2025-12-05', '2025-11-20']
        })
        warehouse_west.to_excel(writer, sheet_name='Warehouse_West', index=False)
        
        # Sheet 4: Sales Summary (different data type)
        sales_summary = pd.DataFrame({
            'Month': ['January', 'February', 'March', 'April', 'May', 'June', 
                     'July', 'August', 'September', 'October', 'November', 'December'],
            'Total_Sales': [125000, 132000, 145000, 138000, 155000, 162000, 
                          148000, 151000, 167000, 175000, 182000, 195000],
            'Total_Units': [450, 475, 520, 490, 550, 580, 525, 535, 595, 625, 650, 695],
            'Avg_Order_Value': [278, 278, 279, 282, 282, 279, 282, 282, 281, 280, 280, 281],
            'New_Customers': [85, 92, 105, 98, 112, 125, 108, 115, 128, 135, 142, 155],
            'Return_Rate': [2.5, 2.3, 2.1, 2.4, 2.2, 2.0, 2.3, 2.1, 1.9, 2.0, 1.8, 1.7]
        })
        sales_summary.to_excel(writer, sheet_name='Sales_Summary_2024', index=False)
    
    output.seek(0)
    return output

def smart_rate_limit():
    """Smart rate limiting"""
    current_time = time.time()
    time_since_last = current_time - st.session_state.last_request_time
    
    min_wait = 6
    
    if time_since_last < min_wait:
        wait_time = min_wait - time_since_last
        if wait_time > 0:
            with st.spinner(f"⏳ Rate limiting... waiting {wait_time:.1f}s"):
                time.sleep(wait_time)
    
    st.session_state.last_request_time = time.time()

def generate_unit_test_prompt():
    """Generate a comprehensive prompt for unit test document creation"""
    return """Analyze this video and create a Unit Test Document. For EACH screenshot/frame, provide:

1. A clear, concise description of what action is happening in that frame
2. What the user is doing or what screen is shown
3. Any important text, buttons, or UI elements visible

Format your response as:

# UNIT TEST DOCUMENT

## TEST OVERVIEW
- Test ID: [Generate ID]
- Test Name: [Name based on what you see]
- Feature: [What's being tested]
- Date: [Today's date]

## TEST STEPS

For each frame, write:

**Frame 1:**
[Clear description of what's happening - e.g., "User logged into the system" or "Trip selection screen showing trip 0055600-00"]

**Frame 2:**
[Description of action/screen]

**Frame 3:**
[Description of action/screen]

... continue for all frames

## TEST SUMMARY
- Total Steps: [number of frames]
- Status: Pass/Fail
- Notes: [Any observations]

IMPORTANT: Write clear, simple descriptions for each frame that will go UNDER the screenshot in the document."""

def get_inventory_prompt(analysis_type, sheet_name=""):
    """Get AI prompt based on analysis type"""
    
    sheet_context = f"\n**ANALYZING SHEET: {sheet_name}**\n" if sheet_name else ""
    
    prompts = {
        "stockout_risk": f"""
{sheet_context}
Analyze this data and identify:

1. **CRITICAL STOCKOUTS** (immediate action needed):
   - Products with low stock levels vs. sales velocity
   - Estimated days until stockout
   - Revenue at risk
   - Recommended emergency reorder quantities

2. **WARNING ITEMS** (action needed within 2 weeks):
   - Products approaching low stock
   - Recommended reorder timing and quantities

3. **ADEQUATE STOCK** (monitor):
   - Items with healthy stock levels

For each at-risk item, provide:
- SKU and product name
- Current stock level
- Sales velocity (units per day)
- Estimated stockout date
- Recommended reorder quantity
- Revenue impact

Format as a prioritized action list with clear sections.
""",
        
        "slow_movers": f"""
{sheet_context}
Analyze this data and identify:

1. **EXCESS INVENTORY** (overstock items):
   - Products with very high days of inventory on hand
   - Items with declining sales trends
   - Low turnover rate items
   - Seasonal items past their peak

2. **RECOMMENDATIONS** for each item:
   - Suggested discount percentage for clearance
   - Alternative sales channels
   - Return to vendor options
   - Potential write-off considerations

3. **COST IMPACT**:
   - Calculate total carrying cost of slow-moving inventory
   - Potential savings from clearance actions

Format as an actionable report with specific SKUs and financial impact.
""",
        
        "general_insights": f"""
{sheet_context}
Analyze this data and provide a comprehensive overview:

1. **DATA OVERVIEW**:
   - What type of data is this (inventory, sales, financial, etc.)?
   - Overall assessment of the data health

2. **KEY FINDINGS**:
   - Most important insights from this data
   - Notable patterns or trends
   - Anomalies or outliers

3. **TOP PERFORMERS**:
   - Best performing items/categories
   - Items with optimal metrics

4. **PROBLEM AREAS**:
   - Issues requiring attention
   - Risks or concerns
   - Unusual patterns

5. **RECOMMENDATIONS**:
   - Priority actions
   - Strategic suggestions
   - Specific items requiring attention

Provide clear, business-focused insights with specific examples and actionable recommendations.
"""
    }
    
    return prompts.get(analysis_type, prompts["general_insights"])

def load_excel_sheets(file):
    """Load all sheets from an Excel file"""
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(file)
        sheet_names = excel_file.sheet_names
        
        sheets_dict = {}
        for sheet_name in sheet_names:
            df = pd.read_excel(file, sheet_name=sheet_name)
            sheets_dict[sheet_name] = df
        
        return sheets_dict, None
    except Exception as e:
        return None, str(e)

def analyze_sheet_data(df, sheet_name, analysis_type):
    """Analyze a single sheet's data with Gemini AI"""
    
    # Get basic stats
    total_rows = len(df)
    total_columns = len(df.columns)
    
    # Create data summary
    data_summary = f"""
SHEET: {sheet_name}

DATA SUMMARY:
- Total Rows: {total_rows}
- Total Columns: {total_columns}
- Column Names: {', '.join(df.columns.tolist())}

SAMPLE DATA (First 20 rows):
{df.head(20).to_string()}

BASIC STATISTICS:
{df.describe().to_string()}

DATA TYPES:
{df.dtypes.to_string()}
"""
    
    # Get the analysis prompt
    base_prompt = get_inventory_prompt(analysis_type, sheet_name)
    
    # Create full prompt for AI
    full_prompt = f"""
{base_prompt}

Here's the data to analyze:

{data_summary}

Provide actionable insights and recommendations in a clear, well-structured markdown format.
Use headers, bullet points, and clear sections for easy reading.
"""
    
    return full_prompt

def extract_video_frames_with_save(video_path, num_frames=8):
    """Extract frames from video and save as temporary files"""
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    frames = []
    frame_files = []
    frame_indices = [int(i * total_frames / (num_frames + 1)) for i in range(1, num_frames + 1)]
    
    for i, idx in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            frames.append(pil_image)
            
            # Save frame to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            pil_image.save(temp_file.name, 'PNG')
            
            # Calculate timestamp
            timestamp_sec = idx / fps if fps > 0 else 0
            minutes = int(timestamp_sec // 60)
            seconds = int(timestamp_sec % 60)
            
            frame_files.append({
                'file': temp_file.name,
                'index': i + 1,
                'timestamp': f"{minutes:02d}:{seconds:02d}",
                'timestamp_sec': timestamp_sec,
                'frame_number': idx
            })
    
    cap.release()
    return frames, frame_files

def extract_frame_descriptions(test_data, num_frames):
    """Extract descriptions for each frame from the AI response"""
    descriptions = {}
    
    lines = test_data.split('\n')
    current_frame = None
    current_desc = []
    
    for line in lines:
        line = line.strip()
        
        # Look for frame markers
        if line.startswith('**Frame ') and ':' in line:
            # Save previous frame description
            if current_frame and current_desc:
                descriptions[current_frame] = ' '.join(current_desc).strip()
            
            # Start new frame
            try:
                frame_num = int(line.split('Frame ')[1].split(':')[0].strip())
                current_frame = frame_num
                # Get description after the colon
                desc_part = ':'.join(line.split(':')[1:]).strip().strip('*')
                current_desc = [desc_part] if desc_part else []
            except:
                pass
        
        elif current_frame and line and not line.startswith('#') and not line.startswith('**'):
            # Continue description for current frame
            if len(current_desc) < 3:  # Limit description length
                current_desc.append(line)
    
    # Save last frame
    if current_frame and current_desc:
        descriptions[current_frame] = ' '.join(current_desc).strip()
    
    # Fill in missing descriptions
    for i in range(1, num_frames + 1):
        if i not in descriptions:
            descriptions[i] = f"Test execution step {i}"
    
    return descriptions

def create_clean_document_with_images(test_data, frame_files, video_duration=0, video_name="test_video"):
    """Create a clean Word document with large screenshots and descriptions"""
    
    doc = Document()
    
    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    
    # Title
    title = doc.add_heading('Unit Test Document', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Test ID
    test_id = f"UT-{datetime.now().strftime('%Y%m%d%H%M')}"
    
    # Metadata
    doc.add_paragraph(f'Test ID: {test_id}')
    doc.add_paragraph(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    doc.add_paragraph(f'Video: {video_name}')
    doc.add_paragraph(f'Duration: {int(video_duration//60)}m {int(video_duration%60)}s')
    doc.add_paragraph('_' * 80)
    doc.add_paragraph()
    
    # Extract frame descriptions from AI response
    frame_descriptions = extract_frame_descriptions(test_data, len(frame_files))
    
    # Test Steps with Screenshots
    doc.add_heading('TEST EXECUTION STEPS', level=1)
    doc.add_paragraph('Each screenshot below shows a key step in the test execution.')
    doc.add_paragraph()
    
    for frame_info in frame_files:
        frame_num = frame_info['index']
        
        # Step heading
        step_heading = doc.add_heading(f"Step {frame_num} - Time {frame_info['timestamp']}", level=2)
        
        # Screenshot (LARGE - 6 inches wide for readability)
        try:
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.add_run().add_picture(frame_info['file'], width=Inches(6.0))
        except Exception as e:
            doc.add_paragraph(f"[Screenshot error: {str(e)}]")
        
        doc.add_paragraph()
        
        # Description UNDER the screenshot
        desc_para = doc.add_paragraph()
        desc_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        description = frame_descriptions.get(frame_num, f"Test step {frame_num}")
        
        # Add description in italic, centered
        desc_run = desc_para.add_run(description)
        desc_run.italic = True
        desc_run.font.size = Pt(10)
        desc_run.font.color.rgb = RGBColor(80, 80, 80)
        
        doc.add_paragraph()
        doc.add_paragraph('─' * 80)
        doc.add_paragraph()
    
    # Test Summary Section
    doc.add_page_break()
    doc.add_heading('TEST SUMMARY', level=1)
    
    # Extract summary info from test_data
    doc.add_paragraph(f"Test ID: {test_id}")
    doc.add_paragraph(f"Total Steps: {len(frame_files)}")
    doc.add_paragraph(f"Status: ✓ Completed")
    doc.add_paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    doc.add_paragraph()
    
    # Add AI analysis if available
    if test_data:
        doc.add_heading('Detailed Analysis', level=2)
        
        # Add only the relevant parts of AI response (skip frame-by-frame)
        lines = test_data.split('\n')
        skip_frames = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip the frame-by-frame section (we already have it above)
            if 'TEST STEPS' in line or '**Frame' in line:
                skip_frames = True
            elif line.startswith('##') and 'SUMMARY' in line:
                skip_frames = False
            
            if not skip_frames:
                if line.startswith('## '):
                    doc.add_heading(line.replace('## ', ''), level=2)
                elif line.startswith('# '):
                    continue  # Skip main title
                elif line.startswith('- '):
                    doc.add_paragraph(line[2:], style='List Bullet')
                elif not line.startswith('**Frame'):
                    doc.add_paragraph(line)
    
    # Footer
    doc.add_paragraph()
    doc.add_paragraph('_' * 80)
    footer = doc.add_paragraph('Generated by Shakti-Gemini AI Assistant')
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Save to bytes
    doc_bytes = io.BytesIO()
    doc.save(doc_bytes)
    doc_bytes.seek(0)
    
    return doc_bytes

# Header
st.markdown('<p class="shakti-title">⚡ SHAKTI-GEMINI ⚡</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-Powered Assistant for Unit Testing & Data Analysis</p>', unsafe_allow_html=True)

#

import os
import subprocess
import shutil
from typing import Optional

def convert_docx_to_pdf(docx_path: str, pdf_path: str) -> bool:
    """
    Attempts to convert a docx file to pdf.
    Tries multiple strategies:
    1. LibreOffice headless CLI (common for self-hosted Linux/Windows servers)
    2. pythoncom/win32com (if running on Windows with MS Word installed)
    3. Fallback warning if no converters are available.
    """
    if not os.path.exists(docx_path):
        return False
        
    # Strategy 1: Look for LibreOffice
    # Common Windows install paths
    libreoffice_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "soffice"  # if in PATH
    ]
    
    libreoffice_bin = None
    for path in libreoffice_paths:
        if path == "soffice" and shutil.which("soffice"):
            libreoffice_bin = "soffice"
            break
        elif os.path.exists(path):
            libreoffice_bin = path
            break
            
    if libreoffice_bin:
        try:
            out_dir = os.path.dirname(pdf_path)
            cmd = [
                libreoffice_bin,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                out_dir,
                docx_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            # LibreOffice output name is the same as docx but with .pdf extension
            expected_output = os.path.join(out_dir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
            if os.path.exists(expected_output):
                if expected_output != pdf_path:
                    shutil.move(expected_output, pdf_path)
                return True
        except Exception as e:
            print(f"LibreOffice conversion failed: {e}")

    # Strategy 2: Windows COM Interop (if MS Word is installed)
    try:
        import win32com.client
        import pythoncom
        pythoncom.CoInitialize()
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(os.path.abspath(docx_path))
        # 17 is the constant for PDF export
        doc.SaveAs(os.path.abspath(pdf_path), FileFormat=17)
        doc.Close()
        word.Quit()
        return True
    except Exception as e:
        print(f"Windows COM Word conversion failed: {e}")

    # If all converters fail, copy docx or return False
    return False

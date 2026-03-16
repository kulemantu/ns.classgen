import os
from pdf_generator import generate_pdf_from_markdown

def test_generate_pdf_from_markdown():
    sample_markdown = """
**Plan A**
- This is a test plan.
- Here is a second bullet.

**Plan B**
- Alternative test plan.
"""
    
    filename = generate_pdf_from_markdown(sample_markdown)
    
    assert filename.startswith("lesson_plan_")
    assert filename.endswith(".pdf")
    
    # Check if file was actually created in the static dir
    current_dir = os.path.dirname(os.path.dirname(__file__))
    static_dir = os.path.join(current_dir, "static")
    expected_path = os.path.join(static_dir, filename)
    
    assert os.path.exists(expected_path)
    
    # Clean up the test file
    if os.path.exists(expected_path):
        os.remove(expected_path)

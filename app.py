import streamlit as st
import nbformat
import base64
import io
from PIL import Image
from openai import OpenAI

client = st.secrets["OPENAI_API_KEY"]#OpenAI(api_key="")

st.title("Notebook Plot Insight Generator")

uploaded_file = st.file_uploader("Upload executed .ipynb notebook", type=["ipynb"])


def extract_images_from_cell(cell):
    images = []

    if "outputs" not in cell:
        return images

    for output in cell["outputs"]:
        if "data" in output:
            data = output["data"]

            if "image/png" in data:
                img_base64 = data["image/png"]
                images.append(img_base64)

    return images

INSIGHT_PATTERNS = [

"""
Provide a short analytical summary of this chart in about 80–100 words.

Structure:
1. Chart type and variables
2. Main distribution or trend
3. Key insight or takeaway

Keep it concise and written like an EDA observation.
""",

"""
Write a compact insight (~100 words) explaining this visualization.

Focus on:
• what the chart represents
• notable patterns or relationships
• any dominant category or trend

If numeric values or percentages are visible, mention them briefly.
""",

"""
Act as a data analyst documenting EDA findings.

Explain the chart in under 100 words including:
- chart type
- variables compared
- notable trends, clusters, or proportions
- one key takeaway.

Keep it concise and professional.
""",

"""
Summarize this visualization in approximately 100 words.

Describe:
• what variables are shown
• how the values relate
• the most important insight

Avoid repeating obvious visual elements and keep the summary readable.
""",

"""
Write a brief EDA insight (~80–100 words).

Explain:
1. What the visualization shows
2. Key patterns or differences
3. One meaningful interpretation

If the chart is a pie or bar chart, mention the dominant categories.
"""
]

def analyze_chart(image_base64, prompt_pattern):

    prompt = prompt_pattern

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    },
                ],
            }
        ],
        max_tokens=180,  # ~100 words
    )

    return response.choices[0].message.content


def process_notebook(nb):

    new_cells = []

    for cell in nb.cells:

        import random
        selected_pattern = random.choice(INSIGHT_PATTERNS)

        new_cells.append(cell)

        if cell.cell_type == "code":

            images = extract_images_from_cell(cell)

            for img in images:

                insight = analyze_chart(img,selected_pattern)

                markdown = nbformat.v4.new_markdown_cell(
                    f"{insight}"
                )

                new_cells.append(markdown)

    nb.cells = new_cells
    return nb


if uploaded_file:

    nb = nbformat.read(uploaded_file, as_version=4)

    st.write("Processing notebook...")

    updated_nb = process_notebook(nb)

    output = io.StringIO()
    nbformat.write(updated_nb, output)

    st.success("Insights added!")

    st.download_button(
        label="Download Updated Notebook",
        data=output.getvalue(),
        file_name="insight_notebook.ipynb",
        mime="application/json",
    )

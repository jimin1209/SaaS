"""Definitions for Notion database templates and sample data."""

DATABASE_TEMPLATES = [
    {
        "template_title": "출장 요청서",
        "icon_emoji": "✈️",
        "properties": {
            "제목": {"title": {}},
            "출장기간": {"date": {}},
            "상태": {"status": {}},
        },
    }
]

DUMMY_ITEMS = {
    "출장 요청서": [
        {"제목": "출장1", "출장기간": "2024-06-01/2024-06-05", "상태": "진행중"},
        {"제목": "출장2", "출장기간": "2024-06-10/2024-06-12", "상태": "승인됨"},
        {"제목": "출장3", "출장기간": "2024-06-15/2024-06-18", "상태": "진행중"},
        {"제목": "출장4", "출장기간": "2024-06-20/2024-06-22", "상태": "미처리"},
        {"제목": "출장5", "출장기간": "2024-06-25/2024-06-27", "상태": "진행중"},
    ]
}


def get_template(title: str):
    """Return a template dict for the given title."""
    for tmpl in DATABASE_TEMPLATES:
        if tmpl["template_title"] == title:
            return tmpl
    return None


def get_dummy_items(title: str):
    """Return dummy items list for a template title."""
    return DUMMY_ITEMS.get(title, [])

# Example usage:
# from notion_templates import DATABASE_TEMPLATES, get_dummy_items
